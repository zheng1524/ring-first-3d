"""Corrected inner/outer observation blocks for the joint BA.

Two fixes vs 010:
  * arc-length weights  r_j = sqrt(w_j * ds_j / L_ref) * (d_j - tau)_+ / sigma
    (M = 128/256/512 give the same normalised loss)
  * signed residual defined as  (p_DXY - p_CAD) . n_outward(CAD)  with an analytic check
  * UNOBSERVED -> zero residual + status (never a constant that fakes a gradient)
"""
import json
from pathlib import Path
import numpy as np
import contour_geometry as CG

DXY_DIR = Path('/home/liu/ring_first_3d_workspace/experiments/TASK-E4-RING-RGB-JOINT-BA-011/metrics/DXY_OBSERVATIONS')
SIGMA = 1.0
TAU = 0.0


def load(view):
    p = DXY_DIR/(view+'.json')
    return json.loads(p.read_text()) if p.exists() else None


def ellipse_pts(e, n=720):
    t = np.linspace(0, 2*np.pi, n, endpoint=False)
    c, s = np.cos(np.deg2rad(e['angle_deg'])), np.sin(np.deg2rad(e['angle_deg']))
    x = e['major_radius']*np.cos(t); y = e['minor_radius']*np.sin(t)
    return np.c_[c*x - s*y + e['cx'], s*x + c*y + e['cy']]


def trusted_support(rec, key, labels, tol=1.5, n=720):
    import cv2
    e = rec.get(key)
    if e is None:
        return None, None
    pts = ellipse_pts(e, n)
    edge = cv2.Canny(((labels == 2).astype(np.uint8))*255, 50, 150)
    ys, xs = np.nonzero(edge)
    if len(ys) == 0:
        return pts, np.zeros(n, bool)
    from scipy.spatial import cKDTree
    d, _ = cKDTree(np.c_[xs, ys].astype(float)).query(pts, k=1)
    return pts, d <= tol


def blocks(pose, K, obs, which='both', tau=TAU, sigma=SIGMA, m=256):
    from ring_first_3d.mainline.native.camera import torus_contours
    ci, co = CG.split_by_area(torus_contours(np.asarray(pose), np.asarray(K)))
    spec = ([('inner', ci)] if which == 'inner' else [('outer', co)] if which == 'outer'
            else [('inner', ci), ('outer', co)])
    parts, status = [], []
    for name, curve in spec:
        poly, vis = obs.get(name+'_pts'), obs.get(name+'_vis')
        if curve is None or poly is None:
            parts.append(np.zeros(m)); status.append(name+':NO_DATA'); continue
        pts = CG.resample_closed(curve, m)
        d = CG.dist_to_polyline(pts, poly)
        w = np.zeros(m)
        if vis is not None and np.asarray(vis).any():
            from scipy.spatial import cKDTree
            _, idx = cKDTree(np.asarray(poly, float)).query(pts, k=1)
            w = np.asarray(vis, bool)[idx].astype(float)
        if w.sum() < 4:
            parts.append(np.zeros(m)); status.append(name+':UNOBSERVED'); continue
        L_curve = float(np.linalg.norm(np.diff(np.r_[pts, pts[:1]], axis=0), axis=1).sum())
        ds = L_curve/m
        r = np.sqrt(w*ds/L_curve) * np.maximum(0.0, d-tau)/sigma     # ds/L_ref with L_ref=L_curve
        parts.append(r); status.append(f'{name}:ok(vis={int(w.sum())}/{m})')
    return np.concatenate(parts), status


def signed_residual(curve, poly, vis, n=720):
    """(p_DXY - p_CAD) . n_outward(CAD); positive = DXY lies outside the CAD curve."""
    from scipy.spatial import cKDTree
    p = np.asarray(poly, float)[np.asarray(vis, bool)]
    if len(p) == 0:
        return None
    dense = CG.resample_closed(curve, n)
    d, idx = cKDTree(dense).query(p, k=1)
    c = dense[idx]
    nrm = _outward(dense, idx)
    return ((p-c)*nrm).sum(1)


def _outward(dense, idx):
    nxt = dense[(idx+4) % len(dense)]; prv = dense[(idx-4) % len(dense)]
    tg = nxt-prv; tg /= np.maximum(np.linalg.norm(tg, axis=1, keepdims=True), 1e-9)
    nrm = np.c_[-tg[:, 1], tg[:, 0]]
    ctr = dense.mean(0)
    flip = ((dense[idx]-ctr)*nrm).sum(1) < 0
    nrm[flip] *= -1
    return nrm
