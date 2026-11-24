#!/usr/bin/env python3
"""M2F1: corrected B-camera standard A-to-B for NEW gated HERO only."""
import sys,json,pathlib,hashlib
import numpy as np,pandas as pd
WS=pathlib.Path('/home/liu/ring_first_3d_workspace');sys.path[:0]=[str(WS/'src'),str(WS/'src/ring_first_3d/mainline/frozen_registry'),str(WS/'src/ring_first_3d/mainline/lineage/experiments/TASK-VIEW-OBSERVABILITY-GT-EVAL-001/code')]
import reprojection as rp,open3d as o3d
from ring_first_3d.mainline.native.geometry import native_rgb_labels
O=WS/'runs/m2f1_w0_admission_restoration';H=O/'hero';E=O/'evaluation';E.mkdir(parents=True,exist_ok=True)
exe=pd.read_csv(H/'HERO_EXECUTION_RESULTS.csv');exe=exe[exe.status=='PASS'];S=pd.read_csv(O/'selection/FINAL_HERO_TUPLES.csv');S=S[S.ready==True].copy();S['video_id']=S.video_id.astype(int).map(lambda x:f'{x:03d}');S=S.set_index(['group_id','video_id','arm','target_id'])
D=pd.read_csv(WS/'runs/m2c_corrective_completion/W0_79_VIDEO_RESULTS.csv');dmap={(r.group_id,f'{int(r.video_id):03d}'):r for _,r in D.iterrows()}
PREP=WS/'runs/m1_final_39/prepared';roots=[PREP,WS/'runs/m2a_w0_recovery/prepared_c2b',WS/'runs/m2a_w0_recovery/prepared_c2',WS/'runs/m2a_w0_recovery/prepared_b1r',WS/'runs/m2a_w0_recovery/prepared_c3',WS/'runs/m2a_w0_recovery/prepared_c3b',WS/'runs/m2c_trajectory_admission/A_correctness/prepared_c3']
def load(g,v,view):
 for root in roots:
  p=root/f'{g}_{v}'/'PREPARED.json'
  if p.exists():
   by={x['view']:x for x in json.loads(p.read_text())['views']}
   if view in by:return dict(np.load(by[view]['cache']))
 raise KeyError(view)
def cams(g,v):
 cr=np.load(pathlib.Path(dmap[(g,v)].output_path)/'camera_result.npz');return {str(i):np.asarray(c,float) for i,c in zip(cr['ids'],cr['c2w'])}
_cad={}
def cad_scene(kind):
 if kind not in _cad:
  d=dict(np.load(WS/f'runs/m2f1_w0_admission_restoration/cad/{kind}.npz'));sc=o3d.t.geometry.RaycastingScene(nthreads=2);sc.add_triangles(o3d.core.Tensor(d['V'].astype(np.float32)),o3d.core.Tensor(d['F'].astype(np.uint32)));_cad[kind]=sc
 return _cad[kind]
rp.cad_scene=cad_scene
rows=[]
for n,(_,e) in enumerate(exe.iterrows(),1):
 g,v,target,arm=str(e.group_id),f'{int(e.video_id):03d}',str(e.target_id),str(e.arm);s=S.loc[(g,v,arm,target)];sups=str(s.support_ids).split(';');Cmap=cams(g,v);out=pathlib.Path(e.output_dir);raw=np.load(out/'RAW_NATIVE_MESH.npz');V=raw['V'];F=raw['F'];ta=load(g,v,target);K=np.asarray(ta['K'],float);rn,rl,_=native_rgb_labels(ta['RGB'],ta['labels'],K);Cv=rn[raw['uv'][:,1],raw['uv'][:,0]]/255.
 for Bid in sups:
  B=load(g,v,Bid);BK=np.asarray(B['K'],float);Bpose=Cmap[Bid];pred=rp.render(V,F,Cv,BK,Bpose,np.eye(4),'R5' if 'R5' in g else 'R10');Bimg=np.asarray(B['RGB']);lab=np.asarray(B['labels']);met,mae,common=rp.evaluate(pred,Bimg,lab)
  met.update(group_id=g,video_id=v,arm=arm,target_id=target,target_B_id=Bid,target_camera_used_for_projection=False,target_B_camera_used=True,source_mesh=str(out/'RAW_NATIVE_MESH.npz'),source_mesh_sha256=hashlib.sha256((out/'RAW_NATIVE_MESH.npz').read_bytes()).hexdigest(),target_intrinsics_sha256=hashlib.sha256(BK.tobytes()).hexdigest(),target_pose_sha256=hashlib.sha256(Bpose.tobytes()).hexdigest(),status='GATED_NEW_HERO')
  rows.append(met)
 print(n,'/',len(exe),g,v,arm,'pairs',len(rows),flush=True)
pd.DataFrame(rows).to_csv(E/'A_TO_B_METRICS.csv',index=False);print('rows',len(rows))
