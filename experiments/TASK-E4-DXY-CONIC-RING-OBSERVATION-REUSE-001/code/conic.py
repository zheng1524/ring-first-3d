"""Conic utilities: DXY ellipse -> homogeneous conic, Sampson distance, CAD contour split.

Only the Ring geometry observation and its pose-optimisation interface are touched.
The CAD contour generator itself (native.camera.torus_contours) is reused unchanged.
"""
import numpy as np
import cv2


def ellipse_from_dict(e):
    return dict(cx=float(e['cx']), cy=float(e['cy']),
                major_radius=float(e['major_radius']), minor_radius=float(e['minor_radius']),
                angle_deg=float(e['angle_deg']))


def conic_from_ellipse(e):
    """Homogeneous conic matrix for DXY ellipse {cx,cy,major_radius,minor_radius,angle_deg}."""
    e = ellipse_from_dict(e)
    c, s = np.cos(np.deg2rad(e['angle_deg'])), np.sin(np.deg2rad(e['angle_deg']))
    R = np.array([[c, -s], [s, c]])
    A = R @ np.diag([1.0 / e['major_radius'] ** 2, 1.0 / e['minor_radius'] ** 2]) @ R.T
    ctr = np.array([e['cx'], e['cy']])
    C = np.zeros((3, 3))
    C[:2, :2] = A
    C[:2, 2] = -A @ ctr
    C[2, :2] = C[:2, 2]
    C[2, 2] = ctr @ A @ ctr - 1.0
    n = np.linalg.norm(C)
    assert np.isfinite(n) and n > 0, 'degenerate conic'
    return C / n


def sampson(points, C):
    """First-order geometric distance of points to conic C (pixels)."""
    p = np.asarray(points, float)
    h = np.c_[p, np.ones(len(p))]
    Ch = h @ C
    num = np.abs(np.einsum('ni,ni->n', h, Ch))
    den = np.sqrt((2 * Ch[:, 0]) ** 2 + (2 * Ch[:, 1]) ** 2 + 1e-12)
    return num / den


def sample_curve(curve, n=64):
    c = np.asarray(curve, float)
    if len(c) == 0:
        return c
    return c[np.linspace(0, len(c) - 1, min(n, len(c)), dtype=int)]


def split_curves(curves):
    """Return (inner, outer) by enclosed area. Never assume output order."""
    areas = [abs(cv2.contourArea(np.asarray(c, np.float32).reshape(-1, 1, 2))) for c in curves]
    if len(areas) == 1:
        return curves[0], None
    i = int(np.argmin(areas)); j = int(np.argmax(areas))
    return curves[i], curves[j]


def quality_weight(rec):
    """Continuous confidence from DXY diagnostics; never a hard rejection."""
    d = rec.get('diagnostics') or {}
    def _f(key, default):
        v = d.get(key, default)
        return float(default if v is None else v)
    cov = _f('inner_arc_coverage', 0.5)
    res = _f('inner_normalized_residual', 0.05)
    ins = _f('inner_sector_instability', 0.1)
    branch = str(rec.get('branch') or '')
    inferred = 0.6 if branch.startswith('centerline_symmetry') else 1.0
    w = max(0.2, min(1.0, cov)) * 1.0 / (1.0 + 10.0 * res) * 1.0 / (1.0 + 5.0 * ins) * inferred
    return float(max(0.05, min(1.0, w)))


def conic_residual(pose, ob, K, mode='A1', aux_weight=0.2, base_residual=None, n_q=0):
    """Vector residual: Sampson distance of projected CAD contours to DXY conics.

    mode A1: DXY conics only (replaces the raw boundary term)
    mode A2: DXY conics + aux_weight * raw-boundary term
    """
    from ring_first_3d.mainline.native.camera import torus_contours
    curves = torus_contours(np.asarray(pose), np.asarray(K))
    inner_c, outer_c = split_curves(curves)
    vals = []
    for key, curve in (('inner', inner_c), ('outer', outer_c)):
        C = ob.get(f'dxy_{key}_conic')
        if C is None or curve is None:
            continue
        w = float(ob.get(f'dxy_{key}_weight', 1.0))
        pts = sample_curve(curve, 64)
        d = np.clip(sampson(pts, np.asarray(C, float)), 0.0, 200.0)
        vals.append(np.sqrt(w) * d)
    q = np.concatenate(vals) if vals else np.zeros(4)
    if mode == 'A2' and base_residual is not None and n_q:
        q = np.r_[q, np.sqrt(aux_weight) * np.asarray(base_residual, float)[:n_q]]
    return q
