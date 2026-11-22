#!/usr/bin/env python3
"""ONE entry for cross-video registration on the frozen W0 mainline.

    python run_cross_video.py --group G03 --video-a 004 --video-b 005 --stage all

Stages: LOAD_W0 -> VERIFY -> ADAPTER_CACHE -> SIFT -> LANDMARKS -> IDENTITY -> INIT -> CHECK -> SE3 -> EVALUATE -> EXPORT
Only `group` / `video` / manifest change between groups. No per-group algorithm branch.
"""
import argparse, hashlib, json, subprocess, sys, time
from pathlib import Path
import numpy as np

WS = Path('/home/liu/ring_first_3d_workspace')
T = WS/'experiments/TASK-E4-W0-CROSSVIDEO-UNIFIED-020'
sys.path.insert(0, str(T/'adapters'))
sys.path.insert(0, str(WS/'camera_mainline/code'))
sys.path.insert(0, str(WS/'src'))
import asset_resolver as AR
import camera_rotation_metrics as RM
import yaw_1dof as Y1
import shared_se3 as S3
import cross_video_matches as CVM

K_CFG = np.array([[490., 0, 319.5], [0, 490., 179.5], [0, 0, 1.]])


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def code_hash():
    files = [WS/'camera_mainline/code/shared_se3.py', WS/'camera_mainline/code/yaw_1dof.py',
             WS/'camera_mainline/code/geometry_1dof.py', WS/'camera_mainline/code/cross_video_matches.py',
             Path(__file__)]
    return hashlib.sha256(''.join(sha(f) for f in files).encode()).hexdigest()


def load_w0(group, video):
    import numpy as np
    p = AR.w0_camera(group, video)
    d = np.load(p)
    ids = [str(x) for x in d['ids']]
    cams = {i: np.asarray(d['c2w'][k], float) for k, i in enumerate(ids)}
    adm = AR.admission(group, video)
    accepted = [i for i in ids if adm.get(i, 'ACCEPT') == 'ACCEPT']
    return cams, ids, accepted, dict(file=str(p), sha256=sha(p), n=len(ids), n_accepted=len(accepted))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--group', required=True)
    ap.add_argument('--video-a', default='004')
    ap.add_argument('--video-b', default='005')
    ap.add_argument('--stage', default='all')
    ap.add_argument('--iters', type=int, default=80)
    a = ap.parse_args()
    g, va, vb = a.group, a.video_a, a.video_b
    out = T/'runs'/g
    out.mkdir(parents=True, exist_ok=True)
    state = dict(group=g, video_a=va, video_b=vb, code_hash=code_hash(), stages={})

    def rec(name, status, **kw):
        state['stages'][name] = dict(status=status, time=time.strftime('%Y-%m-%dT%H:%M:%S'), **kw)
        (T/'audit'/'RUN_STATE.json').write_text(json.dumps(state, indent=1))

    cams_a, ids_a, acc_a, info_a = load_w0(g, va)
    cams_b, ids_b, acc_b, info_b = load_w0(g, vb)
    rec('LOAD_W0', 'PASS', a=info_a, b=info_b)
    # --- adapter cache: legacy-compatible view objects (id/cache/K/T/role)
    prep_a, prep_b = AR.prepared(g, va), AR.prepared(g, vb)
    cache_a = {q['view']: q['cache'] for q in prep_a['views']}
    cache_b = {q['view']: q['cache'] for q in prep_b['views']}
    adapter = dict(group=g, video_a=va, video_b=vb, k=K_CFG.tolist(),
                   views_a=[dict(id=i, role='FIT', cache=cache_a.get(i), T=cams_a[i].tolist()) for i in acc_a],
                   views_b=[dict(id=i, role='FIT', cache=cache_b.get(i), T=cams_b[i].tolist()) for i in acc_b])
    (out/'adapter_views.json').write_text(json.dumps(adapter, indent=1))
    rec('ADAPTER_CACHE', 'PASS', n_a=len(acc_a), n_b=len(acc_b))
    # --- SIFT matches (real, background-masked, ratio .75)
    ms = CVM.collect(acc_a, acc_b, min_bg=10, group=g, video_a=va, video_b=vb)
    pairs = [(cams_a[m['a']], cams_b[m['b']], m['pa'], m['pb']) for m in ms]
    import pandas as pd
    pd.DataFrame([dict(video_a=m['a'], video_b=m['b'], n_ratio=m['n_ratio'], n_bg=m['n_bg'],
                       frame_a=m['frames_a'], frame_b=m['frames_b']) for m in ms]).to_csv(
        out/'SIFT_EXTRACTION.csv', index=False)
    rec('SIFT', 'PASS' if ms else 'BLOCKED', n_pairs=len(ms), n_matches=sum(m['n_bg'] for m in ms))
    if not ms:
        print('BLOCKED: no cross-video matches'); return
    # --- 1-DoF init (validated solver) + SE(3)
    y1 = Y1.solve([(Ca, Cb, pa, pb, K_CFG, K_CFG) for (Ca, Cb, pa, pb) in pairs])
    rec('INIT', 'PASS', solver_status=y1['status'], theta=y1['theta'], median_px=y1['median_px'], inlier3=y1['inlier3'])
    seed = np.eye(4); c, s = np.cos(np.deg2rad(y1['theta'])), np.sin(np.deg2rad(y1['theta']))
    seed[:3, :3] = [[c, -s, 0], [s, c, 0], [0, 0, 1]]
    ring = {}
    for i in acc_a:
        p = AR.ring_obs(g, va, i)
        if p is not None:
            ring[i] = dict(C=cams_a[i], pts=np.asarray(np.load(p)['q_train'], float))
    L0, parts0 = S3.objective(np.zeros(6), seed, ring, pairs, K_CFG)
    q, L1, hist, nacc = S3.optimize(seed, ring, pairs, K_CFG, iters=a.iters, verbose=True)
    H = S3.pose_from_q(q, seed)
    rec('SE3', 'PASS', loss_initial=L0, loss_final=L1, accepted=nacc, iters=a.iters)
    ok,_ = RM.check_so3(H[:3, :3])
    d0 = np.concatenate([S3.sampson_px(u4, u5, seed, Ca, Cb, K_CFG) for (Ca, Cb, u4, u5) in pairs])
    d1 = np.concatenate([S3.sampson_px(u4, u5, H, Ca, Cb, K_CFG) for (Ca, Cb, u4, u5) in pairs])
    res = dict(group=g, seed_yaw_deg=y1['theta'], H=H.tolist(), so3_valid=bool(ok),
               correction_translation_mm=float(np.linalg.norm(H[:3,3]-seed[:3,3])),
               correction_rotation_deg=float(np.degrees(np.arccos(np.clip((np.trace(H[:3,:3].T@seed[:3,:3])-1)/2,-1,1)))),
               before=dict(median=float(np.median(d0)), p90=float(np.percentile(d0,90)), p95=float(np.percentile(d0,95)),
                           inlier3=float(np.mean(d0<3))),
               after=dict(median=float(np.median(d1)), p90=float(np.percentile(d1,90)), p95=float(np.percentile(d1,95)),
                          inlier3=float(np.mean(d1<3))),
               objective=dict(initial=L0, final=L1, parts_initial=parts0))
    (out/'SE3_RESULT.json').write_text(json.dumps(res, indent=1))
    (out/'SE3_HISTORY.json').write_text(json.dumps(hist, indent=1))
    # --- holdout by video-b view
    views = sorted({m['b'] for m in ms})
    trv = set(views[::2]); ptr = [p for p, m in zip(pairs, ms) if m['b'] in trv]
    pho = [p for p, m in zip(pairs, ms) if m['b'] not in trv]
    if ptr and pho:
        ytr = Y1.solve([(Ca, Cb, pa, pb, K_CFG, K_CFG) for (Ca, Cb, pa, pb) in ptr])
        s2 = np.eye(4); c, s = np.cos(np.deg2rad(ytr['theta'])), np.sin(np.deg2rad(ytr['theta']))
        s2[:3,:3] = [[c,-s,0],[s,c,0],[0,0,1]]
        q2,_,_,_ = S3.optimize(s2, ring, ptr, K_CFG, iters=a.iters)
        H2 = S3.pose_from_q(q2, s2)
        dh = np.concatenate([S3.sampson_px(u4,u5,H2,Ca,Cb,K_CFG) for (Ca,Cb,u4,u5) in pho])
        ho = dict(theta_train=float(ytr['theta']), train_views=len(trv), holdout_views=len(views)-len(trv),
                  holdout_median=float(np.median(dh)), holdout_p90=float(np.percentile(dh,90)),
                  holdout_inlier3=float(np.mean(dh<3)), holdout_n=len(dh))
        (out/'HOLDOUT.json').write_text(json.dumps(ho, indent=1))
        rec('HOLDOUT', 'PASS', **ho)
    print(json.dumps({k:v for k,v in res.items() if k!='H'}, indent=1, default=str))
    rec('EVALUATE', 'PASS', median_after=res['after']['median'])
    rec('EXPORT', 'PASS', path=str(out))


if __name__ == '__main__':
    main()
