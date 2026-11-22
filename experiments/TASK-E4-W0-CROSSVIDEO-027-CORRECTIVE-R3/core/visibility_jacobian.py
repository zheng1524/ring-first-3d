#!/usr/bin/env python3
"""P3 visibility-association audit + P4 Jacobian / direction-derivative checks (H-only frame)."""
import json, os, sys
from pathlib import Path
import numpy as np, pandas as pd
WS = Path('/home/liu/ring_first_3d_workspace')
R3 = WS/'experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R3'
sys.path.insert(0, str(R3/'core')); sys.path.insert(0, str(R3/'replay')); sys.path.insert(0, str(WS/'src'))
os.environ.update(E4_RUN_DIR=str(R3/'replay'),
    RING_CAD=str(WS/'assets/retained_sources/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-HERO-BODY-ADAPT-018/inputs/G03/RING.npz'),
    RING_NORM=str(WS/'assets/retained_sources/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/FREE_VERTEX_013/inputs/G03/NORMALIZATION.json'))
import r2_synth as S
import r3_run as R
import ring_energy as RE
import ba_core_r2 as BA
from ring020_026 import RingRenderer
from se3 import exp_se3
OUT = R3/'runs/controlled'; rr = RingRenderer(sorted(S.C4 + S.C5))


def edge_set(C, c):
    K = np.asarray(S.views[c]['K'], float)
    seg = rr.curves.segments(np.asarray(C, float), K)
    return {k: np.asarray(seg[k], int).reshape(-1, 2) for k in ('inner', 'outer')}


def main():
    sc = S.build_scene(seed=0, H_rot_deg=(0.7, -0.4, 12.0))
    ring_obs = S.ring_observations(sc, rr)
    ring_obs = {c: {k: (v[::4] if k == 'mid' else v[::2]) for k, v in d.items()} for c, d in ring_obs.items()}
    obs = S.rgb_observations(sc)
    cams_world0 = {c: np.asarray(T, float) for c, (v, T) in sc['cams'].items()}
    X_init, ids = S.triangulate([o for o in obs if sc['cams'][o[0]][0] == '005'],
                                {c: ('x', sc['C_gt'][c]) for c in S.C5}, sc['K_of'], 12)
    # visibility audit: edges chosen from GT / 3deg / 12deg init, Ring energy always measured at GT camera
    rows = []
    for c in S.C4:
        T0 = np.asarray(sc['cams'][c][1], float)
        for label, dH in (('GT', np.eye(4)), ('3deg', exp_se3(np.r_[np.zeros(3), np.deg2rad([0, 0, 3.0])])),
                          ('12deg', exp_se3(np.r_[np.zeros(3), np.deg2rad([0, 0, 12.0])]))):
            C_edge = dH @ (sc['H'] @ T0)          # camera used ONLY to select edges (diagnostic)
            g = {}
            for key, blk, w in (('inner', 'I', .35), ('outer', 'O', .35)):
                g['V_' + key] = np.asarray(rr.curves.V, float)
                g['E_' + key] = edge_set(C_edge, c)[key]
            g['V_mid'] = np.vstack([np.asarray(rr.curves.mid, float), np.asarray(rr.curves.mid, float)[:1]])
            g['E_mid'] = np.c_[np.arange(len(g['V_mid'])-1), np.arange(1, len(g['V_mid']))]
            Ctrue = sc['C_gt'][c]
            row = dict(cam=c, edge_source=label, n_inner=len(g['E_inner']), n_outer=len(g['E_outer']))
            for key, blk, w in (('inner', 'I', .35), ('outer', 'O', .35), ('mid', 'C', .05)):
                d = BA.poly_dist(Ctrue, sc['K_of'][c], g['V_' + key], g['E_' + key],
                                 ring_obs[c][key] if key != 'mid' else ring_obs[c]['mid'])
                row['E_' + blk] = float(RE.rho(d/3).mean()) if len(d) else None
                row['n_' + blk] = int(len(d))
            rows.append(row)
    df = pd.DataFrame(rows); df.to_csv(OUT/'VISIBILITY_ASSOCIATION.csv', index=False)
    # edge-set overlap between GT and 3/12 deg
    ov = []
    for c in S.C4:
        T0 = np.asarray(sc['cams'][c][1], float)
        eG = edge_set(sc['H'] @ T0, c)
        for label, dH in (('3deg', exp_se3(np.r_[np.zeros(3), np.deg2rad([0, 0, 3.0])])),
                          ('12deg', exp_se3(np.r_[np.zeros(3), np.deg2rad([0, 0, 12.0])]))):
            eX = edge_set(dH @ (sc['H'] @ T0), c)
            for k in ('inner', 'outer'):
                a = {tuple(x) for x in eG[k]}; b = {tuple(x) for x in eX[k]}
                ov.append(dict(cam=c, source=label, kind=k, n_gt=len(a), n_src=len(b),
                               overlap=len(a & b), jaccard=len(a & b)/max(len(a | b), 1)))
    pd.DataFrame(ov).to_csv(OUT/'VISIBILITY_EDGE_OVERLAP.csv', index=False)
    # Jacobian / direction-derivative for H-only residual at GT
    P = BA.BAProblemR2(sc['cams'], sc['K_of'], obs, ring_obs, X_init,
                       R.camvar.CameraVariables(sc['cams'], S.C4[0], []),
                       R.geometry({c: (sc['H'] @ np.asarray(sc['cams'][c][1], float)) if sc['cams'][c][0] == '004'
                                   else np.asarray(sc['cams'][c][1], float) for c in sc['cams']}, rr),
                       lam_ring=1.0)
    def f(t):
        blocks = R.res_blocks(P, P.cv, exp_se3(t[:6]) @ sc['H'], X_init, {c: np.zeros(6) for c in P.cams})
        blocks['rgb'] = [np.concatenate(blocks['rgb'])] if blocks['rgb'] else []
        return R.res_vector(blocks, 'huber')
    h = 1e-5
    t0 = np.zeros(6); f0 = f(t0)
    J = np.zeros((len(f0), 6))
    for k in range(6):
        tp = t0.copy(); tp[k] += h; tm = t0.copy(); tm[k] -= h
        J[:, k] = (f(tp)-f(tm))/(2*h)
    # direction derivative: random directions, compare FD of f vs J@d
    rng = np.random.default_rng(0); dir_err = []
    for _ in range(5):
        d = rng.normal(size=6); d /= np.linalg.norm(d)
        fd = (f(t0+1e-4*d)-f(t0-1e-4*d))/2e-4
        dir_err.append(float(np.linalg.norm(fd - J @ d)/max(np.linalg.norm(fd), 1e-12)))
    sv = np.linalg.svd(J, compute_uv=False)
    jac = dict(n_res=len(f0), n_params=6, rank=int(np.linalg.matrix_rank(J)),
               smin=float(sv[-1]), smax=float(sv[0]), cond=float(sv[0]/max(sv[-1], 1e-30)),
               direction_derivative_rel_err_max=max(dir_err), rms_at_gt=float(np.sqrt((f0**2).mean())),
               grad_norm_at_gt=float(np.linalg.norm(J.T @ f0)))
    (OUT/'JACOBIAN_H_ONLY.json').write_text(json.dumps(jac, indent=1))
    print(json.dumps(dict(jacobian=jac), indent=1))
    print(df.to_string(index=False))


if __name__ == '__main__':
    main()
