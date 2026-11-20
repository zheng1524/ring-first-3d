"""Read-only adapter over the frozen DXY 2-D ring geometry (exported JSON + conic helpers)."""
import json
from pathlib import Path
import numpy as np

DXY_JSON = Path('/home/liu/ring_first_3d_workspace/experiments/TASK-E4-DXY-CONIC-RING-OBSERVATION-REUSE-001/metrics/DXY_OBSERVATIONS')


def load(view_id):
    p = DXY_JSON / (view_id + '.json')
    if not p.exists():
        return None
    return json.loads(p.read_text())


def conic(ellipse):
    e = ellipse
    c, s = np.cos(np.deg2rad(e['angle_deg'])), np.sin(np.deg2rad(e['angle_deg']))
    R = np.array([[c, -s], [s, c]])
    A = R @ np.diag([1 / e['major_radius'] ** 2, 1 / e['minor_radius'] ** 2]) @ R.T
    ctr = np.array([e['cx'], e['cy']])
    M = np.zeros((3, 3)); M[:2, :2] = A; M[:2, 2] = -A @ ctr; M[2, :2] = M[:2, 2]
    M[2, 2] = ctr @ A @ ctr - 1
    return M / np.linalg.norm(M)


def sample(ellipse, n=240):
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    c, s = np.cos(np.deg2rad(ellipse['angle_deg'])), np.sin(np.deg2rad(ellipse['angle_deg']))
    x = ellipse['major_radius'] * np.cos(t); y = ellipse['minor_radius'] * np.sin(t)
    return np.c_[c * x - s * y + ellipse['cx'], s * x + c * y + ellipse['cy']]


def visible_mask(ellipse, ring_labels, band=6, n=240):
    """Arc support: which samples of the ellipse lie near a real ring pixel (visible evidence)."""
    ys, xs = np.nonzero(ring_labels == 2)
    if len(ys) == 0:
        return np.zeros(n, bool)
    pts = np.c_[xs, ys].astype(float)
    from scipy.spatial import cKDTree
    tree = cKDTree(pts)
    q = sample(ellipse, n)
    d, _ = tree.query(q, k=1)
    return d <= band
