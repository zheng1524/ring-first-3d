"""R5 core: corrected perturbations, M3a/M3b/M4, Ring-only H candidates, epipolar selection,
cross-video triangulation under a fixed H, and pipeline comparison. One BA implementation (ba_core_r4).
"""
import json, os, sys, time
from pathlib import Path
import numpy as np, pandas as pd
from scipy.optimize import least_squares
WS = Path('/home/liu/ring_first_3d_workspace')
R5 = WS/'experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R5'
sys.path.insert(0, str(R5/'core')); sys.path.insert(0, str(R5/'replay')); sys.path.insert(0, str(WS/'src'))
os.environ.update(E4_RUN_DIR=str(R5/'replay'),
    RING_CAD=str(WS/'assets/retained_sources/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-HERO-BODY-ADAPT-018/inputs/G03/RING.npz'),
    RING_NORM=str(WS/'assets/retained_sources/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/FREE_VERTEX_013/inputs/G03/NORMALIZATION.json'))
import r2_synth as S
import ring_energy as RE
import camvar, ba_core_r4 as BA
import fixed_track_tri as FTT
import features019 as F19
from ring020_026 import RingRenderer
from se3 import exp_se3
OUT = R5/'runs'
YAW_GT = 12.0
RING_W = {'I': 0.35, 'C': 0.05, 'O': 0.35}


def unit(v):
    n = np.linalg.norm(v)
    return v/n if n > 0 else v


def perturb_cams(sc, ids, deg_rad, mm, seed, which=('004',), anchor=None):
    """Exact-magnitude perturbation: rotation angle == deg_rad, translation == mm.

    The 004 anchor (default S.C4[0]) is never perturbed, by construction.
    """
    from scipy.spatial.transform import Rotation
    anchor = S.C4[0] if anchor is None else anchor
    rng = np.random.default_rng(seed)
    cams = {c: np.asarray(T, float).copy() for c, (v, T) in sc['cams'].items()}
    info = []
    for c in ids:
        v = sc['cams'][c][0]
        if v not in which or c == anchor: continue
        w = np.r_[unit(rng.normal(size=3))*mm, unit(rng.normal(size=3))*deg_rad]
        cams[c] = exp_se3(w) @ cams[c]
        d = cams[c] @ np.linalg.inv(np.asarray(sc['cams'][c][1], float))
        ang = np.degrees(np.linalg.norm(Rotation.from_matrix(d[:3, :3]).as_rotvec()))
        info.append(dict(cam=c, rot_deg=float(ang), trans_mm=float(np.linalg.norm(d[:3, 3]))))
    return cams, info


def build_fixed(nlm=12, yaw=YAW_GT, sub=8, seed=0):
    rr = RingRenderer(sorted(S.C4 + S.C5))
    sc = S.build_scene(seed=seed, nlm=nlm, H_rot_deg=(0.7, -0.4, yaw))
    ring_obs = S.ring_observations(sc, rr)
    ring_obs = {c: {k: (v[::2*sub] if k == 'mid' else v[::sub]) for k, v in d.items()} for c, d in ring_obs.items()}
    obs = S.rgb_observations(sc)
    X0, ids = S.triangulate([o for o in obs if sc['cams'][o[0]][0] == '005'],
                            {c: ('x', sc['C_gt'][c]) for c in S.C5}, sc['K_of'], nlm)
    world0 = {c: (np.asarray(sc['cams'][c][1], float) if sc['cams'][c][0] == '004' else np.asarray(sc['cams'][c][1], float))
              for c in sc['cams']}
    geom4 = geom_from(world0, rr)          # visibility frozen from the INITIAL cameras
    return dict(sc=sc, rr=rr, ring_obs=ring_obs, obs=obs, X0=X0, ids=ids, geom4=geom4)


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


def make_problem(F, cams_used, released=()):
    sc = F['sc']
    cams = {c: (sc['cams'][c][0], np.asarray(cams_used[c], float)) for c in sc['cams']}
    cv = camvar.CameraVariables(cams, S.C4[0], list(released))
    world = {c: cams[c][1] for c in cams}
    return BA.BAProblemR4(cams, sc['K_of'], F['obs'], F['ring_obs'], F['X0'], cv,
                          geom_from(world, F['rr']), lam_ring=1.0)


def solve(P, X_init, mode, H0=np.eye(4), budget=60, rgb_mode='huber', tol=1e-10):
    dx0 = {c: np.zeros(6) for c in P.cams}
    t0 = time.time()
    nX = len(X_init)
    if mode == 'M1':
        f = lambda t: P.residual_vector(H0, dx0, t.reshape(-1, 3), rgb_mode)[0]
        res = least_squares(f, X_init.ravel(), method='trf', loss='linear', x_scale='jac',
                            max_nfev=budget, ftol=tol, xtol=tol, gtol=tol)
        H, X, info = H0, res.x.reshape(-1, 3), dict(n_params=3*nX)
    elif mode == 'M2':
        f = lambda t: P.residual_vector(exp_se3(t[:6]) @ H0, dx0, X_init, rgb_mode)[0]
        res = least_squares(f, np.zeros(6), method='trf', loss='linear', x_scale='jac',
                            max_nfev=budget, ftol=tol, xtol=tol, gtol=tol)
        H, X, info = exp_se3(res.x) @ H0, X_init, dict(n_params=6)
    elif mode in ('M3a', 'M3b'):
        fh = lambda t: P.residual_vector(exp_se3(t[:6]) @ H0, dx0, X_init, rgb_mode)[0]
        r1 = least_squares(fh, np.zeros(6), method='trf', loss='linear', x_scale='jac',
                           max_nfev=max(1, budget//2), ftol=tol, xtol=tol, gtol=tol)
        H1 = exp_se3(r1.x) @ H0
        if mode == 'M3a':
            fx = lambda t: P.residual_vector(H1, dx0, t.reshape(-1, 3), rgb_mode)[0]
            r2 = least_squares(fx, X_init.ravel(), method='trf', loss='linear', x_scale='jac',
                               max_nfev=max(1, budget-int(r1.nfev)), ftol=tol, xtol=tol, gtol=tol)
            H, X = H1, r2.x.reshape(-1, 3); info = dict(n_params=6+3*nX)
        else:
            def fj(t):
                return P.residual_vector(exp_se3(t[:6]) @ H1, dx0, t[6:].reshape(-1, 3), rgb_mode)[0]
            th0 = np.r_[np.zeros(6), X_init.ravel()]
            r2 = least_squares(fj, th0, method='trf', loss='linear', x_scale='jac',
                               max_nfev=max(1, budget-int(r1.nfev)), ftol=tol, xtol=tol, gtol=tol)
            H, X = exp_se3(r2.x[:6]) @ H1, r2.x[6:].reshape(-1, 3); info = dict(n_params=6+3*nX)
        res = r2; info['stage1'] = dict(success=bool(r1.success), nfev=int(r1.nfev), cost=float(r1.cost))
    elif mode == 'M4':
        nr = len(P.cv.released)
        def f4(t):
            Ht = exp_se3(t[:6]) @ H0
            dx = {c: np.zeros(6) for c in P.cams}
            for i, c in enumerate(P.cv.released): dx[c] = t[6+6*i:12+6*i]
            return P.residual_vector(Ht, dx, t[6+6*nr:].reshape(-1, 3), rgb_mode)[0]
        th0 = np.r_[np.zeros(6), np.zeros(6*nr), X_init.ravel()]
        res = least_squares(f4, th0, method='trf', loss='linear', x_scale='jac',
                            max_nfev=budget, ftol=tol, xtol=tol, gtol=tol)
        H = exp_se3(res.x[:6]) @ H0
        dx = {c: np.zeros(6) for c in P.cams}
        for i, c in enumerate(P.cv.released): dx[c] = res.x[6+6*i:12+6*i]
        X = res.x[6+6*nr:].reshape(-1, 3)
        P._last_dx = dx; info = dict(n_params=6+6*nr+3*nX)
    else:
        raise ValueError(mode)
    J = res.jac.toarray() if hasattr(res.jac, 'toarray') else np.asarray(res.jac)
    info.update(success=bool(res.success), status=int(res.status), nfev=int(res.nfev),
                cost=float(res.cost), rank=int(np.linalg.matrix_rank(J)),
                cond=float(np.linalg.svd(J, compute_uv=False)[0]/max(np.linalg.svd(J, compute_uv=False)[-1], 1e-30)),
                seconds=round(time.time()-t0, 2))
    return H, X, info


# ---------------- H candidates ----------------
def ring_energy_for_H(F, H, geom=None):
    """Ring I+C+O energy for the 004 cameras placed by H (no RGB, no GT).

    geom: FROZEN edge sets computed once from the INITIAL cameras (never GT). Projection is
    re-evaluated for each candidate H, so the energy still responds to H.
    """
    sc = F['sc']
    g = geom or F['geom4']
    cams = {c: np.asarray(sc['cams'][c][1], float) for c in sc['cams']}
    world = {c: (H @ cams[c] if sc['cams'][c][0] == '004' else cams[c]) for c in cams}
    e = 0.0
    for c in S.C4:
        for key, blk, w in (('inner', 'I', RING_W['I']), ('outer', 'O', RING_W['O']), ('mid', 'C', RING_W['C'])):
            d = BA.poly_dist(world[c], sc['K_of'][c], g[c]['V_' + key], g[c]['E_' + key],
                             F['ring_obs'][c].get(key, np.zeros((0, 2))))
            if len(d): e += 1.0*w*float(RE.rho(d/3).mean())
    return e


def sampson_px(Fm, p, q):
    p = np.c_[np.asarray(p, float), np.ones(len(p))]
    q = np.c_[np.asarray(q, float), np.ones(len(q))]
    Fa = (Fm @ p.T).T; Ftb = (Fm.T @ q.T).T
    num = np.abs(np.einsum('ij,ij->i', q, Fa))
    den = np.sqrt((Fa[:, :2]**2).sum(1) + (Ftb[:, :2]**2).sum(1)) + 1e-12
    return num/den


def epipolar_energy(F, H, fit_ids):
    """Median Sampson error over FIT cross-video identity observations, using only 2D data."""
    sc = F['sc']
    C4 = {c: H @ np.asarray(sc['cams'][c][1], float) for c in S.C4}
    C5 = {c: np.asarray(sc['C_gt'][c], float) for c in S.C5}
    obs = F['obs']
    by = {}
    for c, i, uv in obs:
        by.setdefault(i, []).append((c, np.asarray(uv, float)))
    errs = []
    for i in fit_ids:
        lst = by.get(i, [])
        for c4 in S.C4:
            for c5 in S.C5:
                u = [uv for (c, uv) in lst if c == c4]
                v = [uv for (c, uv) in lst if c == c5]
                if not u or not v: continue
                T = np.linalg.inv(C5[c5]) @ C4[c4]
                tx = np.array([[0, -T[2, 3], T[1, 3]], [T[2, 3], 0, -T[0, 3]], [-T[1, 3], T[0, 3], 0]])
                Fm = np.linalg.inv(sc['K_of'][c5]).T @ tx @ T[:3, :3] @ np.linalg.inv(sc['K_of'][c4])
                n = np.linalg.norm(Fm)
                if n < 1e-15: continue
                errs.extend(sampson_px(Fm/n, np.array(u), np.array(v)).tolist())
    return float(np.median(errs)) if errs else None


def ring_candidates(F, yaw_step=15, n_refine=6, lam_ring=1.0, lam_epi=1.0, fit_ids=None, seed=0):
    """H1: Ring-compatible candidates (coarse yaw grid + local Ring refinement), then H2 epipolar ranking."""
    sc = F['sc']
    fit_ids = fit_ids if fit_ids is not None else []
    cands = []
    for yaw in np.arange(0, 360, yaw_step):
        H0 = exp_se3(np.r_[np.zeros(3), np.array([0., 0., np.deg2rad(yaw)])])
        e = ring_energy_for_H(F, H0)
        # local refinement of the 6 DoF on Ring only (rotation/translation), starting at H0
        def f(t):
            H = exp_se3(t) @ H0
            return np.array([ring_energy_for_H(F, H)])
        r = least_squares(f, np.zeros(6), method='trf', loss='linear', x_scale='jac', max_nfev=40)
        Hr = exp_se3(r.x) @ H0
        cands.append(dict(yaw_init=float(yaw), H=Hr, ring=float(ring_energy_for_H(F, Hr)),
                          ring_raw=float(e), nfev=int(r.nfev)))
    cands.sort(key=lambda d: d['ring'])
    keep = cands[:max(n_refine, 12)]
    for i, d in enumerate(keep):
        d['id'] = i
        d['epi'] = epipolar_energy(F, d['H'], fit_ids)
        d['score'] = lam_ring*d['ring'] + lam_epi*(d['epi'] if d['epi'] is not None else 1e6)
    keep.sort(key=lambda d: d['score'])
    return cands, keep


# ---------------- joint triangulation under fixed H ----------------
def triangulate_under_H(F, H, obs=None, cams_extra=None, min_views=3):
    """Fix all cameras (004 via H) and triangulate each identity from its 2D observations."""
    sc = F['sc']; obs = obs if obs is not None else F['obs']
    world = {}
    for c in sc['cams']:
        T0 = np.asarray(sc['cams'][c][1], float)
        world[c] = (H @ T0) if sc['cams'][c][0] == '004' else T0
    nlm = len(F['X0'])
    xy = {c: np.full((nlm, 2), np.nan) for c in world}
    tracks = {i: [] for i in range(nlm)}
    for c, i, uv in obs:
        xy[c][i] = np.asarray(uv, float); tracks[i].append((c, i))
    shim = {c: dict(id=c, T=world[c], K=sc['K_of'][c]) for c in world}
    def fake(v):
        return dict(xy=xy[v['id']], des=np.zeros((nlm, 128), np.float32))
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


def gt_metrics(F, H, X, ids):
    sc = F['sc']
    dH = np.asarray(H) @ np.linalg.inv(sc['H'])
    H_rot = float(np.degrees(np.arccos(np.clip((np.trace(dH[:3, :3])-1)/2, -1, 1))))
    H_tr = float(np.linalg.norm(dH[:3, 3]))
    lm = float(np.median(np.linalg.norm(X - sc['X'][ids], axis=1))) if len(X) else None
    lm_mean = float(np.mean(np.linalg.norm(X - sc['X'][ids], axis=1))) if len(X) else None
    return dict(H_rot=H_rot, H_trans=H_tr, lm_med=lm, lm_mean=lm_mean, n_lm=int(len(X)))
