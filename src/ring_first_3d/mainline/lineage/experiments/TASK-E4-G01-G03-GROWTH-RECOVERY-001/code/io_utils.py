"""Only audited 002 inputs; no candidate search, GT or HERO access here."""
from ring_first_3d.mainline.paths import historical_path as _mainline_path
from pathlib import Path
import sys, json, hashlib
import numpy as np
OLD_ROOT=Path(str(_mainline_path('/home/liu/ring_first_3d_structured_body_002')))
OLD=OLD_ROOT/'experiments/TASK-E4-STRUCTURED-BODY-UPDATE-002'
sys.path.insert(0,str(OLD/'code'))
from common import load_case,legacy,dump
TD=Path(__file__).resolve().parents[1]
def read(p): return json.loads(Path(p).read_text())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def body(p): return dict(np.load(p))
def source_folder(case):
    assert case in ['G01','G03'], 'CASE_SCOPE'
    return OLD/'runs'/case/'DEFORM_SWEEP'

def load_inputs(case,role=None):
    """Read the saved Initial reference, never rerun any initializer or optimizer."""
    folder=source_folder(case);row=next(r for r in read(__import__('common').SOURCES)['cases']if r['case']==case)
    initial=body(folder/'INITIAL.npz');ring=body(row['static']['RING.npz']['path']);views=[]
    for split in ['FIT','HOLDOUT']:
        if role and role!=split:continue
        for v in row[split]:
            a=body(v['cache']['path']);m=v['meta']
            views.append(dict(id=m['id'],video=m['video'],role=split,direction_block=m.get('direction_block',0),K=a['K'],C=a['T'],labels=a['labels'],RGB=a['RGB']))
    return initial,views,ring,read(row['static']['BASE_SELECTION.json']['path']),read(row['static']['CHART.json']['path']),row

