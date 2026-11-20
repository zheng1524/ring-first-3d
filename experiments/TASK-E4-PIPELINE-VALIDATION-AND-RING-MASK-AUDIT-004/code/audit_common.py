"""Shared helpers for the read-only audit TASK-E4-PIPELINE-VALIDATION-AND-RING-MASK-AUDIT-004.

No writes outside this audit directory. No solver is modified or re-run.
DXY is NOT imported; the small-hole rule is re-implemented here from its source text
(src/dxy_mid/_engine/ring_holes.py, RULE version 'ring_enclosed_small_background_v1').
"""
import json, math, hashlib, random
from pathlib import Path
import numpy as np
import cv2

WS = Path('/home/liu/ring_first_3d_workspace')
T002 = WS / 'experiments/TASK-E4-UNIFIED-PIPELINE-COMPLETION-002'
T001 = WS / 'experiments/TASK-E4-UNIFIED-RING-FIRST-HERO-DEPTH-001'
RUNS = T002 / 'runs/RF_ONLY_V1'
V6 = Path('/home/liu/polyp_research/ring_anchor_3d/experiments/ring_first_v6_local_reconstruction')
AUD = WS / 'experiments/TASK-E4-PIPELINE-VALIDATION-AND-RING-MASK-AUDIT-004'
GROUPS = ['G01', 'G02', 'G03', 'G05', 'G06']
VIDEOS = ['004', '005']

# ---------------------------------------------------------------- identity
def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()

def asset(p):
    p = Path(p)
    return dict(path=str(p), sha256=sha256(p), bytes=p.stat().st_size)

def jread(p):
    return json.loads(Path(p).read_text())

# ---------------------------------------------------------------- views
def views():
    return jread(T002 / 'audit/SELECTED_VIEWS.json')

def instance_views(g, v, role='FIT'):
    return [x for x in views()
            if x['meta']['case'] == g and x['meta']['video'] == v and x['meta']['role'] == role]

def load_cache(x):
    d = np.load(x['cache']['path'])
    return dict(RGB=d['RGB'], labels=d['labels'], K=d['K'])

# ---------------------------------------------------------------- cameras
def final_camera(g, v, cid):
    """Camera actually used downstream. 002 re-solves new instances; the four
    inherited 004 cases keep 001's frozen CAMERA_RESULT (never re-solved here)."""
    for base in (RUNS, T001 / 'runs/RF_ONLY_V1'):
        p = base / g / v / 'camera' / cid / 'CAMERA_RESULT.json'
        if p.exists():
            d = jread(p)
            d['_source_path'] = str(p)
            d['_source_task'] = '002_RF_ONLY_V1' if base == RUNS else '001_FROZEN_REFERENCE'
            return d
    return None

def ba_dir(g, v):
    for rev in ('REV2', 'REV1'):
        p = RUNS / g / v / 'reference_build' / rev / 'predictions'
        if (p / 'NATIVE_CALIBRATION_0.npz').exists():
            return p
    return None

def ba_cameras(g, v):
    d = ba_dir(g, v)
    if d is None:
        return None
    out = {'ids': list(np.load(d / 'NATIVE_CALIBRATION_0.npz')['ids'])}
    for ver in (0, 1):
        f = d / f'NATIVE_CALIBRATION_{ver}.npz'
        if f.exists():
            out[ver] = np.load(f)['c2w']
    return out

def obs_path(g, v, cid):
    d = ba_dir(g, v)
    if d is None:
        return None
    p = d.parent / 'observations' / f'{cid}_ring.npz'
    return p if p.exists() else None

def tracks_path(g, v):
    d = ba_dir(g, v)
    if d is None:
        return None
    p = d.parent / 'observations/tracks005.npz'
    return p if p.exists() else None

# ---------------------------------------------------------------- geometry
def project(X, C, K):
    q = (np.asarray(X, float) - C[:3, 3]) @ C[:3, :3]
    p = q @ np.asarray(K, float).T
    z = p[..., 2]
    with np.errstate(divide='ignore', invalid='ignore'):
        uv = p[..., :2] / np.where(np.abs(z) > 1e-12, z, np.nan)[..., None]
    return uv, z

def triangulate(x1, x2, C1, C2, K):
    """DLT for one point from two views (c2w)."""
    def rows(uv, C):
        P = np.asarray(K) @ np.c_[C[:3, :3].T, -C[:3, :3].T @ C[:3, 3]]
        u, v = uv
        return np.r_[u * P[2] - P[0], v * P[2] - P[1]].reshape(2, 4)
    A = np.r_[rows(x1, C1), rows(x2, C2)]
    _, _, Vt = np.linalg.svd(A)
    Xh = Vt[-1]
    if abs(Xh[3]) < 1e-12:
        return None
    return Xh[:3] / Xh[3]

def rot_deg(R0, R1):
    c = (np.trace(np.asarray(R0).T @ np.asarray(R1)) - 1) / 2
    return float(np.degrees(np.arccos(np.clip(c, -1, 1))))

def torus_mae(C, K, q):
    from ring_first_3d.mainline.native.camera import torus_contours
    from scipy.spatial import cKDTree
    cr = torus_contours(np.asarray(C), np.asarray(K)).reshape(-1, 2)
    d = cKDTree(cr).query(np.asarray(q))[0]
    d = np.asarray(d, float)
    if not len(d):
        return dict(N=0, MAE=float('nan'), p95=float('nan'))
    return dict(N=int(len(d)), MAE=float(d.mean()),
                median=float(np.median(d)), p95=float(np.percentile(d, 95)),
                maximum=float(d.max()))

# ---------------------------------------------------------------- ring observation variants
def edge_pts(mask):
    y, x = np.nonzero(mask[:, :-1] != mask[:, 1:]); a = np.c_[x + .5, y]
    y, x = np.nonzero(mask[:-1] != mask[1:]); return np.r_[a, np.c_[x, y + .5]]

def sample_pts(a, n=128):
    a = np.asarray(a)
    return a[np.linspace(0, len(a) - 1, min(n, len(a)), dtype=int)] if len(a) else a

def observed_boundary(labels):
    """Boundary points that native observe() actually samples from (occlusion-unknown removed)."""
    rm = labels == 2; pm = labels == 1
    bd = edge_pts(rm)
    near = cv2.dilate(pm.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    ix = np.clip(np.floor(bd + .5).astype(int), [0, 0], [639, 359])
    unknown = near[ix[:, 1], ix[:, 0]]
    return bd[~unknown]


def observe_train(labels, n=128):
    """Reproduce native.camera.observe()'s q_train exactly (same edge, same 5x5 polyp guard, same linspace)."""
    rm = labels == 2; pm = labels == 1
    bd = edge_pts(rm)
    near = cv2.dilate(pm.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    ix = np.clip(np.floor(bd + .5).astype(int), [0, 0], [639, 359])
    unknown = near[ix[:, 1], ix[:, 0]]
    return sample_pts(bd[~unknown], n), n

def dxy_hole_fill(labels):
    """Faithful re-implementation of DXY ring_holes.run (RULE ring_enclosed_small_background_v1).
    Copied semantics from src/dxy_mid/_engine/ring_holes.py; DXY is not imported or executed."""
    R = dict(area_fraction_max=.025, local_width_area_factor=.5, width_reference_quantile=.9,
             max_hole_span_width_factor=1.5, central_protection_area_radius_factor=.35)
    ring = labels == 2; result = labels.copy(); fill = np.zeros(labels.shape, bool)
    ys, xs = np.nonzero(ring); area = int(len(xs))
    if not area:
        return result, fill, dict(ring_area_px=0, filled_area_px=0, holes=[])
    dist = cv2.distanceTransform(ring.astype(np.uint8), cv2.DIST_L2, 5)
    width = 2 * float(np.quantile(dist[ring], R['width_reference_quantile']))
    limit = min(R['area_fraction_max'] * area, R['local_width_area_factor'] * width ** 2)
    centroid = np.array([xs.mean(), ys.mean()])
    prot = R['central_protection_area_radius_factor'] * math.sqrt(area / math.pi)
    n, cc, stats, centers = cv2.connectedComponentsWithStats((~ring).astype(np.uint8), 8)
    external = set(np.r_[cc[0, :], cc[-1, :], cc[:, 0], cc[:, -1]].tolist())
    holes = []
    for i in range(1, n):
        if i in external:
            continue
        x, y, w, h, a = map(int, stats[i]); pixels = cc == i; reason = ''
        if not np.all(labels[pixels] == 0):
            reason = 'contains_polyp_or_nonbackground_preserve'
        elif a > limit:
            reason = 'area_above_small_hole_limit_preserve_center'
        elif max(w, h) > R['max_hole_span_width_factor'] * width:
            reason = 'elongated_or_large_span_preserve'
        elif np.linalg.norm(centers[i] - centroid) < prot:
            reason = 'near_ring_material_centroid_preserve_center'
        boundary = cv2.dilate(pixels.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool) & ~pixels
        if not reason and not np.all(ring[boundary]):
            reason = 'not_completely_enclosed_by_actual_material'
        if not reason:
            fill |= pixels
        holes.append(dict(component=int(i), area_px=a, filled=not reason, reason=reason or 'filled_small_closed_hole'))
    result[fill] = 2
    assert np.array_equal(result == 1, labels == 1), 'POLYP_LABEL_CHANGED'
    assert np.array_equal(result[~fill], labels[~fill])
    assert not np.any(fill & (labels != 0))
    return result, fill, dict(ring_area_px=area, ring_width_reference_px=width,
                              area_limit_px=limit, filled_area_px=int(fill.sum()), holes=holes)

def components(labels):
    n, cc, stats, centers = cv2.connectedComponentsWithStats((labels == 2).astype(np.uint8), 8)
    comps = []
    for i in range(1, n):
        a = int(stats[i, cv2.CC_STAT_AREA])
        comps.append(dict(index=i, area_px=a, centroid=[float(centers[i][0]), float(centers[i][1])]))
    comps.sort(key=lambda c: -c['area_px'])
    return n - 1, comps, cc

def keep_only(labels, cc, comp_index):
    out = labels.copy(); rm = out == 2
    keep = cc == comp_index
    out[rm & ~keep] = 0
    return out

def close_open(labels, k=5):
    m = (labels == 2).astype(np.uint8)
    ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
    return cv2.morphologyEx(cv2.morphologyEx(m, cv2.MORPH_CLOSE, ker), cv2.MORPH_OPEN, ker)

# ---------------------------------------------------------------- bodies / iou
def load_body(g, v, arm='B1', which='FINAL'):
    p = RUNS / g / v / 'body' / arm / f'{which}.npz'
    if not p.exists():
        p = RUNS / g / v / 'body' / arm / 'FINAL.npz'
    if p.exists():
        d = np.load(p)
        return dict(V=d['V'], F=d['F'], path=str(p))
    # inherited 004: use exported aligned world mesh if present
    q = RUNS / g / v / 'exported'
    return None

def silhouette_iou(C, K, V, F, labels):
    q = (np.asarray(V, float) - C[:3, 3]) @ C[:3, :3]
    z = q[:, 2]
    with np.errstate(divide='ignore', invalid='ignore'):
        uv = (q @ np.asarray(K, float).T)[:, :2] / np.where(np.abs(z) > 1e-12, z, np.nan)[:, None]
    m = np.zeros(labels.shape, np.uint8)
    ok = np.isfinite(uv).all(1)
    for f in F:
        if not all(ok[f]) or not np.all(z[f] > 1e-6):
            continue
        cv2.fillPoly(m, [np.rint(uv[f]).astype(np.int32)], 1)
    gt = (labels == 1).astype(np.uint8)
    inter = int((m & gt).sum()); uni = int(((m > 0) | (gt > 0)).sum())
    return dict(IoU=inter / uni if uni else float('nan'), silture_px=int(m.sum()), polyp_px=int(gt.sum()))
