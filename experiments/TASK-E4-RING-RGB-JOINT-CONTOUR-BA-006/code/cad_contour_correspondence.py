"""Assign CAD inner/outer by enclosed area; measure distance to the matching DXY polyline."""
import numpy as np, cv2


def split(curves):
    areas = [abs(cv2.contourArea(np.asarray(c, np.float32).reshape(-1, 1, 2))) for c in curves]
    if len(areas) == 1:
        return curves[0], None
    i, j = int(np.argmin(areas)), int(np.argmax(areas))
    return curves[i], curves[j]


def sampled(curve, m=256):
    c = np.asarray(curve, float)
    if len(c) == 0:
        return c
    idx = np.linspace(0, len(c)-1, min(m, len(c)), dtype=int)
    return c[idx]


_TREE = {}


def _dense(poly):
    key = ('d', id(poly), len(poly))
    if key in _TREE: return _TREE[key]
    p = np.asarray(poly, float); seg = np.r_[p, p[:1]]; dense = []
    for a, b in zip(seg[:-1], seg[1:]):
        k = max(2, int(np.linalg.norm(b - a) / 1.0))
        t = np.linspace(0, 1, k, endpoint=False)[:, None]
        dense.append(a + (b - a) * t)
    d = np.vstack(dense); _TREE[key] = d; return d


def dist_to_polyline(pts, poly):
    """Euclidean distance from each point to a closed polyline (cached tree)."""
    from scipy.spatial import cKDTree
    d = _dense(poly); key = ('t', id(poly), len(poly))
    if key not in _TREE: _TREE[key] = cKDTree(d)
    dist, _ = _TREE[key].query(np.asarray(pts, float), k=1)
    return dist
