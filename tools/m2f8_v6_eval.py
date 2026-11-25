#!/usr/bin/env python3
"""Summarize V6-GENERALIZED runs without changing any prediction."""
import sys,json,pathlib,itertools
import numpy as np,pandas as pd
from scipy.spatial import cKDTree
WS=pathlib.Path('/home/liu/ring_first_3d_workspace');BASE=WS/'runs/m2f8_v6_general';V=BASE/'v6'
CAD={}
for kind in ['R5','R10']:
 d=dict(np.load(WS/f'runs/m2f5_unified/cad/{kind}.npz'));CAD[kind]=d
from ring_first_3d.mainline.native._mesh_renderer import actual_mesh_image
from matplotlib import pyplot as plt
import trimesh,open3d as o3d
scene={}
for kind,d in CAD.items():
 s=o3d.t.geometry.RaycastingScene(nthreads=2);s.add_triangles(o3d.core.Tensor(d['V'].astype(np.float32)),o3d.core.Tensor(d['F'].astype(np.uint32)));scene[kind]=s
rows=[];vis=[]
for root in sorted(V.glob('*_*')):
 g=root.name.rsplit('_',1)[0];v=root.name.rsplit('_',1)[1];kind='R5' if '_R5_' in g else 'R10';val=root/'metrics/local_validation.json'
 if not val.exists():rows.append(dict(group_id=g,video_id=v,ring=kind,status='NO_BA'));continue
 d=json.loads(val.read_text());v0=next((x for x in d.get('versions',[]) if x['version']==0),{});v1=next((x for x in d.get('versions',[]) if x['version']==1),{})
 hero=len(list((root/'raw').glob('*.npz'))) if (root/'raw').exists() else 0
 # surface geometry
 srows=[]
 for p in sorted((root/'predictions').glob('*_surface.npz')):
  z=np.load(p);depth=z['depth_mm'];labels=z['labels'];pose=z['pose'];K=z['K'];yy,xx=np.mgrid[:depth.shape[0],:depth.shape[1]];uv=np.c_[xx.ravel(),yy.ravel(),np.ones(xx.size)];dirs=(uv@np.linalg.inv(K).T)@pose[:3,:3].T;rays=np.c_[np.broadcast_to(pose[:3,3],dirs.shape),dirs];hit=scene[kind].cast_rays(o3d.core.Tensor(rays.astype(np.float32)))['t_hit'].numpy().reshape(depth.shape);valid=np.isfinite(hit)&(hit>0)&(depth>0)&(labels==2);r=(depth[valid]/hit[valid]) if valid.any() else np.array([]);srows.append(dict(tag=p.stem.replace('_surface',''),pixels=int(valid.sum()),ratio=float(np.median(r)) if len(r) else None,ratio_mae=float(np.mean(abs(r-1))) if len(r) else None,res_mae=float(np.mean(abs(depth[valid]-hit[valid]))) if valid.any() else None,area=None))
  # surface pair distances from PLY
 m={'tag':x['tag'] for x in srows}
 pdists=[]
 meshes={}
 for p in sorted((root/'meshes').glob('*_Polyp.ply')):
  try:meshes[p.stem.replace('_Polyp','')]=trimesh.load(p,process=False).vertices
  except:pass
 for a,b in itertools.combinations(meshes,2):
  A=meshes[a][::max(1,len(meshes[a])//1500)][:1500];B=meshes[b][::max(1,len(meshes[b])//1500)][:1500];ta=cKDTree(A);tb=cKDTree(B);da,_=tb.query(A);db,_=ta.query(B);pdists.append(float(np.median(np.r_[da,db])))
 rows.append(dict(group_id=g,video_id=v,ring=kind,status='RUN',validated_v0=v0.get('VALIDATED'),model_v0=v0.get('MODEL_PREDICTED'),validated_v1=v1.get('VALIDATED'),hero_unsupported=hero,surface_targets=len(srows),hero_cad_ratio_median=float(np.nanmedian([x['ratio'] for x in srows if x['ratio'] is not None])) if srows else None,hero_cad_ratio_mae=float(np.nanmedian([x['ratio_mae'] for x in srows if x['ratio_mae'] is not None])) if srows else None,hero_cad_residual_mae_mm=float(np.nanmedian([x['res_mae'] for x in srows if x['res_mae'] is not None])) if srows else None,surface_nn_median_mm=float(np.median(pdists)) if pdists else None,reference_alias=json.loads((root/'inputs/REFERENCE_RECEIPT.json').read_text()).get('alias_459') if (root/'inputs/REFERENCE_RECEIPT.json').exists() else None))
 for s in srows:vis.append(dict(group_id=g,video_id=v,ring=kind,**s))
# M2F6 existing read-only comparison
m2=WS/'runs/m2f6_unified/formal_002/evaluation/GROUP_LEVEL_COMPARISON.csv';mg=pd.read_csv(m2) if m2.exists() else pd.DataFrame()
df=pd.DataFrame(rows);df.to_csv(BASE/'V6_10_VIDEO_COMPARISON.csv',index=False);pd.DataFrame(vis).to_csv(BASE/'V6_HERO_GEOMETRY.csv',index=False)
print('runs',len(df),'geometry',len(vis));print(df.to_string(index=False))
