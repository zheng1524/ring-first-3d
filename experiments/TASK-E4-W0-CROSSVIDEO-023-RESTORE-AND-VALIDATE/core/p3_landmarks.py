#!/usr/bin/env python3
"""P3: run the UNMODIFIED historical features019.features/landmarks on current G03 W0 views.

Replay dir: replay_019_020/ (common.py copied from 020 with only REPO repointed).
Inputs: W0 camera_result.npz + PREPARED caches (real RGB/labels/K/T).
Outputs: replay_019_020/runs/p3/{features,matches,landmarks,metrics}.
"""
import argparse, json, os, sys, time
from pathlib import Path
import numpy as np
WS = Path('/home/liu/ring_first_3d_workspace')
N = WS/'experiments/TASK-E4-W0-CROSSVIDEO-023-RESTORE-AND-VALIDATE'
RUN = N/'replay_019_020/runs/p3'
RUN.mkdir(parents=True, exist_ok=True)
os.environ['E4_RUN_DIR'] = str(RUN)
sys.path.insert(0, str(N/'replay_019_020/code'))
import common
import features019 as F19
PREP = WS/'experiments/TASK-E4-UNIFIED-RING-CONTOUR-REFINEMENT-005/runs/prepared'


def view_objects(video):
    d = np.load(WS/'camera_mainline/G03'/f'video{video}'/'camera_result.npz')
    import pandas as pd
    adm = pd.read_csv(WS/'camera_mainline/G03'/f'video{video}'/'admission.csv')
    st = dict(zip(adm['view'].astype(str), adm['admission_status'].astype(str)))
    prep = {x['view']: x for x in json.loads((PREP/f'G03_{video}'/'PREPARED.json').read_text())['views']}
    out = {}
    for k, vid in enumerate([str(x) for x in d['ids']]):
        if st.get(vid) != 'ACCEPT':
            continue
        x = prep[vid]
        out[vid] = dict(id=vid, video=video, raw_frame=int(x['raw_frame']), cache=x['cache'],
                        T=np.asarray(d['c2w'][k], float), K=np.asarray(d['K'], float),
                        RGB_SHA256=common.sha(Path(x['cache'])))
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--video', required=True)
    a = ap.parse_args(); v = a.video
    views = view_objects(v)
    common.VIEWS = views          # features019 reads the module-level VIEWS
    F19.VIEWS = views
    t0 = time.time(); feats = {}
    for vid in views:
        f = F19.features(views[vid]); feats[vid] = dict(n=len(f['xy']), des=int(f['des'].shape[0]))
    print('features', {k: v_['n'] for k, v_ in feats.items()}, flush=True)
    ids = sorted(views)
    lm = F19.landmarks(ids, f'G03_{v}')
    # the triangulation metrics are written by landmarks(); read them back for the report
    tri = common.load(RUN/'metrics'/f'G03_{v}_TRIANGULATION.json')
    out = dict(video=v, views=len(views), features=feats,
               tracks_min3=tri['tracks_min3'], qualified_landmarks=tri['qualified'],
               pair_counts=tri['pair_counts'], seconds=round(time.time()-t0, 1),
               landmarks_file=str(RUN/'landmarks'/f'G03_{v}.npz'))
    (N/'metrics').mkdir(exist_ok=True)
    (N/'metrics'/f'P3_landmarks_{v}.json').write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps({k: out[k] for k in ('video','views','tracks_min3','qualified_landmarks','seconds')}, indent=1))


if __name__ == '__main__':
    main()
