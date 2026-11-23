"""R6 core: single H convention (T004_world = H @ dT @ T0), Ring residual VECTOR candidates,
reference-camera-aware epipolar scoring, stage-separated pipelines, HOLDOUT helpers.

Fixes R5: (a) Ring candidate refinement used a SCALAR energy; (b) H was baked into cameras
AND passed as H0 (double application); (c) epipolar scoring read GT 005 cameras.
"""
import json, os, sys, time
from pathlib import Path
import numpy as np, pandas as pd
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
WS = Path('/home/liu/ring_first_3d_workspace')
R6 = WS/'experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R6'
sys.path.insert(0, str(R6/'core')); sys.path.insert(0, str(R6/'replay')); sys.path.insert(0, str(WS/'src'))
os.environ.update(E4_RUN_DIR=str(R6/'replay'),
    RING_CAD=str(WS/'assets/retained_sources/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-HERO-BODY-ADAPT-018/inputs/G03/RING.npz'),
    RING_NORM=str(WS/'assets/retained_sources/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/FREE_VERTEX_013/inputs/G03/NORMALIZATION.json'))
import r2_synth as S
import ring_energy as RE
import camvar, ba_core_r4 as BA
import fixed_track_tri as FTT
import features019 as F19
from ring020_026 import RingRenderer
from se3 import exp_se3
OUT = R6/'runs'
RING_W = {'I': 0.35, 'C': 0.05, 'O': 0.35}


def unit(v):
    n = np.linalg.norm(v); return v/n if n > 0 else v


def perturb_cams(sc, ids, deg_rad, mm, seed, which=('004',), anchor=None):
    """Exact magnitude; the 004 anchor is never perturbed."""
    anchor = S.C4[0] if anchor is None else anchor
    rng = np.random.default_rng(seed)
    cams = {c: np.asarray(T, float).copy() for c, (v, T) in sc['cams'].items()}
    info = []
    for c in ids:
        if sc['cams'][c][0] not in which or c == anchor: continue
        w = np.r_[unit(rng.normal(size=3))*mm, unit(rng.normal(size=3))*deg_rad]
        cams[c] = exp_se3(w) @ cams[c]
        d = cams[c] @ np.linalg.inv(np.asarray(sc['cams'][c][1], float))
        info.append(dict(cam=c, rot_deg=float(np.degrees(np.linalg.norm(Rotation.from_matrix(d[:3, :3]).as_rotvec()))),
                         trans_mm=float(np.linalg.norm(d[:3, 3]))))
    return cams, info


def build_fixed(nlm=12, yaw=12.0, sub=8, seed=0):
    rr = RingRenderer(sorted(S.C4 + S.C5))
    sc = S.build_scene(seed=seed, nlm=nlm, H_rot_deg=(0.7, -0.4, yaw))
    ring_obs = S.ring_observations(sc, rr)
    ring_obs = {c: {k: (v[::2*sub] if k == 'mid' else v[::sub]) for k, v in d.items()} for c, d in ring_obs.items()}
    obs = S.rgb_observations(sc)
    X0, ids = S.triangulate([o for o in obs if sc['cams'][o[0]][0] == '005'],
                            {c: ('x', sc['C_gt'][c]) for c in S.C5}, sc['K_of'], nlm)
    return dict(sc=sc, rr=rr, ring_obs=ring_obs, obs=obs, X0=X0, ids=ids, X_gt_map={int(i): sc['X'][i] for i in ids})


def cam_world(T0, video, H, dx=None):
    C = exp_se3(np.zeros(6) if dx is None else np.asarray(dx, float)) @ np.asarray(T0, float)
    return H @ C if video == '004' else C


def geom_from(F, H, cams=None):
    """CAD visible edges for the INITIAL cameras (H applied once), never from GT."""
    sc = F['sc']
    cams = cams or {c: np.asarray(sc['cams'][c][1], float) for c in sc['cams']}
    g = {}
    mid = np.asarray(F['rr'].curves.mid, float); Vm = np.vstack([mid, mid[:1]])
    Em = np.c_[np.arange(len(Vm)-1), np.arange(1, len(Vm))]
    for c, T0 in cams.items():
        v = sc['cams'][c][0]
        C = cam_world(T0, v, H)
        K = np.asarray(sc['K_of'][c], float)
        seg = F['rr'].curves.segments(C, K)
        g[c] = {'V_inner': np.asarray(F['rr'].curves.V, float), 'E_inner': np.asarray(seg['inner'], int).reshape(-1, 2),
                'V_outer': np.asarray(F['rr'].curves.V, float), 'E_outer': np.asarray(seg['outer'], int).reshape(-1, 2),
                'V_mid': Vm, 'E_mid': Em}
    return g


def make_problem(F, H_init, released=(), cams=None, Xprior=None):
    """Cameras passed here are ALWAYS the W0/perturbed base poses; H lives inside the BA only."""
    sc = F['sc']
    cams = cams or {c: np.asarray(sc['cams'][c][1], float) for c in sc['cams']}
    cams_d = {c: (sc['cams'][c][0], np.asarray(cams[c], float)) for c in cams}
    cv = camvar.CameraVariables(cams_d, S.C4[0], list(released))
    P = BA.BAProblemR4(cams_d, sc['K_of'], F['obs'], F['ring_obs'],
                       F['X0'] if Xprior is None else Xprior, cv, geom_from(F, H_init, cams), lam_ring=1.0)
    P.geom = geom_from(F, H_init, cams)
    return P


def ring_vector_for_H(F, H, geom):
    """Formal Ring I/C/O residual vector (identical construction to BAProblemR4.blocks)."""
    sc = F['sc']; out = []
    for c in S.C4:
        C = cam_world(np.asarray(sc['cams'][c][1], float), '004', H)
        g = geom[c]
        for key, w in (('inner', RING_W['I']), ('outer', RING_W['O']), ('mid', RING_W['C'])):
            d = BA.poly_dist(C, np.asarray(sc['K_of'][c], float), g['V_' + key], g['E_' + key],
                             F['ring_obs'][c].get(key, np.zeros((0, 2))))
            if len(d): out.append(RE.ring_residuals(d, 1.0, w))
    return np.concatenate(out) if out else np.zeros(0)


def ring_energy_for_H(F, H, geom):
    r = ring_vector_for_H(F, H, geom)
    return float(0.5*(r**2).sum())


def sampson_px(Fm, p, q):
    p = np.c_[np.asarray(p, float), np.ones(len(p))]
    q = np.c_[np.asarray(q, float), np.ones(len(q))]
    Fa = (Fm @ p.T).T; Ftb = (Fm.T @ q.T).T
    num = np.abs(np.einsum('ij,ij->i', q, Fa))
    den = np.sqrt((Fa[:, :2]**2).sum(1) + (Ftb[:, :2]**2).sum(1)) + 1e-12
    return num/den


def epipolar_energy(F, H, ids, cams):
    """Per-identity aggregated Sampson error using the ACTUAL reference cameras (no C_gt)."""
    sc = F['sc']
    by = {}
    for c, i, uv in F['obs']:
        by.setdefault(i, []).append((c, np.asarray(uv, float)))
    per = {}
    for i in ids:
        errs = []
        for c4 in S.C4:
            for c5 in S.C5:
                u = [uv for (c, uv) in by.get(i, []) if c == c4]
                v = [uv for (c, uv) in by.get(i, []) if c == c5]
                if not u or not v: continue
                C4 = cam_world(np.asarray(cams[c4], float), '004', H)
                C5 = np.asarray(cams[c5], float)
                T = np.linalg.inv(C5) @ C4
                tx = np.array([[0, -T[2, 3], T[1, 3]], [T[2, 3], 0, -T[0, 3]], [-T[1, 3], T[0, 3], 0]])
                Fm = np.linalg.inv(sc['K_of'][c5]).T @ tx @ T[:3, :3] @ np.linalg.inv(sc['K_of'][c4])
                n = np.linalg.norm(Fm)
                if n < 1e-15: continue
                errs.extend(sampson_px(Fm/n, np.array(u), np.array(v)).tolist())
        if errs: per[int(i)] = float(np.median(errs))
    return per


def ring_candidates(F, ids, cams, yaw_step=15, lam_ring=1.0, lam_epi=1.0, max_nfev=40):
    """H1 candidates: Ring residual-VECTOR optimisation; H2 ranking by per-identity Sampson."""
    geom0 = geom_from(F, np.eye(4), cams)
    cands = []
    for yaw in np.arange(0, 360, yaw_step):
        H0 = exp_se3(np.r_[np.zeros(3), np.array([0., 0., np.deg2rad(yaw)])])
        e0 = ring_energy_for_H(F, H0, geom0)
        f = lambda t: ring_vector_for_H(F, exp_se3(t) @ H0, geom0)
        r = least_squares(f, np.zeros(6), method='trf', loss='linear', x_scale='jac', max_nfev=max_nfev)
        Hr = exp_se3(r.x) @ H0
        cands.append(dict(yaw_initial=float(yaw), H_initial=H0.tolist(), H=Hr,
                          ring_initial=e0, ring=ring_energy_for_H(F, Hr, geom0),
                          refine_rot_deg=float(np.degrees(np.linalg.norm(Rotation.from_matrix(
                              (Hr @ np.linalg.inv(H0))[:3, :3]).as_rotvec()))),
                          refine_trans_mm=float(np.linalg.norm((Hr @ np.linalg.inv(H0))[:3, 3])),
                          nfev=int(r.nfev), success=bool(r.success), status=int(r.status)))
    per_id = {i: epipolar_energy(F, c['H'], [i], cams).get(i) for i in ids for c in cands[:0]}  # no-op
    for c in cands:
        per = epipolar_energy(F, c['H'], ids, cams)
        c['epi_per_id'] = per
        c['epi'] = float(np.median(list(per.values()))) if per else None
        c['score'] = lam_ring*c['ring'] + lam_epi*(c['epi'] if c['epi'] is not None else 1e6)
    cands.sort(key=lambda d: d['score'])
    return cands


def triangulate_under_H(F, H, obs=None, cams=None, min_views=3):
    sc = F['sc']; obs = obs if obs is not None else F['obs']
    cams = cams or {c: np.asarray(sc['cams'][c][1], float) for c in sc['cams']}
    world = {c: cam_world(np.asarray(cams[c], float), sc['cams'][c][0], H) for c in cams}
    nlm = len(F['X0'])
    xy = {c: np.full((nlm, 2), np.nan) for c in world}; tracks = {i: [] for i in range(nlm)}
    for c, i, uv in obs:
        xy[c][i] = np.asarray(uv, float); tracks[i].append((c, i))
    shim = {c: dict(id=c, T=world[c], K=sc['K_of'][c]) for c in world}
    def fake(v): return dict(xy=xy[v['id']], des=np.zeros((nlm, 128), np.float32))
    old = F19.features; F19.features = fake
    X, ids = [], []
    try:
        for i, tr in tracks.items():
            if len(tr) < min_views: continue
            r = FTT.triangulate_tracks([tr], shim)[0]
            X.append(r['X']); ids.append(i)
    finally:
        F19.features = old
    return np.array(X), np.array(ids)


def solve(P, X_init, mode, H0=np.eye(4), budget=60, rgb_mode='huber', tol=1e-10):
    dx0 = {c: np.zeros(6) for c in P.cams}; nX = len(X_init); t0 = time.time()
    if mode == 'M1':
        f = lambda t: P.residual_vector(H0, dx0, t.reshape(-1, 3), rgb_mode)[0]
        res = least_squares(f, X_init.ravel(), method='trf', loss='linear', x_scale='jac', max_nfev=budget, ftol=tol, xtol=tol, gtol=tol)
        H, X, np_ = H0, res.x.reshape(-1, 3), 3*nX
    elif mode == 'M2':
        f = lambda t: P.residual_vector(exp_se3(t[:6]) @ H0, dx0, X_init, rgb_mode)[0]
        res = least_squares(f, np.zeros(6), method='trf', loss='linear', x_scale='jac', max_nfev=budget, ftol=tol, xtol=tol, gtol=tol)
        H, X, np_ = exp_se3(res.x) @ H0, X_init, 6
    elif mode == 'M3b':
        fh = lambda t: P.residual_vector(exp_se3(t[:6]) @ H0, dx0, X_init, rgb_mode)[0]
        r1 = least_squares(fh, np.zeros(6), method='trf', loss='linear', x_scale='jac', max_nfev=max(1, budget//2), ftol=tol, xtol=tol, gtol=tol)
        H1 = exp_se3(r1.x) @ H0
        fj = lambda t: P.residual_vector(exp_se3(t[:6]) @ H1, dx0, t[6:].reshape(-1, 3), rgb_mode)[0]
        r2 = least_squares(fj, np.r_[np.zeros(6), X_init.ravel()], method='trf', loss='linear', x_scale='jac',
                           max_nfev=max(1, budget-int(r1.nfev)), ftol=tol, xtol=tol, gtol=tol)
        H, X, np_ = exp_se3(r2.x[:6]) @ H1, r2.x[6:].reshape(-1, 3), 6+3*nX
        res = r2; P.stage1 = dict(success=bool(r1.success), nfev=int(r1.nfev), H=H1, cost=float(r1.cost))
    elif mode == 'M4':
        nr = len(P.cv.released)
        f = lambda t: P.residual_vector(exp_se3(t[:6]) @ H0,
                                        {**{c: np.zeros(6) for c in P.cams}, **{c: t[6+6*i:12+6*i] for i, c in enumerate(P.cv.released)}},
                                        t[6+6*nr:].reshape(-1, 3), rgb_mode)[0]
        res = least_squares(f, np.r_[np.zeros(6), np.zeros(6*nr), X_init.ravel()], method='trf', loss='linear',
                            x_scale='jac', max_nfev=budget, ftol=tol, xtol=tol, gtol=tol)
        H = exp_se3(res.x[:6]) @ H0
        dx = {c: np.zeros(6) for c in P.cams}
        for i, c in enumerate(P.cv.released): dx[c] = res.x[6+6*i:12+6*i]
        X = res.x[6+6*nr:].reshape(-1, 3); np_ = 6+6*nr+3*nX; P.dx_final = dx
    else:
        raise ValueError(mode)
    J = res.jac.toarray() if hasattr(res.jac, 'toarray') else np.asarray(res.jac)
    return H, X, dict(mode=mode, n_params=int(np_), success=bool(res.success), status=int(res.status),
                      nfev=int(res.nfev), cost=float(res.cost),
                      rank=int(np.linalg.matrix_rank(J)), seconds=round(time.time()-t0, 2))


def gt_metrics(F, H, X, ids):
    sc = F['sc']; dH = np.asarray(H) @ np.linalg.inv(sc['H'])
    rot = float(np.degrees(np.linalg.norm(Rotation.from_matrix(dH[:3, :3]).as_rotvec())))
    lm = float(np.median(np.linalg.norm(X - sc['X'][ids], axis=1))) if len(X) else None
    return dict(H_rot=rot, H_trans=float(np.linalg.norm(dH[:3, 3])), lm_med=lm, n_lm=int(len(X)))
