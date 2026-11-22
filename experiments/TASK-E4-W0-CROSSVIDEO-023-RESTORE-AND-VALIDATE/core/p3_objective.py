#!/usr/bin/env python3
"""P3: historical Ring + SIFT3D + EPI + Prior objective on current G03 W0, with checkpointing.

L(H) = L_Ring + 0.2*L_SIFT3D + 0.02*L_EPI + 0.01*L_Prior,  H = H_(005<-004)
Reuses: features019.landmarks (3D points + observations), features019.match_desc (identity),
camera_mainline W0 cameras, 021 se3.exp (exact 6-DoF), torus_contours (Ring term).
"""
import json, os, sys, time
from pathlib import Path
import numpy as np
WS = Path('/home/liu/ring_first_3d_workspace')
N = WS/'experiments/TASK-E4-W0-CROSSVIDEO-023-RESTORE-AND-VALIDATE'
RUN = N/'replay_019_020/runs/p3'
sys.path.insert(0, str(N/'replay_019_020/code')); sys.path.insert(0, str(N/'core'))
sys.path.insert(0, str(WS/'camera_mainline/code'))
sys.path.insert(0, str(WS/'src'))
import common
import features019 as F19
import se3
from ring_first_3d.mainline.native.camera import torus_contours

W = dict(ring=1.0, sift3d=0.2, epi=0.02, prior=0.01)
SCALE = np.array([0.6, 0.6, 0.6, np.deg2rad(5), np.deg2rad(5), np.deg2rad(5)], float)
MAX_T, MAX_R = 1.2, 10.0


def sha(p): return common.sha(Path(p))


def load_w0():
    import pandas as pd
    out = {}
    for v in ('004', '005'):
        d = np.load(WS/'camera_mainline/G03'/f'video{v}'/'camera_result.npz')
        adm = pd.read_csv(WS/'camera_mainline/G03'/f'video{v}'/'admission.csv')
        st = dict(zip(adm['view'].astype(str), adm['admission_status'].astype(str)))
        out[v] = {str(i): np.asarray(d['c2w'][k], float) for k, i in enumerate(d['ids']) if st.get(str(i)) == 'ACCEPT'}
        out[v+'_K'] = np.asarray(d['K'], float)
    return out


def load_landmarks(video):
    z = np.load(RUN/'landmarks'/f'G03_{video}.npz')
    obs = common.load(RUN/'landmarks'/f'G03_{video}_OBSERVATIONS.json')
    return np.asarray(z['X'], float), np.asarray(z['des'], np.float32), obs


def hub(x, eps=1.0):
    x = np.abs(x)
    return np.where(x < eps, 0.5*x*x, eps*(x - 0.5*eps))


def project(X, C, K):
    q = (X - C[:3, 3]) @ C[:3, :3]
    p = q @ K.T
    return p[:2]/p[2], q[2]


def build_problem(H0_theta=None):
    cams = load_w0(); K = cams['004_K']
    X4, D4, O4 = load_landmarks('004'); X5, D5, O5 = load_landmarks('005')
    ident = F19.match_desc(D4, D5)          # historical ratio 0.72 + mutual
    print('cross-video descriptor identities:', len(ident), flush=True)
    # bidirectional 3D->2D constraints, split by four-quadrant view split of 004 and 005
    v4 = sorted(cams['004']); v5 = sorted(cams['005'])
    fit4 = set(v4[::2]); ho4 = set(v4) - fit4
    fit5 = set(v5[::2]); ho5 = set(v5) - fit5
    fwd_fit, fwd_ho, rev_fit, rev_ho = [], [], [], []
    for i, j in ident:
        x4 = X4[i]; x5 = X5[j]
        for o in O5[j]['observations']:
            C = cams['005'].get(o['view'])
            if C is None: continue
            (fwd_fit if o['view'] in fit5 else fwd_ho).append((x4, C, np.asarray(o['uv'], float), o['view']))
        for o in O4[i]['observations']:
            C = cams['004'].get(o['view'])
            if C is None: continue
            (rev_fit if o['view'] in fit4 else rev_ho).append((x5, C, np.asarray(o['uv'], float), o['view']))
    ring = {}
    run = WS/'experiments/TASK-E4-W0-MAINLINE-CONSOLIDATION-015/runs/G03_004'
    for v in fit4:
        p = run/'observations'/(v+'_ring.npz')
        if p.exists():
            ring[v] = dict(C=cams['004'][v], pts=np.asarray(np.load(p)['q_train'], float))
    epi = [(cams['004'][a], cams['005'][b], u4, u5) for a, b, u4, u5 in []]  # filled below
    M = np.load(WS/'experiments/TASK-E4-W0-CROSSVIDEO-021-CORRECTIVE/runs/G03/MATCHES.npz')
    m4 = [str(x) for x in M['a']]; m5 = [str(x) for x in M['b']]; off = M['off']
    for k in range(len(m4)):
        if m4[k] in fit4 and m5[k] in fit5:
            lo, hi = int(off[k]), int(off[k+1])
            epi.append((cams['004'][m4[k]], cams['005'][m5[k]], M['pa'][lo:hi], M['pb'][lo:hi]))
    return dict(cams=cams, K=K, ident=ident, fwd_fit=fwd_fit, fwd_ho=fwd_ho, rev_fit=rev_fit, rev_ho=rev_ho,
                ring=ring, epi=epi, split=dict(fit4=sorted(fit4), ho4=sorted(ho4), fit5=sorted(fit5), ho5=sorted(ho5)))


H_SEED = np.eye(4)


def losses(q, P, which='fit'):
    H = se3.exp_se3(np.asarray(q, float)*SCALE) @ H_SEED
    Kinv = np.linalg.inv(P['K'])
    out = {}
    # Ring
    if which == 'fit' and P['ring']:
        tot, n = 0.0, 0
        for cid, r in P['ring'].items():
            C = H @ r['C']; pts = r['pts'][::4]
            try: cs = torus_contours(C, P['K'])
            except ValueError: return None, None
            d = np.minimum.reduce([np.linalg.norm(pts[:, None, :]-np.asarray(c, float)[None], axis=2).min(1) for c in cs])
            tot += hub(d/3.).sum(); n += len(pts)
        out['ring'] = tot/max(n, 1)
    else:
        out['ring'] = 0.0
    # SIFT3D bidirectional
    fw = P['fwd_fit'] if which == 'fit' else P['fwd_ho']
    rv = P['rev_fit'] if which == 'fit' else P['rev_ho']
    def rp(items, M):
        errs = []
        for X, C, uv, _ in items:
            pr = project(M[:3, :3] @ X + M[:3, 3], C, P['K'])
            if pr[1] <= 0: continue
            errs.append(np.linalg.norm(pr[0]-uv))
        return np.array(errs)
    ef = rp(fw, H); er = rp(rv, np.linalg.inv(H))
    out['sift3d_fwd'] = float(hub(ef/3.).mean()) if len(ef) else 0.0
    out['sift3d_rev'] = float(hub(er/3.).mean()) if len(er) else 0.0
    out['sift3d'] = 0.5*(out['sift3d_fwd']+out['sift3d_rev'])
    out['n_fwd'], out['n_rev'] = int(len(ef)), int(len(er))
    # EPI (use the same pairs on both splits to keep them comparable; report separately later)
    d = []
    for (C4, C5, u4, u5) in (P['epi'] if which == 'fit' else []):
        T = np.linalg.inv(C5) @ (H @ C4); R, t = T[:3, :3], T[:3, 3]
        tx = np.array([[0, -t[2], t[1]], [t[2], 0, -t[0]], [-t[1], t[0], 0]])
        F = Kinv.T @ (tx @ R) @ Kinv; n = np.linalg.norm(F)
        if n < 1e-15: continue
        F /= n
        a = np.c_[u4, np.ones(len(u4))]; b = np.c_[u5, np.ones(len(u5))]
        Fa = (F @ a.T).T; Ftb = (F.T @ b.T).T
        d.append(np.abs(np.einsum('ij,ij->i', b, Fa))/np.sqrt((Fa[:, :2]**2).sum(1)+(Ftb[:, :2]**2).sum(1)+1e-12))
    out['epi'] = float(hub(np.concatenate(d)/3.).mean()) if d else 0.0
    out['prior'] = float(np.sum(np.asarray(q, float)**2)/6.)
    out['total'] = W['ring']*out['ring'] + W['sift3d']*out['sift3d'] + W['epi']*out['epi'] + W['prior']*out['prior']
    return out['total'], out


def optimize(q, P, iters=80, lr=0.01, b1=0.9, b2=0.999, eps=1e-8, ckpt=None):
    q = np.asarray(q, float).copy(); m = np.zeros(6); v = np.zeros(6)
    best, parts = losses(q, P, 'fit')
    hist = []
    for it in range(1, iters+1):
        g = np.zeros(6)
        for k in range(6):
            qp = q.copy(); qp[k] += 1e-4; qm = q.copy(); qm[k] -= 1e-4
            lp = losses(qp, P, 'fit')[0]; lm = losses(qm, P, 'fit')[0]
            g[k] = (lp-lm)/2e-4
        if not np.isfinite(g).all():
            hist.append(dict(it=it, accepted=False, reason='NONFINITE_GRADIENT')); continue
        om, ov = m.copy(), v.copy()
        m = b1*m + (1-b1)*g; v = b2*v + (1-b2)*g*g
        mh = m/(1-b1**it); vh = v/(1-b2**it)
        step = lr*mh/(np.sqrt(vh)+eps)
        alpha, ok = 1.0, False
        for _ in range(8):
            cand = q - alpha*step
            dH = se3.exp_se3(cand*SCALE)   # cumulative correction w.r.t. H_seed
            t = float(np.linalg.norm(dH[:3, 3]))
            ang = float(np.degrees(np.arccos(np.clip((np.trace(dH[:3, :3])-1)/2, -1, 1))))
            if t > MAX_T or ang > MAX_R:
                alpha *= .5; continue
            L, pt = losses(cand, P, 'fit')
            if L is not None and np.isfinite(L) and L < best:
                q, best, ok = cand, L, True
                hist.append(dict(it=it, accepted=True, loss=float(L), t_mm=t, r_deg=ang)); break
            alpha *= .5
        if not ok:
            m, v = om, ov
            hist.append(dict(it=it, accepted=False, reason='NO_DECREASE'))
        if ckpt and it % 10 == 0:
            np.savez(ckpt, q=q, m=m, v=v, it=it, best=best)
    return q, best, hist


def main():
    global H_SEED
    P = build_problem()
    sys.path.insert(0, str(WS/'experiments/TASK-E4-W0-CROSSVIDEO-021-CORRECTIVE/core'))
    import yaw_1dof as Y1
    y1 = Y1.solve([(A, B, u, v, P["K"], P["K"]) for (A, B, u, v) in P["epi"]])
    th = np.deg2rad(y1['theta']); c, s_ = np.cos(th), np.sin(th)
    H_SEED = np.eye(4); H_SEED[:3, :3] = [[c, -s_, 0], [s_, c, 0], [0, 0, 1]]
    print('seed yaw', round(y1['theta'], 3), y1['status'], 'median', round(y1['median_px'], 3), flush=True)
    print('split', {k: len(v) for k, v in P['split'].items()}, 'identities', len(P['ident']),
          'sift3d obs', len(P['fwd_fit']), len(P['fwd_ho']), len(P['rev_fit']), len(P['rev_ho']),
          'epi pairs', len(P['epi']), 'ring views', len(P['ring']), flush=True)
    L0, p0 = losses(np.zeros(6), P, 'fit')
    t0 = time.time()
    q, L1, hist = optimize(np.zeros(6), P, iters=80, ckpt=N/'runs/G03/P3_ckpt.npz')
    H = se3.exp_se3(q*SCALE) @ H_SEED
    Lf, pf = losses(q, P, 'fit'); Lo, po = losses(q, P, 'holdout')
    dH = H @ np.linalg.inv(H_SEED)
    t_mm = float(np.linalg.norm(dH[:3, 3])); r_deg = float(np.degrees(np.arccos(np.clip((np.trace(dH[:3, :3])-1)/2, -1, 1))))
    out = dict(H=H.tolist(), H_seed=H_SEED.tolist(), seed_yaw_deg=float(y1['theta']), seed_status=y1['status'], q=q.tolist(), accepted=int(sum(1 for h in hist if h['accepted'])) , iters=len(hist),
               split_views={k: len(v) for k, v in P['split'].items()},
               identities=len(P['ident']),
               obs=dict(fwd_fit=len(P['fwd_fit']), fwd_holdout=len(P['fwd_ho']),
                        rev_fit=len(P['rev_fit']), rev_holdout=len(P['rev_ho'])),
               loss_fit_initial=p0, loss_fit_final=pf, loss_holdout_final=po,
               correction=dict(mm=t_mm, deg=r_deg), seconds=round(time.time()-t0, 1),
               weights=W, note='L_SIFT3D uses historical landmarks + historical match_desc identities; '
                               'landmark triangulation used ALL views, so the view split is only partial leakage control')
    (N/'runs/G03/P3_RESULT.json').write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps({k: v for k, v in out.items() if k not in ('H', 'q', 'H_seed')}, indent=1, default=str))


if __name__ == '__main__':
    main()
