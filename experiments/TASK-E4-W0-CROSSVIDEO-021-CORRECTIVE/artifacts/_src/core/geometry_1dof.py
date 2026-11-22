"""Canonical camera geometry: legal SO(3) c2w rig, E/F, Sampson, metrics."""
import numpy as np


def look_at(C, target=(0.0, 0.0, 0.0), up=(0.0, 0.0, 1.0)):
    """Legal c2w pose at C looking at target. R = [x_c, y_c, z_c] with det = +1."""
    C = np.asarray(C, float)
    z = np.asarray(target, float) - C
    z = z / np.linalg.norm(z)                     # camera +z points AT the target
    x = np.cross(z, np.asarray(up, float))
    if np.linalg.norm(x) < 1e-8:
        x = np.cross(z, np.array([1.0, 0.0, 0.0]))
    x = x / np.linalg.norm(x)
    y = np.cross(z, x)
    T = np.eye(4)
    T[:3, :3] = np.c_[x, y, z]
    T[:3, 3] = C
    return T


def check_so3(R, tol=1e-9):
    R = np.asarray(R, float)
    if not np.isfinite(R).all():
        return False, 'NONFINITE'
    if not np.allclose(R @ R.T, np.eye(3), atol=tol):
        return False, f'NOT_ORTHONORMAL(max={np.abs(R@R.T-np.eye(3)).max():.2e})'
    d = float(np.linalg.det(R))
    if abs(d - 1.0) > tol:
        return False, f'DET={d:.9f}'
    return True, ''


def Rz(t):
    c, s = np.cos(t), np.sin(t)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


def rot_about_ring(C, theta):
    """Rotate a c2w pose about the Ring axis (world z through the CAD centre = origin)."""
    R = Rz(theta)
    out = np.asarray(C, float).copy()
    out[:3, :3] = R @ C[:3, :3]
    out[:3, 3] = R @ C[:3, 3]
    return out


def project(X, C, K):
    q = (np.asarray(X, float) - C[:3, 3]) @ C[:3, :3]
    p = q @ np.asarray(K, float).T
    return p[..., :2] / p[..., 2:], q[..., 2]


def essential(Ca, Cb):
    T = np.linalg.inv(np.asarray(Cb, float)) @ np.asarray(Ca, float)
    R, t = T[:3, :3], T[:3, 3]
    tx = np.array([[0, -t[2], t[1]], [t[2], 0, -t[0]], [-t[1], t[0], 0.0]])
    return tx @ R, t


def fundamental(Ca, Cb, Ka, Kb):
    E, t = essential(Ca, Cb)
    F = np.linalg.inv(Kb).T @ E @ np.linalg.inv(Ka)
    n = np.linalg.norm(F)
    return (F / n if n > 1e-15 else np.zeros((3, 3))), float(np.linalg.norm(t))


def sampson(pa, pb, F):
    a = np.c_[np.asarray(pa, float), np.ones(len(pa))]
    b = np.c_[np.asarray(pb, float), np.ones(len(pb))]
    Fa = (F @ a.T).T
    Ftb = (F.T @ b.T).T
    return np.abs(np.einsum('ij,ij->i', b, Fa)) / (
        np.sqrt(Fa[:, 0]**2 + Fa[:, 1]**2 + Ftb[:, 0]**2 + Ftb[:, 1]**2) + 1e-12)


def robust_loss(d, clip=5.0, eps=1.0):
    """Huber on |d|. NOTE: each residual is bounded by clip, so the MEAN is bounded by clip."""
    sat = float(np.mean(d > clip)) if len(d) else 0.0
    r = np.minimum(d, clip)
    return float(np.mean(np.where(r <= eps, 0.5 * r * r, eps * (r - 0.5 * eps)))), sat


def metrics(d, clip=5.0):
    if len(d) == 0:
        return dict(n=0, median_px=None, mae_px=None, p90_px=None, p95_px=None,
                    inlier3=0.0, saturation=0.0, loss=None)
    L, sat = robust_loss(d, clip)
    return dict(n=int(len(d)), median_px=float(np.median(d)), mae_px=float(np.mean(d)),
                p90_px=float(np.percentile(d, 90)), p95_px=float(np.percentile(d, 95)),
                inlier3=float(np.mean(d < 3.0)), saturation=sat, loss=L)
