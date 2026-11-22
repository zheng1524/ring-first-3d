"""Controlled synthetic experiments A1-A7 (no real data, fixed seeds)."""
import json, sys
from pathlib import Path
import numpy as np
C = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(C/'core')); sys.path.insert(0, '/home/liu/ring_first_3d_workspace/src')
import shared_se3 as S3, yaw_1dof as Y1
from ring_first_3d.mainline.native.camera import torus_contours
K = np.array([[490., 0, 319.5], [0, 490., 179.5], [0, 0, 1.]])


def cam(pos, yaw=0.0):
    Cm = np.eye(4); Cm[:3, :3] = np.diag([1., -1., -1.]); Cm[:3, 3] = pos
    th = np.deg2rad(yaw); c, s = np.cos(th), np.sin(th)
    Cm[:3, :3] = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]]) @ Cm[:3, :3]
    return Cm


def scene(n=200, seed=0):
    rng = np.random.default_rng(seed)
    return np.c_[rng.uniform(-4, 4, n), rng.uniform(-4, 4, n), rng.uniform(-3, 3, n)]


def proj(X, Cm):
    q = (X - Cm[:3, 3]) @ Cm[:3, :3]; p = q @ K.T
    return p[:, :2] / p[:, 2:]


def make_pairs(theta_deg, n_views=5, seed=1, outlier_frac=0.0, noise=0.5):
    rng = np.random.default_rng(seed); X = scene(seed=seed + 5)
    H = np.eye(4); th = np.deg2rad(theta_deg); c, s = np.cos(th), np.sin(th)
    H[:3, :3] = [[c, -s, 0], [s, c, 0], [0, 0, 1]]
    out = []
    for k in range(n_views):
        C4 = cam([20 + 3 * k, -2 * k, 40 + k], yaw=0.0)
        C5 = cam([-18 + 2 * k, 4 - k, 41 + k], yaw=0.0)
        u4 = proj(np.einsum('ij,nj->ni', H[:3, :3], X), C4); u5 = proj(X, C5)
        if outlier_frac:
            m = int(outlier_frac * len(u4)); idx = rng.permutation(len(u4))[:m]
            u4[idx] = rng.uniform([0, 0], [640, 360], (m, 2))
        if noise:
            u4 = u4 + rng.normal(0, noise, u4.shape); u5 = u5 + rng.normal(0, noise, u5.shape)
        out.append((C4, C5, u4, u5))
    return out


def wrap(a):
    return abs(((a + 180) % 360) - 180)


def main():
    rows = []
    # A1 pure yaw 30 deg, EPI only
    p = make_pairs(30.0)
    y = Y1.solve([(A, B, u, v, K, K) for (A, B, u, v) in p])
    rows.append(dict(case='A1_pure_yaw_30deg', model='EPI yaw', truth=-30.0,
                     estimate=round(y['theta'], 4), error=round(wrap(y['theta'] + 30.0), 4),
                     unit='deg', status=y['status'], median_px=round(y['median_px'], 4),
                     inlier3=round(y['inlier3'], 4)))
    # A4 30% outliers
    p = make_pairs(30.0, outlier_frac=0.3)
    y = Y1.solve([(A, B, u, v, K, K) for (A, B, u, v) in p])
    rows.append(dict(case='A4_outliers_30pct', model='EPI yaw', truth=-30.0,
                     estimate=round(y['theta'], 4), error=round(wrap(y['theta'] + 30.0), 4),
                     unit='deg', status=y['status'], median_px=round(y['median_px'], 4),
                     inlier3=round(y['inlier3'], 4)))
    # A7 same-video identity (truth = 0)
    p = make_pairs(0.0)
    y = Y1.solve([(A, B, u, v, K, K) for (A, B, u, v) in p])
    rows.append(dict(case='A7_identity_control', model='EPI yaw', truth=0.0,
                     estimate=round(y['theta'], 4), error=round(wrap(y['theta']), 4),
                     unit='deg', status=y['status'], median_px=round(y['median_px'], 4),
                     inlier3=round(y['inlier3'], 4)))
    # A2 pure translation, Ring only, single view (scale is fixed, tangent is not)
    C4 = cam([20., 0., 40.]); pts = np.asarray(torus_contours(C4, K)[0], float)
    ring = {'v': dict(C=C4, pts=pts)}
    Htrue = np.eye(4); Htrue[:3, 3] = [0.25, -0.15, 0.1]
    q, L, _, _ = S3.optimize(np.eye(4), ring, [], K, iters=150)
    t_mm, r_deg = S3.delta_size(S3.pose_from_q(q, np.eye(4)) @ np.linalg.inv(Htrue))
    rows.append(dict(case='A2_translation_ring_only', model='Ring 1 view', truth=0.30,
                     estimate=round(t_mm, 4), error=round(abs(t_mm - 0.30), 4), unit='mm',
                     status='RECORDED_TANGENT_AMBIGUOUS', median_px=None, inlier3=None))
    # A3 mixed 6-DoF: Ring + EPI, 3 ring views
    p = make_pairs(6.0, n_views=3)
    ring3 = {}
    for k, (A, B, u, v) in enumerate(p):
        ring3[f'v{k}'] = dict(C=A, pts=np.asarray(torus_contours(A, K)[0], float))
    q, L, _, _ = S3.optimize(np.eye(4), ring3, p, K, iters=150)
    H = S3.pose_from_q(q, np.eye(4))
    th = np.deg2rad(-6.0); c, s = np.cos(th), np.sin(th)   # model-truth sign (scene-rotated observations)
    Ht = np.eye(4); Ht[:3, :3] = [[c, -s, 0], [s, c, 0], [0, 0, 1]]
    t3, r3 = S3.delta_size(H @ np.linalg.inv(Ht))
    rows.append(dict(case='A3_mixed_6dof', model='Ring+EPI', truth=0.0,
                     estimate=round(t3, 4), error=round(r3, 4), unit='mm/deg',
                     status='RECORDED', median_px=None, inlier3=None))
    # A6 Ring yaw symmetry
    Ls = []
    for yaw in (0.0, 10.0, 20.0, 40.0):
        Cc = cam([20., 0., 40.]); yy = np.eye(4); th = np.deg2rad(yaw); c, s = np.cos(th), np.sin(th)
        yy[:3, :3] = [[c, -s, 0], [s, c, 0], [0, 0, 1]]
        Cc = yy @ Cc
        Ls.append(S3.ring_term(np.eye(4), {'v': dict(C=Cc, pts=np.asarray(torus_contours(Cc, K)[0], float))}, K))
    rows.append(dict(case='A6_ring_yaw_symmetry', model='Ring', truth=0.0,
                     estimate=round(float(np.ptp(Ls)), 9), error=round(float(np.ptp(Ls)), 9),
                     unit='loss spread', status='PASS' if np.ptp(Ls) < 1e-6 else 'FAIL',
                     median_px=None, inlier3=None))
    import pandas as pd
    df = pd.DataFrame(rows)
    (C/'metrics').mkdir(exist_ok=True)
    df.to_csv(C/'metrics'/'GEOMETRY_CORRECTNESS.csv', index=False)
    print(df.to_string(index=False))


if __name__ == '__main__':
    main()
