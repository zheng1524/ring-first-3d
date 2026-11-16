import numpy as np


def ellipse_coordinates(uv, center, basis):
    """T04 native-pixel basis convention: columns are ellipse semi-axis vectors."""
    b = np.asarray(basis, float)
    if b.shape != (2, 2) or not np.isfinite(b).all() or abs(np.linalg.det(b)) < 1e-12:
        raise ValueError("Expected finite invertible 2x2 pixel basis")
    return (np.asarray(uv, float) - np.asarray(center, float)) @ np.linalg.inv(b).T


def resize_intrinsics(K, old_wh, new_wh):
    scale = np.asarray(new_wh, float) / np.asarray(old_wh, float)
    if (np.asarray(old_wh) <= 0).any() or (np.asarray(new_wh) <= 0).any():
        raise ValueError("Positive image dimensions required")
    A = np.diag([*scale, 1.])
    A[:2, 2] = (scale - 1) / 2
    return A @ np.asarray(K, float)


def validate_c2w(T):
    T = np.asarray(T, float)
    if T.shape != (4, 4) or not np.isfinite(T).all():
        raise ValueError("Expected finite camera c2w 4x4")
    R = T[:3, :3]
    if not np.allclose(R.T @ R, np.eye(3), atol=1e-6) or not np.isclose(np.linalg.det(R), 1., atol=1e-6) or not np.allclose(T[3], [0, 0, 0, 1]):
        raise ValueError("Expected proper rigid c2w")
    return T


def w2c(T):
    return np.linalg.inv(validate_c2w(T))


def convert_units(values, source, target):
    scales = {"mm": .001, "m": 1.}
    if source not in scales or target not in scales:
        raise ValueError("Explicit mm or m units required")
    return np.asarray(values) * scales[source] / scales[target]


def project(points, K, T):
    T = validate_c2w(T)
    p = (np.asarray(points) - T[:3, 3]) @ T[:3, :3]
    if (p[..., 2] <= 0).any():
        raise ValueError("Points must be in front of camera")
    q = p @ np.asarray(K).T
    return q[..., :2] / q[..., 2:], p[..., 2]


def unproject(uv, axial_z, K, T):
    T = validate_c2w(T)
    p = np.concatenate([np.asarray(uv), np.ones((*np.asarray(uv).shape[:-1], 1))], axis=-1) @ np.linalg.inv(K).T
    return (p * np.asarray(axial_z)[..., None]) @ T[:3, :3].T + T[:3, 3]


def z_to_range(uv, axial_z, K):
    rays = np.c_[np.asarray(uv), np.ones(len(uv))] @ np.linalg.inv(K).T
    return np.asarray(axial_z) * np.linalg.norm(rays, axis=-1)


def validate_ring(V, inner_diameter_mm, wire_diameter_mm=1.2, atol_mm=.03):
    V = np.asarray(V, float)
    radius = np.linalg.norm(V[:, :2], axis=1)
    measured = [2 * radius.min(), 2 * radius.max(), np.ptp(V[:, 2])]
    expected = [inner_diameter_mm, inner_diameter_mm + 2 * wire_diameter_mm, wire_diameter_mm]
    if not np.allclose(measured, expected, atol=atol_mm, rtol=0):
        raise ValueError(f"CAD dimensions inconsistent with mm Ring contract: {measured}")
    return dict(inner_mm=measured[0], outer_mm=measured[1], wire_mm=measured[2])
