"""Geometry-validated RGB held evaluation (no filtering by the target-view error!)."""
import numpy as np

K_DEFAULT = np.array([[490., 0, 319.5], [0, 490., 179.5], [0, 0, 1]])
MIN_BASELINE_MM = 2.0
MIN_ANGLE_DEG = 2.0
SRC_REPROJ_MAX_PX = 3.0


def project(X, C, K=K_DEFAULT):
    q = (np.asarray(X) - C[:3, 3]) @ C[:3, :3]
    p = q @ K.T
    return p[..., :2] / p[..., 2:], q[..., 2]


def triangulate(u1, u2, C1, C2, K=K_DEFAULT):
    P1 = K @ np.c_[C1[:3, :3].T, -C1[:3, :3].T @ C1[:3, 3]]
    P2 = K @ np.c_[C2[:3, :3].T, -C2[:3, :3].T @ C2[:3, 3]]
    A = np.r_[u1[0]*P1[2]-P1[0], u1[1]*P1[2]-P1[1], u2[0]*P2[2]-P2[0], u2[1]*P2[2]-P2[1]].reshape(4, 4)
    _, s, Vt = np.linalg.svd(A)
    X = Vt[-1]
    if abs(X[3]) < 1e-12:
        return None, 0.0
    cond = float(s[0] / max(s[-1], 1e-12))
    return X[:3] / X[3], cond


def best_pair(xy, t, i, cams):
    """Pick a source pair with real parallax (baseline and angle), not just max baseline."""
    others = [j for j in range(len(cams)) if j != i and np.isfinite(xy[t, j, 0])]
    best = None
    for a in range(len(others)):
        for b in range(a + 1, len(others)):
            j, k = others[a], others[b]
            base = float(np.linalg.norm(cams[j][:3, 3] - cams[k][:3, 3]))
            if base < MIN_BASELINE_MM:
                continue
            X, cond = triangulate(xy[t, j], xy[t, k], cams[j], cams[k])
            if X is None:
                continue
            r1 = X - cams[j][:3, 3]; r2 = X - cams[k][:3, 3]
            ang = float(np.degrees(np.arccos(np.clip(r1 @ r2 / (np.linalg.norm(r1) * np.linalg.norm(r2)), -1, 1))))
            if ang < MIN_ANGLE_DEG:
                continue
            uj, zj = project(X, cams[j]); uk, zk = project(X, cams[k])
            uj = np.atleast_1d(uj)[:2]; uk = np.atleast_1d(uk)[:2]
            zj = float(np.atleast_1d(zj)[0]); zk = float(np.atleast_1d(zk)[0])
            if zj <= 0 or zk <= 0:
                continue
            if np.linalg.norm(uj - xy[t, j]) > SRC_REPROJ_MAX_PX or np.linalg.norm(uk - xy[t, k]) > SRC_REPROJ_MAX_PX:
                continue
            score = base
            if best is None or score > best['baseline']:
                best = dict(j=j, k=k, X=X, baseline=base, angle=ang, cond=cond)
    return best


def evaluate_view(xy, held, ids, cams, i, K=K_DEFAULT):
    """Return raw / valid statistics plus explicit failure counts for target view i."""
    raw_err, valid_err, src_depth_fail, tgt_depth_fail, degen, no_pair = [], [], 0, 0, 0, 0
    for t in np.flatnonzero(held):
        u = xy[t, i]
        if not np.isfinite(u[0]):
            continue
        # raw: max-baseline pair, no geometry filter
        others = [j for j in range(len(cams)) if j != i and np.isfinite(xy[t, j, 0])]
        if len(others) >= 2:
            best, bd = None, -1
            for a in range(len(others)):
                for b in range(a + 1, len(others)):
                    j, k = others[a], others[b]
                    d = float(np.linalg.norm(cams[j][:3, 3] - cams[k][:3, 3]))
                    if d > bd:
                        bd, best = d, (j, k)
            X, _ = triangulate(xy[t, best[0]], xy[t, best[1]], cams[best[0]], cams[best[1]])
            if X is not None:
                uv, z = project(X, cams[i])
                uv = np.atleast_1d(uv)[:2]; z = float(np.atleast_1d(z)[0])
                if np.isfinite(uv).all() and z > 0:
                    raw_err.append(float(np.linalg.norm(uv - u)))
        bp = best_pair(xy, t, i, cams)
        if bp is None:
            others2 = [j for j in range(len(cams)) if j != i and np.isfinite(xy[t, j, 0])]
            if len(others2) < 2:
                no_pair += 1
            else:
                degen += 1
            continue
        uv, z = project(bp['X'], cams[i])
        uv = np.atleast_1d(uv)[:2]; z = float(np.atleast_1d(z)[0])
        if not np.isfinite(uv).all():
            degen += 1; continue
        if z <= 0:
            tgt_depth_fail += 1; continue
        valid_err.append(float(np.linalg.norm(uv - u)))
    return dict(raw_err=np.array(raw_err), valid_err=np.array(valid_err),
                source_depth_fail=src_depth_fail, target_depth_fail=tgt_depth_fail,
                degenerate=degen, no_pair=no_pair)
