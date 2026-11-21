"""Faithful copy of 020/code/named_candidate020.py::rigid + its 256-trial RANSAC loop.

Source (commit 5636aae):
    def rigid(A,B):
     a=A.mean(0);b=B.mean(0);rot,_=Rotation.align_vectors(A-a,B-b);H=np.eye(4);H[:3,:3]=rot.as_matrix();H[:3,3]=a-H[:3,:3]@b;return H
    ... rng=np.random.default_rng(20261111); 256 trials; d=||A-(B H^T + t)||; pick max count then min median
"""
import numpy as np
from scipy.spatial.transform import Rotation

SEED = 20261111
TRIALS = 256
TOL_MM = 0.75


def rigid(A, B):
    a = A.mean(0); b = B.mean(0)
    rot, _ = Rotation.align_vectors(A - a, B - b)
    H = np.eye(4); H[:3, :3] = rot.as_matrix(); H[:3, 3] = a - H[:3, :3] @ b
    return H


def run(X4, X5, seed=SEED, trials=TRIALS, tol=TOL_MM):
    rng = np.random.default_rng(seed)
    c = []
    for _ in range(trials):
        idx = rng.choice(len(X4), 3, replace=False)
        H = rigid(X4[idx], X5[idx])
        d = np.linalg.norm(X4 - (X5 @ H[:3, :3].T + H[:3, 3]), axis=1)
        c.append((int((d <= tol).sum()), float(np.median(d)), H, d))
    best = min(c, key=lambda a: (-a[0], a[1]))
    keep = best[3] <= tol
    H = rigid(X4[keep], X5[keep]) if keep.sum() >= 3 else best[2]
    d = np.linalg.norm(X4 - (X5 @ H[:3, :3].T + H[:3, 3]), axis=1)
    count = int((d <= tol).sum())
    center = float(np.linalg.norm(H[:3, 3]))
    tilt = float(np.degrees(np.arccos(np.clip(abs(H[2, 2]), -1, 1))))
    return dict(T=H, named_pairs=len(X4), within_075mm=count, residual_mm=dict(
        median=float(np.median(d)), mean=float(np.mean(d)), p90=float(np.percentile(d, 90)),
        max=float(np.max(d))), center_mm=center, tilt_deg=tilt)
