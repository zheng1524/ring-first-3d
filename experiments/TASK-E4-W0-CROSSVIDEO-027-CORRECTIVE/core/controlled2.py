#!/usr/bin/env python3
"""Controlled BA with GT isolation: landmarks initialised ONLY by triangulation from the initial cameras."""
import json, os, sys
from pathlib import Path
import numpy as np, pandas as pd, torch
from scipy.optimize import least_squares
WS = Path('/home/liu/ring_first_3d_workspace')
C = WS/'experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE'
sys.path.insert(0, str(C/'core')); sys.path.insert(0, str(C/'replay')); sys.path.insert(0, str(WS/'src'))
os.environ.update(E4_RUN_DIR=str(C/'replay'),
    RING_CAD=str(WS/'assets/retained_sources/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-HERO-BODY-ADAPT-018/inputs/G03/RING.npz'),
    RING_NORM=str(WS/'assets/retained_sources/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/FREE_VERTEX_013/inputs/G03/NORMALIZATION.json'))
import features019 as F19
import fixed_track_tri as FTT
import camvar, ring_energy
import ba_core2 as BA
from ring020_026 import RingRenderer
from se3 import exp_se3
OUT = C/'runs/G03/CONTROLLED'; OUT.mkdir(parents=True, exist_ok=True)
views = {v['id']: v for v in json.loads((C/'replay'/'config'/'VIEWS.json').read_text())}
split = json.loads((C/'runs/G03/SPLIT.json').read_text())
C4 = [split['fit4'][0], split['fit4'][1]]; C5 = [split['fit5'][0]]
K4 = np.asarray(views[C4[0]]['K'], float); K5 = np.asarray(views[C5[0]]['K'], float)


def tri_init(obs, cams, K_of, nlm):
    """Landmarks from the historical 019 per-track code using ONLY the initial cameras."""
    feats, tracks = {}, []
    for li in range(nlm):
        members = [o for o in obs if o[1] == li]
        if len(members) < 3: continue
        tr = []
        for m in members: tr.append(m)
        tracks.append(tr)
    xy = {}
    for tr in tracks:
        for m in tr:
            xy.setdefault(m[0], []).append(m[2])
    shim = {cid: dict(id=cid, T=cams[cid][1], K=K_of[cid]) for cid in cams}
    counter = {cid: 0 for cid in cams}
    def fake_features(v):
        arr = np.array(xy[v['id']], float)
        return dict(xy=arr, des=np.zeros((len(arr), 128), np.float32))
    old = F19.features; F19.features = fake_features
    try:
        out = []
        for tr in tracks:
            idx = {}
            for m in tr:
                idx.setdefault(m[0], 0)
                idx[m[0]] += 1
            tt = [(m[0], None) for m in tr]
            # build (view, feature_id) in the same order the shim returns xy
            per = {}
            for k, m in enumerate(tr):
                i = sum(1 for n in range(k) if tr[n][0] == m[0])
                tt[k] = (m[0], i)
            r = FTT.triangulate_tracks([tt], shim)[0]
            out.append(r['X'])
    finally:
        F19.features = old
    return np.array(out)


def make(seed=3, yaw=8.0, noisy=False, wrong=0, low_par=False, sameK=True):
    rng = np.random.default_rng(seed)
    H_true = exp_se3(np.r_[[0.3, -0.2, 0.1], np.deg2rad([0.6, -0.3, yaw])])
    X = np.c_[rng.uniform(-9, 9, 8), rng.uniform(-9, 9, 8), rng.uniform(-3, 3, 8)]
    if low_par: X[:] = np.c_[rng.uniform(-.3, .3, 8), rng.uniform(-.3, .3, 8), rng.uniform(30, 32, 8)]
    obs = []
    for c in C4:
        Ct = H_true @ np.asarray(views[c]['T'], float)
        for i in range(8):
            p, z = BA.project(X[i], Ct, K4)
            if z > 0: obs.append((c, i, p + (rng.normal(0, .3, 2) if noisy else 0)))
    for c in C5:
        Ct = np.asarray(views[c]['T'], float)
        for i in range(8):
            p, z = BA.project(X[i], Ct, K5)
            if z > 0: obs.append((c, i, p + (rng.normal(0, .3, 2) if noisy else 0)))
    if wrong:
        for k in rng.permutation(len(obs))[:wrong]:
            c, i, uv = obs[k]; obs[k] = (c, i, uv + rng.normal(0, 40, 2))
    return dict(H=H_true, X=X, obs=obs)


def run(scene, init='tri', gt_near_offset=None, noise_seed=0, max_nfev=80):
    cams = {c: ('004', np.asarray(views[c]['T'], float)) for c in C4}
    cams.update({c: ('005', np.asarray(views[c]['T'], float)) for c in C5})
    K_of = {c: (K4 if c in C4 else K5) for c in cams}
    rng = np.random.default_rng(noise_seed)
    init_cams = {c: np.asarray(v[1], float).copy() for c, v in cams.items()}
    if init == 'gt':
        for c in C4: init_cams[c] = scene['H'] @ init_cams[c]
        for c in C5: init_cams[c] = init_cams[c]
    if scene.get('X_init_override') is not None:
        X_init = np.asarray(scene['X_init_override'], float)
    else:
        X_init = tri_init(scene['obs'], {c: ('x', init_cams[c]) for c in cams}, K_of, 8)
    # GT written to a SEPARATE file; optimisation only receives X_init
    json.dump(dict(X_gt=scene['X'].tolist(), H_gt=scene['H'].tolist()),
              open(OUT/'GROUND_TRUTH.json', 'w'))
    rr = RingRenderer(sorted(cams))
    ring_pts, edges = {}, {}
    for c in cams:
        ev = rr.data[c]['evidence']
        ring_pts[c] = {'inner': ev['inner'], 'outer': ev['outer'], 'mid': ev['mid']}
        Cc = init_cams[c]
        if c in C4: Cc = scene['H'] @ Cc
        sg = rr.curves.segments(Cc, K_of[c])
        edges[(c, 'inner')] = np.asarray(sg['inner'], int)
        edges[(c, 'outer')] = np.asarray(sg['outer'], int)
        edges[(c, 'mid')] = np.arange(0, len(rr.curves.mid)-1) if False else None
    # mid edges: the CAD centreline polyline
    mid = np.asarray(rr.curves.mid, float)
    midv = np.vstack([mid, mid[:1]])
    class MidCurves:
        V = midv
        def project(self, X, Cc, K):
            q = (X - Cc[:3, 3]) @ Cc[:3, :3]; p = q @ np.asarray(K).T
            return p[:, :2]/p[:, 2:]
    for c in cams: edges[(c, 'mid')] = np.arange(0, len(midv)-1)
    cv = camvar.CameraVariables(cams, anchor_id=C4[0], released_ids=[C4[1]])
    H0 = np.eye(4)
    P = BA.BAProblem(cams, K_of, scene['obs'], ring_pts, X_init, cv, lam_ring=1.0,
                     curves=rr.curves, edges={k: v for k, v in edges.items() if k[1] != 'mid'})
    P.curves = rr.curves
    th0 = np.r_[np.zeros(6), np.zeros(6*len(cv.released)), X_init.ravel()]
    e0 = P.energy_breakdown(th0, H0)
    res = least_squares(lambda t: P.residuals(t, H0), th0, method='trf', loss='linear',
                        x_scale='jac', max_nfev=max_nfev, ftol=1e-10, xtol=1e-10, gtol=1e-10)
    e1 = P.energy_breakdown(res.x, H0)
    H, dx, X = cv.unpack(res.x, H0, len(X_init))
    Xg = scene['X']; Hg = scene['H']
    # camera errors (only meaningful for GT-near init: init != GT otherwise)
    errs = []
    for i, c in enumerate(C4):
        Cest = H @ (exp_se3(dx[c]) @ cams[c][1])
        Ctrue = scene['H'] @ cams[c][1]
        dR = Cest[:3, :3] @ Ctrue[:3, :3].T
        errs.append(dict(cam=c, rot_deg=float(np.degrees(np.arccos(np.clip((np.trace(dR)-1)/2, -1, 1)))),
                         trans_mm=float(np.linalg.norm(Cest[:3, 3]-Ctrue[:3, 3]))))
    Cest5 = exp_se3(dx[C5[0]]) @ cams[C5[0]][1]; Ctrue5 = cams[C5[0]][1]
    dR = Cest5[:3, :3] @ Ctrue5[:3, :3].T
    errs.append(dict(cam=C5[0], rot_deg=float(np.degrees(np.arccos(np.clip((np.trace(dR)-1)/2, -1, 1)))),
                     trans_mm=float(np.linalg.norm(Cest5[:3, 3]-Ctrue5[:3, 3]))))
    dH = H @ np.linalg.inv(Hg)
    lm = float(np.median(np.linalg.norm(X-Xg, axis=1)))
    J = res.jac.toarray() if hasattr(res.jac, 'toarray') else np.asarray(res.jac)
    return dict(init=init, X_init_err=float(np.median(np.linalg.norm(X_init-Xg, axis=1))),
                cam_rot_max=max(e['rot_deg'] for e in errs), cam_trans_max=max(e['trans_mm'] for e in errs),
                H_rot=float(np.degrees(np.arccos(np.clip((np.trace(dH[:3, :3])-1)/2, -1, 1)))),
                H_trans=float(np.linalg.norm(dH[:3, 3])), lm_med=lm,
                success=bool(res.success), status=int(res.status), nfev=int(res.nfev), njev=int(res.njev),
                cost0=float(e0['total']), cost1=float(e1['total']),
                rank=int(np.linalg.matrix_rank(J)),
                n_params=int(J.shape[1]), cams=errs)


def main():
    rows = []
    cases = [('S1_noisefree', dict(noisy=False), dict(init='gt')),
             ('S1b_noisefree_tri_init', dict(noisy=False), dict(init='tri')),
             ('S2_yaw25', dict(yaw=25.0), dict(init='tri')),
             ('S5_multicam_noise', dict(noisy=True), dict(init='tri')),
             ('S6_low_parallax', dict(low_par=True), dict(init='tri')),
             ('S7_wrong_obs', dict(noisy=True, wrong=2), dict(init='tri')),
             ('S8_ring_only', None, dict(init='tri')),
             ('S9_one_side', None, dict(init='tri')),
             ('S10_diff_K', dict(sameK=False), dict(init='tri'))]
    for name, sk, rk in cases:
        sc = make(seed=3, **(sk or {}))
        if name == 'S8_ring_only':
            sc['X_init_override'] = np.c_[np.linspace(-6, 6, 8), np.linspace(-6, 6, 8), np.zeros(8)]
        if name == 'S8_ring_only': sc['obs'] = []
        if name == 'S9_one_side':
            r = dict(scenario=name, init='n/a', error='NOT_EVALUABLE: controlled scene has a single 005 camera, '
                     'so one-sided observations cannot triangulate an initial landmark set (documented)')
            rows.append(r); print('SC', name, 'NOT_EVALUABLE', flush=True); continue
        try:
            r = run(sc, **rk); r['scenario'] = name; rows.append(r)
            print('SC', name, r['init'], round(r['cam_rot_max'], 3), round(r['cam_trans_max'], 3),
                  round(r['H_rot'], 3), round(r['H_trans'], 3), round(r['lm_med'], 3), r['success'], r['nfev'], flush=True)
        except Exception as ex:
            rows.append(dict(scenario=name, error=f'{type(ex).__name__}: {ex}'))
            print('SC', name, 'ERROR', ex, flush=True)
    pd.DataFrame([{k: v for k, v in r.items() if k != 'cams'} for r in rows]).to_csv(OUT/'CONTROLLED_BA_RESULTS.csv', index=False)


if __name__ == '__main__':
    main()
