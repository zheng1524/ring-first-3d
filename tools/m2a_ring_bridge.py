#!/usr/bin/env python3
"""M2A B1R: replace missing Ring frames with real raw-video frames (q_train>=20)."""
import json,sys
from pathlib import Path
import cv2,numpy as np,pandas as pd
WS=Path('/home/liu/ring_first_3d_workspace'); OUT=WS/'runs/m2a_w0_recovery'; PREP=WS/'runs/m1_final_39/prepared'
sys.path.insert(0,str(WS/'src')); sys.path.insert(0,str(WS/'experiments/TASK-E4-UNIFIED-RING-CONTOUR-REFINEMENT-005/code'))
sys.path.insert(0,str(WS/'experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R6/replay'))
sys.path.insert(0,str(WS/'tools'))
from prepare import prepare_view
from ring_first_3d.mainline.native.camera import observe
import features019 as F19
from m2a_recover import run_one
F19.R=OUT/'features019_ringbridge'; F19.R.mkdir(parents=True,exist_ok=True)
TARGETS=[('GP_IIa_22.0mm_closed_R5_single_refY','005'),('GP_Is_18.0mm_closed_R5_single_refY','005')]

def vd(q):
 a=np.load(q['cache']); return dict(id=q['view'],cache=str(q['cache']),raw_frame=int(q['raw_frame']),K=np.asarray(a['K']).tolist(),T=np.eye(4).tolist(),RGB_SHA256=q.get('rgb_sha256') or '')

def main():
 rows=[]
 for g,v in TARGETS:
  meta=json.loads((PREP/f'{g}_{v}'/'PREPARED.json').read_text()); orig=meta['views']
  diag=pd.read_csv(OUT/'RING_FRAME_DIAGNOSTICS.csv'); keep=set(diag[(diag.group_id==g)&(diag.video_id==int(v))&(diag.q_train_count>=20)].frame_id)
  base=[q for q in orig if q['view'] in keep]
  views={q['view']:vd(q) for q in base}; F19.VIEWS=views
  raw=Path(meta['video_path']); cap=cv2.VideoCapture(str(raw)); n=int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); cap.release()
  origs={int(q['raw_frame']) for q in orig}; cands=[f for f in np.linspace(20,n-20,16,dtype=int) if all(abs(int(f)-o)>6 for o in origs)]
  found=[]
  for f in cands:
   cache=OUT/'bridge'/f'{g}_{v}'/'ringframes'/f'M2A_RINGBRIDGE_{g}_{v}_raw{int(f):05d}.npz'; cache.parent.mkdir(parents=True,exist_ok=True)
   r=prepare_view(raw,int(f),cache); a=np.load(cache)
   if len(observe(a['labels'])['q_train'])<20: continue
   vv=dict(id=f'M2A_RINGBRIDGE_{g}_{v}_raw{int(f):05d}',cache=str(cache),raw_frame=int(f),K=np.asarray(a['K']).tolist(),T=np.eye(4).tolist(),RGB_SHA256=r['rgb_sha256'])
   views[vv['id']]=vv; F19.VIEWS[vv['id']]=vv
   hits=[]
   for b in base:
    try: m=F19.matches(vv,views[b['view']]); hits.append(int(np.asarray(m['RGB_RANSAC']).sum()))
    except Exception: hits.append(0)
   if hits and max(hits)>=12: found.append((f,vv,hits))
  if not found: print('NO_RING_BRIDGE',g,v); continue
  found.sort(key=lambda x:(sum(h>=12 for h in x[2]),max(x[2])),reverse=True)
  sel=found[:4]
  dst=OUT/'prepared_b1r'/f'{g}_{v}'; dst.mkdir(parents=True,exist_ok=True)
  m2=dict(meta); m2['views']=base+[dict(view=x[1]['id'],raw_frame=int(x[0]),cache=x[1]['cache']) for x in sel]
  m2['bridge_frames']=[x[1]['id'] for x in sel]; m2['original_frame_ids']=[q['view'] for q in orig]
  m2['selection_reason']='M2A_B1R_REAL_RING_VISIBLE_BRIDGE'
  (dst/'PREPARED.json').write_text(json.dumps(m2,indent=1))
  r=run_one(g,v,OUT/'prepared_b1r','B1R',OUT/'recovery/B1R',OUT/'work/B1R',list(range(1,len(m2['views']))))
  r['bridge_frames']=';'.join(m2['bridge_frames']); rows.append(r); print('B1R',g,v,r['execution_status'],r['n_w0_poses'],len(m2['views']),flush=True)
 pd.DataFrame(rows).to_csv(OUT/'RECOVERY_B1R.csv',index=False)
 print(pd.DataFrame(rows)[['group_id','video_id','execution_status','n_w0_poses','n_accept']].to_string(index=False) if rows else 'NONE')
if __name__=='__main__': main()
