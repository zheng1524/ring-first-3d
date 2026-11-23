"""R2 synthetic Ring+RGB scene: GT -> observations -> (initial estimates) -> BA.

GT is produced by `build_scene` and consumed ONLY by `make_observations` and the final
evaluation. Optimisation inputs are observations + initial cameras + triangulated landmarks.
Feature ids are the landmark ids themselves (never re-derived from track order).
"""
import json, os, sys
from pathlib import Path
import numpy as np
WS = Path('/home/liu/ring_first_3d_workspace')
R = WS/'experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R5'
sys.path.insert(0, str(R/'core')); sys.path.insert(0, str(R/'replay')); sys.path.insert(0, str(WS/'src'))
os.environ.update(E4_RUN_DIR=str(R/'replay'),
    RING_CAD=str(WS/'assets/retained_sources/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-HERO-BODY-ADAPT-018/inputs/G03/RING.npz'),
    RING_NORM=str(WS/'assets/retained_sources/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/FREE_VERTEX_013/inputs/G03/NORMALIZATION.json'))
from se3 import exp_se3
import features019 as F19
import fixed_track_tri as FTT
from ring020_026 import RingRenderer
views = {v['id']: v for v in json.loads((R/'replay'/'config'/'VIEWS.json').read_text())}
split = json.loads((R/'runs'/'\u0053PLIT.json').read_text()) if (R/'runs/SPLIT.json').exists() else None
C4 = ['G03_v004_raw00202', 'G03_v004_raw00242', 'G03_v004_raw00263']
C5 = ['G03_v005_raw00070', 'G03_v005_raw00099', 'G03_v005_raw00114']


def project(X, C, K):
    q = (np.asarray(X, float) - C[:3, 3]) @ C[:3, :3]
    p = q @ np.asarray(K, float).T
    return p[:2]/p[2], p[2]


def build_scene(seed=0, nlm=12, H_rot_deg=(0.7, -0.4, 12.0), H_mm=(0.4, -0.3, 0.2), Kdiff=False):
    rng = np.random.default_rng(seed)
    H = exp_se3(np.r_[np.asarray(H_mm, float), np.deg2rad(H_rot_deg)])
    cams, Cgt, K_of = {}, {}, {}
    for c in C4:
        T0 = np.asarray(views[c]['T'], float); K = np.asarray(views[c]['K'], float)
        cams[c] = ('004', T0); Cgt[c] = H @ T0; K_of[c] = K * (1.04 if Kdiff else 1.0)
    for c in C5:
        T0 = np.asarray(views[c]['T'], float); K = np.asarray(views[c]['K'], float)
        cams[c] = ('005', T0); Cgt[c] = T0; K_of[c] = K
    X = np.c_[rng.uniform(-7, 7, nlm), rng.uniform(-7, 7, nlm), rng.uniform(-2, 2, nlm)]
    return dict(H=H, cams=cams, C_gt=Cgt, K_of=K_of, X=X, seed=seed)


def ring_observations(scene, rr):
    """GT Ring observations: project the fixed CAD with each GT camera (inner/outer/mid)."""
    obs = {}
    for c, C in scene['C_gt'].items():
        K = scene['K_of'][c]
        seg = rr.curves.segments(C, K)
        d = {}
        for key in ('inner', 'outer'):
            e = np.asarray(seg[key], int)
            V = rr.curves.V[e].reshape(-1, 3)
            d[key] = rr.curves.project(V, C, K).reshape(-1, 2) if len(e) else np.zeros((0, 2))
        mid = np.vstack([np.asarray(rr.curves.mid, float)])
        d['mid'] = rr.curves.project(mid, C, K)
        obs[c] = d
    return obs


def rgb_observations(scene, noise=0.0, wrong=0, seed=1):
    rng = np.random.default_rng(seed)
    obs = []
    for c, C in scene['C_gt'].items():
        for i in range(len(scene['X'])):
            p, z = project(scene['X'][i], C, scene['K_of'][c])
            if z > 0: obs.append((c, i, p + rng.normal(0, noise, 2) if noise else p))
    if wrong:
        idx = rng.permutation(len(obs))[:wrong]
        for k in idx:
            c, i, uv = obs[k]; obs[k] = (c, i, uv + rng.normal(0, 40, 2))
    return obs


def triangulate(obs, cams, K_of, nlm):
    """Historical 019 per-track code on STABLE (view, feature_id=landmark_id) keys."""
    xy = {c: np.full((nlm, 2), np.nan) for c in cams}
    tracks = {i: [] for i in range(nlm)}
    for c, i, uv in obs:
        xy[c][i] = uv; tracks[i].append((c, i))
    shim = {c: dict(id=c, T=cams[c][1], K=K_of[c]) for c in cams}
    def fake(v):
        return dict(xy=xy[v['id']], des=np.zeros((nlm, 128), np.float32))
    old = F19.features; F19.features = fake
    ids, out = [], []
    try:
        for i, tr in tracks.items():
            if len(tr) < 3: continue
            r = FTT.triangulate_tracks([tr], shim)[0]
            ids.append(i); out.append(r['X'])
    finally:
        F19.features = old
    return np.array(out), np.array(ids)
