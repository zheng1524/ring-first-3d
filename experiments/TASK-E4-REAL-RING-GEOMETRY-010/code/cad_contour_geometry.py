"""Correct DXY<->CAD geometry: spatial correspondence, perimeter-normalised weights.

Fixes 009:
  * correspondence by 2-D position (nearest DXY sample), never by sample index
  * normalisation by the FULL ellipse perimeter L_full (short arcs give LESS evidence)
  * no constant residual for UNOBSERVED (zero contribution + explicit status)
"""
import numpy as np
from pathlib import Path
import json
import contour_geometry as CG

DXY_DIR = Path('/home/liu/ring_first_3d_workspace/experiments/TASK-E4-REAL-RING-GEOMETRY-010/metrics/DXY_OBSERVATIONS')
TAU = 0.0
SIGMA = 1.0


def load(view):
    p = DXY_DIR/(view+'.json')
    return json.loads(p.read_text()) if p.exists() else None


def ellipse_pts(e, n=720):
    t = np.linspace(0, 2*np.pi, n, endpoint=False)
    c, s = np.cos(np.deg2rad(e['angle_deg'])), np.sin(np.deg2rad(e['angle_deg']))
    x = e['major_radius']*np.cos(t); y = e['minor_radius']*np.sin(t)
    return np.c_[c*x - s*y + e['cx'], s*x + c*y + e['cy']]


def perimeter(e, n=720):
    p = ellipse_pts(e, n)
    return float(np.linalg.norm(np.diff(np.r_[p, p[:1]], axis=0), axis=1).sum())


def boundary_support(rec, key, labels, tol=1.5, n=720):
    """Trusted real boundary support: DXY samples that coincide with actual ring-mask edge."""
    import cv2
    e = rec.get(key)
    if e is None:
        return None, None, None
    pts = ellipse_pts(e, n)
    ring = (labels == 2).astype(np.uint8)
    edge = cv2.Canny(ring*255, 50, 150)
    ys, xs = np.nonzero(edge)
    if len(ys) == 0:
        return pts, np.zeros(n, bool), perimeter(e, n)
    from scipy.spatial import cKDTree
    d, _ = cKDTree(np.c_[xs, ys].astype(float)).query(pts, k=1)
    return pts, d <= tol, perimeter(e, n)


def cad_blocks(pose, K, obs, which='both', tau=TAU, sigma=SIGMA, m=256):
    """Per-sample residual with perimeter normalisation + explicit UNOBSERVED handling."""
    from ring_first_3d.mainline.native.camera import torus_contours
    ci, co = CG.split_by_area(torus_contours(np.asarray(pose), np.asarray(K)))
    spec = ([('inner', ci)] if which == 'inner' else [('outer', co)] if which == 'outer'
            else [('inner', ci), ('outer', co)])
    parts, status = [], []
    for name, curve in spec:
        poly = obs.get(name+'_pts'); vis = obs.get(name+'_vis'); L = obs.get(name+'_perim')
        if curve is None or poly is None or L is None:
            parts.append(np.zeros(m)); status.append(name+':NO_DATA'); continue
        pts = CG.resample_closed(curve, m)
        d = CG.dist_to_polyline(pts, poly)
        w = np.zeros(m)
        if vis is not None and np.asarray(vis).any():
            # spatial correspondence: each CAD sample inherits the visibility of its nearest DXY sample
            from scipy.spatial import cKDTree
            _, idx = cKDTree(np.asarray(poly, float)).query(pts, k=1)
            w = np.asarray(vis, bool)[idx].astype(float)
        if w.sum() < 4:
            parts.append(np.zeros(m)); status.append(name+':UNOBSERVED'); continue
        r = np.maximum(0.0, d - tau)/sigma * np.sqrt(w/L)   # L_full, not sum(w)
        parts.append(r); status.append(f'{name}:ok(vis={int(w.sum())}/{m})')
    return np.concatenate(parts), status


def build_obs(view, labels, ob):
    rec = load(view)
    out = {'q_train': ob['q_train']}
    if rec is None or not rec.get('valid'):
        return out, None
    for key in ('inner', 'outer'):
        pts, vis, L = boundary_support(rec, key, labels)
        if pts is None:
            continue
        out[key+'_pts'] = pts; out[key+'_vis'] = vis; out[key+'_perim'] = L
    out['rec'] = rec
    return out, rec
