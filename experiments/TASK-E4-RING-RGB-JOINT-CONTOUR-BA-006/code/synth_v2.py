"""Repaired synthetic validation: correct c2w convention, no clipping, per-sample Ring residual.

Camera convention (native.geometry.project):  q = R^T (X - t), depth = q_z.
A camera at (0,0,d) looking at the Ring origin therefore needs R e_z = -e_z.
"""
import sys
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation as Rot
sys.path.insert(0, str(Path(__file__).resolve().parent))
import joint_loss as JL, cad_contour_correspondence as CC

K = np.array([[490., 0, 319.5], [0, 490., 179.5], [0, 0, 1]])
from ring_first_3d.mainline.native.camera import torus_contours
from ring_first_3d.mainline.native.geometry import project

BASE = Rot.from_euler('x', 180, degrees=True).as_matrix()   # camera looks toward -Z world


def make_pose(d=45., tilt=0., yaw=0., shift=(0., 0.)):
    """c2w pose: camera on +Z shell looking at the Ring centre; yaw about world Z."""
    Rt = Rot.from_euler('z', yaw, degrees=True).as_matrix()
    Rx = Rot.from_euler('x', tilt, degrees=True).as_matrix()
    R = Rt @ Rx @ BASE
    M = np.eye(4); M[:3, :3] = R; M[:3, 3] = [shift[0], shift[1], d]
    return M


def check_pose(M, X=None):
    R = M[:3, :3]
    assert np.allclose(R @ R.T, np.eye(3), atol=1e-9), 'not orthonormal'
    assert abs(np.linalg.det(R) - 1) < 1e-9, 'det != 1'
    uv, z = project(np.zeros((1, 3)), M, K)
    assert z[0] > 0, f'Ring centre behind camera (z={z[0]})'
    if X is not None:
        _, zz = project(X, M, K)
        frac = float((zz > 0).mean())
        assert frac > 0.99, f'positive depth fraction {frac:.3f}'
        return frac
    return 1.0


def ring_obs(M, scale=1.0, offset=(0., 0.), occ=0.0, n=360):
    import cv2
    ci, co = CC.split(torus_contours(M, K))
    def fit(c):
        (cx, cy), (d1, d2), ang = cv2.fitEllipse(np.asarray(c, np.float32).reshape(-1, 1, 2))
        t = np.linspace(0, 2 * np.pi, n, endpoint=False)
        al = np.deg2rad(ang); ca, sa = np.cos(al), np.sin(al)
        x = scale * d1 / 2 * np.cos(t); y = scale * d2 / 2 * np.sin(t)
        return np.c_[ca * x - sa * y + cx + offset[0], sa * x + ca * y + cy + offset[1]]
    pin, pout = fit(ci), fit(co)
    vin = np.ones(n, bool); vout = np.ones(n, bool)
    if occ > 0:
        k = int(occ * n); vin[:k] = False; vout[:k] = False
    return dict(inner=pin, outer=pout, inner_vis=vin, outer_vis=vout, quality={})


def scene_points(M, n=60, seed=0):
    rng = np.random.default_rng(seed)
    th = rng.uniform(0, 2 * np.pi, n)
    X = np.c_[(5.6 + 0.6 * np.cos(th)) * np.cos(th), (5.6 + 0.6 * np.cos(th)) * np.sin(th), 0.6 * np.sin(th)]
    X += rng.normal(0, 0.05, X.shape)
    return X


def symmetry_metrics(M, Mhat):
    """Ring symmetry acts on yaw only; the normal has a 2-fold sign ambiguity."""
    n = M[:3, :3] @ np.array([0, 0, 1.]); nh = Mhat[:3, :3] @ np.array([0, 0, 1.])
    c = abs(float(n @ nh))
    normal_err = float(np.degrees(np.arccos(np.clip(c, -1, 1))))
    # raw and symmetry-equivalent rotation errors
    Rrel = Mhat[:3, :3] @ M[:3, :3].T
    raw = float(np.degrees(np.linalg.norm(Rot.from_matrix(Rrel).as_rotvec())))
    # yaw about the true ring axis (removed by ring symmetry)
    v = np.cross(n, nh); s = np.linalg.norm(v)
    Rt = np.eye(3) if s < 1e-9 else Rot.from_rotvec(v / s * np.arctan2(s, float(n @ nh))).as_matrix()
    R_no_tilt = Rt.T @ Mhat[:3, :3]
    # remaining rotation is about n: that is the unobservable yaw
    Rn = Rot.from_rotvec(n * np.degrees(1.0)).as_matrix()
    a = (R_no_tilt @ M[:3, :3].T @ n)
    yaw = float(np.degrees(np.arctan2(float(a @ (np.cross(n, [1, 0, 0]) if abs(n[0]) < 0.9 else np.cross(n, [0, 1, 0]))),
                                    float(a @ n) if False else float(np.dot(a, n))))) if False else None
    # robust yaw: angle of R_sym = R_no_tilt w.r.t. rotation about n
    M2 = np.linalg.inv(M[:3, :3]) @ R_no_tilt
    yaw = float(np.degrees(abs(Rot.from_matrix(M2).as_rotvec() @ n)))
    return dict(normal_deg=normal_err, raw_rot_deg=raw, equiv_rot_deg=normal_err,
                yaw_deg=yaw, trans_mm=float(np.linalg.norm(Mhat[:3, 3] - M[:3, 3])))


def make_res(obs, X, uv, lam_rgb, sigma=0.7, use_ring=True):
    def res(p):
        M = np.eye(4); M[:3, :3] = Rot.from_rotvec(p[:3]).as_matrix(); M[:3, 3] = p[3:]
        parts = []
        if use_ring:
            parts.append(JL.ring_vector(M, K, obs) * np.sqrt(0.5))
        if uv is not None and lam_rgb > 0:
            uvhat, z = project(X, M, K)
            r = (uvhat - uv).ravel() / sigma
            parts.append(lam_rgb * r * 0.1)
        return np.concatenate(parts) if parts else np.zeros(6)
    return res


def solve(res, M0, robust=True):
    p0 = np.r_[Rot.from_matrix(M0[:3, :3]).as_rotvec(), M0[:3, 3]]
    out = least_squares(res, p0, loss='huber' if robust else 'linear', f_scale=1.0, max_nfev=400)
    M = np.eye(4); M[:3, :3] = Rot.from_rotvec(out.x[:3]).as_matrix(); M[:3, 3] = out.x[3:]
    return M, out


def _p(M):
    return np.r_[Rot.from_matrix(M[:3,:3]).as_rotvec(), M[:3,3]]
