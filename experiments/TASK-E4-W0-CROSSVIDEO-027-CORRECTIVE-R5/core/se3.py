"""Exact SE(3) exponential with an explicit parameter order: xi = (v, omega).

H = [[exp([w]x), V v], [0, 1]]  with  V = I + (1-cos t)/t^2 [w]x + (t-sin t)/t^3 [w]x^2
This matches scipy.linalg.expm(hat(xi)) to machine precision (tested).
Historical 020 used pytorch3d.se3_exp_map, whose argument order is (rotation, translation)
and whose matrix is the transpose (row-vector convention); see tests/test_se3_math.py.
"""
import numpy as np


def skew(w):
    w = np.asarray(w, float)
    return np.array([[0, -w[2], w[1]], [w[2], 0, -w[0]], [-w[1], w[0], 0]])


def hat(xi):
    xi = np.asarray(xi, float)
    M = np.zeros((4, 4))
    M[:3, :3] = skew(xi[3:6])
    M[:3, 3] = xi[0:3]
    return M


def exp_se3(xi):
    xi = np.asarray(xi, float).reshape(6)
    v, w = xi[:3], xi[3:]
    t = float(np.linalg.norm(w))
    W = skew(w)
    if t < 1e-12:
        R = np.eye(3) + W
        V = np.eye(3) + 0.5 * W
    else:
        R = np.eye(3) + np.sin(t) / t * W + (1 - np.cos(t)) / t**2 * (W @ W)
        V = np.eye(3) + (1 - np.cos(t)) / t**2 * W + (t - np.sin(t)) / t**3 * (W @ W)
    H = np.eye(4)
    H[:3, :3] = R
    H[:3, 3] = V @ v
    return H
