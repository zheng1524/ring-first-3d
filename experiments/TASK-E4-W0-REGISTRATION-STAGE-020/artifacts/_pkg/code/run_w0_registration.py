#!/usr/bin/env python3
"""Cross-video registration stage that lives inside the W0 program.

Inputs : W0 cameras (camera_mainline/G03/video00{4,5}), ring observations, real SIFT matches.
Method : historical 020 core methods (shared SE(3) correction, Adam lr .01 + backtracking + bounds,
         Ring curve term, bidirectional epipolar term, prior) ported into camera_mainline/code.
Output : research candidate only - never written into camera_mainline production files.
"""
import argparse, json, sys
from pathlib import Path
import numpy as np

WS = Path('/home/liu/ring_first_3d_workspace')
sys.path.insert(0, str(WS/'camera_mainline/code'))
sys.path.insert(0, str(WS/'src'))
import shared_se3 as S3
import camera_rotation_metrics as RM
import yaw_1dof as Y1

T = WS/'experiments/TASK-E4-W0-REGISTRATION-STAGE-020'
RUN4 = WS/'experiments/TASK-E4-W0-MAINLINE-CONSOLIDATION-015/runs/G03_004'
FIX = WS/'experiments/TASK-E4-RING-CROSS-VIDEO-018-REPAIR/fixtures'
K = np.array([[490., 0, 319.5], [0, 490., 179.5], [0, 0, 1.]])


def load(path):
    d = np.load(path)
    return {str(i): d['c2w'][k] for k, i in enumerate(d['ids'])}, d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--iters', type=int, default=80)
    ap.add_argument('--holdout', action='store_true')
    a = ap.parse_args()
    c4, d4 = load(WS/'camera_mainline/G03/video004/camera_result.npz')
    c5, d5 = load(WS/'camera_mainline/G03/video005/accepted_cameras.npz')
    import pandas as pd
    adm = pd.read_csv(WS/'camera_mainline/G03/video004/admission.csv')
    acc4 = [str(v) for v, s in zip(adm['view'], adm['admission_status']) if str(s) == 'ACCEPT']
    acc4 = [v for v in acc4 if v in c4]
    print('004 ACCEPT views:', len(acc4), '| 005:', len(c5), flush=True)
    ring = {}
    for cid in acc4:
        q = np.load(RUN4/'observations'/(cid+'_ring.npz'))
        ring[cid] = dict(C=c4[cid], pts=np.asarray(q['q_train'], float))
    ms = np.load(FIX/'CROSS_VIDEO_B_ACCEPT_matches.npz')
    pairs, pair_view = [], []
    for k in range(len(ms['a'])):
        a_id, b_id = str(ms['a'][k]), str(ms['b'][k])
        if a_id not in acc4:
            continue
        lo, hi = int(ms['off'][k]), int(ms['off'][k+1])
        pairs.append((c4[a_id], c5[b_id], ms['pa'][lo:hi], ms['pb'][lo:hi]))
        pair_view.append(b_id)
    print('pairs used:', len(pairs), 'matches:', sum(len(p[2]) for p in pairs), flush=True)
    # seed: the VALIDATED 1-DoF solver (018-REPAIR) - not a hand-rolled loss
    y1 = Y1.solve([(C4, C5, u4, u5, K, K) for (C4, C5, u4, u5) in pairs])
    th0 = float(y1['theta'])
    print('1-DoF solver: theta=%.2f status=%s median=%.2f inlier3=%.3f' % (
        th0, y1['status'], y1['median_px'], y1['inlier3']), flush=True)
    seed = np.eye(4); c, s = np.cos(np.deg2rad(th0)), np.sin(np.deg2rad(th0))
    seed[:3, :3] = [[c, -s, 0], [s, c, 0], [0, 0, 1]]
    L0, parts0 = S3.objective(np.zeros(6), seed, ring, pairs, K)
    print('seed yaw %.2f deg  initial loss %.6f  parts %s' % (th0, L0, {k: round(v, 4) for k, v in parts0.items()}), flush=True)
    q, L1, hist, nacc = S3.optimize(seed, ring, pairs, K, iters=a.iters, verbose=True)
    H = S3.pose_from_q(q, seed)
    ok = RM.check_so3(H[:3, :3])
    d_before = np.concatenate([S3.sampson_px(u4, u5, seed, C4, C5, K) for (C4, C5, u4, u5) in pairs])
    d_after = np.concatenate([S3.sampson_px(u4, u5, H, C4, C5, K) for (C4, C5, u4, u5) in pairs])
    out = dict(seed_yaw_deg=th0, q=q.tolist(), H=H.tolist(), so3_valid=bool(ok[0]),
               iters=a.iters, accepted=nacc, loss_initial=L0, loss_final=L1, parts_initial=parts0,
               forward_before=dict(median=float(np.median(d_before)), inlier3=float(np.mean(d_before < 3))),
               forward_after=dict(median=float(np.median(d_after)), inlier3=float(np.mean(d_after < 3))),
               correction_translation_mm=float(np.linalg.norm(H[:3, 3] - seed[:3, 3])),
               correction_rotation_deg=float(np.degrees(np.arccos(np.clip((np.trace(H[:3, :3].T @ seed[:3, :3]) - 1)/2, -1, 1)))),
               note='research candidate only; not written to camera_mainline')
    (T/'metrics').mkdir(parents=True, exist_ok=True)
    (T/'metrics/SE3_RESULT.json').write_text(json.dumps(out, indent=1))
    (T/'metrics/SE3_HISTORY.json').write_text(json.dumps(hist, indent=1))
    print(json.dumps({k: (round(v, 6) if isinstance(v, float) else v) for k, v in out.items()
                      if k not in ('H', 'q', 'parts_initial')}, indent=1))
    # holdout by 005 view: fit on one half, evaluate on the other
    if a.holdout:
        views = sorted(set(pair_view)); tr = set(views[::2])
        ptr = [p for p, v in zip(pairs, pair_view) if v in tr]
        pho = [p for p, v in zip(pairs, pair_view) if v not in tr]
        y_tr = Y1.solve([(C4, C5, u4, u5, K, K) for (C4, C5, u4, u5) in ptr])
        seed_tr = np.eye(4); c, s = np.cos(np.deg2rad(y_tr['theta'])), np.sin(np.deg2rad(y_tr['theta']))
        seed_tr[:3, :3] = [[c, -s, 0], [s, c, 0], [0, 0, 1]]
        q_tr, _, _, _ = S3.optimize(seed_tr, ring, ptr, K, iters=a.iters)
        H_tr = S3.pose_from_q(q_tr, seed_tr)
        dh = np.concatenate([S3.sampson_px(u4, u5, H_tr, C4, C5, K) for (C4, C5, u4, u5) in pho])
        ho = dict(train_views=len(tr), holdout_views=len(views) - len(tr),
                  theta_train=float(y_tr['theta']), holdout_median=float(np.median(dh)),
                  holdout_inlier3=float(np.mean(dh < 3)))
        (T/'metrics/HOLDOUT.json').write_text(json.dumps(ho, indent=1))
        print('holdout:', json.dumps(ho), flush=True)


if __name__ == '__main__':
    main()
