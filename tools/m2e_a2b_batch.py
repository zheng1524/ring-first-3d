#!/usr/bin/env python3
"""M2E standard A-to-B: historical reprojection.render/evaluate for every HERO target."""
import sys,json,pathlib,hashlib
import numpy as np,pandas as pd,cv2
from PIL import Image
WS=pathlib.Path('/home/liu/ring_first_3d_workspace');sys.path[:0]=[str(WS/'src'),str(WS/'src/ring_first_3d/mainline/frozen_registry'),str(WS/'src/ring_first_3d/mainline/lineage/experiments/TASK-VIEW-OBSERVABILITY-GT-EVAL-001/code')]
import reprojection as rp,open3d as o3d
from ring_first_3d.mainline.native.geometry import native_rgb_labels
_cad={}
def _cad_scene(kind):
 if kind not in _cad:
  p=WS/'runs/m2e_historical_method_integration/cad'/f'{kind}.npz';d=dict(np.load(p));sc=o3d.t.geometry.RaycastingScene(nthreads=2);sc.add_triangles(o3d.core.Tensor(np.asarray(d['V'],np.float32)),o3d.core.Tensor(np.asarray(d['F'],np.uint32)));_cad[kind]=sc
 return _cad[kind]
rp.cad_scene=_cad_scene
O=WS/'runs/m2e_historical_method_integration';H=O/'hero';A=O/'a_to_b';A.mkdir(parents=True,exist_ok=True)
exe=pd.read_csv(H/'HERO_EXECUTION_RESULTS.csv');exe=exe[exe.status!='FAIL'];D=pd.read_csv(WS/'runs/m2c_corrective_completion/W0_79_VIDEO_RESULTS.csv');dmap={(r.group_id,f'{int(r.video_id):03d}'):r for _,r in D.iterrows()};S=pd.read_csv(O/'support/SUPPORT_SELECTION_RESULTS.csv');S['video_id']=S.video_id.astype(int).map(lambda x:f'{x:03d}');S=S.set_index(['group_id','video_id','target_id'])
PREP=WS/'runs/m1_final_39/prepared';roots=[PREP,WS/'runs/m2a_w0_recovery/prepared_c2b',WS/'runs/m2a_w0_recovery/prepared_c2',WS/'runs/m2a_w0_recovery/prepared_b1r',WS/'runs/m2a_w0_recovery/prepared_c3',WS/'runs/m2a_w0_recovery/prepared_c3b',WS/'runs/m2c_trajectory_admission/A_correctness/prepared_c3']
def load(g,v,view):
 by={}
 for root in roots:
  p=root/f'{g}_{v}'/'PREPARED.json'
  if p.exists():
   for x in json.loads(p.read_text())['views']:
    if x['view'] not in by:by[x['view']]=x
 a=dict(np.load(by[view]['cache']));return a
def cams(g,v):
 cr=np.load(pathlib.Path(dmap[(g,v)].output_path)/'camera_result.npz');return {str(i):np.asarray(c,float) for i,c in zip(cr['ids'],cr['c2w'])}
rows=[];pairs=[]
# first pass one support per target, plus all supports for first 8 groups
batch_groups=set(exe.group_id.unique()[:8])
for n,(_,e) in enumerate(exe.iterrows(),1):
 g,v,target=str(e.group_id),f'{int(e.video_id):03d}',str(e.target_id);s=S.loc[(g,v,target)];ids=str(s.support_ids).split(';');use=ids if g in batch_groups else ids[:1];Cmap=cams(g,v)
 out=pathlib.Path(e.output_dir); raw=dict(np.load(out/'RAW_NATIVE_MESH.npz')); V=np.asarray(raw['V']);F=np.asarray(raw['F']);target_a=load(g,v,target);K=np.asarray(target_a['K'],float);rgb=np.asarray(target_a['RGB']);labels=np.asarray(target_a['labels']);rn,rl,_=native_rgb_labels(rgb,labels,K);Cv=rn[raw['uv'][:,1],raw['uv'][:,0]]/255.
 for j,Bid in enumerate(use):
  B=load(g,v,Bid); pred=rp.render(V,F,Cv,K,Cmap[target],np.eye(4),'R5' if 'R5' in g else 'R10'); Bimg=np.asarray(B['RGB']);Blab=np.asarray(B['labels']);met,mae,common=rp.evaluate(pred,Bimg,Blab)
  met.update(group_id=g,video_id=v,target_id=target,support_id=Bid,arm='T13',tuple_id=hashlib.sha256(f'{g}|{v}|{target}|{";".join(ids)}'.encode()).hexdigest()[:12],source_mesh=str(out/'RAW_NATIVE_MESH.npz'),support_index=j,standard_renderer='reprojection.render',bitwise_status='NOT_COMPARABLE_NO_HISTORICAL_OUTPUT_FOR_CURRENT_TUPLE')
  rows.append(met);pairs.append(dict(tuple_id=met['tuple_id'],group_id=g,video_id=v,target_id=target,support_id=Bid,source_mesh=met['source_mesh'],role='SUPPORT_VIEW'))
 print(n,'/',len(exe),g,v,target,'done',len(rows),flush=True)
pd.DataFrame(rows).to_csv(A/'A_TO_B_METRICS.csv',index=False);pd.DataFrame(pairs).to_csv(A/'PAIR_SELECTION.csv',index=False)
print('A2B rows',len(rows),'targets',len(exe),'groups',exe.group_id.nunique())
