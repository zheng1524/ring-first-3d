"""S0-S8 controlled experiments with legal SO(3) c2w rigs and GT known.

Design rules (018-REPAIR):
  * camera poses obey R^T R = I, det R = +1, and all points have Z_c > 0;
  * S5 changes the BASELINE BEFORE generating the observations;
  * every case is repeated over several seeds.
"""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import geometry as G
import yaw_solver as YS

K = np.array([[490., 0, 319.5], [0, 490., 179.5], [0, 0, 1.]])


def rig(n=8, radius=45.0, seed=0):
    rng = np.random.default_rng(seed)
    C = []
    for i in range(n):
        th = np.pi + rng.uniform(-0.7, 0.7)
        C.append(G.look_at([radius * np.cos(th), radius * np.sin(th) * 0.5, radius * 0.5]))
    return C


def scene(n=140, seed=1):
    rng = np.random.default_rng(seed)
    th = rng.uniform(0, 2 * np.pi, n); r = rng.uniform(8, 18, n); z = rng.uniform(-5, 5, n)
    return np.c_[r * np.cos(th), r * np.sin(th), z]


def make_pairs(theta_gt, noise=0.0, outliers=0.0, seed=2, ncam=6, bz=None, Kb=None,
               shuffle=False, flip_normal=False):
    A = rig(ncam, seed=seed)
    B0 = rig(ncam, seed=seed + 100)      # the two rigs MUST have different centres
    X = scene(seed=seed + 1)
    Xb = np.einsum('ij,nj->ni', G.Rz(np.deg2rad(theta_gt)), X)
    if bz is not None:
        B = [G.look_at(A[i][:3, 3] + bz * (B0[i][:3, 3] - A[i][:3, 3])) for i in range(len(A))]
    else:
        B = B0

    rng = np.random.default_rng(seed + 7)
    pairs, deps = [], []
    for i in range(len(A)):
        ua, za = G.project(X, A[i], K)
        Kb_i = K if Kb is None else Kb
        ub, zb = G.project(Xb, B[i], Kb_i)
        ok = (za > 0.2) & (zb > 0.2)
        ua, ub = ua[ok], ub[ok]; deps.append((za[ok], zb[ok]))
        if noise:
            ua = ua + rng.normal(0, noise, ua.shape)
            ub = ub + rng.normal(0, noise, ub.shape)
        if outliers > 0:
            k = int(outliers * len(ua))
            idx = rng.permutation(len(ua))[:k]
            ub[idx] = rng.uniform([0, 0], [640, 360], (k, 2))
        if shuffle:
            ub = ub[rng.permutation(len(ub))]
        Ca = A[i]
        if flip_normal:                       # solver is handed the wrong normal branch
            Rx = np.diag([1., -1., -1.])
            Ca = A[i].copy(); Ca[:3, :3] = Rx @ A[i][:3, :3]; Ca[:3, 3] = Rx @ A[i][:3, 3]
        pairs.append((Ca, B[i], ua, ub, K, Kb_i))
    zs = np.concatenate([d[0] for d in deps]) if deps else np.array([])
    zbs = np.concatenate([d[1] for d in deps]) if deps else np.array([])
    bl = float(np.median([np.linalg.norm(A[i][:3, 3] - B0[i][:3, 3]) for i in range(len(A))]))
    Zmed = float(np.median(np.linalg.norm(X, axis=1)))
    bl_eff = bl * (bz if bz is not None else 1.0)
    tri_ang = float(np.degrees(np.arctan2(bl_eff, Zmed)))
    return pairs, dict(z_a_min=(float(zs.min()) if len(zs) else None),
                       z_b_min=(float(zbs.min()) if len(zbs) else None), bz=bz,
                       median_depth=Zmed, baseline_mm=bl_eff, bz_ratio=bl_eff / max(Zmed, 1e-9),
                       tri_angle_deg=tri_ang)


def run(theta_gt, **kw):
    pairs, info = make_pairs(theta_gt, **kw)
    out = YS.solve(pairs)
    err = None if out['theta'] is None else float(abs(YS.wrap180(out['theta'] - theta_gt)))
    return dict(theta_gt=theta_gt, theta_hat=out['theta'], err_deg=err, status=out['status'],
                loss=out['loss'], median_px=out['median_px'], p95_px=out['p95_px'],
                inlier3=out['inlier3'], saturation=out['saturation'],
                clusters=json.dumps(out['clusters']), **info)


if __name__ == '__main__':
    import pandas as pd
    rows = []
    for seed in (0, 1, 2):
        for th in (0, 30, -120, 179):
            rows.append(dict(case='S0', seed=seed, **run(th, seed=seed + 10, ncam=6)))
        rows.append(dict(case='S1', seed=seed, **run(30, noise=0.5, seed=seed + 10)))
        rows.append(dict(case='S2', seed=seed, **run(30, noise=1.5, seed=seed + 10)))
        rows.append(dict(case='S3', seed=seed, **run(30, noise=0.5, outliers=0.2, seed=seed + 10)))
        rows.append(dict(case='S4', seed=seed, **run(30, noise=0.5, outliers=0.5, seed=seed + 10)))
        for bz in (0.2, 0.1, 0.05, 0.01):
            rows.append(dict(case='S5', seed=seed, bz_target=bz, **run(30, noise=0.5, seed=seed + 10, bz=bz)))
        rows.append(dict(case='S6', seed=seed, **run(30, seed=seed + 10, ncam=2)))
        rows.append(dict(case='S7', seed=seed, **run(30, seed=seed + 10, flip_normal=True)))
        rows.append(dict(case='S8', seed=seed, **run(30, seed=seed + 10,
                         Kb=np.array([[980., 0, 639.], [0, 980., 359.], [0, 0, 1.]]))))
    df = pd.DataFrame(rows)
    df.to_csv(Path(__file__).resolve().parents[1] / 'metrics' / 'SYNTHETIC_RESULTS.csv', index=False)
    print(df.groupby('case').agg(n=('err_deg', 'size'), err_med=('err_deg', 'median'),
                                 err_max=('err_deg', 'max')).round(3).to_string())
    print()
    print(df[df.case.isin(['S0', 'S5', 'S6', 'S7'])][['case', 'seed', 'theta_gt', 'theta_hat', 'err_deg',
                                                      'status', 'median_px', 'inlier3']].round(2).to_string(index=False))
