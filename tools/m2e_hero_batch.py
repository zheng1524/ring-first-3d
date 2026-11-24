#!/usr/bin/env python3
"""M2E real HERO batch on T13-selected tuples, with historical cleaning."""
import sys,json,time,pathlib,hashlib,traceback
import numpy as np,pandas as pd,torch
WS=pathlib.Path('/home/liu/ring_first_3d_workspace');sys.path[:0]=[str(WS/'src'),str(WS/'experiments/TASK-E4-UNIFIED-RING-FIRST-HERO-DEPTH-001/code')]
cfg=json.loads((WS/'mainline/configs/SITE.local.json').read_text());sys.path[:0]=[str(x) for x in cfg.get('readonly_dependency_paths',[])]
from ring_first_3d.mainline.native.hero import load_official,infer
from ring_first_3d.mainline.native.cleaning import classify_native
from ring_first_3d.mainline.native.io import save_json,sha256
O=WS/'runs/m2e_historical_method_integration'; H=O/'hero';H.mkdir(parents=True,exist_ok=True)
D=pd.read_csv(WS/'runs/m2c_corrective_completion/W0_79_VIDEO_RESULTS.csv');dmap={(r.group_id,f'{int(r.video_id):03d}'):r for _,r in D.iterrows()}
S=pd.read_csv(O/'support/SUPPORT_SELECTION_RESULTS.csv');S=S[S.status=='READY'].copy();PREP=WS/'runs/m1_final_39/prepared';CLEAN=WS/'runs/m2c_trajectory_admission/clean_labels'
roots=[PREP,WS/'runs/m2a_w0_recovery/prepared_c2b',WS/'runs/m2a_w0_recovery/prepared_c2',WS/'runs/m2a_w0_recovery/prepared_b1r',WS/'runs/m2a_w0_recovery/prepared_c3',WS/'runs/m2a_w0_recovery/prepared_c3b',WS/'runs/m2c_trajectory_admission/A_correctness/prepared_c3']
def load_frames(g,v,target,sups):
 r=dmap[(g,v)];p=pathlib.Path(r.output_path);cr=np.load(p/'camera_result.npz');ids=[str(x) for x in cr['ids']];cams=np.asarray(cr['c2w'],float);by={}
 for root in roots:
  fp=root/f'{g}_{v}'/'PREPARED.json'
  if fp.exists():
   for x in json.loads(fp.read_text())['views']:
    if x['view'] not in by:by[x['view']]=x
 frames=[]
 for cid in [target]+sups:
  q=by[cid];a=np.load(q['cache']);lab=a['labels'];cp=CLEAN/f'{g}_{v}'/(cid+'.npz')
  if cp.exists():lab=np.load(cp)['labels']
  frames.append(dict(id=cid,RGB=a['RGB'],labels=lab,K=np.asarray(a['K'],float),c2w_mm=cams[ids.index(cid)]))
 return frames,cams,ids
model,receipt=load_official(cfg['mvs_root'],cfg['checkpoint'],cfg['dino_root'],json.loads((WS/'src/ring_first_3d/mainline/native/upstream_source_lock.json').read_text()));save_json(H/'MODEL_RECEIPT.json',receipt)
rows=[];clean=[]
for n,(_,s) in enumerate(S.iterrows(),1):
 g,v,target=str(s.group_id),f'{int(s.video_id):03d}',str(s.target_id);sups=str(s.support_ids).split(';');out=H/g/v/target;out.mkdir(parents=True,exist_ok=True)
 try:
  if not (out/'HERO_native.npz').exists():
   frames,cams,ids=load_frames(g,v,target,sups);rec=infer(model,frames,out);status='PASS'
  else:rec=json.loads((out/'INFERENCE.json').read_text()) if (out/'INFERENCE.json').exists() else {};status='REUSED'
  ring=O/'cad'/('R5.npz' if 'R5' in g else 'R10.npz');cr=classify_native(out,str(ring))
  rows.append(dict(group_id=g,video_id=v,target_id=target,support_ids=';'.join(sups),status=status,seconds=rec.get('seconds'),peak_gpu_bytes=rec.get('peak_GPU_bytes'),raw_faces=rec.get('raw_faces'),output_dir=str(out),herO_native_sha=sha256(out/'HERO_native.npz')))
  clean.append(dict(group_id=g,video_id=v,target_id=target,**cr['counts'],confirmed_gap_edges=cr['confirmed_gap_edges'],protocol_sha256=cr['protocol_sha256']))
  print(n,'/',len(S),g,v,target,status,cr['counts'],flush=True)
 except Exception as e:
  rows.append(dict(group_id=g,video_id=v,target_id=target,support_ids=';'.join(sups),status='FAIL',error=repr(e),output_dir=str(out)))
  print('FAIL',n,g,v,target,repr(e),flush=True)
 pd.DataFrame(rows).to_csv(H/'HERO_EXECUTION_RESULTS.csv',index=False);pd.DataFrame(clean).to_csv(O/'cleaning/CLEANING_METRICS.csv',index=False)
print('DONE',len(rows),'clean',len(clean))
