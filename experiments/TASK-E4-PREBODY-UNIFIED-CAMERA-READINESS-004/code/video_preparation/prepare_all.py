"""Prepare every instance from raw video with the frozen INIT model (unified, same code)."""
import json, os, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
from prepare import prepare_view, sha

WS = Path('/home/liu/ring_first_3d_workspace')
T = WS / 'experiments/TASK-E4-PREBODY-UNIFIED-CAMERA-READINESS-004'
ALL = json.loads(Path('/home/liu/polyp_research/ring-first-3d/experiments/TASK-E4-PYTORCH3D-014/config/ALL_VIEWS.json').read_text())
MAXV = int(os.environ.get('PREP_MAX', '22'))

def nested(n, cap):
    idx = sorted(set(np.linspace(0, cap - 1, n).round().astype(int).tolist()))
    return idx

def main():
    mp = pd.read_csv(T / 'metrics/VIDEO_FRAME_MAP.csv')
    manifest = []
    for _, r in mp.iterrows():
        g, v = r.group, str(r.video).zfill(3)
        video = Path(r.video_path)
        views = [x for x in ALL if x['case'] == g and x['video'] == v and isinstance(x.get('raw_frame'), int)]
        views.sort(key=lambda x: x['raw_frame'])
        views = views[:MAXV]
        outdir = T / 'runs/prepared' / f'{g}_{v}'
        recs = []
        for x in views:
            p = outdir / (x['id'] + '.npz')
            if p.exists():
                recs.append(dict(view=x['id'], raw_frame=int(x['raw_frame']), cache=str(p)))
                continue
            r2 = prepare_view(video, int(x['raw_frame']), p)
            rec = dict(view=x['id'], raw_frame=int(x['raw_frame'])); rec.update(r2); rec['cache'] = str(p); recs.append(rec)
            print('prep', g, v, x['id'], flush=True)
        (outdir / 'PREPARED.json').write_text(json.dumps(dict(group=g, video=v, video_path=str(video),
                                                              video_sha256=sha(video),
                                                              init_model='/home/liu/polyp_research/models/preserved_best_multiclass_overlapaware_20260405',
                                                              n=len(recs), views=recs), indent=1))
        manifest += [dict(group=g, video=v, view=q['view'], raw_frame=q['raw_frame'], cache=q['cache']) for q in recs]
    pd.DataFrame(manifest).to_csv(T / 'metrics/PREPARED_VIEWS.csv', index=False)
    print('prepared', len(manifest), 'views')

if __name__ == '__main__':
    main()
