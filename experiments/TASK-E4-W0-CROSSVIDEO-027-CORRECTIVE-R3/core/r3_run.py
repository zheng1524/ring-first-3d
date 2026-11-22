#!/usr/bin/env python3
"""R3 controlled BA: true H-only (6 params), progressive, joint; per-run directories; angle sweep.

Every run writes runs/controlled/<tag>/ with config, init/final H, X, cameras, optimizer state, metrics.
GT is used ONLY to synthesise observations and to score the final result.
"""
import argparse, json, os, sys, time
from pathlib import Path
import numpy as np, pandas as pd
from scipy.optimize import least_squares
WS = Path('/home/liu/ring_first_3d_workspace')
R3 = WS/'experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R3'
sys.path.insert(0, str(R3/'core')); sys.path.insert(0, str(R3/'replay')); sys.path.insert(0, str(WS/'src'))
os.environ.update(E4_RUN_DIR=str(R3/'replay'),
    RING_CAD=str(WS/'assets/retained_sources/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-HERO-BODY-ADAPT-018/inputs/G03/RING.npz'),
    RING_NORM=str(WS/'assets/retained_sources/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/FREE_VERTEX_013/inputs/G03/NORMALIZATION.json'))
import r2_synth as S
import ring_energy as RE
import camvar, ba_core_r2 as BA
from ring020_026 import RingRenderer
from se3 import exp_se3
RING_W = {'I': 0.35, 'C': 0.05, 'O': 0.35}


def geometry(cams_init_cworld, rr):
    g = {}
    mid = np.asarray(rr.curves.mid, float); Vm = np.vstack([mid, mid[:1]])
    Em = np.c_[np.arange(len(Vm)-1), np.arange(1, len(Vm))]
    for c, C in cams_init_cworld.items():
        K = np.asarray(S.views[c]['K'], float)
        seg = rr.curves.segments(np.asarray(C, float), K)
        for key in ('inner', 'outer'):
            g.setdefault(c, {})['V_' + key] = np.asarray(rr.curves.V, float)
            g[c]['E_' + key] = np.asarray(seg[key], int).reshape(-1, 2)
        g[c]['V_mid'] = Vm; g[c]['E_mid'] = Em
    return g


def res_blocks(P, camvars, H, X, dx):
    """shared residual builder for H-only and joint (P = BAProblemR2)"""
    blocks = {'rgb': [], 'I': [], 'C': [], 'O': []}
    C = {}
    for c in P.cams:
        Cc = exp_se3(np.asarray(dx[c], float)) @ np.asarray(P.cams[c][1], float)
        if P.cams[c][0] == '004': Cc = H @ Cc
        C[c] = Cc
    for cid, li, uv in P.obs:
        p, z = BA.project(X[li], C[cid], P.K_of[cid])
        blocks['rgb'].append(p - np.asarray(uv, float))
    for cid, ro in P.ring_obs.items():
        g = P.geom[cid]
        for key, blk, w in (('inner', 'I', RING_W['I']), ('outer', 'O', RING_W['O']), ('mid', 'C', RING_W['C'])):
            d = BA.poly_dist(C[cid], P.K_of[cid], g['V_' + key], g['E_' + key], ro.get(key, np.zeros((0, 2))))
            if len(d): blocks[blk].append(RE.ring_residuals(d, P.lam, w))
    return blocks


def res_vector(blocks, rgb_mode='huber'):
    out = []
    if blocks['rgb']:
        r = np.concatenate(blocks['rgb']).reshape(-1, 2)
        if rgb_mode == 'squared':
            out.append(r.ravel()/3.0)
        elif rgb_mode == 'huber':
            out.append(np.sqrt(2.0*RE.rho(np.linalg.norm(r, axis=1)/3.0)))
        elif rgb_mode == 'dir2d':
            e = r/3.0; s = np.linalg.norm(e, axis=1)
            f = np.where(s <= 1.0, 1.0, np.sqrt(2.0*RE.rho(s))/np.maximum(s, 1e-12))
            out.append((e*f[:, None]).ravel())
        else:
            raise ValueError(rgb_mode)
    for k in ('I', 'C', 'O'):
        if blocks.get(k): out.append(np.concatenate(blocks[k]))
    return np.concatenate(out) if out else np.zeros(0)


def energies(blocks, rgb_mode='huber'):
    e = {}
    if blocks['rgb']:
        r = np.concatenate(blocks['rgb']).reshape(-1, 2)
        e['rgb'] = float(0.5*(res_vector({'rgb': [r]}, rgb_mode)[0]**2).sum())
        e['rgb_median'] = float(np.median(np.linalg.norm(r, axis=1)))
    for k in ('I', 'C', 'O'):
        e['ring_' + k] = float(0.5*(np.concatenate(blocks[k])**2).sum()) if blocks.get(k) else 0.0
    e['ring_total'] = e.get('ring_I', 0)+e.get('ring_C', 0)+e.get('ring_O', 0)
    e['total'] = e.get('rgb', 0)+e['ring_total']
    return e


def se3_err(A, B):
    d = A @ np.linalg.inv(B)
    return float(np.degrees(np.arccos(np.clip((np.trace(d[:3, :3])-1)/2, -1, 1)))), float(np.linalg.norm(d[:3, 3]))


def setup(scene, rr, ring_obs, obs, X_init, cams_world, released, anchor):
    cv = camvar.CameraVariables(scene['cams'], anchor, released)
    P = BA.BAProblemR2(scene['cams'], scene['K_of'], obs, ring_obs, X_init, cv,
                       geometry(cams_world, rr), lam_ring=1.0, use_centerline=True)
    return P, cv


def solve(P, cv, H0, X_fixed, mode, rgb_mode='huber', max_nfev=200, x_scale='jac', tol=1e-10):
    """mode=='h_only': theta=[dH(6)] with X frozen; mode=='joint': theta=[dH, dl, dX]."""
    t0 = time.time()
    if mode == 'h_only':
        def fun(t):
            blocks = res_blocks(P, cv, exp_se3(t[:6]) @ H0, X_fixed, {c: np.zeros(6) for c in P.cams})
            blocks['rgb'] = [np.concatenate(blocks['rgb'])] if blocks['rgb'] else []
            return res_vector(blocks, rgb_mode)
        res = least_squares(fun, np.zeros(6), method='trf', loss='linear', x_scale=x_scale,
                            max_nfev=max_nfev, ftol=tol, xtol=tol, gtol=tol)
        H = exp_se3(res.x) @ H0; X = X_fixed
        n_params = 6
    else:
        def fun(t):
            return P.residuals(t, H0)
        th0 = np.r_[np.zeros(6), np.zeros(6*len(cv.released)), X_fixed.ravel()]
        res = least_squares(fun, th0, method='trf', loss='linear', x_scale=x_scale,
                            max_nfev=max_nfev, ftol=tol, xtol=tol, gtol=tol)
        H, dx, X = cv.unpack(res.x, H0, len(X_fixed))
        n_params = len(res.x)
    J = res.jac.toarray() if hasattr(res.jac, 'toarray') else np.asarray(res.jac)
    sv = np.linalg.svd(J, compute_uv=False)
    st = dict(mode=mode, rgb_mode=rgb_mode, success=bool(res.success), status=int(res.status),
              message=str(res.message), nfev=int(res.nfev), njev=int(res.njev),
              cost=float(res.cost), optimality=float(getattr(res, 'optimality', np.nan)),
              rank=int(np.linalg.matrix_rank(J)), n_params=int(n_params),
              cond=float(sv[0]/max(sv[-1], 1e-30)), seconds=round(time.time()-t0, 1))
    return H, X, st


def run_case(tag, yaw, mode, rgb_mode='huber', max_nfev=200, nlm=12, use_005_only_init=True,
             ring_subsample=True, coarse=None, progressive=False):
    out = R3/'runs/controlled'/tag; out.mkdir(parents=True, exist_ok=True)
    rr = RingRenderer(sorted(S.C4 + S.C5))
    sc = S.build_scene(seed=0, nlm=nlm, H_rot_deg=(0.7, -0.4, yaw))
    ring_obs = S.ring_observations(sc, rr)
    if ring_subsample:
        ring_obs = {c: {k: (v[::4] if k == 'mid' else v[::2]) for k, v in d.items()} for c, d in ring_obs.items()}
    obs = S.rgb_observations(sc)
    # initial estimate: 005-only triangulation (NO GT landmarks, NO H)
    cams_world0 = {}
    for c, (v, T) in sc['cams'].items():
        cams_world0[c] = np.asarray(T, float) if v == '005' else np.asarray(T, float)   # H0 = I
    X_init, ids = S.triangulate([o for o in obs if o[2] is not None and sc['cams'][o[0]][0] == '005'],
                                {c: ('x', cams_world0[c]) for c in S.C5}, sc['K_of'], nlm)
    # 004 observations are expressed in the 005 world only through H; initial X from 005 alone
    P, cv = setup(sc, rr, ring_obs, obs, X_init, cams_world0, [], S.C4[0])
    H0 = np.eye(4)
    e_init = energies(res_blocks(P, cv, H0, X_init, {c: np.zeros(6) for c in P.cams}), rgb_mode)
    if coarse:
        # frozen coarse-to-fine: run at f_scale_c, then restart at target scale
        pass
    st_pre = None
    if progressive:
        H1, X1, st_pre = solve(P, cv, H0, X_init, 'h_only', rgb_mode, max_nfev)
        H, X, st = solve(P, cv, H1, X_init, 'joint', rgb_mode, max_nfev)
        st['stage1'] = st_pre
    else:
        H, X, st = solve(P, cv, H0, X_init, mode, rgb_mode, max_nfev)
    e_fin = energies(res_blocks(P, cv, H, X, {c: np.zeros(6) for c in P.cams}), rgb_mode)
    H_rot, H_tr = se3_err(H, sc['H'])
    H0_rot, H0_tr = se3_err(H0, sc['H'])
    lm = float(np.median(np.linalg.norm(X - sc['X'][:len(X)], axis=1))) if len(X) == len(sc['X']) else None
    meta = dict(tag=tag, yaw_init_deg=yaw, mode=mode, rgb_mode=rgb_mode, nlm=len(X_init),
                H_init_rot=H0_rot, H_init_trans=H0_tr, H_rot=H_rot, H_trans=H_tr,
                lm_med=lm, n_obs=len(obs), n_ring={k: sum(len(x) for x in [v.get(k, np.zeros((0, 2)))]) for k, v in ring_obs.items()},
                **{f'e0_{k}': v for k, v in e_init.items()}, **{f'e1_{k}': v for k, v in e_fin.items()})
    meta['progressive'] = bool(progressive)
    meta['stage1'] = st.get('stage1')
    (out/'METRICS.json').write_text(json.dumps({**meta, **st}, indent=1))
    np.savez(out/'RESULT.npz', H_init=H0, H=H, X_init=X_init, X=X, ids=ids,
             cams=np.array([str(sc['cams'][c][1].tolist()) for c in P.cams], dtype=object) if False else np.zeros(1))
    json.dump(dict(tag=tag, yaw=yaw, mode=mode, rgb_mode=rgb_mode, max_nfev=max_nfev,
                   seed=0, nlm=nlm, ring_subsample=ring_subsample, H_gt=sc['H'].tolist()),
              open(out/'CONFIG.json', 'w'), indent=1)
    return {**meta, **st}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--what', default='h_only_sweep')
    ap.add_argument('--yaws', default='0,1,3,6,9,12,18')
    ap.add_argument('--mode', default='h_only')
    ap.add_argument('--rgb-mode', default='huber')
    ap.add_argument('--max-nfev', type=int, default=80)
    ap.add_argument('--tag-prefix', default='')
    ap.add_argument('--progressive', action='store_true')
    a = ap.parse_args()
    rows = []
    if a.what == 'h_only_sweep':
        for y in [float(x) for x in a.yaws.split(',')]:
            rows.append(run_case(f'{a.tag_prefix}Honly_yaw{int(y):02d}', y, 'h_only', a.rgb_mode, a.max_nfev,
                                 coarse='coarse' if a.rgb_mode == 'coarse' else None))
            print('RUN', rows[-1]['tag'], round(rows[-1]['H_init_rot'], 2), '->', round(rows[-1]['H_rot'], 4),
                  'success', rows[-1]['success'], rows[-1]['nfev'], flush=True)
    elif a.what == 'compare':
        plan = [(12.0, 'joint', 'huber'), (12.0, 'prog', 'huber'), (12.0, 'joint', 'squared'),
                (12.0, 'prog', 'squared')]
        for y, mode, rm in plan:
            prog = (mode == 'prog')
            tag = f'{rm}_{"progressive" if prog else mode}_yaw{int(y):02d}'
            rows.append(run_case(tag, y, 'joint' if prog else mode, rm, a.max_nfev, progressive=prog))
            print('RUN', rows[-1]['tag'], round(rows[-1]['H_rot'], 4), round(rows[-1].get('lm_med') or 0, 3),
                  rows[-1]['success'], rows[-1]['nfev'], flush=True)
    elif a.what == 'repro':
        rows.append(run_case('R3_repro_h_only_yaw03', 3.0, 'h_only', 'huber', 40))
        rows.append(run_case('R3_repro_h_only_yaw12', 12.0, 'h_only', 'huber', 40))
    pd.DataFrame(rows).to_csv(R3/'runs/controlled'/f'SUMMARY_{a.what}.csv', index=False)


if __name__ == '__main__':
    main()
