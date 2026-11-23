#!/usr/bin/env python3
"""028-CORRECTIVE unified pipeline (real data, group-agnostic).

ONE code path for every group. The group id only selects input paths and physical parameters.
Stages: ctx -> W0 (read or auto-replay) -> view selection -> Ring evidence/scores ->
features/landmarks -> cross-video identities (2D-geometry validated) -> FIT/HOLDOUT ->
H init (old reference-triangulation / new Ring+epipolar) -> joint triangulation -> joint BA -> eval.
"""
import argparse, hashlib, json, os, subprocess, sys, time
from pathlib import Path
import numpy as np, pandas as pd
WS = Path('/home/liu/ring_first_3d_workspace')
U = WS/'experiments/TASK-E4-W0-CROSSVIDEO-028-CORRECTIVE-FINAL'
ASSETS = WS/'assets/retained_sources/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/FREE_VERTEX_013/inputs'
PREP = WS/'experiments/TASK-E4-UNIFIED-RING-CONTOUR-REFINEMENT-005/runs/prepared'
DXY = Path('/home/liu/new-polyp-dxy/src/dxy_mid')
R6REPLAY = WS/'experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R6/replay'
sys.path.insert(0, str(U/'core'))
sys.path.insert(0, str(R6REPLAY))
import fixed_track_tri as FTT   # historical 019 triangulation code
sys.path.insert(0, str(WS/'camera_mainline/code'))
sys.path.insert(0, str(WS/'src'))


def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()


class Ctx:
    def __init__(self, group, max_views=6):
        self.g = group; self.max_views = max_views
        self.root = U/'runs'/group
        self.dirs = {k: self.root/k for k in ('input_manifest','w0','view_selection','ring','rgb_features',
                                              'identities','h_initialization','triangulation','ba','evaluation','figures')}
        for d in self.dirs.values(): d.mkdir(parents=True, exist_ok=True)
        self.manifest = {}
        self.cfg = json.loads((U/'config'/'PIPELINE.json').read_text())
        self.log = []

    def note(self, **kw):
        kw['t'] = round(time.time()-self.root.stat().st_mtime, 0)
        self.log.append(kw)

    def save_manifest(self):
        (self.dirs['input_manifest']/'MANIFEST.json').write_text(json.dumps(self.manifest, indent=1, default=str))
        pd.DataFrame(self.manifest.get('views', [])).to_csv(self.dirs['input_manifest']/'VIEWS.csv', index=False)


def videos_of(group):
    return [p.name.split('_')[-1] for p in sorted(PREP.glob(f'{group}_*')) if p.is_dir()]


def admission_of(group, video):
    for base in (WS/'camera_mainline'/group, U/'runs'/group/'w0'):
        p = base/f'video{video}'/'admission.csv'
        if p.exists():
            d = pd.read_csv(p)
            return dict(zip(d['view'].astype(str), d['admission_status'].astype(str))), str(p)
    return {}, None


def w0_ensure(ctx, video):
    """Return path to camera_result.npz; recompute with the FORMAL entry when missing."""
    g = ctx.g
    for p in (WS/'camera_mainline'/g/f'video{video}'/'camera_result.npz',
              ctx.dirs['w0']/f'video{video}'/'camera_result.npz'):
        if p.exists():
            return p, 'existing'
    out = ctx.dirs['w0']/f'video{video}'
    cmd = [sys.executable, str(WS/'tools'/'run_w0_camera.py'), '--group', g, '--video', video,
           '--stage', 'all', '--output', str(out)]
    r = subprocess.run(cmd, env=dict(os.environ), capture_output=True, text=True)
    (ctx.dirs['w0']/f'w0_{video}.log').write_text(r.stdout+r.stderr)
    if r.returncode != 0 or not (out/'camera_result.npz').exists():
        raise RuntimeError(f'W0_RECOMPUTE_FAILED {g}/{video} rc={r.returncode}')
    return out/'camera_result.npz', 'recomputed'


def ring_module():
    import importlib, types
    sys.path.insert(0, str(DXY.parent))
    pkg = types.ModuleType('dxy_mid'); pkg.__path__ = [str(DXY)]; sys.modules.setdefault('dxy_mid', pkg)
    return importlib.import_module('dxy_mid._engine.ring_component')


def ring_evidence(ctx, prep_views, ids):
    mod = ring_module(); out = ctx.dirs['ring']
    valid = {}
    for vid in ids:
        npz, js = out/(vid+'.npz'), out/(vid+'.json')
        if js.exists() and npz.exists():
            rep = json.loads(js.read_text())
        else:
            a = np.load(prep_views[vid]['cache'])
            rep, pay = mod.recover(a['labels'], a['RGB'][:, :, ::-1], 10.)
            np.savez_compressed(npz, inner=pay.get('inner_points', np.zeros((0,2))),
                                outer=pay.get('outer_points', np.zeros((0,2))),
                                rejected=pay.get('rejected_points', np.zeros((0,2))))
            js.write_text(json.dumps(rep))
        valid[vid] = bool(rep.get('inner') and rep.get('outer') and rep.get('centerline'))
    return valid


def build_views(ctx, video, ids, meta, T, K):
    """caches in the GROUP run dir with REAL sha256 of RGB/labels."""
    rep = ctx.dirs['rgb_features']/'replay'
    (rep/'inputs'/ctx.g).mkdir(parents=True, exist_ok=True)
    keep = (ctx.dirs['view_selection']/'frozen_views.json')
    frozen = json.loads(keep.read_text())[video] if (keep.exists() and video in json.loads(keep.read_text())) else None
    V = []
    for vid in ids:
        src = np.load(meta[vid]['cache'])
        rgb = src['RGB']; labels = src['labels']
        h = hashlib.sha256(rgb.tobytes()).hexdigest()[:32]
        dst = rep/'inputs'/ctx.g/(vid+'.npz')
        np.savez_compressed(dst, RGB=rgb, labels=labels, K=K, T=T[vid], RGB_SHA256=h)
        V.append(dict(id=vid, group=ctx.g, video=video, role='FIT', cache=str(dst), T=T[vid].tolist(),
                      K=K.tolist(), raw_frame=int(meta[vid]['raw_frame']), RGB_SHA256=h,
                      rgb_sha256_full=h))
        ctx.manifest.setdefault('views', []).append(dict(group=ctx.g, video=video, view=vid,
            raw_frame=int(meta[vid]['raw_frame']), rgb_sha256=h,
            cache_sha256=sha256(dst), cache=str(dst)))
    (rep/'config').mkdir(parents=True, exist_ok=True)
    (rep/'config'/'VIEWS.json').write_text(json.dumps(V, indent=1))
    return V, rep


def sift_count(rgb, labels):
    import cv2
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    ok = ((cv2.dilate((labels == 2).astype(np.uint8), np.ones((5, 5), np.uint8)) == 0) &
          (gray >= 12) & (gray < 245)).astype(np.uint8)
    ok[:8] = ok[-8:] = 0; ok[:, :8] = ok[:, -8:] = 0
    k, d = cv2.SIFT_create(nfeatures=4000, contrastThreshold=.01).detectAndCompute(gray, ok*255)
    return int(0 if k is None else len(k))


def select_views(ctx, video, cand, ring_valid, meta, T, max_views):
    """Unified selector: Ring-valid OR RGB-capable; greedy angular coverage; no time order."""
    rows = []
    for vid in cand:
        a = np.load(meta[vid]['cache'])
        nf = sift_count(a['RGB'], a['labels'])
        rows.append(dict(group=ctx.g, video=video, view=vid, raw_frame=int(meta[vid]['raw_frame']),
                         ring_valid=bool(ring_valid.get(vid)), n_sift=nf,
                         rgb_ok=bool(nf >= ctx.cfg['min_sift'])))
    df = pd.DataFrame(rows).sort_values('view').reset_index(drop=True)
    if df.empty: return df, []
    pool = df[df.ring_valid | df.rgb_ok]
    chosen = []
    if len(pool):
        C = {r.view: np.asarray(T[r.view], float)[:3, 3] for _, r in pool.iterrows()}
        # start from the view with the best (ring_valid, n_sift)
        first = pool.assign(k=pool.ring_valid.astype(int)*1000+pool.n_sift).sort_values('k', ascending=False).iloc[0]
        chosen = [first.view]
        while len(chosen) < min(max_views, len(pool)):
            best, bestd = None, -1
            for _, r in pool.iterrows():
                if r.view in chosen: continue
                d = min(np.linalg.norm(C[r.view]-C[c]) for c in chosen)
                score = d + (50.0 if r.ring_valid else 0.0) + 0.01*r.n_sift
                if score > bestd: bestd, best = score, r.view
            if best is None: break
            chosen.append(best)
    df['selected'] = df.view.isin(chosen)
    df['reason'] = np.where(df.selected, np.where(df.ring_valid, 'ring_valid+coverage', 'rgb_only+coverage'), '')
    return df, chosen


def ring_scores(ctx, rr, vid, cams, views_by_id):
    import torch
    from ring020_026 import tensor
    rows = []
    for v in vid:
        L, _, _ = rr.losses(tensor(np.eye(4), torch.float64), v)
        rows.append(dict(view=v, group=ctx.g, M=float(L['M']), I=float(L['I']), C=float(L['C']), O=float(L['O']),
                         MIO=0.25*float(L['M'])+0.35*float(L['I'])+0.35*float(L['O']),
                         MICO=0.25*float(L['M'])+0.35*float(L['I'])+0.05*float(L['C'])+0.35*float(L['O'])))
    return pd.DataFrame(rows)


def set_runtime(rep, V, feats):
    import common, features019 as F19
    common.R = rep; F19.R = rep
    F19.VIEWS = {x['id']: x for x in V}
    return F19, common


def compute_landmarks(ctx, F19, common, ids, label):
    lm = F19.landmarks(list(ids), label)
    obs = json.loads((ctx.dirs['rgb_features']/'replay'/'landmarks'/(label+'_OBSERVATIONS.json')).read_text())
    return dict(X=np.asarray(lm['X'], float), des=np.asarray(lm['des'], np.float32), obs=obs)


def build_identities(ctx, F19, ref, other, L_ref, L_oth, views_ref, views_oth, Vmap):
    amap = {(o['view'], int(f)): i for i, t in enumerate(L_ref['obs']) for o in t['observations'] for f in [o['feature_id']]}
    bmap = {(o['view'], int(f)): j for j, t in enumerate(L_oth['obs']) for o in t['observations'] for f in [o['feature_id']]}
    votes = {}
    for a in views_ref:
        for b in views_oth:
            try:
                m = F19.matches(Vmap[a], Vmap[b])
            except Exception:
                continue
            for k in np.flatnonzero(m['RGB_RANSAC']):
                ia, ib = m['index_pairs'][k]
                i = amap.get((a, int(ia))); j = bmap.get((b, int(ib)))
                if i is None or j is None: continue
                votes.setdefault((int(i), int(j)), []).append(dict(a=a, b=b, fa=int(ia), fb=int(ib),
                                                                   p=m['p'][k].tolist(), q=m['q'][k].tolist()))
    rows, rej = [], []
    used_i, used_j = set(), set()
    for (i, j), ev in sorted(votes.items(), key=lambda kv: -len(kv[1])):
        n_pairs = len({(e['a'], e['b']) for e in ev})
        st = 'MULTIVIEW_IDENTITY_SUPPORTED' if n_pairs >= 2 else 'TWO_VIEW_GEOMETRY_SUPPORTED'
        row = dict(identity=f'{ref}:{i}-{other}:{j}', ref_index=i, other_index=j, n_evidence=len(ev),
                   n_view_pairs=n_pairs, status=st,
                   support_ref=';'.join(sorted({e['a'] for e in ev})),
                   support_other=';'.join(sorted({e['b'] for e in ev})),
                   evidence=json.dumps(ev[:6]))
        if i in used_i or j in used_j:
            row['status'] = 'GEOMETRIC_CONFLICT'
            rej.append(row); continue
        used_i.add(i); used_j.add(j); rows.append(row)
    return pd.DataFrame(rows), pd.DataFrame(rej)


def triangulate_identities(F19, FTT, X0n, ids_rows, L_ref, L_oth, ref, other, cams, H, K):
    """One 3D point per identity from ALL its real 2D observations (both videos, fixed cameras)."""
    obs_ref = {i: L_ref['obs'][i]['observations'] for i in range(len(L_ref['obs']))}
    obs_oth = {j: L_oth['obs'][j]['observations'] for j in range(len(L_oth['obs']))}
    X, meta = [], []
    for _, r in ids_rows.iterrows():
        pts = []
        for o in obs_ref[int(r.ref_index)]:
            C = np.asarray(cams[ref][o['view']], float)
            pts.append((o['view'], np.asarray(o['uv'], float), C, ref))
        for o in obs_oth[int(r.other_index)]:
            C = H @ np.asarray(cams[other][o['view']], float)
            pts.append((o['view'], np.asarray(o['uv'], float), C, other))
        if len(pts) < 3: continue
        # historical 019 per-track code via shim features
        xy = np.array([p[1] for p in pts]); Cw = [p[2] for p in pts]
        shim = {f'v{k}': dict(id=f'v{k}', T=Cw[k], K=np.asarray(K[pts[k][3]], float)) for k in range(len(pts))}
        tr = [(f'v{k}', k) for k in range(len(pts))]
        def fake(v, _xy=xy, _n=len(xy)):
            return dict(xy=_xy, des=np.zeros((_n, 128), np.float32))
        old = F19.features; F19.features = fake
        try:
            res = FTT.triangulate_tracks([tr], shim)[0]
        finally:
            F19.features = old
        X.append(res['X'])
        meta.append(dict(identity=r.identity, n_obs=len(pts), view_pairs=int(r.n_view_pairs),
                         parallax_deg=float(res['parallax']), reproj_max=float(res['reproj'].max()),
                         zmin=float(res['z'].min()), status=r.status))
    return np.array(X), pd.DataFrame(meta)


def ring_vector(rr, video, view, C):
    """Formal I/C/O residual vector at an ACTUAL camera (same construction as the BA)."""
    import torch
    from ring020_026 import tensor
    inc = np.asarray(C, float) @ np.linalg.inv(np.asarray(rr.data[view]['meta']['T'], float).reshape(4, 4))
    L, _, _ = rr.losses(tensor(inc, torch.float64), view)
    e = rr.data[view]['evidence']
    seg = rr.curves.segments(np.asarray(C, float), np.asarray(rr.data[view]['meta']['K'], float).reshape(3, 3))
    out = []
    mid = np.asarray(rr.curves.mid, float); Vm = np.vstack([mid, mid[:1]])
    cand = (('inner', 0.35, np.asarray(rr.curves.V, float), np.asarray(seg['inner'], int).reshape(-1, 2)),
            ('outer', 0.35, np.asarray(rr.curves.V, float), np.asarray(seg['outer'], int).reshape(-1, 2)),
            ('mid', 0.05, Vm, np.c_[np.arange(len(Vm)-1), np.arange(1, len(Vm))]))
    for key, w, Vfull, E in cand:
        if not len(E): continue
        Vv = Vfull[E].reshape(-1, 3)
        P = rr.curves.project(Vv, np.asarray(C, float), np.asarray(rr.data[view]['meta']['K'], float).reshape(3, 3)).reshape(-1, 2)
        q = np.asarray(e[key], float)
        A, B = P[0::2], P[1::2]; v = B - A; den = (v*v).sum(1)+1e-12
        t = np.clip(((q[:, None]-A[None])*v[None]).sum(-1)/den[None], 0, 1)
        cl = A[None]+t[..., None]*v[None]
        d = np.sqrt(((q[:, None]-cl)**2).sum(-1).min(1)+1e-12)
        out.append(np.sqrt(2.0*w*np.where(d/3 < 1, 0.5*(d/3)**2, np.abs(d/3)-0.5)/max(len(d), 1)))
    if not out: return None                     # RING_EDGE_NOT_EVALUABLE (never silently zero)
    return np.concatenate(out)


def ring_candidates(ctx, rr, ref, other, cams, K, views_oth, fit_ids, ids_rows, yaw_step=30, max_nfev=30):
    rows, cands = [], []
    for yaw in np.arange(0, 360, yaw_step):
        H0 = __import__('se3').exp_se3(np.r_[np.zeros(3), np.array([0., 0., np.deg2rad(yaw)])])
        def f(t):
            H = __import__('se3').exp_se3(t) @ H0
            parts = [ring_vector(rr, other, v, H @ np.asarray(cams[other][v], float)) for v in views_oth]
            if any(x is None for x in parts): return np.full(1, 1e3)   # unobservable candidate penalty
            return np.concatenate(parts)
        from scipy.optimize import least_squares
        r = least_squares(f, np.zeros(6), method='trf', loss='linear', x_scale='jac', max_nfev=max_nfev)
        H = __import__('se3').exp_se3(r.x) @ H0
        ring_e = float(0.5*(f(r.x)**2).sum())
        ep = epipolar_score(ids_rows, fit_ids, ref, other, cams, K, H)
        valid = (ep['status'] == 'OK')
        score = (ctx.cfg['lam_ring']*ring_e + ctx.cfg['lam_epi']*ep['epi']) if valid else float('inf')
        cands.append(dict(yaw_initial=float(yaw), H=H, ring=ring_e, epi=ep['epi'],
                          epi_status=ep['status'], n_fit_ids=ep['n_ids'], n_corr=ep['n_corr'],
                          valid=bool(valid), score=score, nfev=int(r.nfev), success=bool(r.success)))
    rows = [{k: v for k, v in c.items() if k != 'H'} for c in cands]
    pd.DataFrame(rows).to_csv(ctx.dirs['h_initialization']/'H_CANDIDATES.csv', index=False)
    valid_c = [c for c in cands if c['valid']]
    pool = valid_c if valid_c else cands
    pool.sort(key=lambda c: (c['score'], c['ring']))
    return pool, (valid_c != [])


def sampson_px(Fm, p, q):
    Fa = Fm @ p; Fb = Fm.T @ q
    return abs(float(q @ Fa))/float(np.sqrt(Fa[0]**2+Fa[1]**2+Fb[0]**2+Fb[1]**2+1e-12))


def epipolar_score(ids_rows, fit_rows, ref, other, cams, K, H):
    """FIT identities are selected by CSV ROW POSITION (identity id), never by landmark index.

    F is built for x_other^T F x_ref = 0 with T = C_other^-1 C_ref:
        F = K_other^-T [t]_x R K_ref^-1
    """
    errs, n_corr, n_ids = [], 0, 0
    sub = ids_rows.iloc[list(fit_rows)] if len(ids_rows) else ids_rows
    for _, r in sub.iterrows():
        ev = json.loads(r.evidence)
        per = []
        for e in ev:
            Ca = np.asarray(cams[ref][e['a']], float); Cb = H @ np.asarray(cams[other][e['b']], float)
            T = np.linalg.inv(Cb) @ Ca
            R, t = T[:3, :3], T[:3, 3]
            tx = np.array([[0, -t[2], t[1]], [t[2], 0, -t[0]], [-t[1], t[0], 0]])
            Fm = np.linalg.inv(np.asarray(K[other], float)).T @ tx @ R @ np.linalg.inv(np.asarray(K[ref], float))
            n = np.linalg.norm(Fm)
            if n < 1e-15: continue
            Fm = Fm/n; p = np.r_[e['p'], 1.]; q = np.r_[e['q'], 1.]
            v = sampson_px(Fm, p, q)
            if np.isfinite(v): per.append(v); n_corr += 1
        if per: errs.append(float(np.median(per))); n_ids += 1
    epi = float(np.median(errs)) if errs else None
    return dict(epi=epi, n_ids=n_ids, n_corr=n_corr, status='OK' if (epi is not None and n_ids > 0 and n_corr > 0) else 'EPIPOLAR_UNOBSERVABLE')


def solve_pipeline(ctx, rr, ref, other, cams, K, ids_rows, L_ref, L_oth, X0n, H_init, mode, budget):
    import ba_core_r4 as BA, camvar
    from se3 import exp_se3
    # BA core expects one transformed video ('004' role) + one reference ('005' role):
    role = {ref: '005', other: '004'}
    cams_d = {c: (role[v], np.asarray(cams[v][c], float)) for v in (ref, other) for c in cams[v]}
    obs = []
    for k, (_, r) in enumerate(ids_rows.iterrows()):
        for o in L_ref['obs'][int(r.ref_index)]['observations']:
            obs.append((o['view'], k, np.asarray(o['uv'], float)))
        for o in L_oth['obs'][int(r.other_index)]['observations']:
            obs.append((o['view'], k, np.asarray(o['uv'], float)))
    cv = camvar.CameraVariables(cams_d, list(cams[ref].keys())[0], [])
    # ring observations (all views, I/C/O evidence arrays)
    ring_obs = {v: {k: np.asarray(rr.data[v]['evidence'][k], float) for k in ('inner', 'outer', 'mid')}
                for v in cams_d}
    geom = {}
    for v in cams_d:
        # geometry from INITIAL cameras (H_init applied to the other video's cameras)
        C0 = (np.asarray(cams[ref][v], float) if v in cams[ref] else H_init @ np.asarray(cams[other][v], float))
        seg = rr.curves.segments(np.asarray(C0, float), K[ref] if v in cams[ref] else K[other])
        mid = np.asarray(rr.curves.mid, float); Vm = np.vstack([mid, mid[:1]])
        geom[v] = {'V_inner': np.asarray(rr.curves.V, float), 'E_inner': np.asarray(seg['inner'], int).reshape(-1, 2),
                   'V_outer': np.asarray(rr.curves.V, float), 'E_outer': np.asarray(seg['outer'], int).reshape(-1, 2),
                   'V_mid': Vm, 'E_mid': np.c_[np.arange(len(Vm)-1), np.arange(1, len(Vm))]}
    P = BA.BAProblemR4(cams_d, {**{v: K[ref] for v in cams[ref]}, **{v: K[other] for v in cams[other]}},
                       obs, ring_obs, X0n, cv, geom, lam_ring=1.0)
    from scipy.optimize import least_squares
    dx0 = {c: np.zeros(6) for c in P.cams}
    if mode == 'M2':
        f = lambda t: P.residual_vector(__import__('se3').exp_se3(t[:6]) @ H_init, dx0, X0n, 'huber')[0]
        r = least_squares(f, np.zeros(6), method='trf', loss='linear', x_scale='jac', max_nfev=budget)
        H = __import__('se3').exp_se3(r.x) @ H_init; X = X0n
    elif mode == 'M3b':
        fh = lambda t: P.residual_vector(__import__('se3').exp_se3(t[:6]) @ H_init, dx0, X0n, 'huber')[0]
        r1 = least_squares(fh, np.zeros(6), method='trf', loss='linear', x_scale='jac', max_nfev=max(1, budget//2))
        H1 = __import__('se3').exp_se3(r1.x) @ H_init
        fj = lambda t: P.residual_vector(__import__('se3').exp_se3(t[:6]) @ H1, dx0, t[6:].reshape(-1, 3), 'huber')[0]
        r = least_squares(fj, np.r_[np.zeros(6), X0n.ravel()], method='trf', loss='linear', x_scale='jac',
                          max_nfev=max(1, budget-int(r1.nfev)))
        H = __import__('se3').exp_se3(r.x[:6]) @ H1; X = r.x[6:].reshape(-1, 3)
    else:
        raise ValueError(mode)
    J = r.jac.toarray() if hasattr(r.jac, 'toarray') else np.asarray(r.jac)
    return H, X, dict(mode=mode, success=bool(r.success), status=int(r.status), nfev=int(r.nfev),
                      cost=float(r.cost), n_params=int(J.shape[1]), rank=int(np.linalg.matrix_rank(J)))


def evaluate(ctx, rr, ref, other, cams, K, ids_rows, X, H, fit_idx, ho_idx):
    rows = []
    for k, (_, r) in enumerate(ids_rows.iterrows()):
        for video, lm_i, sign in ((ref, int(r.ref_index), 1), (other, int(r.other_index), -1)):
            obs = (ctx.L[ref] if video == ref else ctx.L[other])['obs'][lm_i]['observations']
            Kk = K[ref] if video == ref else K[other]
            for o in obs:
                C = np.asarray(cams[ref][o['view']], float) if video == ref else H @ np.asarray(cams[other][o['view']], float)
                q = (X[k]-C[:3, 3]) @ C[:3, :3]; p = q @ Kk.T
                if p[2] <= 0: rows.append(dict(identity=k, group='fit' if k in fit_idx else 'holdout', neg=1, err=np.nan)); continue
                rows.append(dict(identity=k, group='fit' if k in fit_idx else 'holdout', neg=0,
                                 err=float(np.linalg.norm(p[:2]/p[2]-np.asarray(o['uv'], float)))))
    d = pd.DataFrame(rows)
    out = {}
    for g in ('fit', 'holdout'):
        e = d[(d.group == g) & (d.neg == 0)].err.dropna()
        out[g] = dict(n=int(len(e)), median=float(e.median()) if len(e) else None,
                      p90=float(e.quantile(.9)) if len(e) else None, neg=int(d[(d.group == g)].neg.sum()))
    ring = []
    for video in (ref, other):
        for v in cams[video]:
            C = np.asarray(cams[video][v], float) if video == ref else H @ np.asarray(cams[video][v], float)
            rv = ring_vector(rr, video, v, C)
            ring.append(dict(video=video, view=v, ring_energy=float(0.5*(rv**2).sum())))
    rg = pd.DataFrame(ring)
    out['ring'] = dict(median_energy=float(rg.ring_energy.median()), n_views=int(len(rg)))
    return out, d, rg


def _tri_one(F19, FTT, pts, K):
    if len(pts) < 3: return None, None
    xy = np.array([p[1] for p in pts]); Cw = [p[2] for p in pts]
    shim = {f'v{k}': dict(id=f'v{k}', T=Cw[k], K=np.asarray(K, float)) for k in range(len(pts))}
    tr = [(f'v{k}', k) for k in range(len(pts))]
    def fake(v, _xy=xy):
        return dict(xy=_xy, des=np.zeros((len(_xy), 128), np.float32))
    old = F19.features; F19.features = fake
    try:
        r = FTT.triangulate_tracks([tr], shim)[0]
    finally:
        F19.features = old
    return r['X'], r


def triangulate_ref_only(F19, FTT, rows, L_ref, ref, cams, K):
    X, meta = [], []
    for _, r in rows.iterrows():
        pts = [(o['view'], np.asarray(o['uv'], float), np.asarray(cams[ref][o['view']], float))
               for o in L_ref['obs'][int(r.ref_index)]['observations']]
        Xi, rr = _tri_one(F19, FTT, pts, K)
        if Xi is None:
            meta.append(dict(identity=r.identity, status='TRIANGULATION_FAILED')); continue
        X.append(Xi); meta.append(dict(identity=r.identity, n_ref_obs=len(pts), parallax_deg=float(rr['parallax']),
                                       reproj_max=float(rr['reproj'].max()), status='REF_ONLY_OK'))
    return (np.array(X) if X else np.zeros((0, 3))), pd.DataFrame(meta)


def reproj_stats(X, H, rows, L_ref, L_oth, ref, other, cams, K, out_csv=None):
    errs, neg, rec = [], 0, []
    for k, (_, r) in enumerate(rows.iterrows()):
        if k >= len(X): break
        for video, li in ((ref, int(r.ref_index)), (other, int(r.other_index))):
            obs = (L_ref if video == ref else L_oth)['obs'][li]['observations']
            Kk = np.asarray(K[ref] if video == ref else K[other], float)
            for o in obs:
                C = np.asarray(cams[ref][o['view']], float) if video == ref else H @ np.asarray(cams[other][o['view']], float)
                q = (X[k]-C[:3, 3]) @ C[:3, :3]; p = q @ Kk.T
                if p[2] <= 0: neg += 1; rec.append(dict(identity=k, video=video, view=o['view'], neg=1, err=np.nan)); continue
                e = float(np.linalg.norm(p[:2]/p[2]-np.asarray(o['uv'], float)))
                errs.append(e); rec.append(dict(identity=k, video=video, view=o['view'], neg=0, err=e))
    if out_csv is not None: pd.DataFrame(rec).to_csv(out_csv, index=False)
    a = np.array(errs) if errs else np.zeros(0)
    return dict(n=int(len(a)), median=float(np.median(a)) if len(a) else None,
                p90=float(np.percentile(a, 90)) if len(a) else None, neg=int(neg))


def holdout_stats(H, rows_ho, L_ref, L_oth, ref, other, cams, K, F19, FTT, out_csv=None):
    """Independent: triangulate from REF observations ONLY, then predict OTHER-video observations."""
    errs, neg, rec = [], 0, []
    for _, r in rows_ho.iterrows():
        pts = [(o['view'], np.asarray(o['uv'], float), np.asarray(cams[ref][o['view']], float))
               for o in L_ref['obs'][int(r.ref_index)]['observations']]
        Xi, _ = _tri_one(F19, FTT, pts, K[ref])
        if Xi is None:
            rec.append(dict(identity=r.identity, status='TRIANGULATION_FAILED')); continue
        for o in L_oth['obs'][int(r.other_index)]['observations']:
            C = H @ np.asarray(cams[other][o['view']], float)
            q = (Xi-C[:3, 3]) @ C[:3, :3]; p = q @ np.asarray(K[other], float).T
            if p[2] <= 0: neg += 1; rec.append(dict(identity=r.identity, neg=1, err=np.nan)); continue
            e = float(np.linalg.norm(p[:2]/p[2]-np.asarray(o['uv'], float)))
            errs.append(e); rec.append(dict(identity=r.identity, view=o['view'], neg=0, err=e))
    if out_csv is not None: pd.DataFrame(rec).to_csv(out_csv, index=False)
    a = np.array(errs) if errs else np.zeros(0)
    return dict(n=int(len(a)), median=float(np.median(a)) if len(a) else None,
                p90=float(np.percentile(a, 90)) if len(a) else None, neg=int(neg))


def ring_energy_all(rr, ref, other, cams, K, H):
    e = []
    for video, sign in ((ref, 1), (other, -1)):
        for v in cams[video]:
            C = np.asarray(cams[video][v], float) if video == ref else H @ np.asarray(cams[other][v], float)
            rv = ring_vector(rr, video, v, C)
            if rv is not None: e.append(float(0.5*(rv**2).sum()))
    a = np.array(e) if e else np.zeros(0)
    return dict(median=float(np.median(a)) if len(a) else None, n_valid=int(len(a)))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--group', required=True)
    ap.add_argument('--max-views', type=int, default=6)
    a = ap.parse_args(); ctx = Ctx(a.group, a.max_views)
    t0 = time.time(); g = ctx.g
    cams, K, prep_all, ring_valid = {}, {}, {}, {}
    vids = videos_of(g)
    admission = {}
    for v in vids:
        p, how = w0_ensure(ctx, v)
        cam = np.load(p); ids = [str(x) for x in cam['ids']]
        prep = json.loads((PREP/f'{g}_{v}'/'PREPARED.json').read_text())
        meta = {x['view']: x for x in prep['views']}
        cams[v] = {i: np.asarray(cam['c2w'][k], float) for k, i in enumerate(ids)}
        K[v] = np.asarray(cam['K'], float); prep_all[v] = meta
        admission[v] = admission_of(g, v)[0]
        ring_valid.update(ring_evidence(ctx, meta, ids))
        ctx.manifest[f'w0_{v}'] = dict(path=str(p), how=how, sha256=sha256(p), n_views=len(ids),
                                       n_accept=sum(1 for i in ids if admission[v].get(i) == 'ACCEPT'))
    # unified view selection (same rule for all groups/videos)
    sel = {}
    for v in vids:
        df, chosen = select_views(ctx, v, list(cams[v]), ring_valid, prep_all[v], cams[v], a.max_views)
        df.to_csv(ctx.dirs['view_selection']/f'SELECT_{v}.csv', index=False)
        sel[v] = chosen
        if not chosen: raise RuntimeError(f'NO_VIEW_SELECTED {g}/{v}')
    ctx.dirs['view_selection'].joinpath('frozen_views.json').write_text(json.dumps({v: sel[v] for v in sel}, indent=1))
    cams = {v: {k: cams[v][k] for k in sel[v]} for v in vids}     # only selected views enter the geometry
    # build caches and runtime
    V, rep = [], None
    for v in vids:
        Vi, rep = build_views(ctx, v, sel[v], prep_all[v], cams[v], K[v]); V += Vi
    (rep/'config'/'VIEWS.json').write_text(json.dumps(V, indent=1))
    import common, features019 as F19
    common.R = rep; F19.R = rep; F19.VIEWS = {x['id']: x for x in V}
    for x in V: F19.features(F19.VIEWS[x['id']])
    # landmarks per video (selected views only)
    Lm = {}
    for v in vids:
        Lm[v] = compute_landmarks(ctx, F19, common, sel[v], f'{g}_{v}_FIT')
    # reference video: unified rule = most admitted views, then most landmarks
    ref = max(vids, key=lambda v: (sum(1 for i in cams[v] if admission[v].get(i) == 'ACCEPT'), len(Lm[v]['X']), -int(v)))
    others = [v for v in vids if v != ref]
    if not others: raise RuntimeError('SINGLE_VIDEO_GROUP')
    other = others[0]
    ctx.L = Lm
    ids_rows, rejected = build_identities(ctx, F19, ref, other, Lm[ref], Lm[other], sel[ref], sel[other], F19.VIEWS)
    ids_rows.to_csv(ctx.dirs['identities']/'IDENTITIES.csv', index=False)
    rejected.to_csv(ctx.dirs['identities']/'REJECTED.csv', index=False)
    rng = np.random.default_rng(2028); idx = np.arange(len(ids_rows)); rng.shuffle(idx)
    nfit = max(1, int(round(0.7*len(ids_rows)))) if len(ids_rows) else 0
    fit_idx, ho_idx = sorted(idx[:nfit].tolist()), sorted(idx[nfit:].tolist())
    (ctx.dirs['identities']/'SPLIT.json').write_text(json.dumps(dict(ref=ref, other=other, n=int(len(ids_rows)),
        fit=[int(x) for x in fit_idx], holdout=[int(x) for x in ho_idx]), indent=1))
    # Ring scores for BOTH videos (all selected views)
    if not (rep/'ring').exists(): (rep/'ring').symlink_to(ctx.dirs['ring'])
    os.environ['E4_RUN_DIR'] = str(rep)
    os.environ['RING_CAD'] = str(ASSETS/g/'RING.npz')
    os.environ['RING_NORM'] = str(ASSETS/g/'NORMALIZATION.json')
    import ring020_026, torch
    ring020_026.R = rep
    rr = ring020_026.RingRenderer(sorted(x['id'] for x in V))
    rs = []
    for v in vids: rs.append(ring_scores(ctx, rr, sel[v], cams[v], F19.VIEWS))
    pd.concat(rs).to_csv(ctx.dirs['ring']/'RING_SCORES.csv', index=False)
    status = dict(group=g, videos=vids, ref=ref, other=other, n_views={v: len(sel[v]) for v in vids},
                  n_landmarks={v: int(len(Lm[v]['X'])) for v in vids}, n_identities=int(len(ids_rows)),
                  n_rejected=int(len(rejected)), n_fit=int(len(fit_idx)), n_holdout=int(len(ho_idx)),
                  ring_MIO_median=float(pd.concat(rs).MIO.median()))
    if len(ids_rows) < 3:
        status['status'] = 'GEOMETRY_INSUFFICIENT_EVIDENCE'
        status['reason'] = f'only {len(ids_rows)} cross-video identities after 2D validation'
        (ctx.root/'SUMMARY.json').write_text(json.dumps(status, indent=1, default=int))
        print('INSUFFICIENT', g, status['reason']); return
    # ---- FIT-only optimisation, HOLDOUT touched only for evaluation (A3/A4) ----
    rows_fit = ids_rows.iloc[fit_idx].reset_index(drop=True)
    rows_ho = ids_rows.iloc[ho_idx].reset_index(drop=True)
    X_ref, meta_ref = triangulate_ref_only(F19, FTT, rows_fit, Lm[ref], ref, cams, K[ref])
    meta_ref.to_csv(ctx.dirs['triangulation']/'X_REF_ONLY.csv', index=False)
    cands, epi_ok = ring_candidates(ctx, rr, ref, other, cams, K, sel[other], list(range(len(rows_fit))), rows_fit,
                                    yaw_step=45, max_nfev=15)
    H_new = cands[0]['H']
    rows = []
    # OLD: reference-only structure -> H-only -> joint triangulation -> Joint(H,X)
    H_old, _, i2 = solve_pipeline(ctx, rr, ref, other, cams, K, rows_fit, Lm[ref], Lm[other], X_ref, np.eye(4), 'M2', 40)
    Xn_old, m_old = triangulate_identities(F19, FTT, None, rows_fit, Lm[ref], Lm[other], ref, other, cams, H_old, K)
    m_old.to_csv(ctx.dirs['triangulation']/'TRI_old.csv', index=False)
    H_old3, X_old3, i3 = solve_pipeline(ctx, rr, ref, other, cams, K, rows_fit, Lm[ref], Lm[other], Xn_old, H_old, 'M3b', 40)
    # NEW: Ring+RGB candidate -> joint triangulation -> Joint(H,X)
    Xn_new, m_new = triangulate_identities(F19, FTT, None, rows_fit, Lm[ref], Lm[other], ref, other, cams, H_new, K)
    m_new.to_csv(ctx.dirs['triangulation']/'TRI_new.csv', index=False)
    H_new3, X_new3, i4 = solve_pipeline(ctx, rr, ref, other, cams, K, rows_fit, Lm[ref], Lm[other], Xn_new, H_new, 'M3b', 40)
    for name, H0, Hf, Xf, info, Xtri in (('old', H_old, H_old3, X_old3, i3, Xn_old), ('new', H_new, H_new3, X_new3, i4, Xn_new)):
        fit_ev = reproj_stats(Xf, Hf, rows_fit, Lm[ref], Lm[other], ref, other, cams, K)
        ho_ev = holdout_stats(Hf, rows_ho, Lm[ref], Lm[other], ref, other, cams, K, F19, FTT)
        ring_now = ring_energy_all(rr, ref, other, cams, K, Hf)
        rows.append(dict(pipeline=name, H_init_rot_deg=float(np.degrees(np.linalg.norm(
                                        __import__('scipy.spatial.transform', fromlist=['Rotation']).Rotation.from_matrix(
                                            (H0 @ np.linalg.inv(np.array([[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]])))[:3,:3]).as_rotvec()))),
                         success=bool(info['success']), nfev=info['nfev'], n_params=info['n_params'],
                         fit_median=fit_ev['median'], fit_p90=fit_ev['p90'], fit_n=fit_ev['n'], neg=fit_ev['neg'],
                         ho_median=ho_ev['median'], ho_p90=ho_ev['p90'], ho_n=ho_ev['n'], ho_neg=ho_ev['neg'],
                         ring_energy=ring_now['median'], ring_valid_views=ring_now['n_valid']))
        np.savez(ctx.dirs['ba']/f'{name}.npz', H_initial=H0, H=Hf, X=Xf, X_init=Xtri)
        reproj_stats(Xf, Hf, rows_fit, Lm[ref], Lm[other], ref, other, cams, K, out_csv=ctx.dirs['evaluation']/f'REPROJ_FIT_{name}.csv')
        holdout_stats(Hf, rows_ho, Lm[ref], Lm[other], ref, other, cams, K, F19, FTT,
                      out_csv=ctx.dirs['evaluation']/f'REPROJ_HOLDOUT_{name}.csv')
        print('PIPE', g, name, 'fit', None if fit_ev['median'] is None else round(fit_ev['median'], 2),
              'hold', None if ho_ev['median'] is None else round(ho_ev['median'], 2),
              'ring', round(ring_now['median'], 4), flush=True)
    pd.DataFrame(rows).to_csv(ctx.dirs['evaluation']/'OLD_VS_NEW.csv', index=False)
    status.update(dict(status='GEOMETRY_OK' if all(np.isfinite(r['fit_median'] or np.nan) for r in rows) else 'GEOMETRY_PARTIAL',
                       pipelines=rows, epi_available=bool(epi_ok),
                       n_fit_used=int(len(rows_fit)), n_holdout_used=int(len(rows_ho)),
                       seconds=round(time.time()-t0, 1)))
    (ctx.root/'SUMMARY.json').write_text(json.dumps(status, indent=1, default=int))
    ctx.save_manifest()
    print('DONE', g, json.dumps({'status': status['status'], 'n_fit': int(len(rows_fit)),
                                 'n_hold': int(len(rows_ho)), 'epi_ok': bool(epi_ok)}))


if __name__ == '__main__':
    main()
