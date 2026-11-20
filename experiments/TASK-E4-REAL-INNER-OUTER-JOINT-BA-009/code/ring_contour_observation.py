"""DXY continuous inner/outer contours as the Ring observation (read-only adapter)."""
import json
from pathlib import Path
import numpy as np, cv2
from scipy.spatial import cKDTree

DXY = Path("/home/liu/ring_first_3d_workspace/experiments/TASK-E4-REAL-INNER-OUTER-JOINT-BA-009/metrics/DXY_OBSERVATIONS")


def load(view):
    p = DXY/(view+'.json')
    return json.loads(p.read_text()) if p.exists() else None


def ellipse_points(e, n=360):
    t = np.linspace(0, 2*np.pi, n, endpoint=False)
    c, s = np.cos(np.deg2rad(e['angle_deg'])), np.sin(np.deg2rad(e['angle_deg']))
    x = e['major_radius']*np.cos(t); y = e['minor_radius']*np.sin(t)
    return np.c_[c*x - s*y + e['cx'], s*x + c*y + e['cy']]


def visible_arc(rec, key, boundary_pts, tol=2.0, n=360):
    """Arc support from the real Ring boundary samples (not from arbitrary material pixels)."""
    e = rec.get(key)
    if e is None or boundary_pts is None or len(boundary_pts) == 0:
        return np.zeros(n, bool)
    q = ellipse_points(e, n)
    d, _ = cKDTree(np.asarray(boundary_pts, float)).query(q, k=1)
    return d <= tol


def observation(view_id, boundary_pts=None, n=360):
    rec = load(view_id)
    if rec is None or not rec.get('valid') or not rec.get('inner') or not rec.get('outer'):
        return None
    return dict(inner=ellipse_points(rec['inner'], n), outer=ellipse_points(rec['outer'], n),
                inner_vis=visible_arc(rec, 'inner', boundary_pts, n=n),
                outer_vis=visible_arc(rec, 'outer', boundary_pts, n=n),
                quality=dict(coverage=(rec.get('diagnostics') or {}).get('inner_arc_coverage'),
                             residual=(rec.get('diagnostics') or {}).get('inner_normalized_residual'),
                             branch=rec.get('branch')))
