"""Single place that maps (group, video) -> W0 assets / prepared caches / ring observations."""
from pathlib import Path
import json

WS = Path('/home/liu/ring_first_3d_workspace')
PREP = WS/'experiments/TASK-E4-UNIFIED-RING-CONTOUR-REFINEMENT-005/runs/prepared'
RUNS = WS/'experiments/TASK-E4-W0-MAINLINE-CONSOLIDATION-015/runs'


def w0_camera(group, video):
    for name in ('camera_result.npz', 'accepted_cameras.npz'):
        p = WS/'camera_mainline'/group/f'video{video}'/name
        if p.exists():
            return p
    raise FileNotFoundError(f'NO_W0_FOR_{group}_{video}')


def w0_run_dir(group, video):
    p = RUNS/f'{group}_{video}'
    if not p.exists():
        raise FileNotFoundError(f'NO_W0_RUN_DIR_{group}_{video}')
    return p


def prepared(group, video):
    p = PREP/f'{group}_{video}'/'PREPARED.json'
    if not p.exists():
        raise FileNotFoundError(f'NO_PREPARED_{group}_{video}')
    return json.loads(p.read_text())


def admission(group, video):
    import pandas as pd
    p = WS/'camera_mainline'/group/f'video{video}'/'admission.csv'
    if not p.exists():
        return {}
    a = pd.read_csv(p)
    return dict(zip(a['view'].astype(str), a['admission_status'].astype(str)))


def ring_obs(group, video, view):
    p = w0_run_dir(group, video)/'observations'/(view+'_ring.npz')
    return p if p.exists() else None
