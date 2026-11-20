"""Prepare FIT views from raw video with the frozen DXY INIT (bit-exact math)."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
from prepare import prepare_view, sha
WS = Path('/home/liu/ring_first_3d_workspace'); T = WS/'experiments/TASK-E4-UNIFIED-RING-CONTOUR-REFINEMENT-005'
ALL = json.loads(Path('/home/liu/polyp_research/ring-first-3d/experiments/TASK-E4-PYTORCH3D-014/config/ALL_VIEWS.json').read_text())
MAP = pd.read_csv(WS/'experiments/TASK-E4-PREBODY-UNIFIED-CAMERA-READINESS-004/metrics/VIDEO_FRAME_MAP.csv')
N = int(sys.argv[1]) if len(sys.argv) > 1 else 16
rows = []
for _, r in MAP.iterrows():
    g, v = r.group, str(r.video).zfill(3)
    video = Path(r.video_path)
    views = sorted([x for x in ALL if x['case'] == g and x['video'] == v and isinstance(x.get('raw_frame'), int)],
                   key=lambda x: x['raw_frame'])[:N]
    out = T/'runs/prepared'/f'{g}_{v}'; out.mkdir(parents=True, exist_ok=True)
    recs = []
    for x in views:
        p = out/(x['id']+'.npz')
        if not p.exists():
            prepare_view(video, int(x['raw_frame']), p)
        recs.append(dict(view=x['id'], raw_frame=int(x['raw_frame']), cache=str(p)))
        print('prep', g, v, x['id'], flush=True)
    (out/'PREPARED.json').write_text(json.dumps(dict(group=g, video=v, video_path=str(video),
        video_sha256=sha(video), init_weights='/home/liu/polyp_research/experiments/dxy_remeasurement_20260917/02_segmentation/model/model.safetensors',
        init_weight_sha256='981aa596e8906edc4457219581c606d4a5a22bfc6f7e4924d3d9a4b9aff64464',
        math='PIL bilinear 256 /255; bilinear logits upsample; argmax', views=recs), indent=1))
    rows += [dict(group=g, video=v, **q) for q in recs]
pd.DataFrame(rows).to_csv(T/'metrics/INPUT_PROVENANCE.csv', index=False)
print('prepared', len(rows))
