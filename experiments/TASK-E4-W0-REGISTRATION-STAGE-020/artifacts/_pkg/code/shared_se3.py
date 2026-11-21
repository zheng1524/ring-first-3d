"""Shared-SE(3) cross-video refinement, ported into the W0 program.

Reused historical core methods (020/code/{objective020,optimize020}.py):
  * H = exp_se3(q * scale) @ H_seed          (6-DoF correction, frozen seed)
  * Adam(lr=0.01) + backtracking + hard bounds (translation <= 1.2 mm, rotation <= 10 deg)
  * objective = w_R*L_Ring + w_E*L_Epipolar + w_prior*L_prior
Not reused: RingRenderer mesh rasterisation (needs per-view legacy caches). The Ring term is
computed from the CAD curves against the real ring-boundary observations, i.e. the same
quantity W0 already uses, so it plugs into the current pipeline instead of restoring 019/020.
"""
import numpy as np

SCALE = np.array([0.6, 0.6, 0.6, np.deg2rad(5.0), np.deg2rad(5.0), np.deg2rad(5.0)])
W_RING, W_EPI, W_PRIOR = 1.0, 0.02, 0.01
LR, B1, B2, EPS = 0.01, 0.9, 0.999, 1e-8
MAX_T_MM, MAX_R_DEG = 1.2, 10.0


def exp_se3(w):
    w = np.asarray(w, float)[:3]
    th = np.linalg.norm(w)
    W = np.array([[0, -w[2], w[1]], [w[2], 0, -w[0]], [-w[1], w[0], 0]])
    if th < 1e-12:
        R = np.eye(3) + W
    else:
        R = np.eye(3) + np.sin(th) / th * W + (1 - np.cos(th)) / th**2 * (W @ W)
    T = np.eye(4); T[:3, :3] = R
    return T


def pose_from_q(q, seed):
    d = exp_se3(np.asarray(q, float) * SCALE)
    d[:3, 3] = np.asarray(q, float)[:3] * SCALE[:3]
    return d @ seed


def sampson_px(u4, u5, H, C4, C5, K):
    """Bidirectional-friendly Sampson distance (px) for the pair (H*C4, C5)."""
    C4h = H @ C4
    Tr = np.linalg.inv(C5) @ C4h
    R, t = Tr[:3, :3], Tr[:3, 3]
    tx = np.array([[0, -t[2], t[1]], [t[2], 0, -t[0]], [-t[1], t[0], 0]])
    F = np.linalg.inv(K).T @ (tx @ R) @ np.linalg.inv(K)
    n = np.linalg.norm(F)
    if n < 1e-15:
        return np.full(len(u4), 1e6)
    F = F / n
    a = np.c_[u4, np.ones(len(u4))]; b = np.c_[u5, np.ones(len(u5))]
    Fa = (F @ a.T).T; Ftb = (F.T @ b.T).T
    return np.abs(np.einsum('ij,ij->i', b, Fa)) / (np.hypot(Fa[:, 0], Fa[:, 1]) + np.hypot(Ftb[:, 0], Ftb[:, 1]) + 1e-12)


def huber(x, eps=1.0):
    x = np.abs(x)
    return np.where(x < eps, 0.5 * x * x, eps * (x - 0.5 * eps))


def ring_term(H, ring, K, stride=4):
    """Ring curve loss: projected CAD curves vs the view's real ring-boundary observations.

    The CAD curves are recomputed for every candidate H (they are pose dependent); this is the
    same quantity the W0 pipeline already evaluates, so no legacy RingRenderer is required.
    """
    from ring_first_3d.mainline.native.camera import torus_contours
    tot, n = 0.0, 0
    for cid, q in ring.items():
        C = H @ q['C']; pts = q['pts'][::stride]
        try:
            cs = torus_contours(C, np.asarray(K, float))
        except ValueError:
            return 50.0
        best = None
        for c in cs:
            c = np.asarray(c, float)
            d = np.linalg.norm(pts[:, None, :] - c[None, :, :], axis=2).min(1)
            best = d if best is None else np.minimum(best, d)
        tot += float(huber(best / 3.0).sum()); n += len(pts)
    return tot / max(n, 1)


def objective(q, seed, ring, pairs, K):
    H = pose_from_q(q, seed)
    L_R = ring_term(H, ring, K)
    ds = [sampson_px(u4, u5, H, C4, C5, K) for (C4, C5, u4, u5) in pairs]
    d = np.concatenate(ds) if ds else np.zeros(0)
    L_E = float(huber(d / 3.0).mean()) if len(d) else 0.0
    L_P = float(np.sum(np.asarray(q, float) ** 2) / len(q))
    return W_RING * L_R + W_EPI * L_E + W_PRIOR * L_P, dict(ring=L_R, epi=L_E, prior=L_P, n_matches=len(d))


def optimize(seed, ring, pairs, K, iters=80, verbose=False):
    q = np.zeros(6); m = np.zeros(6); v = np.zeros(6)
    best, _ = objective(q, seed, ring, pairs, K)
    hist, accepted = [], 0
    for it in range(1, iters + 1):
        g = np.zeros(6)
        for k in range(6):
            h = 1e-4 if k < 3 else 1e-4
            qp = q.copy(); qp[k] += h; qm = q.copy(); qm[k] -= h
            g[k] = (objective(qp, seed, ring, pairs, K)[0] -
                    objective(qm, seed, ring, pairs, K)[0]) / (2 * h)
        m = B1 * m + (1 - B1) * g; v = B2 * v + (1 - B2) * g * g
        mh = m / (1 - B1 ** it); vh = v / (1 - B2 ** it)
        step = LR * mh / (np.sqrt(vh) + EPS)
        alpha, ok = 1.0, False
        for _ in range(8):                      # backtracking
            cand = q - alpha * step
            dq = pose_from_q(cand, seed) @ np.linalg.inv(pose_from_q(q, seed))
            trans = float(np.linalg.norm(dq[:3, 3]))
            rot = float(np.degrees(np.arccos(np.clip((np.trace(dq[:3, :3]) - 1) / 2, -1, 1))))
            if trans > MAX_T_MM or rot > MAX_R_DEG:
                alpha *= 0.5; continue
            Lc, _ = objective(cand, seed, ring, pairs, K)
            if Lc < best:
                q, best, ok = cand, Lc, True; accepted += 1
                hist.append(dict(it=it, loss=best, alpha=alpha)); break
            alpha *= 0.5
        if not ok:
            hist.append(dict(it=it, loss=best, alpha=0.0))
        if verbose and it % 10 == 0:
            print('SE3', it, round(best, 6), accepted, flush=True)
    return q, best, hist, accepted
