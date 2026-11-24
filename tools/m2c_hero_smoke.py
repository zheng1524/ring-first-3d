#!/usr/bin/env python3
"""One real HERO inference for M2C correctness; no fallback/substitution."""
import json,os,sys,time,pathlib,torch,numpy as np,pandas as pd
WS=pathlib.Path('/home/liu/ring_first_3d_workspace'); OUT=WS/'runs/m2c_corrective_completion'; H=OUT/'hero_smoke'; H.mkdir(parents=True,exist_ok=True)
sys.path[:0]=[str(WS/'src'),str(WS/'experiments/TASK-E4-UNIFIED-RING-FIRST-HERO-DEPTH-001/code')]
cfg=json.loads((WS/'mainline/configs/SITE.local.json').read_text())
sys.path[:0]=[str(x) for x in cfg.get('readonly_dependency_paths',[])]
from ring_first_3d.mainline.native.hero import load_official,infer
from ring_first_3d.mainline.native.io import save_json,sha256
lock=json.loads((WS/'src/ring_first_3d/mainline/native/upstream_source_lock.json').read_text())
# choose G03/005 S0 accepted target/supports
d=pd.read_csv(WS/'runs/m2c_trajectory_admission/A_correctness/W0_79_VIDEO_RESULTS.csv'); r=d[(d.group_id=='GP_Ip_20.0mm_closed_R10_single_refY')&(d.video_id==5)].iloc[0]
p=pathlib.Path(r.output_path); adm=pd.read_csv(p/'admission.csv'); cr=np.load(p/'camera_result.npz'); ids=[str(x) for x in cr['ids']]; cams=np.asarray(cr['c2w'],float)
acc=adm[adm.admission_status=='ACCEPT'].view.astype(str).tolist(); acc=[x for x in acc if x in ids]
# fall back to first four only for smoke if fewer than four, but mark actual admissions
selected=acc[:4]
if len(selected)<4:
    selected=ids[:4]; smoke_note='SMOKE_USES_FIRST_FOUR_NOT_ALL_S0'
else:
    smoke_note='SMOKE_USES_S0_ACCEPTED'
meta=json.loads((WS/'runs/m1_final_39/prepared'/f'{r.group_id}_{int(r.video_id):03d}'/'PREPARED.json').read_text()); by={x['view']:x for x in meta['views']}
frames=[]
for cid in selected:
 q=by[cid]; a=np.load(q['cache']); lab=a['labels']
 cp=WS/'runs/m2c_trajectory_admission/clean_labels'/f'{r.group_id}_{int(r.video_id):03d}'/(cid+'.npz')
 if cp.exists(): lab=np.load(cp)['labels']
 frames.append(dict(id=cid,RGB=a['RGB'],labels=lab,K=np.asarray(a['K'],float),c2w_mm=cams[ids.index(cid)]))
save_json(H/'SMOKE_INPUT.json',dict(group=r.group_id,video=int(r.video_id),ids=selected,note=smoke_note,admission=adm[adm.view.astype(str).isin(selected)][['view','admission_status']].to_dict('records'),checkpoint=cfg['checkpoint'],checkpoint_sha256=sha256(cfg['checkpoint']),cuda=torch.cuda.get_device_name(0),total_memory=torch.cuda.get_device_properties(0).total_memory))
t0=time.time()
try:
 model,receipt=load_official(cfg['mvs_root'],cfg['checkpoint'],cfg['dino_root'],lock)
 save_json(H/'MODEL_RECEIPT.json',receipt)
 rec=infer(model,frames,H/'result')
 rec.update(total_seconds=time.time()-t0,peak_GPU_bytes=torch.cuda.max_memory_allocated(),smoke_note=smoke_note,ids=selected)
 save_json(H/'SMOKE_RESULT.json',rec); print('HERO_SMOKE_PASS',json.dumps(rec),flush=True)
except Exception as e:
 import traceback
 save_json(H/'SMOKE_RESULT.json',dict(status='FAIL',error=repr(e),traceback=traceback.format_exc(),total_seconds=time.time()-t0,smoke_note=smoke_note,ids=selected))
 print('HERO_SMOKE_FAIL',repr(e),flush=True); raise
