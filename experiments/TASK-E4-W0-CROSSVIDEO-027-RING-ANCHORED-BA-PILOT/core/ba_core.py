"""Ring-anchored BA pilot: residual adapter over scipy.optimize.least_squares (no new solver).

Variables (theta):
  H     : 6  (H = Exp(dxi_H) @ H0, H = H_005<-004)
  cam   : 6 * n_released  (T = Exp(dxi) @ T0 ; for 004 the T is the W0 c2w in 004 frame)
  lm    : 3 * n_landmarks (shared background points in the 005 world frame)
Residuals:
  RGB reprojection of each landmark into every real observation (both videos)
  Ring: per-point distances to the historical CAD visible edges (Huber via scipy loss)
  Pose prior: dxi / sigma (frozen scales)
  Geometry prior: weak prior on landmark displacement from the frozen 019 triangulation
"""
import numpy as np
import features019 as F19
from se3 import exp_se3

W_RING = 1.0
SIG_ROT = np.deg2rad(0.5)
SIG_TRANS = 0.25


def apply_cam(dxi, T0):
    C = exp_se3(np.asarray(dxi, float)) @ np.asarray(T0, float)
    return C


def project(X, C, K):
    q = (np.asarray(X, float) - C[:3, 3]) @ C[:3, :3]
    p = q @ np.asarray(K, float).T
    return p[:2]/p[2], p[2]


def ring_distances(C, K, curves, pts, edges=None, cache=None, cid=None):
    """per-point distance to the historical CAD visible edges (inner and outer).

    edges: optional frozen {key: edge-index array} (controlled tests only; visibility frozen
    at the initial pose to keep the numerical Jacobian affordable). Real runs recompute.
    """
    seg = curves.segments(C, K) if edges is None else edges
    if cache is not None and cid is not None and edges is None:
        cache[cid] = seg
    out = {}
    for key in ('inner', 'outer'):
        e = np.asarray(seg[key], int)
        if not len(e): out[key] = np.zeros(0); continue
        V = curves.V[e].reshape(-1, 3)
        P = curves.project(V, C, K).reshape(-1, 2)
        A, B = P[0::2], P[1::2]
        q = np.asarray(pts[key], float)
        if not len(q): out[key] = np.zeros(0); continue
        v = B - A; den = (v*v).sum(1) + 1e-12
        d = np.empty(len(q))
        step = max(1, int(2e6 // max(len(A), 1)))
        for s in range(0, len(q), step):
            Q = q[s:s+step]
            t = ((Q[:, None, :]-A[None])*v[None]).sum(-1)/den[None]
            t = np.clip(t, 0, 1)
            cl = A[None]+t[..., None]*v[None]
            d[s:s+step] = np.sqrt(((Q[:, None, :]-cl)**2).sum(-1).min(1)+1e-12)
        out[key] = d
    return out


class Problem:
    def __init__(self, cams, K_of, obs, rings, pts0, prior, scales, anchor=('005', 0), freeze_edges=False):
        self.freeze_edges = freeze_edges
        self.edge_cache = {}
        self.cams = cams              # {cid: (video, T0)}
        self.K_of = K_of
        self.obs = obs                # list of (cid, lm, uv)
        self.rings = rings            # {cid: {'inner':pts,'outer':pts}}
        self.curves = None
        self.pts0 = pts0
        self.prior = prior            # {cid: T0}
        self.scales = scales          # dict(sig_rot, sig_trans)
        self.order = [c for c in sorted(cams) if c != anchor]
        self.anchor = anchor
        self.dim = 6 + 6*len(self.order) + 3*len(pts0)

    def unpack(self, theta):
        H = exp_se3(theta[:6]) @ self.H0
        d = theta[6:6+6*len(self.order)].reshape(-1, 6)
        dx = {c: d[i] for i, c in enumerate(self.order)}
        dx[self.anchor] = np.zeros(6)
        X = theta[6+6*len(self.order):].reshape(-1, 3)
        return H, dx, X

    def residuals(self, theta, H0):
        self.H0 = H0
        H, dx, X = self.unpack(theta)
        res = []
        for cid, li, uv in self.obs:
            video = self.cams[cid][0]
            C = apply_cam(dx[cid], self.cams[cid][1])
            if video == '004': C = H @ C
            p, z = project(X[li], C, self.K_of[cid])
            r = p - np.asarray(uv, float)
            res.append(r)
        # Ring (per-point; scipy huber(f_scale=3) reproduces historical Huber(d/3))
        for cid, ev in self.rings.items():
            video = self.cams[cid][0]
            C = apply_cam(dx[cid], self.cams[cid][1])
            if video == '004': C = H @ C
            edges = None
            if self.freeze_edges:
                if cid not in self.edge_cache:
                    C0 = apply_cam(dx[cid], self.cams[cid][1])
                    if video == '004': C0 = H @ C0
                    self.edge_cache[cid] = self.curves.segments(C0, self.K_of[cid])
                edges = self.edge_cache[cid]
            d = ring_distances(C, self.K_of[cid], self.curves, ev, edges=edges)
            for key in ('inner', 'outer'):
                if len(d[key]):
                    # historical E_Ring is a WEIGHTED MEAN of Huber(d/3): scale by 1/sqrt(N)
                    # so that sum(r^2) reproduces the mean (quadratic region), not N x the mean.
                    res.append(d[key]/3.0/np.sqrt(len(d[key]))*W_RING)
        # priors
        sg = self.scales
        for cid in self.order:
            dd = dx[cid]
            res.append(dd[:3]/sg['sig_trans']); res.append(dd[3:]/sg['sig_rot'])
        res.append((X-self.pts0).ravel()/sg['sig_geo'])
        return np.concatenate(res)
