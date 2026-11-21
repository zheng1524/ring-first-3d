"""Corrected J2 ring observation: verified CAD margin, pose-dependent invalid fallback.

Only the adapter changes; frozen BA, DXY, CAD are untouched.
"""
import numpy as np
from scipy.spatial import cKDTree
import sys
from pathlib import Path
R_CAD, r_CAD = 5.6, 0.6
MARGIN_SAFE, MARGIN_SCALE, BARRIER_W = 0.30, 0.10, 3.0
TAU, SIGMA, M_DEFAULT = 0.0, 1.0, 256
_DENSE_THETA = np.linspace(0, 2*np.pi, 20001, endpoint=False)


def cad_margin_analytic(pose):
    """min_theta l(theta) - r, l(theta)=sqrt((Cx cos+Cy sin - R)^2 + Cz^2)."""
    C = np.asarray(pose, float)[:3, 3]
    d = float(np.hypot(C[0], C[1]))
    return float(np.sqrt(max(0.0, R_CAD - d)**2 + C[2]**2) - r_CAD)


def cad_margin_numeric(pose, n=None):
    C = np.asarray(pose, float)[:3, 3]
    th = _DENSE_THETA if n is None else np.linspace(0, 2*np.pi, n, endpoint=False)
    u = C[0]*np.cos(th) + C[1]*np.sin(th)
    return float(np.sqrt(((u - R_CAD)**2 + C[2]**2).min()) - r_CAD)


def barrier_block(pose):
    """Continuous, pose-dependent barrier (2 rows, always same length)."""
    v = max(0.0, MARGIN_SAFE - cad_margin_analytic(pose)) / MARGIN_SCALE
    return np.array([np.sqrt(BARRIER_W)*v, np.sqrt(BARRIER_W)*v*0.5])


def _penalty_from_margin(pose, base_level=5.0):
    """Used when the CAD kernel refuses to compute: still pose-dependent (has gradient)."""
    v = max(0.0, MARGIN_SAFE - cad_margin_analytic(pose)) / MARGIN_SCALE + base_level
    return np.sqrt(BARRIER_W)*v


def dist_pts_to_poly(pts, poly):
    a = np.asarray(poly, float); b = np.roll(a, -1, axis=0)
    d = b - a; L2 = np.maximum((d*d).sum(1), 1e-12); P = np.asarray(pts, float)
    ap = P[:, None, :] - a[None, :, :]
    t = np.clip((ap*d[None]).sum(2)/L2[None], 0.0, 1.0)
    proj = a[None] + t[..., None]*d[None]
    return np.linalg.norm(P[:, None, :] - proj, axis=2).min(1)


def resample_closed(curve, m):
    p = np.asarray(curve, float)
    if len(p) == 0:
        return np.zeros((0, 2))
    q = np.r_[p, p[:1]]
    seg = np.linalg.norm(np.diff(q, axis=0), axis=1); tot = seg.sum()
    if tot <= 0:
        return np.repeat(p[:1], m, axis=0)
    cum = np.r_[0, np.cumsum(seg)]; s = np.linspace(0, tot, m, endpoint=False)
    i = np.clip(np.searchsorted(cum, s, side='right')-1, 0, len(seg)-1)
    t = (s-cum[i])/np.maximum(seg[i], 1e-12)
    return q[i] + (q[i+1]-q[i])*t[:, None]


def split_by_area(cs):
    import cv2
    ar = [abs(cv2.contourArea(np.asarray(c, np.float32).reshape(-1, 1, 2))) for c in cs]
    return cs[int(np.argmin(ar))], cs[int(np.argmax(ar))]


def blocks(pose, K, obs, which='both', tau=TAU, sigma=SIGMA, m=M_DEFAULT):
    from ring_first_3d.mainline.native.camera import torus_contours
    try:
        cs = torus_contours(np.asarray(pose), np.asarray(K))
    except ValueError as e:                      # only the explicit CAD validity error
        if 'apparent-contour' not in str(e):
            raise
        n = m if which != 'both' else 2*m
        return np.full(n, _penalty_from_margin(pose)), [f'{which}:CAD_INVALID_PENALTY']
    ci, co = split_by_area(cs)
    spec = ([('inner', ci)] if which == 'inner' else [('outer', co)] if which == 'outer'
            else [('inner', ci), ('outer', co)])
    parts, status = [], []
    for name, curve in spec:
        poly, vis = obs.get(name+'_pts'), obs.get(name+'_vis')
        if curve is None or poly is None or len(np.asarray(poly)) == 0:
            parts.append(np.full(m, 10.0)); status.append(name+':NO_DATA'); continue
        pts = resample_closed(curve, m)
        d = dist_pts_to_poly(pts, poly)
        w = np.zeros(m)
        if vis is not None and np.asarray(vis).any():
            _, idx = cKDTree(np.asarray(poly, float)).query(pts, k=1)
            w = np.asarray(vis, bool)[idx].astype(float)
        if w.sum() < 4:
            parts.append(np.zeros(m)); status.append(name+':UNOBSERVED'); continue
        L = float(np.linalg.norm(np.diff(np.r_[pts, pts[:1]], axis=0), axis=1).sum())
        r = np.sqrt(w*(L/m)/L)*np.maximum(0.0, d-tau)/sigma
        parts.append(r); status.append(f'{name}:ok(vis={int(w.sum())}/{m})')
    return np.concatenate(parts + [barrier_block(pose)]), status + ['barrier']
