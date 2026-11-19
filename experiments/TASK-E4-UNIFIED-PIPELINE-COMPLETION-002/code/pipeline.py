"""Completion IO and fail-closed contracts; the 001 scientific APIs are reused."""
from pathlib import Path
import importlib.util, json, csv, hashlib
import numpy as np
from ring_first_3d.mainline.native.io import save_json,sha256
TASK=Path(__file__).resolve().parents[1];ROOT=TASK.parents[1]
OLD=ROOT/'experiments/TASK-E4-UNIFIED-RING-FIRST-HERO-DEPTH-001'
OUT=TASK/'runs/RF_ONLY_V1';OUT.mkdir(exist_ok=True)
GROUPS=['G01','G02','G03','G05','G06']
spec=importlib.util.spec_from_file_location('_completion_baseline_contracts',OLD/'code/pipeline.py');prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
read=prior.read;cases=prior.cases;check_input=prior.check_input;camera_gate=prior.camera_gate
def table(path,rows):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if not rows:path.write_text('');return
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)
def asset(path):
    p=Path(path);return dict(path=str(p.resolve()),sha256=sha256(p),bytes=p.stat().st_size)
def resolve_asset(value):
    s=str(value)
    for key,val in sorted(read(ROOT/'manifests/PATH_BINDINGS.json').items(),key=lambda a:-len(a[0])):
        if s==key or s.startswith(key+'/'):return Path(val+s[len(key):])
    return Path(s)
def views():return read(OLD/'audit/SELECTED_VIEWS.json')
def instance_views(g,video):return [v for v in views() if v['meta']['case']==g and v['meta']['video']==video]
def inherited(g,video):return video=='004' and g in ['G01','G03','G05','G06']
def arraysha(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def require(condition,code,message):
    from ring_first_3d.policy.contracts import require as original
    return original(condition,code,message)
def verify():
    f=read(TASK/'audit/INPUT_FREEZE.json')
    for r in f['files']:require(sha256(r['path'])==r['sha256'],'FREEZE_SHA',r['path'])
    for r in f['scientific_sources']:require(sha256(r['path'])==r['sha256'],'SOURCE_SHA',r['path'])
    for v in views():check_input(v)
def inherited_file(g,video,relative):return OLD/'runs/RF_ONLY_V1'/g/video/relative
