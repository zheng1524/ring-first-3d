#!/usr/bin/env python3
import json,pathlib,sys
import numpy as np,pandas as pd
WS=pathlib.Path('/home/liu/ring_first_3d_workspace'); O=WS/'runs/m2d_w0_mvs_validation'; A=WS/'runs/m2c_corrective_completion'
D=pd.read_csv(A/'W0_79_VIDEO_RESULTS.csv'); dmap={(r.group_id,f'{int(r.video_id):03d}'):r for _,r in D.iterrows()}
PREP=WS/'runs/m1_final_39/prepared'; CLEAN=WS/'runs/m2c_trajectory_admission/clean_labels'; roots=[PREP,WS/'runs/m2a_w0_recovery/prepared_c2b',WS/'runs/m2a_w0_recovery/prepared_c2',WS/'runs/m2a_w0_recovery/prepared_b1r',WS/'runs/m2a_w0_recovery/prepared_c3',WS/'runs/m2a_w0_recovery/prepared_c3b',WS/'runs/m2c_trajectory_admission/A_correctness/prepared_c3']
def views(g,v):
 by={}
 for root in roots:
  p=root/f'{g}_{v}'/'PREPARED.json'
  if p.exists():
   for x in json.loads(p.read_text())['views']: by[x['view']]=x
 r=dmap[(g,v)]; p=pathlib.Path(r.output_path); cr=np.load(p/'camera_result.npz'); ids=[str(x) for x in cr['ids']]; cams={str(i):np.asarray(c,float) for i,c in zip(cr['ids'],cr['c2w'])}
 return by,cams
def load(g,v,view):
 by,cams=views(g,v); q=by[view]; a=np.load(q['cache']); lab=a['labels']; cp=CLEAN/f'{g}_{v}'/(view+'.npz')
 if cp.exists(): lab=np.load(cp)['labels']
 return a['RGB'],lab,np.asarray(a['K'],float),cams[view]
def metric(V,cA,cB,KB,imgB,labelsB):
 z=(V-cB[:3,3])@cB[:3,:3]; good=z[:,2]>0; uv=np.full((len(V),2),np.nan); uv[good]=(z[good,:2]/z[good,2:3])@KB[:2,:2].T+KB[:2,2]; h,w=labelsB.shape; inside=good&(uv[:,0]>=0)&(uv[:,0]<w)&(uv[:,1]>=0)&(uv[:,1]<h); pix=np.rint(uv[inside]).astype(int); pix[:,0]=np.clip(pix[:,0],0,w-1); pix[:,1]=np.clip(pix[:,1],0,h-1)
 return dict(projected_vertices=int(inside.sum()),coverage_fraction=float(inside.mean()),inside_polyp_fraction=float((labelsB[pix[:,1],pix[:,0]]==1).mean()) if len(pix) else None,unique_target_pixels=len(set(map(tuple,pix))) if len(pix) else 0,positive_depth_fraction=float(good.mean()))
# HERO mesh by target view (first PASS)
exe=pd.read_csv(O/'hero/HERO_EXECUTION_RESULTS.csv'); meshes={}
for _,r in exe[exe.status=='PASS'].iterrows():
 p=pathlib.Path(r.output_dir)/'RAW_NATIVE_MESH.npz'
 if p.exists() and r.target_view not in meshes: meshes[r.target_view]=str(p)
a2b=pd.read_csv(O/'a_to_b/A_TO_B_METRICS.csv'); rev=[]; ind=[]
for _,r in a2b.iterrows():
 g,v=str(r.group_id),f'{int(r.video_id):03d}'; A_id,B_id=r.source_A,r.target_B
 # A->B already; B->A if B mesh exists
 if B_id in meshes:
  V=np.asarray(np.load(meshes[B_id])['V']); imgB,labB,KB,cB=load(g,v,B_id); imgA,labA,KA,cA=load(g,v,A_id)
  m=metric(V,cB,cA,KA,imgA,labA); rev.append(dict(tuple_id=r.tuple_id,group_id=g,video_id=v,source_B=B_id,target_A=A_id,arm=r.arm,**m))
 # independent: any view not in target/support
 sup=set(str(r.target_B).split(';'))
 if A_id in meshes:
  V=np.asarray(np.load(meshes[A_id])['V']); by,cams=views(g,v); cand=[x for x in cams if x!=A_id and x not in sup]
  if cand:
   B=cand[-1]; imgB,labB,KB,cB=load(g,v,B); imgA,labA,KA,cA=load(g,v,A_id); m=metric(V,cA,cB,KB,imgB,labB); ind.append(dict(tuple_id=r.tuple_id,group_id=g,video_id=v,eval_view=B,source_A=A_id,arm=r.arm,**m))
pd.DataFrame(rev).to_csv(O/'a_to_b/B_TO_A_METRICS.csv',index=False)
pd.DataFrame(ind).to_csv(O/'a_to_b/INDEPENDENT_VIEW_METRICS.csv',index=False)
pd.DataFrame(a2b[['tuple_id','group_id','video_id','source_A','target_B','arm']]).to_csv(O/'a_to_b/PAIR_SELECTION.csv',index=False)
print('B2A',len(rev),'independent',len(ind));print(pd.DataFrame(rev).coverage_fraction.describe().to_dict() if rev else {})
