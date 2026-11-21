"""Explicit SE(3) conventions for cross-video transforms (no implicit direction)."""
import numpy as np


def check_pose(T, tol=1e-9):
    T = np.asarray(T, float)
    R = T[:3, :3]
    return dict(orth=float(np.abs(R @ R.T - np.eye(3)).max()),
                det=float(np.linalg.det(R)),
                finite=bool(np.isfinite(T).all()),
                valid=bool(np.abs(R @ R.T - np.eye(3)).max() < tol and abs(np.linalg.det(R) - 1) < tol))


def inverse(T):
    T = np.asarray(T, float)
    R, t = T[:3, :3], T[:3, 3]
    out = np.eye(4); out[:3, :3] = R.T; out[:3, 3] = -R.T @ t
    return out


def apply_to_points(T, X):
    return (np.asarray(T, float) @ np.c_[np.asarray(X, float), np.ones(len(X))].T).T[:, :3]


def yaw_about_axis(theta_deg, axis=(0., 0., 1.)):
    a = np.asarray(axis, float); a = a / np.linalg.norm(a)
    th = np.deg2rad(theta_deg); Kx = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    R = np.eye(3) + np.sin(th) * Kx + (1 - np.cos(th)) * (Kx @ Kx)
    T = np.eye(4); T[:3, :3] = R
    return T


def audit_transform(H, name, source='G03/004', target='G03/005', units='mm'):
    return dict(name=name, source_frame=source, target_frame=target, units=units,
                matrix=np.asarray(H, float).tolist(), inverse_matrix=inverse(H).tolist(),
                handedness='right', pose_convention='c2w', **check_pose(H))
