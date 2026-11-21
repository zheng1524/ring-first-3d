"""Adapter: current W0 cameras -> legacy-020 view objects (one place for all conversions)."""
import json
from pathlib import Path
import numpy as np

WS = Path('/home/liu/ring_first_3d_workspace')


def load_views(video):
    d = WS/'camera_mainline'/'G03'/f'video{video}'
    cams = np.load(d/'camera_result.npz')
    adm = {}
    if (d/'admission.csv').exists():
        import pandas as pd
        a = pd.read_csv(d/'admission.csv')
        adm = dict(zip(a['view'].astype(str), a['admission_status'].astype(str)))
    ids = [str(x) for x in cams['ids']]
    out = []
    for k, vid in enumerate(ids):
        out.append(dict(id=vid, group='G03', video=video,
                        raw_frame=int(cams['raw_frames'][k]) if 'raw_frames' in cams else None,
                        role='FIT', K=np.asarray(cams['K'], float), T=np.asarray(cams['c2w'][k], float),
                        admission=adm.get(vid, 'UNKNOWN'), pose_source='W0'))
    return out


def to_legacy_paths(views):
    """Legacy 019/020 expect id/K/T/cache/role."""
    prep = json.loads((WS/'experiments/TASK-E4-UNIFIED-RING-CONTOUR-REFINEMENT-005/runs/prepared/G03_004/PREPARED.json').read_text())['views']
    cache = {q['view']: q['cache'] for q in prep}
    prep5 = json.loads((WS/'experiments/TASK-E4-UNIFIED-RING-CONTOUR-REFINEMENT-005/runs/prepared/G03_005/PREPARED.json').read_text())['views']
    cache.update({q['view']: q['cache'] for q in prep5})
    for v in views:
        v['cache'] = cache.get(v['id'])
    return views
