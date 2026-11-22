#!/usr/bin/env python3
"""R2 graded controlled BA levels 0-5 on the synthetic Ring+RGB scene."""
import argparse, json, os, sys
from pathlib import Path
import numpy as np, pandas as pd
from scipy.optimize import least_squares
WS = Path('/home/liu/ring_first_3d_workspace')
R = WS/'experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R2'
sys.path.insert(0, str(R/'core')); sys.path.insert(0, str(R/'replay')); sys.path.insert(0, str(WS/'src'))
os.environ.update(E4_RUN_DIR=str(R/'replay'),
    RING_CAD=str(WS/'assets/retained_sources/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-HERO-BODY-ADAPT-018/inputs/G03/RING.npz'),
    RING_NORM=str(WS/'assets/retained_sources/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/FREE_VERTEX_013/inputs/G03/NORMALIZATION.json'))
import r2_synth as S
import camvar, ba_core_r2 as BA
from ring020_026 import RingRenderer
from se3 import exp_se3
OUT = R/'runs/CONTROLLED'; OUT.mkdir(parents=True, exist_ok=True)


def geometry_from(cams_init, rr, cgt_video):
    """CAD edge index sets computed from the INITIAL cameras (never from GT)."""
    g = {}
    mid = np.asarray(rr.curves.mid, float)
    Vmid = np.vstack([mid, mid[:1]])
    Emid = np.c_[np.arange(len(Vmid)-1), np.arange(1, len(Vmid))]
    for c, (video, T) in cams_init.items():
        C = np.asarray(cgt_video[c], float)
        K = np.asarray(S.views[c]['K'], float)
        seg = rr.curves.segments(C, K)
        gi = {}
        for key in ('inner', 'outer'):
            e = np.asarray(seg[key], int).reshape(-1, 2)
            gi['V_' + key] = np.asarray(rr.curves.V, float); gi['E_' + key] = e
        gi['V_mid'] = Vmid; gi['E_mid'] = Emid
        g[c] = gi
    return g


def run(name, level, scene, cams_init, H0, released, anchor, rr, obs, ring_obs, X_init, gt_eval,
        max_nfev=40, use_centerline=True, x_scale='jac'):
    cv = camvar.CameraVariables(cams_init, anchor, released)
    g = geometry_from(cams_init, rr, {c: (exp_se3(np.zeros(6)) @ np.asarray(cams_init[c][1], float)) for c in cams_init})
    # 004 initial cameras in the 005 world use H0
    cworld = {}
    for c, (v, T) in cams_init.items():
        cworld[c] = H0 @ np.asarray(T, float) if v == '004' else np.asarray(T, float)
    g = geometry_from(cams_init, rr, cworld)
    P = BA.BAProblemR2(cams_init, {c: np.asarray(S.views[c]['K'], float) for c in cams_init}, obs, ring_obs,
                       X_init, cv, g, lam_ring=1.0, use_centerline=use_centerline)
    th0 = np.r_[np.zeros(6), np.zeros(6*len(cv.released)), X_init.ravel()]
    e0 = P.energies(th0, H0)
    res = least_squares(lambda t: P.residuals(t, H0), th0, method='trf', loss='linear',
                        x_scale=x_scale, max_nfev=max_nfev, ftol=1e-12, xtol=1e-12, gtol=1e-12)
    e1 = P.energies(res.x, H0)
    H, dx, X = cv.unpack(res.x, H0, len(X_init))
    ev = dict(level=level, name=name, success=bool(res.success), status=int(res.status), nfev=int(res.nfev),
              cost0=float(e0['total']), cost1=float(e1['total']),
              rgb0=float(e0.get('rgb', 0)), rgb1=float(e1.get('rgb', 0)),
              I0=float(e0.get('ring_I', 0)), I1=float(e1.get('ring_I', 0)),
              C0=float(e0.get('ring_C', 0)), C1=float(e1.get('ring_C', 0)),
              O0=float(e0.get('ring_O', 0)), O1=float(e1.get('ring_O', 0)),
              prior1=float(e1.get('prior', 0)), geo1=float(e1.get('geo', 0)),
              n_obs=len(obs), n_lm=len(X_init))
    if gt_eval is not None:
        Hg = gt_eval['H']; Xg = gt_eval['X']; gt_cams = gt_eval['C_gt']
        dH = H @ np.linalg.inv(Hg)
        ev['H_rot'] = float(np.degrees(np.arccos(np.clip((np.trace(dH[:3, :3])-1)/2, -1, 1))))
        ev['H_trans'] = float(np.linalg.norm(dH[:3, 3]))
        errs = []
        for i, c in enumerate(cams_init):
            Cest = cv.unpack(res.x, H0, len(X_init))[2]  # unused
            Cc = exp_se3(dx[c]) @ np.asarray(cams_init[c][1], float)
            if cams_init[c][0] == '004': Cc = H @ Cc
            Ct = np.asarray(gt_cams[c], float)
            dR = Cc[:3, :3] @ Ct[:3, :3].T
            errs.append(dict(cam=c, rot=float(np.degrees(np.arccos(np.clip((np.trace(dR)-1)/2, -1, 1)))),
                             trans=float(np.linalg.norm(Cc[:3, 3]-Ct[:3, 3]))))
        ev['cam_rot_max'] = max(e['rot'] for e in errs); ev['cam_trans_max'] = max(e['trans'] for e in errs)
        ev['lm_med'] = float(np.median(np.linalg.norm(X-Xg[:len(X)], axis=1))) if len(X) == len(Xg) else None
        ev['cams'] = errs
    J = res.jac.toarray() if hasattr(res.jac, 'toarray') else np.asarray(res.jac)
    ev['rank'] = int(np.linalg.matrix_rank(J)); ev['n_params'] = int(J.shape[1])
    return ev, H, dx, X


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--levels', default='0,1,2,3,4,5')
    ap.add_argument('--yaw', type=float, default=12.0)
    a = ap.parse_args(); want = [int(x) for x in a.levels.split(',')]
    rr = RingRenderer(sorted(S.C4 + S.C5))
    # controlled-test speed: subsample Ring observations 1/4 (documented; same geometry, fewer points)
    _ring_obs = S.ring_observations
    def ring_observations(scene, r):
        o = _ring_obs(scene, r)
        return {c: {k: (v[::4] if k == 'mid' else v[::2]) for k, v in d.items()} for c, d in o.items()}
    S.ring_observations = ring_observations
    rows = []
    if 0 in want:
        sc = S.build_scene(seed=0)
        ring_obs = S.ring_observations(sc, rr)
        obs = S.rgb_observations(sc)
        cv = camvar.CameraVariables(sc['cams'], S.C4[0], [S.C4[1], S.C4[2]])
        g = geometry_from(sc['cams'], rr, sc['C_gt'])
        P = BA.BAProblemR2(sc['cams'], sc['K_of'], obs, ring_obs, sc['X'], cv, g, use_centerline=True)
        th = np.r_[np.zeros(6), np.zeros(6*len(cv.released)), sc['X'].ravel()]
        e = P.energies(th, sc['H'])
        # GT residual: H must be H_gt for 004 cameras; camvar uses H0
        P2 = BA.BAProblemR2(sc['cams'], sc['K_of'], obs, ring_obs, sc['X'], cv, g, use_centerline=True)
        res_gt = P2.residuals(th, sc['H'])
        rows.append(dict(level=0, name='L0_residual_at_GT', rgb=e.get('rgb', 0), I=e.get('ring_I', 0),
                         C=e.get('ring_C', 0), O=e.get('ring_O', 0), total=e['total'],
                         residual_max=float(np.abs(res_gt).max()), n_res=len(res_gt)))
        print('L0', rows[-1], flush=True)
    if 1 in want:
        sc = S.build_scene(seed=0); obs = S.rgb_observations(sc)
        gt_cams = {c: ('x', sc['C_gt'][c]) for c in sc['cams']}
        X, ids = S.triangulate(obs, gt_cams, sc['K_of'], 12)
        ring_obs = S.ring_observations(sc, rr)
        ev, H, dx, Xf = run('L1_correct_init', 1, sc, sc['cams'], sc['H'], [S.C4[1], S.C4[2]], S.C4[0], rr,
                            obs, ring_obs, X, sc)
        ev['X_init_err'] = float(np.median(np.linalg.norm(X-sc['X'][:len(X)], axis=1)))
        rows.append(ev); print('L1', {k: ev[k] for k in ('cam_rot_max','H_rot','lm_med','success','nfev')}, flush=True)
    if 2 in want:
        sc = S.build_scene(seed=0, H_rot_deg=(0.7, -0.4, a.yaw)); obs = S.rgb_observations(sc)
        ring_obs = S.ring_observations(sc, rr)
        X, ids = S.triangulate(obs, sc['cams'], sc['K_of'], 12)
        ev, H, dx, Xf = run('L2_H_only', 2, sc, sc['cams'], np.eye(4), [], S.C4[0], rr, obs, ring_obs, X, sc)
        rows.append(ev); print('L2', {k: ev[k] for k in ('H_rot','H_trans','lm_med','success','nfev')}, flush=True)
    if 3 in want:
        sc = S.build_scene(seed=0); obs = S.rgb_observations(sc)
        ring_obs = S.ring_observations(sc, rr)
        X, ids = S.triangulate(obs, sc['cams'], sc['K_of'], 12)
        ev, H, dx, Xf = run('L3_one_camera', 3, sc, sc['cams'], sc['H'], [S.C4[1], S.C4[2]], S.C4[0], rr,
                            obs, ring_obs, X, sc)
        rows.append(ev); print('L3', {k: ev[k] for k in ('cam_rot_max','H_rot','lm_med','success','nfev')}, flush=True)
    if 4 in want:
        sc = S.build_scene(seed=0); obs = S.rgb_observations(sc)
        ring_obs = S.ring_observations(sc, rr)
        X, ids = S.triangulate(obs, sc['cams'], sc['K_of'], 12)
        ev, H, dx, Xf = run('L4_multi_camera', 4, sc, sc['cams'], sc['H'], [S.C4[1], S.C4[2]], S.C4[0], rr,
                            obs, ring_obs, X, sc)
        rows.append(ev); print('L4', {k: ev[k] for k in ('cam_rot_max','H_rot','lm_med','success','nfev')}, flush=True)
    if 5 in want:
        for tag, kw in (('noise', dict(noise=0.3)), ('outliers', dict(noise=0.3, wrong=2)),
                        ('Kdiff', dict(Kdiff=True))):
            sc = S.build_scene(seed=0, **({'Kdiff': True} if tag == 'Kdiff' else {}))
            obs = S.rgb_observations(sc, **kw)
            ring_obs = S.ring_observations(sc, rr)
            X, ids = S.triangulate(obs, sc['cams'], sc['K_of'], 12)
            ev, H, dx, Xf = run('L5_' + tag, 5, sc, sc['cams'], sc['H'], [S.C4[1], S.C4[2]], S.C4[0], rr,
                                obs, ring_obs, X, sc)
            rows.append(ev); print('L5', tag, {k: ev[k] for k in ('cam_rot_max','H_rot','lm_med','success')}, flush=True)
    pd.DataFrame([{k: v for k, v in r.items() if k != 'cams'} for r in rows]).to_csv(OUT/'LEVEL_RESULTS.csv', index=False)


if __name__ == '__main__':
    main()
