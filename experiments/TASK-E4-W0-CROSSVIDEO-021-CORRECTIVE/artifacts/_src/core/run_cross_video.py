#!/usr/bin/env python3
"""ONE corrected cross-video entry (021). FIT/HOLDOUT frozen BEFORE any optimisation."""
import argparse, hashlib, json, sys, time
from pathlib import Path
import numpy as np

WS = Path('/home/liu/ring_first_3d_workspace')
B = WS/'experiments/TASK-E4-W0-CROSSVIDEO-021-REPAIR'
sys.path.insert(0, str(WS/'camera_mainline/code'))
sys.path.insert(0, str(WS/'src'))
import w0_adapter as AD
import yaw_1dof as Y1
import shared_se3 as S3
import cross_video_matches as CVM
import camera_rotation_metrics as RM

K = np.array([[490., 0, 319.5], [0, 490., 179.5], [0, 0, 1.]])


def sha(p):
    p = Path(p)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def code_sha():
    fs = [WS/'camera_mainline/code'/n for n in ('se3.py', 'shared_se3.py', 'yaw_1dof.py',
          'geometry_1dof.py', 'cross_video_matches.py', 'w0_adapter.py')]
    return hashlib.sha256(''.join(sha(f) or '' for f in fs).encode()).hexdigest()


def atomic_json(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix('.tmp')
    tmp.write_text(json.dumps(obj, indent=1, default=str))
    tmp.replace(p)


def standard_sampson(u4, u5, H, C4, C5, K):
    return S3.sampson_px(u4, u5, H, C4, C5, K)


def legacy_sampson(u4, u5, H, C4, C5, K):
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--group', required=True)
    ap.add_argument('--video-a', default='004')
    ap.add_argument('--video-b', default='005')
    ap.add_argument('--iters', type=int, default=80)
    a = ap.parse_args()
    g, va, vb = a.group, a.video_a, a.video_b
    out = B/'runs'/g; out.mkdir(parents=True, exist_ok=True)
    st_path = B/'audit'/g/'RUN_STATE.json'
    state = json.loads(st_path.read_text()) if st_path.exists() else dict(group=g, stages={})
    state['code_sha256'] = code_sha()
    state['config_sha256'] = sha(B/'config/UNIFIED_PROTOCOL.json')

    def rec(name, status, **kw):
        state['stages'][name] = dict(status=status, at=time.strftime('%Y-%m-%dT%H:%M:%S'),
                                     code_sha256=state['code_sha256'], **kw)
        atomic_json(st_path, state)
        print('STAGE', name, status, flush=True)

    views_a, acc_a = AD.load_views(g, va)
    views_b, acc_b = AD.load_views(g, vb)
    rec('LOAD_W0', 'PASS', n_a=len(views_a), acc_a=len(acc_a), n_b=len(views_b), acc_b=len(acc_b),
        admission_sha=sha(WS/'camera_mainline'/g/f'video{va}'/'admission.csv'))
    if not acc_a or not acc_b:
        rec('BLOCKED', 'BLOCKED', reason='BLOCKED_BY_W0_ADMISSION')
        atomic_json(out/'RESULTS.json', dict(group=g, status='BLOCKED_BY_W0_ADMISSION',
                                            acc_a=len(acc_a), acc_b=len(acc_b)))
        return
    cams_a = {v['view']: v['c2w'] for v in acc_a}
    cams_b = {v['view']: v['c2w'] for v in acc_b}
    # --- SIFT (matching only; not fitted)
    ms = CVM.collect(list(cams_a), list(cams_b), min_bg=10, group=g, video_a=va, video_b=vb)
    rec('SIFT', 'PASS' if ms else 'FAIL', n_pairs=len(ms), n_matches=sum(m['n_bg'] for m in ms),
        sift='nfeatures=6000, contrastThreshold=0.01, ratio=0.75, background-mask')
    if not ms:
        rec('BLOCKED', 'BLOCKED', reason='NO_MATCHES')
        return
    import pandas as pd
    pd.DataFrame([dict(pair_a=m['a'], pair_b=m['b'], n_ratio=m['n_ratio'], n_bg=m['n_bg']) for m in ms]).to_csv(
        out/'SIFT_MATCHES.csv', index=False)
    np.savez_compressed(out/'MATCHES.npz', a=np.array([m['a'] for m in ms]), b=np.array([m['b'] for m in ms]),
        pa=np.concatenate([m['pa'] for m in ms]), pb=np.concatenate([m['pb'] for m in ms]),
        off=np.r_[0, np.cumsum([len(m['pa']) for m in ms])],
        ids_a=np.concatenate([m['ids_a'] for m in ms]), ids_b=np.concatenate([m['ids_b'] for m in ms]))
    # --- freeze FIT/HOLDOUT by video-b view BEFORE optimisation
    vbs = sorted({m['b'] for m in ms})
    fit_views = set(vbs[::2]); ho_views = set(vbs) - fit_views
    split = dict(fit=sorted(fit_views), holdout=sorted(ho_views))
    atomic_json(out/'SPLIT.json', split)
    pairs_fit = [(cams_a[m['a']], cams_b[m['b']], m['pa'], m['pb']) for m in ms if m['b'] in fit_views]
    pairs_ho = [(cams_a[m['a']], cams_b[m['b']], m['pa'], m['pb']) for m in ms if m['b'] in ho_views]
    rec('SPLIT', 'PASS', fit_views=len(fit_views), holdout_views=len(ho_views), fit_pairs=len(pairs_fit), holdout_pairs=len(pairs_ho))
    # --- init on FIT only
    y1 = Y1.solve([(A, Bv, u, vv, K, K) for (A, Bv, u, vv) in pairs_fit])
    rec('INIT', 'PASS' if y1['status'] in ('UNIQUE_MINIMUM',) else y1['status'],
        theta=y1['theta'], solver_status=y1['status'], median_px=y1['median_px'], inlier3=y1['inlier3'])
    seed = np.eye(4); th = np.deg2rad(y1['theta']); c, s = np.cos(th), np.sin(th)
    seed[:3, :3] = [[c, -s, 0], [s, c, 0], [0, 0, 1]]
    ring = {}
    for v in acc_a:
        p = WS/'experiments/TASK-E4-W0-MAINLINE-CONSOLIDATION-015/runs'/f'{g}_{va}'/'observations'/(v['view']+'_ring.npz')
        if p.exists():
            ring[v['view']] = dict(C=v['c2w'], pts=np.asarray(np.load(p)['q_train'], float))
    # --- A: yaw only (no SE3 optimisation)
    def stats(pairs, H):
        d = np.concatenate([standard_sampson(u, vv, H, A, Bv, K) for (A, Bv, u, vv) in pairs])
        dl = np.concatenate([legacy_sampson(u, vv, H, A, Bv, K) for (A, Bv, u, vv) in pairs])
        return dict(n=len(d), median=float(np.median(d)), p90=float(np.percentile(d, 90)),
                    p95=float(np.percentile(d, 95)), inlier3=float(np.mean(d < 3)),
                    legacy_median=float(np.median(dl)), legacy_inlier3=float(np.mean(dl < 3)))
    A_res = dict(theta=y1['theta'], status=y1['status'], fit=stats(pairs_fit, seed), holdout=stats(pairs_ho, seed))
    # --- B: corrected 6-DoF SE(3) on FIT
    L0, parts = S3.objective(np.zeros(6), seed, ring, pairs_fit, K)
    q, L1, hist, nacc = S3.optimize(seed, ring, pairs_fit, K, iters=a.iters, verbose=True)
    H = S3.pose_from_q(q, seed)
    ok, why = RM.check_so3(H[:3, :3])
    dH = S3.cumulative_delta(H, seed); t_mm, r_deg = S3.delta_size(dH)
    B_res = dict(q=q.tolist(), H=H.tolist(), so3=bool(ok), so3_reason=why,
                 loss_initial=L0, loss_final=L1, parts=parts, accepted=nacc,
                 cumulative_translation_mm=t_mm, cumulative_rotation_deg=r_deg,
                 fit=stats(pairs_fit, H), holdout=stats(pairs_ho, H),
                 bounds=dict(max_translation_mm=S3.MAX_T_MM, max_rotation_deg=S3.MAX_R_DEG))
    res = dict(group=g, video_a=va, video_b=vb, status='EXECUTED',
               split=dict(fit=len(fit_views), holdout=len(ho_views)),
               ring_views=len(ring), A_yaw_only=A_res, B_se3=B_res,
               note='Sampson is the STANDARD 4-term formula; legacy_median is the old non-standard value on the same matches')
    atomic_json(out/'RESULTS.json', res)
    atomic_json(out/'SE3_HISTORY.json', hist)
    rec('OPTIMIZE', 'PASS', accepted=nacc, loss_initial=L0, loss_final=L1,
        cumulative_mm=t_mm, cumulative_deg=r_deg)
    rec('EVALUATE', 'PASS', fit_median=B_res['fit']['median'], holdout_median=B_res['holdout']['median'])
    print(json.dumps(dict(A=A_res, B={k: v for k, v in B_res.items() if k not in ('q', 'H', 'parts')}), indent=1))


if __name__ == '__main__':
    main()
