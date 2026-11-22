"""Single fail-closed adapter: (group, video) -> view objects for the cross-video stage.

Rules (P1-4):
  * missing admission.csv            -> raise (BLOCKED)
  * view id absent from admission    -> UNKNOWN, excluded from FIT
  * camera file / manifest mismatch  -> raise
  * K mismatch vs the prepared cache -> raise
"""
import json
from pathlib import Path
import numpy as np

WS = Path('/home/liu/ring_first_3d_workspace')
PREP = WS/'experiments/TASK-E4-UNIFIED-RING-CONTOUR-REFINEMENT-005/runs/prepared'
CAM = WS/'camera_mainline'


class W0AdapterError(RuntimeError):
    pass


def load_views(group, video, allowed=('ACCEPT',)):
    d = CAM/group/f'video{video}'
    cam_p, adm_p = d/'camera_result.npz', d/'admission.csv'
    if not cam_p.exists():
        raise W0AdapterError(f'MISSING_W0_CAMERA {cam_p}')
    if not adm_p.exists():
        raise W0AdapterError(f'MISSING_ADMISSION {adm_p}')
    import pandas as pd
    adm = pd.read_csv(adm_p)
    status = dict(zip(adm['view'].astype(str), adm['admission_status'].astype(str)))
    cam = np.load(cam_p)
    ids = [str(x) for x in cam['ids']]
    K = np.asarray(cam['K'], float)
    man = {}
    mp = d/'manifest.json'
    if mp.exists():
        man = json.loads(mp.read_text())
        if 'ids' in man and [str(x) for x in man['ids']] != ids:
            raise W0AdapterError('MANIFEST_ID_MISMATCH')
    prep = json.loads((PREP/f'{group}_{video}'/'PREPARED.json').read_text())
    cache = {q['view']: q for q in prep['views']}
    out = []
    for k, vid in enumerate(ids):
        if vid not in cache:
            continue
        Kc = np.asarray(np.load(cache[vid]['cache'])['K'], float)
        if not np.allclose(Kc, K, atol=1e-9):
            raise W0AdapterError(f'K_MISMATCH {vid}')
        st = status.get(vid, 'UNKNOWN')
        out.append(dict(group=group, video=video, view=vid,
                        raw_frame=int(cache[vid].get('raw_frame', -1)),
                        K=K, c2w=np.asarray(cam['c2w'][k], float),
                        RGB_cache=cache[vid]['cache'], Mask_cache=cache[vid]['cache'],
                        admission=st, source_sha=str(cam_p), pose_source='W0'))
    accepted = [v for v in out if v['admission'] in allowed]
    return out, accepted
