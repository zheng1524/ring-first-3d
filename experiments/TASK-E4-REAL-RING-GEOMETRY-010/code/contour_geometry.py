"""Correct contour geometry: fixed-size arc-length resampling + exact segment distance.

Fixes the 007 defects:
  * no global id()-keyed cache (ids get reused -> stale polylines)
  * exact point-to-segment distance instead of an arbitrary 1 px densification
  * resampling always returns exactly `m` points (closed curve, seam handled)
"""
import numpy as np


def resample_closed(curve, m):
    """Arc-length resample a closed polyline to exactly m points."""
    p = np.asarray(curve, float)
    if len(p) == 0:
        return np.zeros((0, 2))
    if len(p) == 1:
        return np.repeat(p, m, axis=0)
    q = np.r_[p, p[:1]]
    seg = np.linalg.norm(np.diff(q, axis=0), axis=1)
    total = seg.sum()
    if total <= 0:
        return np.repeat(p[:1], m, axis=0)
    cum = np.r_[0, np.cumsum(seg)]
    s = np.linspace(0, total, m, endpoint=False)
    idx = np.clip(np.searchsorted(cum, s, side='right') - 1, 0, len(seg) - 1)
    t = (s - cum[idx]) / np.maximum(seg[idx], 1e-12)
    a, b = q[idx], q[idx + 1]
    return a + (b - a) * t[:, None]


def _segments(poly):
    p = np.asarray(poly, float)
    q = np.r_[p, p[:1]]
    return q[:-1], q[1:]


def dist_to_polyline(pts, poly):
    """Exact Euclidean distance from each point to a closed polyline (no cache)."""
    a, b = _segments(poly)
    d = b - a
    L2 = np.maximum((d * d).sum(1), 1e-12)
    P = np.asarray(pts, float)
    # chunked to keep memory bounded
    out = np.empty(len(P))
    for i in range(0, len(P), 512):
        blk = P[i:i + 512]
        ap = blk[:, None, :] - a[None, :, :]
        t = np.clip((ap * d[None, :, :]).sum(2) / L2[None, :], 0, 1)
        proj = a[None, :, :] + t[:, :, None] * d[None, :, :]
        out[i:i + 512] = np.linalg.norm(blk[:, None, :] - proj, axis=2).min(1)
    return out


def split_by_area(curves):
    import cv2
    areas = [abs(cv2.contourArea(np.asarray(c, np.float32).reshape(-1, 1, 2))) for c in curves]
    if len(areas) == 1:
        return curves[0], None
    return curves[int(np.argmin(areas))], curves[int(np.argmax(areas))]


def boundary_distance(curve, poly, m=256):
    return dist_to_polyline(resample_closed(curve, m), poly)
