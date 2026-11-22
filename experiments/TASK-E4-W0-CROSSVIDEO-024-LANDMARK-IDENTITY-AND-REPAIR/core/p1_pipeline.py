#!/usr/bin/env python3
"""P1/P2/P3: FIT-only landmarks -> cross-video identities -> 3D consistency -> HOLDOUT evaluation."""
import argparse, json, os, sys
from pathlib import Path
import numpy as np, pandas as pd
WS = Path('/home/liu/ring_first_3d_workspace')
M = WS/'experiments/TASK-E4-W0-CROSSVIDEO-024-LANDMARK-IDENTITY-AND-REPAIR'
RUN = M/'replay_019_020/runs'
sys.path.insert(0, str(M/'replay_019_020/code')); sys.path.insert(0, str(M/'core')); sys.path.insert(0, str(WS/'src'))
os.environ['E4_RUN_DIR'] = str(RUN)
import common, features019 as F19
from landmark_consistency import check as id_check
from ring_first_3d.mainline.native.camera import torus_contours

PREP = WS/'experiments/TASK-E4-UNIFIED-RING-CONTOUR-REFINEMENT-005/runs/prepared'
THRESH = 1.0          # pre-registered (see config/CROSS_VIDEO_PROTOCOL.json)


def views_of(group, video):
    import pandas as pd
    d = np.load(WS/'camera_mainline'/group/f'video{video}'/'camera_result.npz')
    adm = pd.read_csv(WS/'camera_mainline'/group/f'video{video}'/'admission.csv')
    st = dict(zip(adm['view'].astype(str), adm['admission_status'].astype(str)))
    prep = {x['view']: x for x in json.loads((PREP/f'{group}_{video}'/'PREPARED.json').read_text())['views']}
    out = {}
    for k, vid in enumerate([str(x) for x in d['ids']]):
        if st.get(vid) != 'ACCEPT':
            continue
        x = prep[vid]
        out[vid] = dict(id=vid, video=video, raw_frame=int(x['raw_frame']), cache=x['cache'],
                        T=np.asarray(d['c2w'][k], float), K=np.asarray(d['K'], float),
                        RGB_SHA256=common.sha(Path(x['cache'])))
    return out


def split(v4, v5):
    a, b = sorted(v4), sorted(v5)
    fit4, ho4 = a[::2], [x for x in a if x not in a[::2]]
    fit5, ho5 = b[::2], [x for x in b if x not in b[::2]]
    return fit4, ho4, fit5, ho5


def ring_mae(cam, pts, K):
    cs = torus_contours(cam, K)
    return float(min(np.linalg.norm(pts[:, None, :]-np.asarray(c, float)[None], axis=2).min(1).mean() for c in cs))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--group', default='G03')
    a = ap.parse_args(); g = a.group
    out = M/'runs'/g; [out.joinpath(d).mkdir(parents=True, exist_ok=True) for d in
                       ('LANDMARKS','IDENTITIES','CONSISTENCY','EVALUATION','VISUALIZATIONS')]
    views4, views5 = views_of(g, '004'), views_of(g, '005')
    if not views4 or not views5:
        (out/'RUN_STATE.json').write_text(json.dumps(dict(group=g, status='BLOCKED_BY_W0_ADMISSION',
                                                          acc4=len(views4), acc5=len(views5)), indent=1))
        print('BLOCKED_BY_W0_ADMISSION', len(views4), len(views5)); return
    fit4, ho4, fit5, ho5 = split(views4, views5)
    json.dump(dict(fit4=fit4, ho4=ho4, fit5=fit5, ho5=ho5, rule='sorted views, even=FIT, odd=HOLDOUT',
                   frozen_before='feature extraction and landmark triangulation'),
              open(out/'SPLIT.json','w'), indent=1)
    allv = {**views4, **views5}; common.VIEWS = allv; F19.VIEWS = allv
    for vid in list(views4)+list(views5):
        F19.features(allv[vid])
    lm4 = F19.landmarks(fit4, 'G03_004_FIT')
    lm5 = F19.landmarks(fit5, 'G03_005_FIT')
    X4, D4 = np.asarray(lm4['X'], float), np.asarray(lm4['des'], np.float32)
    X5, D5 = np.asarray(lm5['X'], float), np.asarray(lm5['des'], np.float32)
    O4 = common.load(RUN/'landmarks'/'G03_004_FIT_OBSERVATIONS.json')
    O5 = common.load(RUN/'landmarks'/'G03_005_FIT_OBSERVATIONS.json')
    pd.DataFrame([dict(landmark=i, views=len(o['observations']), view_ids=';'.join(x['view'] for x in o['observations']),
                       reproj_px=max(o['reprojection_px']), parallax_deg=o['parallax_deg'])
                  for i, o in enumerate(O4)]).to_csv(out/'LANDMARKS'/'FIT_004.csv', index=False)
    pd.DataFrame([dict(landmark=i, views=len(o['observations']), view_ids=';'.join(x['view'] for x in o['observations']),
                       reproj_px=max(o['reprojection_px']), parallax_deg=o['parallax_deg'])
                  for i, o in enumerate(O5)]).to_csv(out/'LANDMARKS'/'FIT_005.csv', index=False)
    # identities (historical matcher)
    ident = F19.match_desc(D4, D5)
    rows = []
    for i, j in ident:
        rows.append(dict(candidate_id=f'{i}_{j}', landmark_004=int(i), landmark_005=int(j),
                         n_support_views_004=len(O4[i]['observations']), n_support_views_005=len(O5[j]['observations']),
                         support_views_004=';'.join(x['view'] for x in O4[i]['observations']),
                         support_views_005=';'.join(x['view'] for x in O5[j]['observations']),
                         X4_x=float(X4[i,0]), X4_y=float(X4[i,1]), X4_z=float(X4[i,2]),
                         X5_x=float(X5[j,0]), X5_y=float(X5[j,1]), X5_z=float(X5[j,2])))
    ids = pd.DataFrame(rows)
    ids.to_csv(out/'IDENTITIES'/'CANDIDATES.csv', index=False)
    # 3D consistency
    if len(ids) >= 3:
        res = id_check(X4[ids.landmark_004.values], X5[ids.landmark_005.values], thresh_mm=THRESH, min_inliers=4, seed=0)
        H = res['H']; res_mm = res['residual_mm']
        sens = []
        for th in (0.5, 1.0, 2.0):
            r = id_check(X4[ids.landmark_004.values], X5[ids.landmark_005.values], thresh_mm=th, min_inliers=4, seed=0)
            sens.append(dict(threshold_mm=th, status=r['status'], n_inliers=r['n_inliers'], fitness=round(float(r['fitness']),3)))
    else:
        res = dict(status='INSUFFICIENT', H=np.eye(4), residual_mm=np.full(len(ids), np.nan), inliers=np.zeros(len(ids), bool), n_inliers=0, fitness=0.0, threshold_mm=THRESH)
        H = res['H']; res_mm = res['residual_mm']; sens = []
    ids['residual_3d_mm'] = res_mm
    ids['ransac_inlier'] = res['inliers']
    ids['final_identity_status'] = np.where(res['inliers'], 'SUPPORTED', 'REJECTED_3D') if res['status'] == 'OK' else 'INSUFFICIENT_EVIDENCE'
    # Ring compatibility of the RANSAC H (004 FIT views)
    ring_rows = []
    for vid in fit4:
        p = WS/'experiments/TASK-E4-W0-MAINLINE-CONSOLIDATION-015/runs'/f'{g}_004'/'observations'/(vid+'_ring.npz')
        if not p.exists(): continue
        pts = np.asarray(np.load(p)['q_train'], float)
        ring_rows.append(dict(view=vid, ring_mae_w0=round(ring_mae(views4[vid]['T'], pts, views4[vid]['K']), 3),
                              ring_mae_ransacH=round(ring_mae(H @ views4[vid]['T'], pts, views4[vid]['K']), 3)))
    pd.DataFrame(ring_rows).to_csv(out/'CONSISTENCY'/'RING_CHECK.csv', index=False)
    # HOLDOUT: independent 2D observations of the same identity in held-out views (descriptor match only)
    def holdout_eval(Xs, Ds, views_ho, target_video, inv):
        errs = []
        for k in range(len(Xs)):
            d = Ds[k][None]
            for vid, vv in views_ho.items():
                f = F19.features(vv); des = f['des']
                if len(des) < 8: continue
                mm = F19.match_desc(d, des)
                if not len(mm): continue
                uv = f['xy'][mm[0,1]]
                X = inv[:3, :3] @ Xs[k] + inv[:3, 3] if target_video == '004' else (H[:3, :3] @ Xs[k] + H[:3, 3])
                T = vv['T']; qv = (X - T[:3, 3]) @ T[:3, :3]; pp = qv @ vv['K'].T
                if pp[2] <= 0: continue
                errs.append(dict(identity=int(k), view=vid, err_px=float(np.linalg.norm(pp[:2]/pp[2]-uv)),
                                 side='004->005' if target_video == '005' else '005->004'))
        return pd.DataFrame(errs)
    ho_f = holdout_eval(X4[ids.landmark_004.values], D4[ids.landmark_004.values], views5 and {k: v for k, v in views5.items() if k in ho5}, '005', H)
    ho_r = holdout_eval(X5[ids.landmark_005.values], D5[ids.landmark_005.values], {k: v for k, v in views4.items() if k in ho4}, '004', None)
    ho = pd.concat([ho_f, ho_r], ignore_index=True) if len(ho_f) or len(ho_r) else pd.DataFrame()
    ho.to_csv(out/'EVALUATION'/'HOLDOUT_2D.csv', index=False)
    ids.to_csv(out/'CONSISTENCY'/'LANDMARK_CONSISTENCY.csv', index=False)
    summary = dict(group=g, status='EXECUTED', split=dict(fit4=len(fit4), ho4=len(ho4), fit5=len(fit5), ho5=len(ho5)),
                   landmarks=dict(n4=int(len(X4)), n5=int(len(X5))),
                   identities=dict(candidates=int(len(ids))),
                   consistency=dict(status=res['status'], n_inliers=int(res['n_inliers']),
                                    fitness=round(float(res['fitness']), 4), threshold_mm=THRESH,
                                    so3=res.get('so3'), degeneracy=res.get('degeneracy'), sensitivity=sens),
                   holdout=dict(n=int(len(ho)), median=float(ho.err_px.median()) if len(ho) else None,
                                p90=float(ho.err_px.quantile(.9)) if len(ho) else None,
                                p95=float(ho.err_px.quantile(.95)) if len(ho) else None),
                   ring=ring_rows)
    (out/'EVALUATION'/'SUMMARY.json').write_text(json.dumps(summary, indent=1, default=str))
    np.savez(out/'CONSISTENCY'/'H_CANDIDATE.npz', H=H)
    print(json.dumps(summary, indent=1, default=str))


if __name__ == '__main__':
    main()
