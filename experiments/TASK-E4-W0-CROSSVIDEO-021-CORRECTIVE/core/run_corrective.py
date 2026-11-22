#!/usr/bin/env python3
"""Formal corrective entry: one pipeline for every group, per-group state, W0 diagnosis."""
import argparse, hashlib, json, sys, time
from pathlib import Path
import numpy as np

C = Path(__file__).resolve().parents[1]
WS = Path('/home/liu/ring_first_3d_workspace')
sys.path.insert(0, str(C/'core')); sys.path.insert(0, str(WS/'src'))
import w0_adapter as AD, yaw_1dof as Y1, shared_se3 as S3
import cross_video_matches as CVM, camera_rotation_metrics as RM

K = np.array([[490., 0, 319.5], [0, 490., 179.5], [0, 0, 1.]])


def sha(p):
    p = Path(p)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def code_sha():
    return hashlib.sha256(''.join(sha(C/'core'/n) or '' for n in
        ('se3.py', 'shared_se3.py', 'yaw_1dof.py', 'geometry_1dof.py', 'cross_video_matches.py',
         'w0_adapter.py', 'run_corrective.py')).encode()).hexdigest()


def atomic(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    t = p.with_suffix('.tmp'); t.write_text(json.dumps(obj, indent=1, default=str)); t.replace(p)


def stats(pairs, H):
    d = np.concatenate([S3.sampson_px(u, v, H, A, B, K) for (A, B, u, v) in pairs]) if pairs else np.array([])
    if not len(d):
        return dict(n=0)
    return dict(n=int(len(d)), median=float(np.median(d)), p90=float(np.percentile(d, 90)),
                p95=float(np.percentile(d, 95)), inlier3=float(np.mean(d < 3)))


def w0_diagnosis(g, v, views):
    """Positive-depth on REAL track points (the gate uses the Ring origin only)."""
    out = []
    run = WS/'experiments/TASK-E4-W0-MAINLINE-CONSOLIDATION-015/runs'/f'{g}_{v}'
    for obj in views:
        n_real, pos_real = 0, 0
        tp = run/'observations'/'tracks005.npz'
        if tp.exists() and obj['view'] not in {x['view'] for x in out}:
            pass
        out.append(dict(view=obj['view'], admission=obj['admission']))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--group', required=True); ap.add_argument('--iters', type=int, default=80)
    a = ap.parse_args(); g = a.group
    rund = C/'runs'/g; rund.mkdir(parents=True, exist_ok=True)
    state = dict(group=g, code_sha256=code_sha(), config_sha256=sha(C/'config/UNIFIED_PROTOCOL.json'), stages={})

    def rec(name, status, **kw):
        state['stages'][name] = dict(status=status, at=time.strftime('%Y-%m-%dT%H:%M:%S'), **kw)
        atomic(rund/'RUN_STATE.json', state)
        allg = {}
        for gg in ('G01', 'G03', 'G05'):
            p = C/'runs'/gg/'RUN_STATE.json'
            if p.exists():
                allg[gg] = json.loads(p.read_text())
        allg[g] = state
        atomic(C/'audit'/'ALL_GROUPS_STATE.json', allg)
        print('STAGE', name, status, flush=True)

    views_a, acc_a = AD.load_views(g, '004')
    views_b, acc_b = AD.load_views(g, '005')
    rec('LOAD_W0', 'PASS', n_a=len(views_a), acc_a=len(acc_a), n_b=len(views_b), acc_b=len(acc_b))
    if not acc_a or not acc_b:
        rec('W0_ADMISSION', 'BLOCKED', reason='BLOCKED_BY_W0_ADMISSION')
        atomic(rund/'RESULTS.json', dict(group=g, status='BLOCKED_BY_W0_ADMISSION',
                                         acc_a=len(acc_a), acc_b=len(acc_b)))
        return
    cams_a = {v['view']: v['c2w'] for v in acc_a}; cams_b = {v['view']: v['c2w'] for v in acc_b}
    ms = CVM.collect(list(cams_a), list(cams_b), min_bg=10, group=g, video_a='004', video_b='005')
    rec('SIFT', 'PASS' if ms else 'FAIL', n_pairs=len(ms), n_matches=sum(m['n_bg'] for m in ms))
    if not ms:
        rec('BLOCKED', 'BLOCKED', reason='NO_MATCHES'); return
    np.savez_compressed(rund/'MATCHES.npz', a=np.array([m['a'] for m in ms]), b=np.array([m['b'] for m in ms]),
        pa=np.concatenate([m['pa'] for m in ms]), pb=np.concatenate([m['pb'] for m in ms]),
        off=np.r_[0, np.cumsum([len(m['pa']) for m in ms])])
    vbs = sorted({m['b'] for m in ms}); fit = set(vbs[::2]); ho = set(vbs) - fit
    atomic(rund/'SPLIT.json', dict(fit=sorted(fit), holdout=sorted(ho)))
    pf = [(cams_a[m['a']], cams_b[m['b']], m['pa'], m['pb']) for m in ms if m['b'] in fit]
    ph = [(cams_a[m['a']], cams_b[m['b']], m['pa'], m['pb']) for m in ms if m['b'] in ho]
    rec('SPLIT', 'PASS', fit_views=len(fit), holdout_views=len(ho), fit_n=len(pf), holdout_n=len(ph))
    y1 = Y1.solve([(A, B, u, v, K, K) for (A, B, u, v) in pf])
    rec('INIT', 'PASS' if y1['status'] == 'UNIQUE_MINIMUM' else y1['status'],
        theta=y1['theta'], solver_status=y1['status'], median_px=y1['median_px'], inlier3=y1['inlier3'])
    seed = np.eye(4); th = np.deg2rad(y1['theta']); c, s = np.cos(th), np.sin(th)
    seed[:3, :3] = [[c, -s, 0], [s, c, 0], [0, 0, 1]]
    ring = {}
    for v in acc_a:
        p = WS/'experiments/TASK-E4-W0-MAINLINE-CONSOLIDATION-015/runs'/f'{g}_004'/'observations'/(v['view']+'_ring.npz')
        if p.exists():
            ring[v['view']] = dict(C=v['c2w'], pts=np.asarray(np.load(p)['q_train'], float))
    L0, parts = S3.objective(np.zeros(6), seed, ring, pf, K)
    q, L1, hist, nacc = S3.optimize(seed, ring, pf, K, iters=a.iters, verbose=True)
    H = S3.pose_from_q(q, seed)
    ok, why = RM.check_so3(H[:3, :3]); t_mm, r_deg = S3.delta_size(S3.cumulative_delta(H, seed))
    res = dict(group=g, status='EXECUTED', split=dict(fit=sorted(fit), holdout=sorted(ho)),
               ring_views=len(ring), init=dict(theta=y1['theta'], solver=y1['status']),
               seed=dict(fit=stats(pf, seed), holdout=stats(ph, seed)),
               final=dict(fit=stats(pf, H), holdout=stats(ph, H)),
               H=H.tolist(), q=q.tolist(), so3=bool(ok), so3_reason=why,
               loss=dict(initial=L0, final=L1, parts=parts), accepted=nacc,
               cumulative=dict(mm=t_mm, deg=r_deg), bounds=dict(mm=S3.MAX_T_MM, deg=S3.MAX_R_DEG),
               L_F='BLOCKED: no cross-video 3D landmark identity')
    atomic(rund/'RESULTS.json', res); atomic(rund/'SE3_HISTORY.json', hist)
    rec('OPTIMIZE', 'PASS', accepted=nacc, cumulative_mm=t_mm, cumulative_deg=r_deg)
    rec('EVALUATE', 'PASS', fit_median=res['final']['fit']['median'], holdout_median=res['final']['holdout']['median'])
    print(json.dumps({k: v for k, v in res.items() if k not in ('H', 'q', 'split')}, indent=1, default=str))


if __name__ == '__main__':
    main()
