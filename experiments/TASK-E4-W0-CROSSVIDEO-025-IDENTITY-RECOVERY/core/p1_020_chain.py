#!/usr/bin/env python3
"""P1: run the REAL historical 019/020 identity chain on current W0 FIT views.

Sequence (verified against features019.cross / features020.make source):
  1) features019.landmarks(fit4, 'CROSS_004')
  2) features019.cross(fit4, fit5, lm004, 'CROSS')          -> CROSS_EPI/PNP
  3) features019.landmarks(fit5, 'INDEPENDENT_005')
  4) features020.make('CROSS', fit5, fit4, 'REVERSE', 'INDEPENDENT_005')
     -> features/CROSS_NAMED_3D_TRACK_PAIRS.json (selected + rejected)
No historical camera, no historical cache is used: VIEWS are current W0 ACCEPT FIT views.
"""
import argparse, json, os, sys
from pathlib import Path
import numpy as np
WS = Path('/home/liu/ring_first_3d_workspace')
N = WS/'experiments/TASK-E4-W0-CROSSVIDEO-025-IDENTITY-RECOVERY'
RUN = N/'replay_019_020/runs'
sys.path.insert(0, str(N/'replay_019_020/code')); sys.path.insert(0, str(N/'core'))
os.environ['E4_RUN_DIR'] = str(RUN)
import common, features019 as F19, features020 as F20
PREP = WS/'experiments/TASK-E4-UNIFIED-RING-CONTOUR-REFINEMENT-005/runs/prepared'


def views_of(group, video):
    import pandas as pd
    d = np.load(WS/'camera_mainline'/group/f'video{video}'/'camera_result.npz')
    adm = pd.read_csv(WS/'camera_mainline'/group/f'video{video}'/'admission.csv')
    st = dict(zip(adm['view'].astype(str), adm['admission_status'].astype(str)))
    prep = {x['view']: x for x in json.loads((PREP/f'{group}_{video}'/'PREPARED.json').read_text())['views']}
    out = {}
    for k, vid in enumerate([str(x) for x in d['ids']]):
        if st.get(vid) != 'ACCEPT': continue
        x = prep[vid]
        out[vid] = dict(id=vid, group=group, video=video, raw_frame=int(x['raw_frame']), cache=x['cache'],
                        T=np.asarray(d['c2w'][k], float), K=np.asarray(d['K'], float),
                        RGB_SHA256=common.sha(Path(x['cache'])), role='FIT')
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--group', default='G03'); a = ap.parse_args()
    g = a.group
    out = N/'runs'/g; [out.joinpath(d).mkdir(parents=True, exist_ok=True) for d in ('IDENTITIES','CONSISTENCY','EVALUATION','VISUALIZATIONS')]
    v4, v5 = views_of(g, '004'), views_of(g, '005')
    if not v4 or not v5:
        (out/'RUN_STATE.json').write_text(json.dumps(dict(group=g, status='BLOCKED_BY_W0_ADMISSION'), indent=1))
        print('BLOCKED_BY_W0_ADMISSION'); return
    a4, a5 = sorted(v4), sorted(v5)
    fit4, ho4 = a4[::2], [x for x in a4 if x not in a4[::2]]
    fit5, ho5 = a5[::2], [x for x in a5 if x not in a5[::2]]
    # HOLDOUT views must NOT be in VIEWS for the identity chain
    views = {**{k: v4[k] for k in fit4}, **{k: v5[k] for k in fit5}}
    for v in views.values(): v['role'] = 'FIT'
    common.VIEWS = views; F19.VIEWS = views; F20.f.VIEWS = views
    json.dump(dict(fit4=fit4, ho4=ho4, fit5=fit5, ho5=ho5,
                   rule='sorted ACCEPT views, even=FIT, odd=HOLDOUT; only FIT passed into 019/020',
                   frozen_before='feature extraction'),
              open(out/'SPLIT.json','w'), indent=1)
    t0 = __import__('time').time()
    lm4 = F19.landmarks(fit4, 'CROSS_004')
    print('L1 004 landmarks', len(np.asarray(lm4['X'])), flush=True)
    F19.cross(fit4, fit5, lm4, 'CROSS')
    print('L2 CROSS epi/pnp done', flush=True)
    lm5 = F19.landmarks(fit5, 'INDEPENDENT_005')
    print('L3 005 landmarks', len(np.asarray(lm5['X'])), flush=True)
    F20.make('CROSS', fit5, fit4, 'REVERSE', 'INDEPENDENT_005')
    print('L4 020 make done', flush=True)
    named = common.load(RUN/'features'/'CROSS_NAMED_3D_TRACK_PAIRS.json')
    epi2d = common.load(RUN/'features'/'CROSS_EPI_2D_ONLY.json')
    pnp_f = common.load(RUN/'features'/'CROSS_PNP.json'); pnp_r = common.load(RUN/'features'/'REVERSE_PNP.json')
    # export for the consistency module (explicit index mapping)
    rows = []
    for k, m in enumerate(named['matches']):
        rows.append(dict(identity_id=k, landmark_004=int(m['landmark004']), landmark_005=int(m['landmark005']),
                         n_votes=len(m['evidence']), support_views_004=';'.join(sorted({e['a'] for e in m['evidence']})),
                         support_views_005=';'.join(sorted({e['b'] for e in m['evidence']})),
                         X004_x=float(m['X004'][0]), X004_y=float(m['X004'][1]), X004_z=float(m['X004'][2]),
                         X005_x=float(m['X005'][0]), X005_y=float(m['X005'][1]), X005_z=float(m['X005'][2])))
    import pandas as pd
    pd.DataFrame(rows).to_csv(out/'IDENTITIES'/'HISTORICAL_020_IDENTITIES.csv', index=False)
    rej = [dict(landmark004=r['landmark004'], landmark005=r['landmark005'], n_votes=len(r['evidence']),
                reason=';'.join(r['reason'])) for r in named['rejected']]
    pd.DataFrame(rej).to_csv(out/'IDENTITIES'/'HISTORICAL_020_REJECTED.csv', index=False)
    summary = dict(group=g, status='EXECUTED', seconds=round(__import__('time').time()-t0, 1),
                   split=dict(fit4=len(fit4), ho4=len(ho4), fit5=len(fit5), ho5=len(ho5)),
                   landmarks=dict(cross_004=int(len(np.asarray(lm4['X']))), independent_005=int(len(np.asarray(lm5['X'])))),
                   cross=dict(epi_pairs=len(epi2d), epi_observations=int(sum(len(x['p']) for x in epi2d)),
                              pnp_success_fwd=int(sum(x['success'] for x in pnp_f)),
                              pnp_success_rev=int(sum(x['success'] for x in pnp_r)),
                              pnp_targets_fwd=len(pnp_f), pnp_targets_rev=len(pnp_r)),
                   identities=dict(selected=len(named['matches']), rejected=len(named['rejected'])),
                   files=dict(named=str(RUN/'features'/'CROSS_NAMED_3D_TRACK_PAIRS.json'),
                              epi2d=str(RUN/'features'/'CROSS_EPI_2D_ONLY.json')))
    (out/'IDENTITIES'/'CHAIN_SUMMARY.json').write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main()
