"""S0-S8 controlled experiments with known ground-truth yaw."""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import yaw_solver as YS

K = np.array([[490., 0, 319.5], [0, 490., 179.5], [0, 0, 1]])


def rig(n=24, dist=45.0, seed=0):
    rng = np.random.default_rng(seed)
    th = rng.uniform(-1.0, 1.0, n) + np.pi      # ring-like spread
    C = np.zeros((n, 4, 4))
    for i in range(n):
        C[i] = np.eye(4)
        C[i][:3, 3] = [dist * np.cos(th[i]), dist * np.sin(th[i]) * 0.4, dist * 0.5]
        # look at the Ring centre: camera +z towards origin, using Rx(pi) base
        f = -C[i][:3, 3] / np.linalg.norm(C[i][:3, 3])
        z = f; x = np.cross([0, 0, 1.], z); x /= max(np.linalg.norm(x), 1e-9)
        C[i][:3, :3] = np.c_[x, np.cross(z, x), -z] @ np.diag([1, -1, 1]) * np.array([1, 1, -1])
    return C


def project(X, C, K):
    q = (X - C[:3, 3]) @ C[:3, :3]
    p = q @ K.T
    return p[..., :2] / p[..., 2:], q[..., 2]


def scene(n=120, seed=1):
    rng = np.random.default_rng(seed)
    th = rng.uniform(0, 2 * np.pi, n); r = rng.uniform(8, 20, n); z = rng.uniform(-6, 6, n)
    return np.c_[r * np.cos(th), r * np.sin(th), z]


def run_case(theta_gt, noise=0.0, outliers=0.0, parallax=1.0, clustered=False, seed=2):
    A = rig(seed=seed)[:8]
    B = rig(seed=seed)[:8]           # second rig has its OWN world frame
    X = scene(seed=seed + 1)
    rng = np.random.default_rng(seed + 7)
    if clustered:
        X = X[:30] * 0.3 + np.array([9., 0, 0])
    Xb = np.einsum('ij,nj->ni', YS.Rz(np.deg2rad(theta_gt)), X)   # same scene in B's frame
    pairs = []
    for i in range(len(A)):
        ua, za = project(X, A[i], K); ub, zb = project(Xb, B[i], K)
        ok = (za > 0) & (zb > 0)
        ua, ub = ua[ok], ub[ok]
        if noise:
            ua = ua + rng.normal(0, noise, ua.shape); ub = ub + rng.normal(0, noise, ub.shape)
        n = len(ua)
        if outliers > 0:
            k = int(outliers * n)
            ub[:k] = ub[:k] + rng.uniform(-200, 200, (k, 2))
        pairs.append((A[i], B[i], ua, ub))
    if parallax < 1.0:
        A2 = []
        for Ca in A:
            Cb = Ca.copy(); Cb[:3, 3] = Ca[:3, 3] * parallax; A2.append(Cb)
        pairs = [(A2[k], B[k], pairs[k][2], pairs[k][3]) for k in range(len(A))]
    out = YS.solve_yaw(pairs, K, K, coarse=2.0)
    err = abs(((out['theta'] - theta_gt + 180) % 360) - 180) if out['theta'] is not None else None
    return dict(theta_gt=theta_gt, theta_hat=out['theta'], err_deg=err, loss=out['loss'],
                median_px=out['median_px'], inlier_frac=out['inlier_frac'],
                saturation=out['saturation'], ambiguous=out['ambiguous'],
                noise=noise, outliers=outliers, parallax=parallax, clustered=clustered)


if __name__ == '__main__':
    rows = []
    for th in (0, 30, -120, 179):
        rows.append(dict(case='S0', **run_case(th)))
    for th in (30, -120):
        rows.append(dict(case='S1', **run_case(th, noise=0.5)))
        rows.append(dict(case='S2', **run_case(th, noise=1.5)))
        rows.append(dict(case='S3', **run_case(th, noise=0.5, outliers=0.2)))
        rows.append(dict(case='S4', **run_case(th, noise=0.5, outliers=0.5)))
        rows.append(dict(case='S5', **run_case(th, parallax=0.05)))
        rows.append(dict(case='S6', **run_case(th, clustered=True)))
    import pandas as pd
    df = pd.DataFrame(rows)
    out = Path(__file__).resolve().parents[1] / 'metrics' / 'SYNTHETIC_GROUND_TRUTH.csv'
    df.to_csv(out, index=False)
    print(df.round(3).to_string(index=False))
