"""Ring-constrained 1-DoF yaw solver (FIXED: F = K2^-T E K1^-1).

Convention: world = fixed Ring CAD frame (mm, z = ring normal), pose = c2w, K = per-camera.
Relative pose between camera A (rotated by yaw about the Ring axis) and camera B:
    T_rel = inv(C_B) @ Rz(theta) @ C_A
    E     = [t]_x R
    F     = inv(K_B)^T E inv(K_A)      <-- 017 omitted this step entirely
"""
import numpy as np


def Rz(t):
    c, s = np.cos(t), np.sin(t)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


def rotate_pose(C, theta):
    """Rotate a c2w pose about the world/Ring z-axis (through the Ring centre = origin)."""
    R = Rz(theta)
    out = np.asarray(C, float).copy()
    out[:3, :3] = R @ C[:3, :3]
    out[:3, 3] = R @ C[:3, 3]
    return out


def essential(Ca, Cb):
    T = np.linalg.inv(np.asarray(Cb, float)) @ np.asarray(Ca, float)
    R, t = T[:3, :3], T[:3, 3]
    tx = np.array([[0, -t[2], t[1]], [t[2], 0, -t[0]], [-t[1], t[0], 0.0]])
    return tx @ R, t


def fundamental(Ca, Cb, Ka, Kb):
    E, t = essential(Ca, Cb)
    F = np.linalg.inv(Kb).T @ E @ np.linalg.inv(Ka)
    return F / (np.linalg.norm(F) + 1e-15), float(np.linalg.norm(t))


def sampson(pa, pb, F):
    a = np.c_[np.asarray(pa, float), np.ones(len(pa))]
    b = np.c_[np.asarray(pb, float), np.ones(len(pb))]
    Fa = (F @ a.T).T
    Ftb = (F.T @ b.T).T
    num = np.abs(np.einsum('ij,ij->i', b, Fa))
    den = np.sqrt(Fa[:, 0]**2 + Fa[:, 1]**2 + Ftb[:, 0]**2 + Ftb[:, 1]**2) + 1e-12
    return num / den


def robust_loss(d, clip=5.0, eps=1.0):
    """Huber-like on the squared Sampson distance; returns (loss, saturation_fraction)."""
    d2 = d * d
    sat = float(np.mean(d > clip)) if len(d) else 0.0
    r = np.minimum(d2, clip * clip)
    return float(np.mean(np.minimum(r, eps * eps) + 2 * eps * np.maximum(0.0, np.sqrt(r) - eps))), sat


def solve_yaw(pairs, K_a, K_b, coarse=2.0, refine=True, max_pairs=None):
    """pairs: list of (C_a, C_b, pa, pb). Returns dict with theta and diagnostics."""
    thetas = np.arange(-180.0, 180.0, coarse)
    curve = []
    for th in thetas:
        losses = []
        for (Ca, Cb, pa, pb) in pairs:
            F, base = fundamental(rotate_pose(Ca, np.deg2rad(th)), Cb, K_a, K_b)
            if len(pa) < 6 or base < 1e-6:
                continue
            d = sampson(pa, pb, F)
            L, _ = robust_loss(d)
            losses.append(L)
        curve.append((float(th), float(np.mean(losses)) if losses else np.nan))
    if not curve:
        return dict(theta=None, reason='NO_VALID_PAIR', curve=[])
    arr = np.array([(a, b) for a, b in curve if np.isfinite(b)])
    order = np.argsort(arr[:, 1])
    best = float(arr[order[0], 0])
    if refine:
        from scipy.optimize import minimize_scalar
        def f(th):
            ls = []
            for (Ca, Cb, pa, pb) in pairs:
                F, base = fundamental(rotate_pose(Ca, np.deg2rad(th)), Cb, K_a, K_b)
                if len(pa) < 6 or base < 1e-6:
                    continue
                L, _ = robust_loss(sampson(pa, pb, F))
                ls.append(L)
            return float(np.mean(ls)) if ls else 1e9
        r = minimize_scalar(f, bounds=(best - coarse, best + coarse), method='bounded',
                            options=dict(xatol=1e-3))
        best = float(r.x)
    # diagnostics at the optimum
    dtot, sat, per = [], [], []
    for (Ca, Cb, pa, pb) in pairs:
        F, base = fundamental(rotate_pose(Ca, np.deg2rad(best)), Cb, K_a, K_b)
        d = sampson(pa, pb, F)
        L, s = robust_loss(d)
        dtot.append(d); sat.append(s); per.append(L)
    d = np.concatenate(dtot) if dtot else np.zeros(0)
    mins = arr[order[:5]]
    return dict(theta=best, loss=float(np.mean(per)) if per else None,
                median_px=float(np.median(d)) if len(d) else None,
                inlier_frac=float(np.mean(d < 3.0)) if len(d) else None,
                saturation=float(np.mean(sat)) if sat else None,
                top5=[(float(a), float(b)) for a, b in mins],
                ambiguous=bool(len(mins) > 1 and mins[1][1] < 1.15 * max(mins[0][1], 1e-9)),
                n_per_pair=[len(p[2]) for p in pairs])
