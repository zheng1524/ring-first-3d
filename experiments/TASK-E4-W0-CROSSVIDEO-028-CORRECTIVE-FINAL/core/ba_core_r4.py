"""R4 BA residual builder — single implementation for M1/M2/M3 and H-only/joint (fixes R3 D1/D2).

rgb_mode is applied in ONE place (residual_blocks) and used by both H-only and joint solves.
Energy bookkeeping is computed from the SAME residual vectors (0.5*||r_block||^2).
"""
import numpy as np
import ring_energy as RE
from se3 import exp_se3


def project(X, C, K):
    q = (np.asarray(X, float) - C[:3, 3]) @ C[:3, :3]
    p = q @ np.asarray(K, float).T
    return p[:2]/p[2], p[2]


def poly_dist(C, K, V, edges, pts):
    if not len(pts) or not len(edges): return np.zeros(0)
    P = (np.asarray(V, float) - C[:3, 3]) @ C[:3, :3]
    P = P @ np.asarray(K, float).T
    P = P[:, :2]/P[:, 2:]
    A, B = P[edges[:, 0]], P[edges[:, 1]]
    v = B - A; den = (v*v).sum(1) + 1e-12
    q = np.asarray(pts, float); d = np.empty(len(q))
    for s in range(0, len(q), 4096):
        Q = q[s:s+4096]
        t = ((Q[:, None]-A[None])*v[None]).sum(-1)/den[None]
        cl = A[None] + np.clip(t, 0, 1)[..., None]*v[None]
        d[s:s+4096] = np.sqrt(((Q[:, None]-cl)**2).sum(-1).min(1)+1e-12)
    return d


def rho(x):
    x = np.abs(np.asarray(x, float))
    return np.where(x < 1.0, 0.5*x*x, x - 0.5)


def rgb_residual(r_px, mode):
    """r_px: (N,2) pixel residuals -> 1-D residual vector whose 0.5*||r||^2 equals the energy."""
    r = np.asarray(r_px, float).reshape(-1, 2)
    if mode == 'huber':
        return np.sqrt(2.0*rho(np.linalg.norm(r, axis=1)/3.0))
    if mode == 'squared':
        return (r/3.0).ravel()
    if mode == 'dir2d':
        e = r/3.0; s = np.linalg.norm(e, axis=1)
        f = np.where(s <= 1.0, 1.0, np.sqrt(2.0*rho(s))/np.maximum(s, 1e-12))
        return (e*f[:, None]).ravel()
    raise ValueError(mode)


class BAProblemR4:
    def __init__(self, cams, K_of, obs, ring_obs, X0, camvar, geom, lam_ring=1.0,
                 sig_rot=np.deg2rad(0.5), sig_trans=0.25, sig_geo=50.0, use_centerline=True):
        self.cams, self.K_of, self.obs, self.ring_obs = cams, K_of, obs, ring_obs
        self.X0 = np.asarray(X0, float); self.cv = camvar; self.geom = geom
        self.lam = lam_ring; self.use_centerline = use_centerline
        self.sig = dict(rot=sig_rot, trans=sig_trans, geo=sig_geo)

    def cameras_from(self, H, dx):
        C = {}
        for cid in self.cams:
            Cc = exp_se3(np.asarray(dx[cid], float)) @ np.asarray(self.cams[cid][1], float)
            if self.cams[cid][0] == '004': Cc = H @ Cc
            C[cid] = Cc
        return C

    def blocks(self, H, dx, X):
        C = self.cameras_from(H, dx)
        blk = {'rgb': [], 'I': [], 'C': [], 'O': [], 'prior': [], 'geo': []}
        for cid, li, uv in self.obs:
            p, z = project(X[li], C[cid], self.K_of[cid])
            blk['rgb'].append(p - np.asarray(uv, float))
        for cid, ro in self.ring_obs.items():
            g = self.geom[cid]
            for key, b, w in (('inner', 'I', 0.35), ('outer', 'O', 0.35), ('mid', 'C', 0.05)):
                if key == 'mid' and not self.use_centerline: continue
                d = poly_dist(C[cid], self.K_of[cid], g['V_' + key], g['E_' + key], ro.get(key, np.zeros((0, 2))))
                if len(d): blk[b].append(RE.ring_residuals(d, self.lam, w))
        for cid in self.cv.released:
            dd = dx[cid]
            blk['prior'] += [dd[:3]/self.sig['trans'], dd[3:]/self.sig['rot']]
        blk['geo'].append((X - self.X0).ravel()/self.sig['geo'])
        return blk

    def residual_vector(self, H, dx, X, rgb_mode='huber'):
        blk = self.blocks(H, dx, X)
        out = []
        if blk['rgb']:
            out.append(rgb_residual(np.concatenate(blk['rgb']), rgb_mode))
        for k in ('I', 'C', 'O'):
            if blk[k]: out.append(np.concatenate(blk[k]))
        for k in ('prior', 'geo'):
            for a in blk[k]: out.append(np.asarray(a).ravel())
        return np.concatenate(out) if out else np.zeros(0), blk

    def energy_table(self, H, dx, X, rgb_mode='huber'):
        r, blk = self.residual_vector(H, dx, X, rgb_mode)
        e = {}
        if blk['rgb']:
            e['rgb'] = float(0.5*(rgb_residual(np.concatenate(blk['rgb']), rgb_mode)**2).sum())
            rr = np.concatenate(blk['rgb']).reshape(-1, 2)
            e['rgb_median_px'] = float(np.median(np.linalg.norm(rr, axis=1)))
            e['rgb_p90_px'] = float(np.percentile(np.linalg.norm(rr, axis=1), 90))
            e['rgb_n'] = int(len(rr))
        for k in ('I', 'C', 'O'):
            e['ring_' + k] = float(0.5*(np.concatenate(blk[k])**2).sum()) if blk[k] else 0.0
            e['n_ring_' + k] = int(sum(len(np.asarray(x)) for x in blk[k])) if blk[k] else 0
        e['prior'] = float(0.5*sum((np.asarray(a)**2).sum() for a in blk['prior']))
        e['geo'] = float(0.5*sum((np.asarray(a)**2).sum() for a in blk['geo']))
        e['total_terms'] = sum(v for k, v in e.items() if k in ('rgb', 'ring_I', 'ring_C', 'ring_O', 'prior', 'geo'))
        e['half_r2'] = float(0.5*(r**2).sum())
        return e, r
