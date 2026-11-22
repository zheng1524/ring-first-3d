"""Corrected Ring-anchored BA (027-CORRECTIVE).

Residual blocks are ALL mapped to energies exactly (0.5*sum r^2 == E_k), so scipy runs with
loss='linear' and there is no unintended second Huber. Weights are ENERGY weights.
Frozen/anchor cameras are excluded from the parameter vector (see camvar.CameraVariables).
"""
import numpy as np
import ring_energy as RE
from se3 import exp_se3


def project(X, C, K):
    q = (np.asarray(X, float) - C[:3, 3]) @ C[:3, :3]
    p = q @ np.asarray(K, float).T
    return p[:2]/p[2], p[2]


def _seg_dist(C, K, curves, edges, pts):
    if not len(pts): return np.zeros(0)
    P = curves.project(curves.V[edges].reshape(-1, 3), C, K).reshape(-1, 2)
    A, B = P[0::2], P[1::2]
    v = B - A; den = (v*v).sum(1) + 1e-12
    q = np.asarray(pts, float); d = np.empty(len(q))
    for s in range(0, len(q), 4096):
        Q = q[s:s+4096]
        t = ((Q[:, None, :]-A[None])*v[None]).sum(-1)/den[None]
        cl = A[None] + np.clip(t, 0, 1)[..., None]*v[None]
        d[s:s+4096] = np.sqrt(((Q[:, None, :]-cl)**2).sum(-1).min(1)+1e-12)
    return d


class BAProblem:
    def __init__(self, cams, K_of, obs, ring_pts, X0, camvar, lam_ring=1.0,
                 sig_rot=np.deg2rad(0.5), sig_trans=0.25, sig_geo=50.0,
                 curves=None, edges=None, use_mask=False):
        self.cams, self.K_of, self.obs = cams, K_of, obs
        self.ring_pts = ring_pts           # {cid: {'inner':..,'outer':..,'mid':..}}
        self.X0 = np.asarray(X0, float)
        self.cv = camvar
        self.lam = lam_ring; self.sig = dict(rot=sig_rot, trans=sig_trans, geo=sig_geo)
        self.curves = curves; self.edges = edges or {}
        self.use_mask = use_mask
        self.ss = None

    def cameras(self, theta, H0):
        H, dx, X = self.cv.unpack(theta, H0, len(self.X0))
        C = {}
        for cid in self.cams:
            Cc = exp_se3(dx[cid]) @ np.asarray(self.cams[cid][1], float)
            if self.cams[cid][0] == '004': Cc = H @ Cc
            C[cid] = Cc
        return H, dx, X, C

    def blocks(self, theta, H0):
        H, dx, X, C = self.cameras(theta, H0)
        rgb, prior, geo = [], [], []
        ring = {'inner': [], 'outer': [], 'mid': []}
        for cid, li, uv in self.obs:
            p, z = project(X[li], C[cid], self.K_of[cid])
            rgb.append(p - np.asarray(uv, float))
        ring_energy = {}
        for cid, ev in self.ring_pts.items():
            for key, block, w in (('inner', 'I', 0.35), ('outer', 'O', 0.35), ('mid', 'C', 0.05)):
                e = self.edges.get((cid, key))
                if e is None: continue
                d = _seg_dist(C[cid], self.K_of[cid], self.curves, e, ev.get(key, np.zeros((0, 2))))
                if len(d):
                    ring[key].append(RE.ring_residuals(d, self.lam, w))
                    ring_energy.setdefault(key, []).append(float(np.mean(RE.rho(d/3.0))))
        for cid in self.cv.released:
            dd = dx[cid]
            prior.append(dd[:3]/self.sig['trans']); prior.append(dd[3:]/self.sig['rot'])
        geo.append((X - self.X0).ravel()/self.sig['geo'])
        rgb = np.concatenate(rgb) if rgb else np.zeros(0)
        r_rgb = np.sqrt(2.0*RE.rho(np.linalg.norm(rgb.reshape(-1, 2), axis=1)/3.0)) if rgb.size else np.zeros(0)
        parts = dict(rgb=rgb, ring=ring, prior=prior, geo=geo)
        return parts, r_rgb, dict(ring_energy=ring_energy, C=C, H=H, dx=dx, X=X)

    def residuals(self, theta, H0):
        parts, r_rgb, _ = self.blocks(theta, H0)
        out = [r_rgb] if r_rgb.size else []
        for key in ('inner', 'outer', 'mid'):
            if parts['ring'][key]: out.append(np.concatenate(parts['ring'][key]))
        for blk in ('prior', 'geo'):
            for a in parts[blk]: out.append(np.asarray(a).ravel())
        return np.concatenate(out) if out else np.zeros(0)

    def energy_breakdown(self, theta, H0):
        parts, r_rgb, info = self.blocks(theta, H0)
        e = {}
        if r_rgb.size: e['rgb'] = float(0.5*(r_rgb**2).sum())
        for key in ('inner', 'outer', 'mid'):
            if parts['ring'][key]:
                rr = np.concatenate(parts['ring'][key]); e['ring_' + key] = float(0.5*(rr**2).sum())
        e['prior'] = float(0.5*sum((np.asarray(a)**2).sum() for a in parts['prior']))
        e['geo'] = float(0.5*sum((np.asarray(a)**2).sum() for a in parts['geo']))
        E = {k: float(np.mean([float(np.mean(vv)) for vv in v])) if len(v) else 0.0
             for k, v in info['ring_energy'].items()}
        e['ring_energy_mean_MIO'] = 0.35*E.get('inner', 0) + 0.35*E.get('outer', 0)
        e['total'] = sum(v for k, v in e.items() if k in ('rgb', 'ring_inner', 'ring_outer', 'ring_mid', 'prior', 'geo'))
        return e
