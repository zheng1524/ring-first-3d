"""BA residual builder for R2 (single implementation; extends 027-CORRECTIVE ba_core2 with Centerline).

Residual = sqrt(2*lam*w*rho(d/3)/N) per block so 0.5*sum r^2 == lam * E_block exactly.
Ring blocks: I (CAD inner visible edge), O (outer), C (CAD centre line, curves.mid).
Edges are computed from the INITIAL cameras (never from GT) and frozen during one solve.
"""
import numpy as np
import ring_energy as RE
from se3 import exp_se3


def project(X, C, K):
    q = (np.asarray(X, float) - C[:3, 3]) @ C[:3, :3]
    p = q @ np.asarray(K, float).T
    return p[:2]/p[2], p[2]


def poly_dist(C, K, V, edges, pts):
    """distance from pts to the projected polyline V[edges] (edges are pairs of vertex ids)."""
    if not len(pts) or not len(edges): return np.zeros(len(pts))
    P = (np.asarray(V, float) - C[:3, 3]) @ C[:3, :3]
    P = P @ np.asarray(K, float).T
    P = P[:, :2]/P[:, 2:]
    A, B = P[edges[:, 0]], P[edges[:, 1]]
    v = B - A; den = (v*v).sum(1) + 1e-12
    q = np.asarray(pts, float); d = np.empty(len(q))
    for s in range(0, len(q), 4096):
        Q = q[s:s+4096]
        t = ((Q[:, None, :]-A[None])*v[None]).sum(-1)/den[None]
        cl = A[None] + np.clip(t, 0, 1)[..., None]*v[None]
        d[s:s+4096] = np.sqrt(((Q[:, None, :]-cl)**2).sum(-1).min(1)+1e-12)
    return d


class BAProblemR2:
    def __init__(self, cams, K_of, obs, ring_obs, X0, camvar, geom, lam_ring=1.0,
                 sig_rot=np.deg2rad(0.5), sig_trans=0.25, sig_geo=50.0, use_centerline=True):
        self.cams, self.K_of, self.obs, self.ring_obs = cams, K_of, obs, ring_obs
        self.X0 = np.asarray(X0, float); self.cv = camvar; self.geom = geom
        self.lam = lam_ring; self.use_centerline = use_centerline
        self.sig = dict(rot=sig_rot, trans=sig_trans, geo=sig_geo)

    def cameras(self, theta, H0):
        H, dx, X = self.cv.unpack(theta, H0, len(self.X0))
        C = {}
        for cid in self.cams:
            Cc = exp_se3(dx[cid]) @ np.asarray(self.cams[cid][1], float)
            if self.cams[cid][0] == '004': Cc = H @ Cc
            C[cid] = Cc
        return H, dx, X, C

    def residuals(self, theta, H0):
        H, dx, X, C = self.cameras(theta, H0)
        blocks = {'rgb': [], 'I': [], 'C': [], 'O': [], 'prior': [], 'geo': []}
        for cid, li, uv in self.obs:
            p, z = project(X[li], C[cid], self.K_of[cid])
            blocks['rgb'].append(p - np.asarray(uv, float))
        for cid, ro in self.ring_obs.items():
            K = self.K_of[cid]; g = self.geom[cid]
            for key, blk, w in (('inner', 'I', 0.35), ('outer', 'O', 0.35), ('mid', 'C', 0.05)):
                if key == 'mid' and not self.use_centerline: continue
                d = poly_dist(C[cid], K, g['V_' + key], g['E_' + key], ro.get(key, np.zeros((0, 2))))
                if len(d): blocks[blk].append(RE.ring_residuals(d, self.lam, w))
        for cid in self.cv.released:
            dd = dx[cid]
            blocks['prior'] += [dd[:3]/self.sig['trans'], dd[3:]/self.sig['rot']]
        blocks['geo'].append((X - self.X0).ravel()/self.sig['geo'])
        out = []
        if blocks['rgb']:
            r = np.concatenate(blocks['rgb'])
            out.append(np.sqrt(2.0*RE.rho(np.linalg.norm(r.reshape(-1, 2), axis=1)/3.0)))
        for k in ('I', 'C', 'O'):
            if blocks[k]: out.append(np.concatenate(blocks[k]))
        for k in ('prior', 'geo'):
            for a in blocks[k]: out.append(np.asarray(a).ravel())
        return np.concatenate(out) if out else np.zeros(0)

    def energies(self, theta, H0):
        H, dx, X, C = self.cameras(theta, H0)
        e = {}
        rgb = []
        for cid, li, uv in self.obs:
            p, z = project(X[li], C[cid], self.K_of[cid]); rgb.append(p-uv)
        if rgb:
            r = np.concatenate(rgb).reshape(-1, 2)
            e['rgb'] = float(RE.rho(np.linalg.norm(r, axis=1)/3.0).sum())
        for cid, ro in self.ring_obs.items():
            K = self.K_of[cid]; g = self.geom[cid]
            for key, blk, w in (('inner', 'I', 0.35), ('outer', 'O', 0.35), ('mid', 'C', 0.05)):
                if key == 'mid' and not self.use_centerline: continue
                d = poly_dist(C[cid], K, g['V_' + key], g['E_' + key], ro.get(key, np.zeros((0, 2))))
                if len(d): e['ring_' + blk] = e.get('ring_' + blk, 0.0) + self.lam*w*float(RE.rho(d/3).mean())
        e['prior'] = float(0.5*sum((np.asarray(a)**2).sum() for a in
                                   [dx[c][:3]/self.sig['trans'] for c in self.cv.released] +
                                   [dx[c][3:]/self.sig['rot'] for c in self.cv.released]))
        e['geo'] = float(0.5*(((X-self.X0)/self.sig['geo'])**2).sum())
        e['ring_total'] = sum(v for k, v in e.items() if k.startswith('ring_'))
        e['total'] = sum(v for k, v in e.items() if k in ('rgb', 'ring_I', 'ring_C', 'ring_O', 'prior', 'geo'))
        return e
