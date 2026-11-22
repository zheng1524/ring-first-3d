"""Small module: are cross-video landmark identities consistent with ONE rigid SE(3)?

Authorised new module (024 P3). It does NOT extract features, build landmarks or
run the main optimiser; it only judges identity consistency.
Open3D RANSAC (with_scaling=False) is used as the mature sampler; no new RANSAC core.
"""
import numpy as np


def _so3(R_):
    U, _, Vt = np.linalg.svd(R_)
    R = U @ Vt
    if np.linalg.det(R) < 0: R = U @ np.diag([1, 1, -1]) @ Vt
    return R


def ransac_rigid(X4, X5, thresh_mm, seed=0, confidence=0.9999, max_iter=100000):
    import open3d as o3d
    import random
    X4 = np.asarray(X4, float); X5 = np.asarray(X5, float)
    n = len(X4)
    if n < 3:
        return dict(status='INSUFFICIENT', n=n, H=np.eye(4), inliers=np.zeros(n, bool))
    random.seed(seed); np.random.seed(seed); o3d.utility.random.seed(seed)
    src = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(X4))
    tgt = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(X5))
    corr = o3d.utility.Vector2iVector(np.c_[np.arange(n), np.arange(n)].astype(np.int32))
    est = o3d.pipelines.registration.TransformationEstimationPointToPoint(with_scaling=False)
    crit = o3d.pipelines.registration.RANSACConvergenceCriteria(int(max_iter), float(confidence))
    r = o3d.pipelines.registration.registration_ransac_based_on_correspondence(
        src, tgt, corr, float(thresh_mm), estimation_method=est, ransac_n=3,
        checkers=[], criteria=crit)
    H = np.asarray(r.transformation, float)
    e = np.linalg.norm((H[:3, :3] @ X4.T).T + H[:3, 3] - X5, axis=1)
    inl = e <= thresh_mm
    return dict(status='OK', n=n, H=H, inliers=inl, residual_mm=e,
                fitness=float(inl.mean()), n_inliers=int(inl.sum()))


def degeneracy(X, min_ratio=0.02):
    """Non-collinearity / spread test on the source points."""
    X = np.asarray(X, float)
    if len(X) < 3: return dict(degenerate=True, reason='TOO_FEW')
    s = np.linalg.svd(X - X.mean(0), compute_uv=False)
    ratio = float(s[1]/(s[0] + 1e-12)) if len(s) > 1 else 0.0
    return dict(degenerate=bool(ratio < min_ratio), ratio=ratio, singular= s.tolist())


def check(X4, X5, thresh_mm=1.0, min_inliers=4, seed=0):
    deg = degeneracy(X4)
    r = ransac_rigid(X4, X5, thresh_mm, seed=seed)
    out = dict(r)
    out['degeneracy'] = deg
    out['threshold_mm'] = thresh_mm
    if r['status'] != 'OK':
        out['status'] = 'INSUFFICIENT'
    elif deg['degenerate']:
        out['status'] = 'DEGENERATE'
    elif r['n_inliers'] < min_inliers:
        out['status'] = 'INSUFFICIENT'
    else:
        R = r['H'][:3, :3]
        ort = float(np.abs(R @ R.T - np.eye(3)).max())
        det = float(np.linalg.det(R))
        out['so3'] = dict(orth=ort, det=det, valid=bool(ort < 1e-6 and abs(det-1) < 1e-6))
        out['status'] = 'SUPPORTED' if out['so3']['valid'] else 'GEOMETRY_CONFLICT'
    return out
