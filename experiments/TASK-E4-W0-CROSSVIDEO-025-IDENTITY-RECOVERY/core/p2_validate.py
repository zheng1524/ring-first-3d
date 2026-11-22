#!/usr/bin/env python3
"""P2/P3/P4: consistency (multi-seed), Ring hypothesis status, HOLDOUT (batch, both directions)."""
import argparse, json, os, sys
from pathlib import Path
import numpy as np, pandas as pd
WS = Path('/home/liu/ring_first_3d_workspace')
N = WS/'experiments/TASK-E4-W0-CROSSVIDEO-025-IDENTITY-RECOVERY'
RUN = N/'replay_019_020/runs'
sys.path.insert(0, str(N/'core')); sys.path.insert(0, str(N/'replay_019_020/code')); sys.path.insert(0, str(WS/'src'))
os.environ['E4_RUN_DIR'] = str(RUN)
import common, features019 as F19
from landmark_consistency import check as id_check
from ring_first_3d.mainline.native.camera import torus_contours


def ring_mae(C, pts, K):
    cs = torus_contours(C, K)
    return float(min(np.linalg.norm(pts[:, None, :]-np.asarray(c, float)[None], axis=2).min(1).mean() for c in cs))


def views_of(group, video):
    import pandas as pd
    d = np.load(WS/'camera_mainline'/group/f'video{video}'/'camera_result.npz')
    adm = pd.read_csv(WS/'camera_mainline'/group/f'video{video}'/'admission.csv')
    st = dict(zip(adm['view'].astype(str), adm['admission_status'].astype(str)))
    prep = {x['view']: x for x in json.loads((WS/'experiments/TASK-E4-UNIFIED-RING-CONTOUR-REFINEMENT-005/runs/prepared'/f'{group}_{video}'/'PREPARED.json').read_text())['views']}
    out = {}
    for k, vid in enumerate([str(x) for x in d['ids']]):
        if st.get(vid) != 'ACCEPT': continue
        x = prep[vid]
        out[vid] = dict(id=vid, video=video, cache=x['cache'], raw_frame=int(x['raw_frame']),
                        T=np.asarray(d['c2w'][k], float), K=np.asarray(d['K'], float),
                        RGB_SHA256=common.sha(Path(x['cache'])))
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--group', default='G03'); a = ap.parse_args(); g = a.group
    out = N/'runs'/g; split = json.loads((out/'SPLIT.json').read_text())
    ids = pd.read_csv(out/'IDENTITIES'/'HISTORICAL_020_IDENTITIES.csv')
    v4, v5 = views_of(g, '004'), views_of(g, '005')
    fit4, ho4, fit5, ho5 = split['fit4'], split['ho4'], split['fit5'], split['ho5']
    X4 = ids[['X004_x','X004_y','X004_z']].values; X5 = ids[['X005_x','X005_y','X005_z']].values
    # ---- consistency: multi-seed
    seeds = [0, 1, 2, 3, 4]
    runs = []
    for s in seeds:
        r = id_check(X4, X5, thresh_mm=1.0, min_inliers=3, seed=s)
        H = r['H']
        dH = np.linalg.inv(runs[0]['H']) @ H if runs else np.eye(4)
        t = float(np.linalg.norm(dH[:3, 3])) if runs else 0.0
        ang = float(np.degrees(np.arccos(np.clip((np.trace(dH[:3,:3])-1)/2, -1, 1)))) if runs else 0.0
        ring4 = [ring_mae(H @ v4[v]['T'], np.asarray(np.load(WS/'experiments/TASK-E4-W0-MAINLINE-CONSOLIDATION-015/runs'/f'{g}_004'/'observations'/(v+'_ring.npz'))['q_train'], float), v4[v]['K']) for v in fit4 if (WS/'experiments/TASK-E4-W0-MAINLINE-CONSOLIDATION-015/runs'/f'{g}_004'/'observations'/(v+'_ring.npz')).exists()]
        ring5 = [ring_mae(np.linalg.inv(H) @ v5[v]['T'], np.asarray(np.load(WS/'experiments/TASK-E4-W0-MAINLINE-CONSOLIDATION-015/runs'/f'{g}_005'/'observations'/(v+'_ring.npz'))['q_train'], float), v5[v]['K']) for v in fit5 if (WS/'experiments/TASK-E4-W0-MAINLINE-CONSOLIDATION-015/runs'/f'{g}_005'/'observations'/(v+'_ring.npz')).exists()]
        ring_w0 = [ring_mae(v4[v]['T'], np.asarray(np.load(WS/'experiments/TASK-E4-W0-MAINLINE-CONSOLIDATION-015/runs'/f'{g}_004'/'observations'/(v+'_ring.npz'))['q_train'], float), v4[v]['K']) for v in fit4]
        runs.append(dict(seed=s, status=r['status'], n_inliers=r['n_inliers'], fitness=float(r['fitness']),
                         inlier_ids=[int(i) for i in np.flatnonzero(r['inliers'])],
                         ring_mae_004_H=float(np.mean(ring4)) if ring4 else None,
                         ring_mae_005_Hinv=float(np.mean(ring5)) if ring5 else None,
                         ring_mae_w0=float(np.mean(ring_w0)),
                         H_rel_first=dict(mm=t, deg=ang), H=H.tolist()))
    # choose the hypothesis with most inliers (diagnostic only; NOT a formal H)
    best = max(runs, key=lambda r: (r['n_inliers'], -r['seed']))
    H = np.array(best['H'])
    pd.DataFrame([{k: v for k, v in r.items() if k not in ('H','inlier_ids')} for r in runs]).to_csv(out/'CONSISTENCY'/'MULTISEED_RANSAC.csv', index=False)
    # Ring status is a HYPOTHESIS property
    ring_conflict = bool(best['ring_mae_004_H'] and best['ring_mae_004_H'] > 2.0 * best['ring_mae_w0'])
    ids['ransac_inlier'] = ids.index.isin(best['inlier_ids'])
    e = np.linalg.norm((H[:3, :3] @ X4.T).T + H[:3, 3] - X5, axis=1)
    ids['residual_3d_mm'] = e
    ids['rigid_status'] = np.where(ids.ransac_inlier, 'RIGID_CONSENSUS_SUPPORTED', 'RIGID_CONSENSUS_CONFLICT')
    ids['hypothesis_status'] = 'RING_CONFLICT' if ring_conflict else 'RING_COMPATIBLE'
    # ---- HOLDOUT (batch descriptors, both directions)
    allv = {**{k: v4[k] for k in ho4}, **{k: v5[k] for k in ho5}}
    common.VIEWS = allv; F19.VIEWS = allv
    feats = {}
    for vid in list(ho4)+list(ho5):
        feats[vid] = F19.features(allv[vid])
    Hi = np.linalg.inv(H)
    X4o = np.load(RUN/'landmarks'/'CROSS_004.npz')['X']; X5o = np.load(RUN/'landmarks'/'INDEPENDENT_005.npz')['X']
    D4o = np.load(RUN/'landmarks'/'CROSS_004.npz')['des']; D5o = np.load(RUN/'landmarks'/'INDEPENDENT_005.npz')['des']
    # BATCH: all landmark descriptors as the query set (single-row queries cannot satisfy mutual k=2)
    def batch_map(Dlm, vid):
        f = feats[vid]
        mm = F19.match_desc(np.asarray(Dlm, np.float32), np.asarray(f['des'], np.float32))
        return {int(q): np.asarray(f['xy'][t], float) for q, t in mm}
    maps = {}
    for vid in ho5: maps[('004->005', vid)] = batch_map(D4o, vid)
    for vid in ho4: maps[('005->004', vid)] = batch_map(D5o, vid)
    rows = []
    for k, r in ids.iterrows():
        i, j = int(r.landmark_004), int(r.landmark_005)
        for side, Xsrc, views_ho, M in (('004->005', X4o[i], ho5, H), ('005->004', X5o[j], ho4, Hi)):
            for vid in views_ho:
                uv = maps[(side, vid)].get(i if side == '004->005' else j)
                if uv is None:
                    rows.append(dict(identity=int(k), side=side, view=vid, category='NO_DESCRIPTOR_MATCH', err_px=np.nan))
                    continue
                C = allv[vid]['T']; K = allv[vid]['K']
                X = M[:3, :3] @ Xsrc + M[:3, 3]
                q = (X - C[:3, 3]) @ C[:3, :3]; p = q @ K.T
                if p[2] <= 0:
                    rows.append(dict(identity=int(k), side=side, view=vid, category='NEGATIVE_DEPTH', err_px=np.nan))
                    continue
                err = float(np.linalg.norm(p[:2]/p[2]-uv))
                rows.append(dict(identity=int(k), side=side, view=vid,
                                 category='MATCHED_VALID' if err < 10 else 'MATCHED_HIGH_ERROR', err_px=err))
    ho = pd.DataFrame(rows)
    ho.to_csv(out/'EVALUATION'/'HOLDOUT_BIDIRECTIONAL.csv', index=False)
    cats = ho.groupby(['side','category']).size().reset_index(name='n')
    (out/'EVALUATION'/'HOLDOUT_CATEGORY_COUNTS.csv').write_text(cats.to_csv(index=False)) if False else None
    ok = ho[ho.category == 'MATCHED_VALID']
    # ---- identity-level final classification
    per = ho.groupby('identity').agg(n_rows=('category','size'), n_valid=('category', lambda s: int((s=='MATCHED_VALID').sum())),
                                     median_valid_px=('err_px','median')).reset_index()
    ids = ids.merge(per, left_index=True, right_on='identity', how='left')
    def cls(r):
        if r['rigid_status'] == 'RIGID_CONSENSUS_SUPPORTED' and r.get('n_valid', 0) and r.get('n_valid', 0) >= 2:
            return 'HOLDOUT_SUPPORTED' if not ring_conflict else 'RIGID_CONSENSUS_SUPPORTED'
        if r['rigid_status'] == 'RIGID_CONSENSUS_SUPPORTED':
            return 'RIGID_CONSENSUS_SUPPORTED'
        return 'RIGID_CONSENSUS_CONFLICT'
    ids['final_identity_status'] = ids.apply(cls, axis=1)
    ids.to_csv(out/'IDENTITIES'/'HISTORICAL_020_IDENTITIES_STATUS.csv', index=False)
    summ = dict(group=g, candidates=int(len(ids)), ransac=dict(best_seed=best['seed'], n_inliers=best['n_inliers'],
                ring_mae_w0=best['ring_mae_w0'], ring_mae_004_H=best['ring_mae_004_H'],
                ring_mae_005_Hinv=best['ring_mae_005_Hinv'], hypothesis_status='RING_CONFLICT' if ring_conflict else 'RING_COMPATIBLE'),
                seed_spread=dict(mm=[r['H_rel_first']['mm'] for r in runs], deg=[r['H_rel_first']['deg'] for r in runs]),
                holdout=dict(rows=int(len(ho)), categories=cats.to_dict('records'),
                             matched_valid=int(len(ok)), median_px=float(ok.err_px.median()) if len(ok) else None,
                             p90_px=float(ok.err_px.quantile(.9)) if len(ok) else None),
                final_status=ids.final_identity_status.value_counts().to_dict())
    (out/'EVALUATION'/'VALIDATION_SUMMARY.json').write_text(json.dumps(summ, indent=1, default=str))
    (out/'CONSISTENCY'/'H_HYPOTHESIS.npz').write_text if False else np.savez(out/'CONSISTENCY'/'H_HYPOTHESIS.npz', H=H)
    print(json.dumps(summ, indent=1, default=str))


if __name__ == '__main__':
    main()
