"""Demonstrate the real integration path for per-view SIFT features.

features019.features(v) consumes v['cache'] (npz with RGB/labels/K/T/RGB_SHA256) and writes
features/<id>.npz {xy, des, region, RGB_SHA256}. That is exactly how the historical 020
features/G01_*.npz were produced. This script runs the historical function unmodified on a
cache that still exists locally, proving the path.
"""
import json, sys
from pathlib import Path
RG = Path(__file__).resolve().parents[1]/'historical/replay_G01'/'experiments'
sys.path.insert(0, str(RG/'TASK-E4-RING-SIFT-SYMMETRIC-REGISTRATION-020'/'code'))
sys.path.insert(0, str(RG/'TASK-E4-RING-POLYP-REGISTRATION-019'/'code'))
import features019 as F
from common import R

views = json.loads((RG/'TASK-E4-RING-POLYP-REGISTRATION-019'/'config'/'VIEWS.json').read_text())
SRC = Path('/home/liu/ring_first_3d_workspace/assets/retained_sources/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-HERO-BODY-ADAPT-018/inputs/G01')
v = dict(views[0])
v['cache'] = str(SRC/(v['id'] + '.npz'))
print('view', v['id'], 'cache', Path(v['cache']).exists())
out = F.features(v)
print('features:', out['xy'].shape, out['des'].shape, 'region sample', out['region'][:5])
print('written to', R/'features'/(v['id']+'.npz'), (R/'features'/(v['id']+'.npz')).exists())
