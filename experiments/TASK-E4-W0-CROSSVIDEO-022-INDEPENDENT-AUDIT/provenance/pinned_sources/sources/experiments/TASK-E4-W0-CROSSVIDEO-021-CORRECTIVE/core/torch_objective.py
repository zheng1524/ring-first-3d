"""Torch (autograd) re-implementation of the EPI + Prior terms, for gradient cross-check."""
import torch

SCALE = torch.tensor([0.6, 0.6, 0.6, 0.0872665, 0.0872665, 0.0872665], dtype=torch.float64)


def skew(w):
    z = torch.zeros((), dtype=w.dtype)
    return torch.stack([torch.stack([z, -w[2], w[1]]),
                        torch.stack([w[2], z, -w[0]]),
                        torch.stack([-w[1], w[0], z])])


def exp_se3_t(xi):
    v, w = xi[:3], xi[3:]
    t = torch.linalg.norm(w).clamp_min(1e-12)
    W = skew(w)
    I = torch.eye(3, dtype=xi.dtype)
    R = I + torch.sin(t) / t * W + (1 - torch.cos(t)) / t**2 * (W @ W)
    V = I + (1 - torch.cos(t)) / t**2 * W + (t - torch.sin(t)) / t**3 * (W @ W)
    H = torch.eye(4, dtype=xi.dtype)
    H = torch.cat([torch.cat([R, V @ v[:, None]], dim=1), H[3:4]], dim=0)
    return H


def epi_prior_loss(q, seed, pairs, K):
    """pairs: list of (C4, C5, u4, u5) as torch tensors; K torch (3,3)."""
    Hd = exp_se3_t(q * SCALE)
    H = Hd @ seed
    Kinv = torch.linalg.inv(K)
    tot = torch.zeros((), dtype=q.dtype)
    n = 0
    for C4, C5, u4, u5 in pairs:
        Tr = torch.linalg.inv(C5) @ (H @ C4)
        R, t = Tr[:3, :3], Tr[:3, 3]
        tx = torch.stack([torch.stack([torch.zeros((), dtype=q.dtype), -t[2], t[1]]),
                          torch.stack([t[2], torch.zeros((), dtype=q.dtype), -t[0]]),
                          torch.stack([-t[1], t[0], torch.zeros((), dtype=q.dtype)])])
        F = Kinv.T @ (tx @ R) @ Kinv
        a = torch.cat([u4, torch.ones((len(u4), 1), dtype=q.dtype)], dim=1)
        b = torch.cat([u5, torch.ones((len(u5), 1), dtype=q.dtype)], dim=1)
        Fa = a @ F.T
        Ftb = b @ F
        num = (b * Fa).sum(1).abs()
        den = torch.sqrt((Fa[:, 0]**2 + Fa[:, 1]**2 + Ftb[:, 0]**2 + Ftb[:, 1]**2)) + 1e-12
        d = num / den
        x = (d / 3.0).clamp(max=1.0)
        tot = tot + (0.5 * x * x).sum() + ((d / 3.0) - 0.5).clamp_min(0).sum()
        n += len(d)
    prior = 0.01 * (q ** 2).sum() / 6.0
    return tot / max(n, 1) + prior
