#!/usr/bin/env python3
"""Read-only V6 HERO geometry audit: R10 CAD depth, surface distances, six-view."""
import sys,json,pathlib
import numpy as np,pandas as pd,trimesh,open3d as o3d
from scipy.spatial import cKDTree
from matplotlib import pyplot as plt
WS=pathlib.Path('/home/liu/ring_first_3d_workspace');O=WS/'runs/m2f7_hist_g01';H=O/'hist_v6';V=H
sys.path[:0]=[str(WS/'src')]
from ring_first_3d.mainline.native._mesh_renderer import actual_mesh_image
CAD=dict(np.load(WS/'runs/m2f5_unified/cad/R10.npz'));scene=o3d.t.geometry.RaycastingScene(nthreads=2);scene.add_triangles(o3d.core.Tensor(CAD['V'].astype(np.float32)),o3d.core.Tensor(CAD['F'].astype(np.uint32)))
# historical reference areas
hist={x['tag']:x.get('parts',{}).get('Polyp',{}).get('topology',{}).get('area_mm2') for x in json.loads((pathlib.Path('/home/liu/polyp_research/ring_anchor_3d/experiments/ring_first_v6_local_reconstruction/metrics/surfaces005.json')).read_text())}
rows=[];meshes={}
for p in sorted((V/'predictions').glob('*_surface.npz')):
 tag=p.name.replace('_surface.npz','');z=np.load(p);depth=z['depth_mm'];labels=z['labels'];pose=z['pose'];K=z['K'];yy,xx=np.mgrid[:depth.shape[0],:depth.shape[1]];uv=np.c_[xx.ravel(),yy.ravel(),np.ones(xx.size)];rays=(uv@np.linalg.inv(K).T)@pose[:3,:3].T+pose[:3,3];rays=np.c_[np.broadcast_to(pose[:3,3],rays.shape),rays-pose[:3,3]];hit=scene.cast_rays(o3d.core.Tensor(rays.astype(np.float32)))['t_hit'].numpy().reshape(depth.shape);valid=np.isfinite(hit)&(hit>0)&(depth>0)&(labels==2);d=depth[valid];c=hit[valid];ratio=d/c;res=d-c;rows.append(dict(tag=tag,condition='historical_unfiltered' if tag in ('005_ref00459','005_ref00000') else 'historical_supported',ring_pixels=int(valid.sum()),hero_ring_depth_median_mm=float(np.median(d)) if len(d) else None,cad_ring_depth_median_mm=float(np.median(c)) if len(c) else None,depth_ratio_median=float(np.median(ratio)) if len(ratio) else None,depth_ratio_mae=float(np.mean(abs(ratio-1))) if len(ratio) else None,residual_mae_mm=float(np.mean(abs(res))) if len(res) else None,residual_p95_mm=float(np.quantile(abs(res),.95)) if len(res) else None,historical_area_mm2=hist.get(tag),current_area_mm2=json.loads((V/'metrics/surfaces005.json').read_text())[next(i for i,x in enumerate(json.loads((V/'metrics/surfaces005.json').read_text())) if x['tag']==tag)]['parts']['Polyp']['topology']['area_mm2']))
 m=trimesh.load(V/'meshes'/f'{tag}_Polyp.ply',process=False);meshes[tag]=m
# surface distances
import itertools
sd=[]
for a,b in itertools.combinations(meshes,2):
 A=meshes[a].vertices;B=meshes[b].vertices;A=A[::max(1,len(A)//2000)][:2000];B=B[::max(1,len(B)//2000)][:2000];ta=cKDTree(A);tb=cKDTree(B);da,_=tb.query(A);db,_=ta.query(B);sd.append(dict(tag_A=a,tag_B=b,centroid_distance_mm=float(np.linalg.norm(A.mean(0)-B.mean(0))),symmetric_nn_median_mm=float(np.median(np.r_[da,db])),symmetric_nn_p95_mm=float(np.quantile(np.r_[da,db],.95)),note='V6 raw meshes, same target video; no ICP/scale'))
pd.DataFrame(rows).to_csv(O/'V6_HERO_GEOMETRY.csv',index=False);pd.DataFrame(sd).to_csv(O/'V6_SURFACE_DISTANCES.csv',index=False)
# six views: target + support refs from V6 cases, fallback raw frame camera
L=json.loads((V/'inputs/ledger005.json').read_text());cam=np.load(V/'predictions/local005_camera_0.npz')['c2w'];rawidx={a['id']:i for i,a in enumerate(L)}
cases=json.loads((V/'inputs/MVS_supported_cases.json').read_text())+json.loads((V/'inputs/MVS_cases.json').read_text())
case_by_tag={x['tag']:x for x in cases};Vall=np.concatenate([meshes[t].vertices for t in meshes],0)
for tag,m in meshes.items():
 c=case_by_tag.get(tag);center=m.vertices.mean(0);views=[]
 ids=[c['reference_id'],*[x['id'] for x in []]] if c else []
 if c:
  ids=[c['reference_id']]+[L[i]['id'] for i in c['sources'][:2]]
 else:ids=[L[rawidx.get('v005_00459',0)]['id']]
 for k,vid in enumerate(ids):
  C=cam[rawidx[vid]];d=C[:3,3]-center;d/=np.linalg.norm(d);views.append((f'camera{k+1}',float(np.degrees(np.arcsin(d[2]))),float(np.degrees(np.arctan2(d[1],d[0])))))
 views += [('WorldX',0,0),('WorldY',0,90),('WorldZ',89.9999,0)]
 fig,ax=plt.subplots(1,6,figsize=(15,3))
 for k,(name,e,a) in enumerate(views):
  im,_=actual_mesh_image(m.vertices,m.faces,CAD['V'],CAD['F'],Vall,e,a,'#d98989');ax[k].imshow(im);ax[k].set_title(name,fontsize=8);ax[k].axis('off')
 fig.suptitle(f'HIST-V6 {tag} | raw metric mesh | R10 CAD');fig.tight_layout();p=O/'visualization/v6_six_views'/f'{tag}.png';fig.savefig(p,dpi=90);plt.close(fig)
print('v6 geometry',len(rows),'distances',len(sd),'six',len(meshes))
