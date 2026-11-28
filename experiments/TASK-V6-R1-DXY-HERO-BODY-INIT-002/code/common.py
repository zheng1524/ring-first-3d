"""Task boundary: reuse audited 001 kernels, write only to the independent 002 task."""
import sys, importlib, subprocess, hashlib
from pathlib import Path
T=Path(__file__).resolve().parents[1]
ROOT=T.parents[1]
BASE_INIT='3b8610075a4959a32097cca83247faaddbf61aa1'
OLD=Path('/home/liu/.config/superpowers/worktrees/ring_first_3d_workspace/TASK-V6-R1-BODY-INIT-001/experiments/TASK-V6-R1-DXY-HERO-BODY-INIT-001')
PREVIOUS=ROOT/'experiments/TASK-V6-R1-DXY-HERO-BODY-INIT-001'
sys.path.append(str(PREVIOUS/'code'))
_legacy_paths=[PREVIOUS/'code'/n for n in ['core.py','geometry.py','observations.py','fit.py','base_plane.py']]
LEGACY_LOCK=[]
for _p in _legacy_paths:
    _raw=subprocess.check_output(['git','show',BASE_INIT+':'+str(_p.relative_to(ROOT))],cwd=ROOT)
    _h=hashlib.sha256(_raw).hexdigest()
    assert hashlib.sha256(_p.read_bytes()).hexdigest()==_h,'001_SOURCE_DRIFT: '+str(_p)
    LEGACY_LOCK.append(dict(path=str(_p),sha256=_h,commit=BASE_INIT))
import core
core.T=T;core.ROOT=ROOT
_original_snapshot=core.snapshot

def snapshot(commit,path):
    old=OLD/'runtime/pinned'/commit/path
    if not old.exists():return _original_snapshot(commit,path)
    raw=subprocess.check_output(['git','show',commit+':'+path],cwd=ROOT)
    if hashlib.sha256(raw).hexdigest()!=core.sha(old):raise ValueError('HISTORICAL_SOURCE_DRIFT: '+path)
    return old
core.snapshot=snapshot
from core import *

def revision_key():
    names=['common.py','observations_revision.py','pipeline_revision.py','fit_revision.py','base_revision.py','dxy_full.py','registration.py']
    for item in LEGACY_LOCK:asset(item['path'],item['sha256'])
    return digest(dict(revision={n:sha(T/'code'/n) for n in names},legacy=LEGACY_LOCK))
