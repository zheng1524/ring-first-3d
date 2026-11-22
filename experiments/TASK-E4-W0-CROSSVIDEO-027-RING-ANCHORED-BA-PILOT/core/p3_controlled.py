#!/usr/bin/env python3
"""P3: controlled Ring-anchored BA with known truth (real CAD + real W0 geometry)."""
import json, os, sys
from pathlib import Path
import numpy as np, pandas as pd, torch
from scipy.optimize import least_squares
WS = Path('/home/liu/ring_first_3d_workspace')
B = WS/'experiments/TASK-E4-W0-CROSSVIDEO-027-RING-ANCHORED-BA-PILOT'
sys.path.insert(0, str(B/'replay')); sys.path.insert(0, str(B/'core')); sys.path.insert(0, str(WS/'src'))
os.environ.update(E4_RUN_DIR=str(B/'replay'),
    RING_CAD=str(WS/'assets/retained_sources/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-HERO-BODY-ADAPT-018/inputs/G03/RING.npz'),
    RING_NORM=str(WS/'assets/retained_sources/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/FREE_VERTEX_013/inputs/G03/NORMALIZATION.json'))
from ring020_026 import RingRenderer
from se3 import exp_se3
import ba_core as BA
OUT = B/'runs/G03/CONTROLLED'; OUT.mkdir(parents=True, exist_ok=True)
views = {v['id']: v for v in json.loads((B/'replay'/'config'/'VIEWS.json').read_text())}
split = json.loads((B/'runs/G03/SPLIT.json').read_text())
rr = RingRenderer(sorted(set(split['fit4']+split['fit5'])))
K505 = np.asarray(views[split['fit5'][0]]['K'], float)
K404 = np.asarray(views[split['fit4'][0]]['K'], float)


def make_scene(nlm=8, seed=0, yaw_deg=8.0, noisy=False, wrong=0, low_par=False, sameK=True):
    rng = np.random.default_rng(seed)
    c4 = [split['fit4'][0], split['fit4'][1]]; c5 = [split['fit5'][0]]
    T4 = {c: np.asarray(views[c]['T'], float) for c in c4}
    T5 = {c: np.asarray(views[c]['T'], float) for c in c5}
    H_true = exp_se3(np.r_[[0.3, -0.2, 0.1], np.deg2rad([0.6, -0.3, yaw_deg])])
    # landmarks visible near the ring, in 005 world
    X = np.c_[rng.uniform(-9, 9, nlm), rng.uniform(-9, 9, nlm), rng.uniform(-3, 3, nlm)]
    if low_par:
        X[:] = np.c_[rng.uniform(-0.3, 0.3, nlm), rng.uniform(-0.3, 0.3, nlm), rng.uniform(30, 32, nlm)]
    obs = []
    for c in c4:
        C = H_true @ T4[c]
        for i in range(nlm):
            p, z = BA.project(X[i], C, K404)
            if z > 0: obs.append((c, i, p + (rng.normal(0, .3, 2) if noisy else 0)))
    for c in c5:
        C = T5[c]
        for i in range(nlm):
            p, z = BA.project(X[i], C, K505)
            if z > 0: obs.append((c, i, p + (rng.normal(0, .3, 2) if noisy else 0)))
    if wrong:
        idx = rng.permutation(len(obs))[:wrong]
        for k in idx:
            c, i, uv = obs[k]; obs[k] = (c, i, uv + rng.normal(0, 40, 2))
    cams = {c: ('004', T4[c]) for c in c4}; cams.update({c: ('005', T5[c]) for c in c5})
    K_of = {c: (K404 if sameK else K404*1.0) for c in c4}; K_of.update({c: (K505 if sameK else K505*1.05) for c in c5})
    rings = {}
    for c in c5:
        C = T5[c]
        ev = rr.data[c]['evidence']
        rings[c] = {'inner': ev['inner'], 'outer': ev['outer']}
    return dict(cams=cams, K_of=K_of, obs=obs, rings=rings, X=X, H=H_true, seed=seed)


def run(scene, H0=None, dx0=None, use_ring=True, release=('004',), sig=(np.deg2rad(0.5), 0.25), max_nfev=60, x_scale=None, lam_ring=1.0):
    BA.W_RING = lam_ring
    cams = scene['cams']; cids = sorted(cams)
    anchor = sorted([c for c in cids if cams[c][0] == '005'])[-1]
    released = [c for c in cids if cams[c][0] in release and c != anchor]
    sub = {c: cams[c] for c in cids}
    P = BA.Problem(sub, scene['K_of'], scene['obs'], scene['rings'] if use_ring else {}, scene['X'].copy(),
                   None, dict(sig_rot=sig[0], sig_trans=sig[1], sig_geo=50.0), anchor=('005', 0), freeze_edges=True)
    P.curves = rr.curves
    H0 = np.eye(4) if H0 is None else H0
    dx0 = {c: np.zeros(6) for c in cids} if dx0 is None else dx0
    theta0 = np.r_[np.zeros(6), np.concatenate([dx0[c] for c in P.order]), scene['X'].ravel() + 0.5]
    r0 = P.residuals(theta0, H0)
    res = least_squares(lambda t: P.residuals(t, H0), theta0, method='trf', loss='huber', f_scale=3.0,
                        x_scale=x_scale if x_scale is not None else 'jac', max_nfev=max_nfev)
    H, dx, X = P.unpack(res.x); P.H0 = H0
    # camera errors vs truth
    err = []
    for c in cids:
        C_est = BA.apply_cam(dx[c], cams[c][1])
        if cams[c][0] == '004': C_true = scene['H'] @ cams[c][1]; C_est = H @ C_est
        else: C_true = cams[c][1]
        dR = C_est[:3, :3] @ C_true[:3, :3].T
        ang = float(np.degrees(np.arccos(np.clip((np.trace(dR)-1)/2, -1, 1))))
        dt = float(np.linalg.norm(C_est[:3, 3]-C_true[:3, 3]))
        err.append(dict(cam=c, rot_deg=ang, trans_mm=dt))
    dH = H @ np.linalg.inv(scene['H'])
    H_err = dict(rot_deg=float(np.degrees(np.arccos(np.clip((np.trace(dH[:3, :3])-1)/2, -1, 1)))),
                 trans_mm=float(np.linalg.norm(dH[:3, 3])))
    lm = float(np.median(np.linalg.norm(X-scene['X'], axis=1)))
    J = res.jac.toarray() if hasattr(res.jac, 'toarray') else np.asarray(res.jac)
    s = np.linalg.svd(J, compute_uv=False)
    return dict(cams=err, H=H_err, lm_med=lm, cost0=float(res.cost*2), cost1=float(res.cost*2),
                nfev=int(res.nfev), success=bool(res.success), rank=int(np.linalg.matrix_rank(J)),
                n_params=int(J.shape[1]), cond=float(s[0]/max(s[-1], 1e-12)))


def main():
    rows = []
    scenarios = [
        ('S1_noisefree_exact', dict(noisy=False), dict(exact=True)),
        ('S2_shared_yaw', dict(yaw_deg=25.0), dict()),
        ('S3_local_rot_err', dict(), dict(video='005')),
        ('S4_local_trans_err', dict(), dict(video='004', trans=True)),
        ('S5_multi_cam_perturb', dict(noisy=True), dict(all_pert=True)),
        ('S6_low_parallax', dict(low_par=True), dict()),
        ('S7_wrong_obs', dict(noisy=True, wrong=2), dict()),
        ('S8_ring_yaw_only', dict(), dict(ring_only=True)),
        ('S9_one_side_few', dict(), dict(one_side=True)),
        ('S10_different_K', dict(sameK=False), dict()),
    ]
    for name, sc_kw, run_kw in scenarios:
        scene = make_scene(seed=3, **sc_kw)
        cids = sorted(scene['cams'])
        dx0 = {c: np.zeros(6) for c in cids}
        if run_kw.get('all_pert'):
            rng = np.random.default_rng(5)
            for c in cids:
                dx0[c] = np.r_[rng.normal(0, .2, 3), np.deg2rad(rng.normal(0, .4, 3))]
        if run_kw.get('video') == '005':
            dx0[sorted([c for c in cids if scene['cams'][c][0] == '005'])[0]] = np.r_[0, 0, 0, np.deg2rad([0.8, -0.5, 0.3])]
        if run_kw.get('video') == '004' and run_kw.get('trans'):
            dx0[sorted([c for c in cids if scene['cams'][c][0] == '004'])[0]] = np.r_[[0.4, -0.2, 0.3], 0, 0, 0]
        if run_kw.get('ring_only'):
            scene['obs'] = []
        if run_kw.get('one_side'):
            scene['obs'] = [o for o in scene['obs'] if scene['cams'][o[0]][0] == '005']
        H0 = scene['H'] if run_kw.get('exact') else np.eye(4)
        try:
            r = run(scene, H0=H0, dx0=dx0, use_ring=True)
        except Exception as ex:
            rows.append(dict(scenario=name, init='truth' if run_kw.get('exact') else 'identity', error=f'{type(ex).__name__}: {ex}')); continue
        cam_r = max(x['rot_deg'] for x in r['cams']); cam_t = max(x['trans_mm'] for x in r['cams'])
        rows.append(dict(scenario=name, init='truth' if run_kw.get('exact') else 'identity', cam_rot_max_deg=cam_r, cam_trans_max_mm=cam_t,
                         H_rot_deg=r['H']['rot_deg'], H_trans_mm=r['H']['trans_mm'],
                         lm_med_mm=r['lm_med'], nfev=r['nfev'], success=r['success'], rank=r['rank'],
                         n_params=r['n_params'], cond=r['cond'], n_obs=len(scene['obs'])))
        print('SC', name, round(cam_r, 3), round(cam_t, 3), round(r['H']['rot_deg'], 3), round(r['H']['trans_mm'], 3), round(r['lm_med'], 3), r['nfev'], flush=True)
    df = pd.DataFrame(rows); df.to_csv(OUT/'CONTROLLED_BA_RESULTS.csv', index=False)


if __name__ == '__main__':
    main()
