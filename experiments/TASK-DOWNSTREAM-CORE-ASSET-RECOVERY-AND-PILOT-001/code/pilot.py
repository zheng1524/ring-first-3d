"""Task-local input wiring to the real SB002 optimizer; no reconstructed stage."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import numpy as np

TASK = Path(__file__).resolve().parents[1]
REPO = TASK.parents[1]

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def inputs():
    records=json.loads((TASK/'evidence/PROTECTED_INPUTS.json').read_text())
    for rec in records:
        p=REPO/rec['retained']
        if sha(p)!=rec['sha256']:
            raise ValueError('INPUT_DRIFT: '+str(p))
    row=json.loads((TASK/'fixtures/SOURCE_G01.json').read_text())
    root=TASK/'fixtures/G01'
    from common import INITIALIZE
    ring=dict(np.load(root/'RING.npz'))
    initial=INITIALIZE(root/'INITIAL.npz',ring,ring)
    views=[]
    for role in ['FIT','HOLDOUT']:
        for r in row[role]:
            m=r['meta'];a=np.load(root/(m['id']+'.npz'))
            views.append(dict(id=m['id'],video=m['video'],role=role,direction_block=m.get('direction_block',0),K=a['K'],C=a['T'],labels=a['labels'],RGB=a['RGB']))
    return initial,views,ring,json.loads((root/'BASE_SELECTION.json').read_text()),json.loads((root/'CHART.json').read_text())

def guard(out):
    def check(event,args):
        if event!='open' or not isinstance(args[0],(str,bytes)):return
        p=Path(os.fsdecode(args[0])).resolve()
        mode=args[1] if isinstance(args[1],str) else ''
        flags=args[2] if isinstance(args[2],int) else 0
        writing=any(x in mode for x in 'wax+') or flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)
        if writing and str(p).startswith('/home/liu/') and not p.is_relative_to(TASK):
            raise PermissionError('TASK_LOCAL_WRITES_ONLY: '+str(p))
        if not writing and ('evaluation_only' in p.parts or p.suffix=='.blend' or 'GT' in p.name):
            raise PermissionError('NO_GT_IN_PREDICTION: '+str(p))
    sys.addaudithook(check)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);a=ap.parse_args()
    out=Path(a.out).resolve()
    if not out.is_relative_to(TASK) or out.exists():raise ValueError('New task-local output directory required')
    from ring_first_3d.mainline.paths import activate
    activate('TASK-E4-STRUCTURED-BODY-UPDATE-002')
    from optimizer import train
    import torch
    guard(out)
    initial,views,ring,base,chart=inputs()
    cfg=json.loads((TASK/'PILOT_CONFIG.json').read_text())
    out.parent.mkdir(exist_ok=True,parents=True)
    before=sha(TASK/'fixtures/G01/INITIAL.npz')
    train(initial,[v for v in views if v['role']=='FIT'],ring,base,chart,cfg,out,'DEFORM_ONLY')
    final=dict(np.load(out/'FINAL.npz'));updates=json.loads((out/'UPDATES.json').read_text())
    displacement=np.linalg.norm(final['V']-initial['V'],axis=1)
    ancestor=np.load(TASK/'fixtures/G01/INITIAL.npz')
    receipt=dict(case='G01',independent_groups=1,initialization_status='HISTORICAL_011_FINAL_AS_013_INITIAL_NOT_PRISTINE_INITIAL',upstream_checkpoint={k:ancestor[k].tolist() for k in ['step','accepted','stage','active_modes']},new_graph_optimizer_zero_initialized=True,initial_sha256=before,final_sha256=sha(out/'FINAL.npz'),outer_iterations=len(updates['iterations']),adam_steps=sum(len(r['gradient_norms']) for r in updates['iterations']),accepted=sum(r['accepted'] for r in updates['iterations']),rejected_trials=sum(len(r['rejections']) for r in updates['iterations']),mean_displacement_mm=float(displacement.mean()),max_displacement_mm=float(displacement.max()),FIT=sum(v['role']=='FIT' for v in views),HOLDOUT=sum(v['role']=='HOLDOUT' for v in views),GT_read=False,HERO_read=False,python=sys.version,torch=torch.__version__,cuda=torch.cuda.is_available(),GPU=torch.cuda.get_device_name(0))
    assert sha(TASK/'fixtures/G01/INITIAL.npz')==before
    (out/'RUN_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))

if __name__=='__main__':main()
