#!/usr/bin/env python3
"""M2F three-source depth diagnosis for the 19 designated surfaces."""
import sys,json,pathlib,hashlib
import numpy as np,pandas as pd,open3d as o3d
from scipy.spatial import cKDTree
WS=pathlib.Path('/home/liu/ring_first_3d_workspace');sys.path.insert(0,str(WS/'src'))
from ring_first_3d.mainline.native.geometry import native_rgb_labels,resize_index_intrinsics
O=WS/'runs/m2f_metric_depth_diagnosis';H=O/'hero';D=pd.read_csv(WS/'runs/m2c_corrective_completion/W0_79_VIDEO_RESULTS.csv');dmap={(r.group_id,f'{int(r.video_id):03d}'):r for _,r in D.iterrows()}
GROUPS=['GP_Ip_12.0mm_closed_R10_single_refY','GP_Is_9.79mm_closed_R10_single_refY','GP_Is_14.0mm_closed_R10_single_refY'];exe=pd.read_csv(O/'hero/HERO_EXECUTION_RESULTS.csv');exe=exe[exe.group_id.isin(GROUPS)&(exe.status!='FAIL')]
cad_cache={}
def cad(kind):
 if kind not in cad_cache:
  d=dict(np.load(WS/f'runs/m2e_historical_method_integration/cad/{kind}.npz'));sc=o3d.t.geometry.RaycastingScene(nthreads=2);sc.add_triangles(o3d.core.Tensor(d['V'].astype(np.float32)),o3d.core.Tensor(d['F'].astype(np.uint32)));cad_cache[kind]=(d,sc)
 return cad_cache[kind]
def cast_ring(V,F,C,K):
 d,sc=cad('R5' if 'R5' in g else 'R10');yy,xx=np.mgrid[:352,:640];uv=np.c_[xx.ravel(),yy.ravel(),np.ones(xx.size)];dirs=(uv@np.linalg.inv(K).T)@C[:3,:3].T;orig=np.broadcast_to(C[:3,3],dirs.shape);rays=np.c_[orig,dirs];h=sc.cast_rays(o3d.core.Tensor(rays.astype(np.float32)))['t_hit'].numpy();return h.reshape(352,640)
def load_view(g,v,view):
 roots=[WS/'runs/m1_final_39/prepared',WS/'runs/m2a_w0_recovery/prepared_c2b',WS/'runs/m2a_w0_recovery/prepared_c2',WS/'runs/m2a_w0_recovery/prepared_b1r',WS/'runs/m2a_w0_recovery/prepared_c3',WS/'runs/m2a_w0_recovery/prepared_c3b',WS/'runs/m2c_trajectory_admission/A_correctness/prepared_c3']
 for root in roots:
  p=root/f'{g}_{v}'/'PREPARED.json'
  if p.exists():
   by={x['view']:x for x in json.loads(p.read_text())['views']}
   if view in by:return dict(np.load(by[view]['cache']))
 raise KeyError(view)
rows=[];rgbrows=[];scale=[];spatial=[]
for n,(_,e) in enumerate(exe.iterrows(),1):
 g,v,target=str(e.group_id),f'{int(e.video_id):03d}',str(e.target_id);out=pathlib.Path(e.output_dir);native=dict(np.load(out/'HERO_native.npz'));lab=np.load(out/'NATIVE_RGB_LABELS.npz')['labels'];z=np.asarray(native['depth_mm']);Kn=np.asarray(native['K_index_native']);pose=np.asarray(native['reference_pose_mm']);C=pose
 cadz=cast_ring(None,None,C,Kn);valid=np.isfinite(cadz)&(cadz>0)&np.isfinite(z)&(z>0)&(lab==2);vz=z[valid];cz=cadz[valid];dv=vz-cz
 rows.append(dict(group_id=g,video_id=v,target_id=target,native_ring_pixels=int((lab==2).sum()),valid_ring_pixels=int(valid.sum()),coverage=float(valid.sum()/max(1,(lab==2).sum())),cad_median_mm=float(np.median(cz)) if len(cz) else None,hero_median_mm=float(np.median(vz)) if len(vz) else None,signed_median_mm=float(np.median(dv)) if len(dv) else None,mae_mm=float(np.mean(abs(dv))) if len(dv) else None,p95_abs_mm=float(np.quantile(abs(dv),.95)) if len(dv) else None,ratio_median=float(np.median(vz/cz)) if len(cz) else None,ring_cad_sha=hashlib.sha256(np.load(WS/f'runs/m2e_historical_method_integration/cad/{"R5" if "R5" in g else "R10"}.npz')["V"].tobytes()).hexdigest()[:16]))
 if len(cz)>2:
  a,b=np.polyfit(cz,vz,1);scale.append(dict(group_id=g,video_id=v,target_id=target,a=float(a),b=float(b),n=int(len(cz)),depth_range_mm=float(cz.max()-cz.min()),identifiable=bool(cz.max()-cz.min()>5)))
 # RGB points target
 r=dmap[(g,v)];w=np.load(r.w0_file);X=np.asarray(w['points'],float);Pt=np.asarray(w['point_track_ids'],int);work=pathlib.Path(r.output_path).parent.parent/'work_A1'/g/v/'observations/tracks005.npz'
 if not work.exists(): work=WS/'runs/m2c_trajectory_admission/A_correctness/work_A1'/g/v/'observations/tracks005.npz'
 try:
  tr=np.load(work);xy=tr['xy'];obs=np.isfinite(xy[Pt,list(map(str,[]))]) if False else None
  cr=np.load(pathlib.Path(r.output_path)/'camera_result.npz');ids=[str(x) for x in cr['ids']];ci=ids.index(target);obs=np.isfinite(xy[Pt,ci,0]);Xo=X[obs];Xc=(Xo-C[:3,3])@C[:3,:3];daxial=Xc[:,2];uv=np.c_[Xc[:,0]/Xc[:,2]*Kn[0,0]+Kn[0,2],Xc[:,1]/Xc[:,2]*Kn[1,1]+Kn[1,2]];ok=(daxial>0)&(uv[:,0]>=0)&(uv[:,0]<640)&(uv[:,1]>=0)&(uv[:,1]<352);uv=uv[ok];daxial=daxial[ok];Xo=Xo[ok];uv=np.rint(uv).astype(int);u=np.clip(uv[:,0],0,639);vv=np.clip(uv[:,1],0,351);reg=lab[vv,u];hz=z[vv,u];good=np.isfinite(hz)&(hz>0);rgbrows.append(dict(group_id=g,video_id=v,target_id=target,rgb_points=int(len(daxial)),valid_compare=int((good).sum()),polyp=int((good&(reg==1)).sum()),ring=int((good&(reg==2)).sum()),background=int((good&(reg==0)).sum()),signed_median_polyp_mm=float(np.median(daxial[good&(reg==1)]-hz[good&(reg==1)])) if (good&(reg==1)).any() else None,mae_polyp_mm=float(np.mean(abs(daxial[good&(reg==1)]-hz[good&(reg==1)]))) if (good&(reg==1)).any() else None,signed_median_ring_mm=float(np.median(daxial[good&(reg==2)]-hz[good&(reg==2)])) if (good&(reg==2)).any() else None))
 except Exception as ex: rgbrows.append(dict(group_id=g,video_id=v,target_id=target,rgb_points=0,valid_compare=0,error=repr(ex)))
 # spatial
 V=np.asarray(np.load(out/'RAW_NATIVE_MESH.npz')['V']);d,sc=cad('R5' if 'R5' in g else 'R10');ringV=d['V'];tree=cKDTree(ringV);dist,_=tree.query(V);hgt=V[:,2];rho=np.linalg.norm(V[:,:2],axis=1);spatial.append(dict(group_id=g,video_id=v,target_id=target,n_vertices=len(V),centroid_x=float(V[:,0].mean()),centroid_y=float(V[:,1].mean()),centroid_z=float(V[:,2].mean()),height_median_mm=float(np.median(hgt)),height_p5_mm=float(np.quantile(hgt,.05)),height_p95_mm=float(np.quantile(hgt,.95)),rho_median_mm=float(np.median(rho)),surface_ring_min_mm=float(dist.min()),surface_ring_median_mm=float(np.median(dist)),camera_distance_mm=float(np.linalg.norm(V-C[:3,3],axis=1).mean()),collision_fraction=float((dist<.7).mean())))
 print(n,'/',len(exe),g,v,target,flush=True)
pd.DataFrame(rows).to_csv(O/'depth_diagnosis/CAD_HERO_DEPTH_COMPARISON.csv',index=False);pd.DataFrame(rgbrows).to_csv(O/'depth_diagnosis/RGB_HERO_DEPTH_COMPARISON.csv',index=False);pd.DataFrame(scale).to_csv(O/'depth_diagnosis/DEPTH_SCALE_DIAGNOSTICS.csv',index=False);pd.DataFrame(spatial).to_csv(O/'depth_diagnosis/SURFACE_RING_SPATIAL_METRICS.csv',index=False)
print('done',len(rows),len(rgbrows),len(scale),len(spatial))
