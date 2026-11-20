"""Test A (single camera, known 3-D points) + Test B (multi-camera, unknown points)."""
import sys, json
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation as Rot
sys.path.insert(0, str(Path(__file__).resolve().parent))
import synth_v2 as S, joint_loss as JL, cad_contour_correspondence as CC

T = Path(__file__).resolve().parents[1]
K = S.K


def grad_check(rgb_res, p, eps=1e-4):
    g = np.zeros(len(p))
    f0 = rgb_res(p)
    for i in range(len(p)):
        pp = p.copy(); pp[i] += eps
        g[i] = (np.sum(rgb_res(pp)**2) - np.sum(f0**2)) / eps
    return g


def test_a():
    rows = []
    for noise in (0.0, 0.7):
        for pert in (dict(dt=[2, -1, 3], rot=5), dict(dt=[8, -6, 12], rot=15)):
            M = S.make_pose(45., 20., 15.); X = S.scene_points(M); S.check_pose(M, X)
            uv, _ = S.project(X, M, K)
            rng = np.random.default_rng(1)
            uvn = uv + rng.normal(0, noise, uv.shape) if noise else uv
            obs = S.ring_obs(M)
            M0 = M.copy(); M0[:3, 3] += pert['dt']
            M0[:3, :3] = Rot.from_euler('y', pert['rot'], degrees=True).as_matrix() @ M0[:3, :3]
            S.check_pose(M0, X)
            for arm, use_ring, lam in (('ring_only', True, 0.0), ('rgb_only', False, 1.0), ('joint', True, 1.0)):
                res = S.make_res(obs, X, uvn, lam_rgb=lam, use_ring=use_ring)
                Mh, out = S.solve(res, M0)
                m = S.symmetry_metrics(M, Mh)
                # gradient evidence at init (RGB arm only)
                gnorm = float(np.linalg.norm(grad_check(lambda p: S.make_res(obs, X, uvn, 1.0, use_ring=False)(p), S._p(M0)))) if arm == 'rgb_only' else np.nan
                rows.append(dict(test='A', noise=noise, pert_rot=pert['rot'], arm=arm,
                                 status=int(out.status), nfev=int(out.nfev),
                                 grad_norm_at_init=gnorm, **m))
    return pd.DataFrame(rows)


def test_b():
    """3 cameras, unknown 3-D points, independent holdout points."""
    n_cam = 3
    poses = [S.make_pose(45., 0., -25.), S.make_pose(42., 12., 0.), S.make_pose(48., 8., 25.)]
    X = S.scene_points(poses[0], n=70, seed=7)
    for M in poses: S.check_pose(M, X)
    uv = [S.project(X, M, K)[0] for M in poses]
    hold = X[:14]                       # independent holdout points
    uv_h = [S.project(hold, M, K)[0] for M in poses]
    obs = [S.ring_obs(M) for M in poses]
    idx_tr = np.arange(14, len(X))

    def pack(Ms, Xs):
        out = []
        for M in Ms: out.append(np.r_[Rot.from_matrix(M[:3, :3]).as_rotvec(), M[:3, 3]])
        return out

    def unpack(p):
        Ms = []
        for i in range(n_cam):
            M = np.eye(4); M[:3, :3] = Rot.from_rotvec(p[6*i:6*i+3]).as_matrix(); M[:3, 3] = p[6*i+3:6*i+6]
            Ms.append(M)
        return Ms

    def residual(arms):
        def f(p):
            Ms = unpack(p); Xs = p[6*n_cam:].reshape(-1, 3); parts = []
            for i, M in enumerate(Ms):
                if 'ring' in arms:
                    parts.append(JL.ring_vector(M, K, obs[i]) * 0.5)
                if 'rgb' in arms:
                    uvh, z = S.project(Xs, M, K)
                    r = (uvh - uv[i][idx_tr]).ravel() / 0.7
                    parts.append(0.08 * r)
            return np.concatenate(parts)
        return f

    X0 = X[idx_tr].copy() + np.random.default_rng(3).normal(0, 1.0, (len(idx_tr), 3))
    p0 = np.concatenate([np.concatenate(pack(poses, X))] + [X0.ravel()])
    # gauge: first camera fixed (remove its 6 params)
    free = np.r_[np.arange(6, 6*n_cam), np.arange(6*n_cam, len(p0))]

    def wrap(fun):
        def g(q):
            p = p0.copy(); p[free] = q; return fun(p)
        return g

    rows = []
    for name, arms in (('ring_only', ['ring']), ('rgb_only', ['rgb']), ('joint', ['ring', 'rgb'])):
        fun = wrap(residual(arms)); q0 = p0[free]
        out = least_squares(fun, q0, loss='huber', f_scale=1.0, max_nfev=200)
        p = p0.copy(); p[free] = out.x; Ms = unpack(p); Xh = p[6*n_cam:].reshape(-1, 3)
        sol = p0.copy(); sol[free] = out.x; Ms = unpack(sol); Xh = sol[6*n_cam:].reshape(-1, 3)
        # evaluation: holdout reprojection + metric scale from ring
        hn = float(np.mean([np.linalg.norm(S.project(hold, M, K)[0] - uvh, axis=1).mean()
                            for M, uvh in zip(Ms, uv_h)]))
        tn = float(np.mean([np.linalg.norm(S.project(Xh, M, K)[0] - uv[i][idx_tr], axis=1).mean()
                            for i, M in enumerate(Ms)]))
        normals, centers = [], []
        for M, M0 in zip(Ms, poses):
            n1 = M[:3, :3] @ np.array([0., 0., 1.])
            n0 = M0[:3, :3] @ np.array([0., 0., 1.])
            c = min(1.0, abs(float(n1 @ n0)))
            normals.append(float(np.degrees(np.arccos(c))))
            centers.append(float(np.linalg.norm(M[:3, 3] - M0[:3, 3])))
        rows.append(dict(test='B', arm=name, status=int(out.status), nfev=int(out.nfev),
                         held_reproj_px=hn, train_reproj_px=tn,
                         normal_err_deg=float(np.mean(normals)), center_err_mm=float(np.mean(centers)),
                         b1_normal=normals[1], b1_center=centers[1]))
    return pd.DataFrame(rows)


if __name__ == '__main__':
    a = test_a(); b = test_b()
    df = pd.concat([a, b], ignore_index=True)
    df.to_csv(T/'metrics/SYNTHETIC_V2.csv', index=False)
    print(a.round(3).to_string(index=False)); print(); print(b.round(3).to_string(index=False))
