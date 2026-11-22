"""SO(3) rotation / translation metrics with explicit c2w convention."""
import numpy as np
from scipy.spatial.transform import Rotation as Rot


def check_so3(R):
    R = np.asarray(R, float)
    if not np.isfinite(R).all():
        return False, 'NONFINITE'
    if not np.allclose(R @ R.T, np.eye(3), atol=1e-6):
        return False, 'NOT_ORTHONORMAL'
    if abs(np.linalg.det(R) - 1.0) > 1e-6:
        return False, 'DET_NOT_1'
    return True, ''


def as_c2w(m, convention='c2w'):
    """Explicit convention switch; never guess from names."""
    m = np.asarray(m, float)
    if convention == 'c2w':
        return m
    if convention == 'w2c':
        R, t = m[:3, :3], m[:3, 3]
        out = np.eye(4); out[:3, :3] = R.T; out[:3, 3] = -R.T @ t
        return out
    raise ValueError('unknown convention ' + convention)


def angle_deg(R_ij):
    c = np.clip((np.trace(R_ij) - 1.0) / 2.0, -1.0, 1.0)
    return float(np.degrees(np.arccos(c)))


def relative_deg(c2w_a, c2w_b):
    """Angle of R_a^T R_b (physical relative rotation between two c2w poses)."""
    Ra, Rb = np.asarray(c2w_a)[:3, :3], np.asarray(c2w_b)[:3, :3]
    return angle_deg(Ra.T @ Rb)


def rotation_from_reference(cams, ref):
    return [relative_deg(cams[ref], c) for c in cams]


def rotation_to_previous(cams, order):
    """order: indices sorted by real frame number. Returns (angles, frame_gaps)."""
    out, gaps = [], []
    for a, b in zip(order[:-1], order[1:]):
        out.append(relative_deg(cams[a], cams[b]))
        gaps.append(int(b - a))
    return out, gaps


def center_distance_mm(c2w_a, c2w_b):
    return float(np.linalg.norm(np.asarray(c2w_a)[:3, 3] - np.asarray(c2w_b)[:3, 3]))
