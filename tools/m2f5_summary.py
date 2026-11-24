import sys,json,pathlib,hashlib,itertools
import numpy as np,pandas as pd,open3d as o3d
from scipy.spatial import cKDTree
WS=pathlib.Path('/home/liu/ring_first_3d_workspace');O=WS/'runs/m2f5_unified'
h=pd.read_csv(O/'hero/HERO_EXECUTION_RESULTS.csv');a=pd.read_csv(O/'evaluation/A_TO_B_METRICS.csv');sel=pd.concat([pd.read_csv(p) for p in (O/'selection').glob('*.csv')])
# CAD-HERO
cad={}
for kind,path in [('R5',O/'cad/R5.npz'),('R10',O/'cad/R10.npz')]:
 d=dict(np.load(path));s=o3d.t.geometry.RaycastingScene(nthreads=2);s.add_triangles(o3d.core.Tensor(d['V'].astype(np.float32)),o3d.core.Tensor(d['F'].astype(np.uint32)));cad[kind]=(d,s)
rows=[];multi=[]
for _,r in h.iterrows():
 if r.status!='PASS':continue
 g,v,t=r.group_id,str(r.video_id).zfill(3),r.target_id;out=pathlib.Path(r.output_dir);z=np.load(out/'HERO_native.npz');H=z['depth_mm'];K=z['K_index_native'];C=z['reference_pose_mm'];lab=np.load(out/'NATIVE_RGB_LABELS.npz')['labels'];kind='R5' if '_R5_' in g else 'R10';d,sc=cad[kind];yy,xx=np.mgrid[:352,:640];uv=np.c_[xx.ravel(),yy.ravel(),np.ones(xx.size)];dirs=(uv@np.linalg.inv(K).T)@C[:3,:3].T;rays=np.c_[np.broadcast_to(C[:3,3],dirs.shape),dirs];cd=sc.cast_rays(o3d.core.Tensor(rays.astype(np.float32)))['t_hit'].numpy().reshape(352,640);valid=np.isfinite(cd)&(cd>0)&(H>0)&(lab==2);dv=H[valid]-cd[valid];rows.append(dict(group_id=g,video_id=v,target_id=t,valid_ring=int(valid.sum()),signed_median_mm=float(np.median(dv)) if len(dv) else None,mae_mm=float(np.mean(abs(dv))) if len(dv) else None,p95_abs_mm=float(np.quantile(abs(dv),.95)) if len(dv) else None,ratio_median=float(np.median(H[valid]/cd[valid])) if len(dv) else None))
pd.DataFrame(rows).to_csv(O/'evaluation/CAD_HERO_GEOMETRY.csv',index=False)
# multisurface by video
for (g,v),sub in h[h.status=='PASS'].groupby(['group_id','video_id']):
 V=[]
 for _,x in sub.iterrows():
  try:V.append(np.load(pathlib.Path(x.output_dir)/'RAW_NATIVE_MESH.npz')['V'])
  except:pass
 if len(V)<2:continue
 for i,j in itertools.combinations(range(len(V)),2):
  A=V[i][::max(1,len(V[i])//2000)][:2000];B=V[j][::max(1,len(V[j])//2000)][:2000];ta=cKDTree(A);tb=cKDTree(B);da,_=tb.query(A);db,_=ta.query(B);multi.append(dict(group_id=g,video_id=v,tuple_A=sub.iloc[i].tuple_sha,tuple_B=sub.iloc[j].tuple_sha,centroid_distance_mm=float(np.linalg.norm(A.mean(0)-B.mean(0))),symmetric_nn_median_mm=float(np.median(np.r_[da,db])),symmetric_nn_p95_mm=float(np.quantile(np.r_[da,db],.95)),interpretation='SAME_VIDEO_WORLD_DIAGNOSTIC_NOT_GT'))
pd.DataFrame(multi).to_csv(O/'evaluation/MULTISURFACE_CONSISTENCY.csv',index=False)
# group summary
gg=[]
for g,sub in a.groupby('group_id'):
 hh=h[(h.group_id==g)&(h.status=='PASS')];cc=[x for x in rows if x['group_id']==g];mm=[x for x in multi if x['group_id']==g]
 gg.append(dict(group_id=g,hero=len(hh),a2b=len(sub),coverage_median=float(sub.target_coverage.median()),rgb_mae_median=float(sub.RGB_MAE_0_255.median()),cad_hero_signed_median=float(pd.Series([x['signed_median_mm'] for x in cc]).median()) if cc else None,cad_hero_mae_median=float(pd.Series([x['mae_mm'] for x in cc]).median()) if cc else None,multisurface_pairs=len(mm),multisurface_nn_median=float(pd.Series([x['symmetric_nn_median_mm'] for x in mm]).median()) if mm else None))
pd.DataFrame(gg).to_csv(O/'evaluation/GROUP_LEVEL_COMPARISON.csv',index=False)
# pipeline summary
ps=[]
for p in sorted((O/'prepared').glob('*/PREPARED.json')):
 g,v=p.parent.name.rsplit('_',1);cp=O/'clean_labels'/p.parent.name;w=O/'w0'/p.parent.name;ss=O/'selection'/f'{g}_{v}.csv';hh=h[(h.group_id==g)&(h.video_id.astype(str).str.zfill(3)==v)&(h.status=='PASS')]
 ps.append(dict(group_id=g,video_id=v,stage_prepare='PASS',frames=len(json.loads(p.read_text())['views']),mask_clean='PASS',stage_w0='PASS' if (w/'camera_result.npz').exists() else 'FAIL',stage_select='PASS' if ss.exists() else 'FAIL',hero=int(len(hh)),a2b=int(((a.group_id==g)&(a.video_id.astype(str).str.zfill(3)==v)).sum())))
pd.DataFrame(ps).to_csv(O/'PIPELINE_EXECUTION_SUMMARY.csv',index=False)
print('cad',len(rows),'multi',len(multi),'groups',len(gg),'pipeline',len(ps))
