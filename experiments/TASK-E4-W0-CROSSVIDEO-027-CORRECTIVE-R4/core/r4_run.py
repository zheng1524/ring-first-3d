#!/usr/bin/env python3
"""R4: fixed synthetic scene (experiment I) + 5-group error-source ablation (A-E) with M0-M3."""
import argparse, json, os, sys, time
from pathlib import Path
import numpy as np, pandas as pd
from scipy.optimize import least_squares
WS = Path('/home/liu/ring_first_3d_workspace')
R4 = WS/'experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R4'
sys.path.insert(0, str(R4/'core')); sys.path.insert(0, str(R4/'replay')); sys.path.insert(0, str(WS/'src'))
os.environ.update(E4_RUN_DIR=str(R4/'replay'),
    RING_CAD=str(WS/'assets/retained_sources/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-HERO-BODY-ADAPT-018/inputs/G03/RING.npz'),
    RING_NORM=str(WS/'assets/retained_sources/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/FREE_VERTEX_013/inputs/G03/NORMALIZATION.json'))
import r2_synth as S
import ring_energy as RE
import camvar, ba_core_r4 as BA
from ring020_026 import RingRenderer
from se3 import exp_se3
ROOT = R4/'runs/controlled_error_ablation'
FIXED_YAW = 12.0


def make_fixed():
    """One fixed GT scene; observations frozen once (experiment I)."""
    rr = RingRenderer(sorted(S.C4 + S.C5))
    sc = S.build_scene(seed=0, nlm=12, H_rot_deg=(0.7, -0.4, FIXED_YAW))
    ring_obs = S.ring_observations(sc, rr)
    ring_obs = {c: {k: (v[::16] if k == 'mid' else v[::8]) for k, v in d.items()} for c, d in ring_obs.items()}
    obs = S.rgb_observations(sc)
    return sc, obs, ring_obs, rr


def geom_from(cams_world, rr):
    g = {}
    mid = np.asarray(rr.curves.mid, float); Vm = np.vstack([mid, mid[:1]])
    Em = np.c_[np.arange(len(Vm)-1), np.arange(1, len(Vm))]
    for c, C in cams_world.items():
        K = np.asarray(S.views[c]['K'], float)
        seg = rr.curves.segments(np.asarray(C, float), K)
        g[c] = {'V_inner': np.asarray(rr.curves.V, float), 'E_inner': np.asarray(seg['inner'], int).reshape(-1, 2),
                'V_outer': np.asarray(rr.curves.V, float), 'E_outer': np.asarray(seg['outer'], int).reshape(-1, 2),
                'V_mid': Vm, 'E_mid': Em}
    return g


def baseline_X(sc, obs):
    """005-only triangulation with the TRUE 005 cameras (baseline reference structure)."""
    gt5 = {c: ('x', sc['C_gt'][c]) for c in S.C5}
    X, ids = S.triangulate([o for o in obs if sc['cams'][o[0]][0] == '005'], gt5, sc['K_of'], 12)
    return X, ids


def perturb_cams(sc, ids4, deg, mm, seed, which=('004',)):
    rng = np.random.default_rng(seed)
    cams = {c: np.asarray(T, float) for c, (v, T) in sc['cams'].items()}
    info = []
    for c in ids4:
        v = sc['cams'][c][0]
        if v not in which: continue
        w = np.r_[rng.normal(0, mm, 3), np.deg2rad(rng.normal(0, deg, 3))]
        if mm > 0: w[:3] *= 1.0/ (np.linalg.norm(w[:3]) + 1e-12)
        cams[c] = exp_se3(w) @ cams[c]
        info.append(dict(cam=c, rot_deg=float(np.degrees(np.linalg.norm(w[3:]))),
                         trans_mm=float(np.linalg.norm(w[:3]))))
    return cams, info


def perturb_X(X, mm, seed, kind='random'):
    rng = np.random.default_rng(seed)
    if kind == 'random':
        d = rng.normal(size=X.shape); d /= np.linalg.norm(d, axis=1, keepdims=True)
        return X + d*mm
    if kind == 'depth':
        d = np.tile(np.array([0., 0., 1.]), (len(X), 1)) * np.sign(rng.normal(size=(len(X), 1)))
        return X + d*mm
    if kind == 'perp':
        d = rng.normal(size=(len(X), 2)); d /= np.linalg.norm(d, axis=1, keepdims=True)
        return X + np.c_[d*mm, np.zeros(len(X))]
    raise ValueError(kind)


def se3_err(A, B):
    d = np.asarray(A) @ np.linalg.inv(np.asarray(B))
    return float(np.degrees(np.arccos(np.clip((np.trace(d[:3, :3])-1)/2, -1, 1)))), float(np.linalg.norm(d[:3, 3]))


def solve(P, X_init, mode, rgb_mode, budget, H0=None, cams_fixed=True):
    H0 = np.eye(4) if H0 is None else H0
    dx0 = {c: np.zeros(6) for c in P.cams}
    t0 = time.time()
    if mode == 'M1':
        def fun(t):
            r, _ = P.residual_vector(H0, dx0, t.reshape(-1, 3), rgb_mode); return r
        res = least_squares(fun, X_init.ravel(), method='trf', loss='linear', x_scale='jac',
                            max_nfev=budget, ftol=1e-10, xtol=1e-10, gtol=1e-10)
        H = H0; X = res.x.reshape(-1, 3)
    elif mode == 'M2':
        def fun(t):
            r, _ = P.residual_vector(exp_se3(t[:6]) @ H0, dx0, X_init, rgb_mode); return r
        res = least_squares(fun, np.zeros(6), method='trf', loss='linear', x_scale='jac',
                            max_nfev=budget, ftol=1e-10, xtol=1e-10, gtol=1e-10)
        H = exp_se3(res.x) @ H0; X = X_init
    elif mode == 'M3':
        def fun_h(t):
            r, _ = P.residual_vector(exp_se3(t[:6]) @ H0, dx0, X_init, rgb_mode); return r
        r1 = least_squares(fun_h, np.zeros(6), method='trf', loss='linear', x_scale='jac',
                           max_nfev=budget//2, ftol=1e-10, xtol=1e-10, gtol=1e-10)
        H1 = exp_se3(r1.x) @ H0
        def fun_x(t):
            r, _ = P.residual_vector(H1, dx0, t.reshape(-1, 3), rgb_mode); return r
        r2 = least_squares(fun_x, X_init.ravel(), method='trf', loss='linear', x_scale='jac',
                           max_nfev=budget - int(r1.nfev), ftol=1e-10, xtol=1e-10, gtol=1e-10)
        H = H1; X = r2.x.reshape(-1, 3)
        res = dict(success=bool(r2.success), status=int(r2.status), nfev=int(r1.nfev)+int(r2.nfev),
                   cost=float(r2.cost), stage1=dict(success=bool(r1.success), nfev=int(r1.nfev), cost=float(r1.cost),
                                                    H_rot=se3_err(H1, P.gt_H)[0] if hasattr(P, 'gt_H') else None))
        J = r2.jac.toarray() if hasattr(r2.jac, 'toarray') else np.asarray(r2.jac)
    elif mode == 'M4':
        def fun(t):
            Ht = exp_se3(t[:6]) @ H0
            dx = {c: np.zeros(6) for c in P.cams}
            for i, c in enumerate(P.cv.released): dx[c] = t[6+6*i:12+6*i]
            X = t[6+6+6*len(P.cv.released):].reshape(-1, 3)
            r, _ = P.residual_vector(Ht, dx, X, rgb_mode); return r
        th0 = np.r_[np.zeros(6), np.zeros(6*len(P.cv.released)), X_init.ravel()]
        res = least_squares(fun, th0, method='trf', loss='linear', x_scale='jac',
                            max_nfev=budget, ftol=1e-10, xtol=1e-10, gtol=1e-10)
        H = exp_se3(res.x[:6]) @ H0
        X = res.x[6+6+6*len(P.cv.released):].reshape(-1, 3)
        J = res.jac.toarray() if hasattr(res.jac, 'toarray') else np.asarray(res.jac)
        res = dict(success=bool(res.success), status=int(res.status), nfev=int(res.nfev), cost=float(res.cost))
    else:
        raise ValueError(mode)
    if mode != 'M3':
        J = res.jac.toarray() if hasattr(res.jac, 'toarray') else np.asarray(res.jac)
        res = dict(success=bool(res.success), status=int(res.status), nfev=int(res.nfev), cost=float(res.cost))
    sv = np.linalg.svd(J, compute_uv=False)
    res['rank'] = int(np.linalg.matrix_rank(J)); res['n_params'] = int(J.shape[1])
    res['cond'] = float(sv[0]/max(sv[-1], 1e-30)); res['seconds'] = round(time.time()-t0, 1)
    return H, X, res


def run_group(name, group, deg=0.0, mm=0.0, lm_mm=0.0, lm_kind='random', seed=0, mode='M0',
              rgb_mode='huber', budget=100, sc=None, obs=None, ring_obs=None, rr=None, X0=None, tag=None):
    sc = sc or RUN_CACHE['sc']; obs = obs or RUN_CACHE['obs']; ring_obs = ring_obs or RUN_CACHE['ring_obs']
    rr = rr or RUN_CACHE['rr']; X0 = RUN_CACHE['X0'] if X0 is None else X0
    tag = tag or f'{group}_{mode}_{lm_kind}_{int(deg*100):03d}_{int(mm*100):03d}_{int(lm_mm*10):02d}_s{seed}'
    out = ROOT/name/tag; out.mkdir(parents=True, exist_ok=True)
    cams_use = {c: np.asarray(T, float) for c, (v, T) in sc['cams'].items()}
    cam_info = []
    if group in ('B', 'D'):
        cams_use, cam_info = perturb_cams(sc, [S.C4[1], S.C4[2]], deg, mm, seed)
    if group == 'B5':
        cams_use, cam_info = perturb_cams(sc, S.C5, deg, mm, seed, which=('005',))
    if group in ('C', 'D'):
        X_init = perturb_X(X0, lm_mm, seed, lm_kind)
    elif group in ('E1', 'E2'):
        if group == 'E1':
            obs_t = [o for o in obs if sc['cams'][o[0]][0] == '005']
            cams_t = {c: ('x', cams_use[c]) for c in S.C5}
        else:
            obs_t = obs; cams_t = {c: ('x', cams_use[c]) for c in sc['cams']}
        X_init, ids = S.triangulate(obs_t, cams_t, sc['K_of'], 12)
    else:
        X_init = X0.copy()
    cv = camvar.CameraVariables(sc['cams'], S.C4[0], ([S.C4[1], S.C4[2]] if mode == 'M4' else []))
    cams_world = {c: (np.eye(4) @ cams_use[c] if sc['cams'][c][0] == '004' else cams_use[c]) for c in cams_use}
    P = BA.BAProblemR4(sc['cams'], sc['K_of'], obs, ring_obs, X0, cv, geom_from(cams_world, rr), lam_ring=1.0)
    # initial state: H=I, camera deltas 0, but the model cameras must be the perturbed ones
    sc_use = dict(sc); sc_use['cams'] = {c: (sc['cams'][c][0], cams_use[c]) for c in sc['cams']}
    P = BA.BAProblemR4(sc_use['cams'], sc['K_of'], obs, ring_obs, X0, cv, geom_from(cams_world, rr), lam_ring=1.0)
    H0 = np.eye(4)
    e0, r0 = P.energy_table(H0, {c: np.zeros(6) for c in P.cams}, X_init, rgb_mode)
    if mode == 'M0':
        H, X = H0, X_init; st = dict(success=None, status=None, nfev=0, cost=float(0.5*(r0**2).sum()),
                                     rank=None, n_params=0, cond=None, seconds=0.0)
    else:
        P.gt_H = sc['H']
        H, X, st = solve(P, X_init, mode, rgb_mode, budget)
    e1, r1 = P.energy_table(H, {c: np.zeros(6) for c in P.cams}, X, rgb_mode)
    H_rot, H_tr = se3_err(H, sc['H'])
    lm = float(np.median(np.linalg.norm(X - sc['X'][:len(X)], axis=1))) if len(X) == len(sc['X']) else None
    lm_init = float(np.median(np.linalg.norm(X_init - sc['X'][:len(X_init)], axis=1))) if len(X_init) == len(sc['X']) else None
    cam_err = []
    for c in sc['cams']:
        v = sc['cams'][c][0]
        Cm = H @ cams_use[c] if v == '004' else cams_use[c]
        Ct = sc['C_gt'][c]
        rr_, tt_ = se3_err(Cm, Ct)
        cam_err.append(dict(cam=c, rot=rr_, trans=tt_))
    meta = dict(group=group, tag=tag, mode=mode, rgb_mode=rgb_mode, seed=seed,
                cam_pert=dict(deg=deg, mm=mm, which=cam_info), lm_pert=dict(mm=lm_mm, kind=lm_kind),
                H_init_rot=se3_err(H0, sc['H'])[0], H_rot=H_rot, H_trans=H_tr,
                lm_init_err=lm_init, lm_err=lm, cam_rot_max=max(c['rot'] for c in cam_err),
                cam_trans_max=max(c['trans'] for c in cam_err),
                e0_total=e0['total_terms'], e1_total=e1['total_terms'],
                e0_half_r2=e0['half_r2'], e1_half_r2=e1['half_r2'],
                rgb0=e0.get('rgb'), rgb1=e1.get('rgb'),
                ring0=e0.get('ring_I', 0)+e0.get('ring_C', 0)+e0.get('ring_O', 0),
                ring1=e1.get('ring_I', 0)+e1.get('ring_C', 0)+e1.get('ring_O', 0),
                n_ring={k: e1.get('n_ring_' + k, 0) for k in ('I', 'C', 'O')},
                rgb_median0=e0.get('rgb_median_px'), rgb_median1=e1.get('rgb_median_px'),
                rgb_p900=e0.get('rgb_p90_px'), rgb_p901=e1.get('rgb_p90_px'), n_rgb=e1.get('rgb_n'),
                energy_consistency=float(abs(e1['total_terms'] - e1['half_r2'])), **st)
    (out/'METRICS.json').write_text(json.dumps(meta, indent=1))
    json.dump(dict(group=group, tag=tag, mode=mode, rgb_mode=rgb_mode, seed=seed, deg=deg, mm=mm, lm_mm=lm_mm,
                   lm_kind=lm_kind, budget=budget, fixed_yaw=FIXED_YAW), open(out/'CONFIG.json', 'w'), indent=1)
    np.savez(out/'RESULT.npz', H=H, X=X, X_init=X_init, H_gt=sc['H'], X_gt=sc['X'], X0=X0)
    return meta


RUN_CACHE = {}


def init_cache():
    sc, obs, ring_obs, rr = make_fixed()
    X0, ids = baseline_X(sc, obs)
    RUN_CACHE.update(dict(sc=sc, obs=obs, ring_obs=ring_obs, rr=rr, X0=X0, ids=ids))
    return RUN_CACHE


def sweep(what='main'):
    init_cache()
    rows = []
    if what == 'leftover':
        plan = []
        for grp, name, kw in (('B', 'B50_camera_only', dict(deg=0.5, mm=0.25)),
                              ('C', 'C3_landmark_only', dict(lm_mm=3.0, lm_kind='random')),
                              ('D', 'D_both', dict(deg=0.5, mm=0.25, lm_mm=3.0)),
                              ('E1', 'E1_retri_005', dict(deg=0.5, mm=0.0)),
                              ('E2', 'E2_retri_both', dict(deg=0.5, mm=0.0))):
            for m in ('M0', 'M3', 'M4'):
                plan.append((name, grp, dict(mode=m, budget=0 if m == 'M0' else 30, seed=0, **kw)))
    elif what == 'baseline':
        plan = [('A_baseline', 'A', dict(mode=m, budget=b)) for m, b in
                (('M0', 0), ('M1', 100), ('M2', 200), ('M3', 200))]
    elif what == 'main':
        plan = []
        for m in ('M0', 'M1', 'M2', 'M3'):
            plan.append(('A_baseline', 'A', dict(mode=m, budget=0 if m == 'M0' else (200 if m == 'M2' else 60))))
        for d in (0.25, 0.5):
            for m in ('M0', 'M1', 'M2', 'M3'):
                plan.append((f'B_camera_only_{int(d*100)}', 'B', dict(deg=d, mm=0.25, mode=m, budget=0 if m == 'M0' else (200 if m == 'M2' else 60), seed=0)))
        for lm in (1.0, 3.0):
            for m in ('M0', 'M1', 'M2', 'M3'):
                plan.append((f'C_landmark_only_{int(lm)}', 'C', dict(lm_mm=lm, lm_kind='random', mode=m, budget=0 if m == 'M0' else (200 if m == 'M2' else 60), seed=0)))
        for d, lm in ((0.5, 3.0),):
            for m in ('M0', 'M1', 'M2', 'M3'):
                plan.append(('D_both', 'D', dict(deg=d, mm=0.25, lm_mm=lm, mode=m, budget=0 if m == 'M0' else (200 if m == 'M2' else 60), seed=0)))
        for m in ('M0', 'M1', 'M2', 'M3'):
            plan.append(('E1_retri_005', 'E1', dict(deg=0.5, mm=0.0, mode=m, budget=0 if m == 'M0' else (200 if m == 'M2' else 60), seed=0)))
        for m in ('M0', 'M1', 'M2', 'M3'):
            plan.append(('E2_retri_both', 'E2', dict(deg=0.5, mm=0.0, mode=m, budget=0 if m == 'M0' else (200 if m == 'M2' else 60), seed=0)))
    for name, group, kw in plan:
        try:
            m = run_group(name, group, **kw)
            rows.append(m); print('RUN', name, group, kw.get('mode'), 'H', round(m['H_rot'], 4),
                                  'X', None if m['lm_err'] is None else round(m['lm_err'], 3),
                                  'succ', m['success'], m['nfev'], flush=True)
        except Exception as ex:
            rows.append(dict(group=group, name=name, error=f'{type(ex).__name__}: {ex}'))
            print('ERR', name, group, ex, flush=True)
    pd.DataFrame([{k: v for k, v in r.items() if k != 'cam_pert'} for r in rows]).to_csv(
        R4/'runs'/f'SUMMARY_{what}.csv', index=False)


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument('--what', default='main'); a = ap.parse_args()
    sweep(a.what)
