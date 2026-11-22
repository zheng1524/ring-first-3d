"""Geometry primitives for 024: exact SE(3), per-side intrinsics, standard Sampson."""
import numpy as np
from se3 import exp_se3, hat


def project(X, C, K):
    q = (np.asarray(X, float) - C[:3, 3]) @ C[:3, :3]
    p = q @ np.asarray(K, float).T
    return p[..., :2] / p[..., 2:], q[..., 2]


def fundamental(Ca, Cb, Ka, Kb):
    T = np.linalg.inv(np.asarray(Cb, float)) @ np.asarray(Ca, float)
    R, t = T[:3, :3], T[:3, 3]
    tx = np.array([[0, -t[2], t[1]], [t[2], 0, -t[0]], [-t[1], t[0], 0.]])
    F = np.linalg.inv(np.asarray(Kb, float)).T @ (tx @ R) @ np.linalg.inv(np.asarray(Ka, float))
    n = np.linalg.norm(F)
    return (F / n if n > 1e-15 else np.zeros((3, 3))), float(np.linalg.norm(t))


def sampson(pa, pb, F):
    a = np.c_[np.asarray(pa, float), np.ones(len(pa))]
    b = np.c_[np.asarray(pb, float), np.ones(len(pb))]
    Fa = (F @ a.T).T
    Ftb = (F.T @ b.T).T
    num = np.abs(np.einsum('ij,ij->i', b, Fa))
    den = np.sqrt((Fa[:, :2]**2).sum(1) + (Ftb[:, :2]**2).sum(1)) + 1e-12
    return num / den


def line_dist(l, p):
    a, b, c = l
    d = np.hypot(a, b)
    return abs(a*p[0] + b*p[1] + c)/d if d > 1e-12 else np.nan
