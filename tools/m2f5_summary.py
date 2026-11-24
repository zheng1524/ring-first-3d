import sys,json,pathlib,hashlib,itertools,argparse,subprocess
import numpy as np,pandas as pd,open3d as o3d
from scipy.spatial import cKDTree
WS=pathlib.Path('/home/liu/ring_first_3d_workspace');ap=argparse.ArgumentParser();ap.add_argument('--output-root',default='runs/m2f5_unified');args=ap.parse_args();O=pathlib.Path(args.output_root).resolve()
h=pd.read_csv(O/'hero/HERO_EXECUTION_RESULTS.csv',dtype={'video_id':str,'target_id':str});a=pd.read_csv(O/'evaluation/A_TO_B_METRICS.csv',dtype={'video_id':str,'target_id':str})
# CAD-HERO
cad={}
for kind,path in [('R5',O/'cad/R5.npz'),('R10',O/'cad/R10.npz')]:
 d=dict(np.load(path));s=o3d.t.geometry.RaycastingScene(nthreads=2);s.add_triangles(o3d.core.Tensor(d['V'].astype(np.float32)),o3d.core.Tensor(d['F'].astype(np.uint32)));cad[kind]=(d,s)
rows=[];multi=[]
for _,r in h.iterrows():
 if r.status!='PASS':
  rows.append(dict(group_id=r.group_id,video_id=str(r.video_id).zfill(3),target_id=r.target_id,status='NOT_EVALUABLE',reason=r.get('reason','HERO_NOT_PASS')));continue
 try:
  g,v,t=r.group_id,str(r.video_id).zfill(3),r.target_id;out=pathlib.Path(r.output_dir);z=np.load(out/'HERO_native.npz');H=z['depth_mm'];K=z['K_index_native'];C=z['reference_pose_mm'];lab=np.load(out/'NATIVE_RGB_LABELS.npz')['labels'];kind='R5' if '_R5_' in g else 'R10';d,sc=cad[kind];yy,xx=np.mgrid[:H.shape[0],:H.shape[1]];uv=np.c_[xx.ravel(),yy.ravel(),np.ones(xx.size)];dirs=(uv@np.linalg.inv(K).T)@C[:3,:3].T;rays=np.c_[np.broadcast_to(C[:3,3],dirs.shape),dirs];cd=sc.cast_rays(o3d.core.Tensor(rays.astype(np.float32)))['t_hit'].numpy().reshape(H.shape);valid=np.isfinite(cd)&(cd>0)&(H>0)&(lab==2);dv=H[valid]-cd[valid];mesh=np.load(out/'RAW_NATIVE_MESH.npz')['V'];centre=np.median(mesh,axis=0) if len(mesh) else np.full(3,np.nan);ring_distance=cKDTree(d['V']).query(mesh[::max(1,len(mesh)//4000)][:4000])[0] if len(mesh) else [];rows.append(dict(group_id=g,video_id=v,target_id=t,status='PASS',valid_ring=int(valid.sum()),signed_median_mm=float(np.median(dv)) if len(dv) else np.nan,mae_mm=float(np.mean(abs(dv))) if len(dv) else np.nan,p95_abs_mm=float(np.quantile(abs(dv),.95)) if len(dv) else np.nan,ratio_median=float(np.median(H[valid]/cd[valid])) if len(dv) else np.nan,cad_hit_median_mm=float(np.median(cd[valid])) if len(dv) else np.nan,hero_native_ring_median_mm=float(np.median(H[valid])) if len(dv) else np.nan,camera_to_ring_center_mm=float(np.linalg.norm(C[:3,3])),depth_source='HERO_native.npz:depth_mm',surface_centroid_x_mm=float(centre[0]),surface_centroid_y_mm=float(centre[1]),surface_centroid_z_mm=float(centre[2]),surface_to_ring_vertex_median_mm=float(np.median(ring_distance)) if len(ring_distance) else np.nan,cad_kind=kind,cad_sha256=hashlib.sha256((O/'cad'/f'{kind}.npz').read_bytes()).hexdigest(),tuple_sha=r.tuple_sha))
 except Exception as exc:
  rows.append(dict(group_id=r.group_id,video_id=str(r.video_id).zfill(3),target_id=r.target_id,status='NOT_EVALUABLE',reason=repr(exc)))
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
for g in sorted(h.group_id.unique()):
 sub=a[(a.group_id==g)&(a.status.isin(['PASS','GATED_NEW_HERO']))] if 'group_id' in a and 'status' in a else pd.DataFrame();hh=h[(h.group_id==g)&(h.status=='PASS')];cc=[x for x in rows if x['group_id']==g and x['status']=='PASS'];mm=[x for x in multi if x['group_id']==g]
 gg.append(dict(group_id=g,hero=len(hh),a2b=len(sub),coverage_median=float(sub.target_coverage.median()) if len(sub) else np.nan,rgb_mae_median=float(sub.RGB_MAE_0_255.median()) if len(sub) else np.nan,cad_hero_signed_median=float(pd.Series([x['signed_median_mm'] for x in cc]).median()) if cc else np.nan,cad_hero_mae_median=float(pd.Series([x['mae_mm'] for x in cc]).median()) if cc else np.nan,multisurface_pairs=len(mm),multisurface_nn_median=float(pd.Series([x['symmetric_nn_median_mm'] for x in mm]).median()) if mm else np.nan))
pd.DataFrame(gg).to_csv(O/'evaluation/GROUP_LEVEL_COMPARISON.csv',index=False)
# pipeline summary
ps=[]
for p in sorted((O/'prepared').glob('*/PREPARED.json')):
 g,v=p.parent.name.rsplit('_',1);receipt=O/'recovery'/f'{g}_{v}_RESULT.json';rr=json.loads(receipt.read_text()) if receipt.exists() else {};final=pathlib.Path(rr.get('final_prepared_path',p));w=pathlib.Path(rr.get('final_w0_path',O/'w0'/p.parent.name));ss=pathlib.Path(rr.get('final_selection_path',O/'selection'/f'{g}_{v}.csv'));hh=h[(h.group_id==g)&(h.video_id.astype(str).str.zfill(3)==v)&(h.status=='PASS')];aa=a[(a.group_id==g)&(a.video_id.astype(str).str.zfill(3)==v)&(a.status.isin(['PASS','GATED_NEW_HERO']))] if 'group_id' in a and 'status' in a else pd.DataFrame()
 q=json.loads((w/'quality_summary.json').read_text()) if (w/'quality_summary.json').exists() else {};s=pd.read_csv(ss) if ss.exists() else pd.DataFrame();cc=[x for x in rows if x['group_id']==g and x['video_id']==v and x['status']=='PASS'];mm=[x for x in multi if x['group_id']==g and x['video_id']==v]
 ps.append(dict(group_id=g,video_id=v,stage_prepare='PASS',frames=len(json.loads(final.read_text())['views']) if final.exists() else np.nan,mask_clean='PASS',stage_w0='PASS' if (w/'W0.npz').exists() else 'FAIL',w0_accept=q.get('n_accept',np.nan),w0_ring_mae_median_px=q.get('ring_mae_median_px',np.nan),w0_held_median_px=q.get('held_median_px',np.nan),w0_held_p95_px=q.get('held_p95_px',np.nan),stage_select='PASS' if ss.exists() else 'FAIL',ready_targets=int(s.ready.sum()) if len(s) else 0,observation_status=rr.get('status','UNKNOWN'),recovery_reason=rr.get('failure_reason',rr.get('recovery_reason','')),hero=int(len(hh)),a2b=int(len(aa)),a2b_coverage_median=float(aa.target_coverage.median()) if len(aa) else np.nan,a2b_rgb_mae_median_0_255=float(aa.RGB_MAE_0_255.median()) if len(aa) else np.nan,cad_hero_mae_median_mm=float(pd.Series([x['mae_mm'] for x in cc]).median()) if cc else np.nan,multisurface_pairs=len(mm),multisurface_nn_median_mm=float(pd.Series([x['symmetric_nn_median_mm'] for x in mm]).median()) if mm else np.nan))
pd.DataFrame(ps).to_csv(O/'PIPELINE_EXECUTION_SUMMARY.csv',index=False)
if (O/'recovery').exists():
 code=subprocess.check_output(['git','rev-parse','HEAD'],cwd=WS,text=True).strip()
 for row in ps:
  g,v=row['group_id'],row['video_id'];path=O/'RUN_TRACE'/f'{g}_{v}.jsonl';path.parent.mkdir(parents=True,exist_ok=True)
  rr=json.loads((O/'recovery'/f'{g}_{v}_RESULT.json').read_text())
  inputs=[O/'hero/HERO_EXECUTION_RESULTS.csv',O/'evaluation/A_TO_B_METRICS.csv',
          pathlib.Path(rr['final_w0_path'])/'W0.npz',O/'cad'/('R5.npz' if '_R5_' in g else 'R10.npz')]
  outputs=[O/'evaluation/CAD_HERO_GEOMETRY.csv',O/'evaluation/MULTISURFACE_CONSISTENCY.csv',
           O/'PIPELINE_EXECUTION_SUMMARY.csv']
  event=dict(run_id='M2F6-UNIFIED-OBSERVATION-001',group_id=g,video_id=v,
             stage='geometry_summary',route_id='rf-m2f5-geometry-summary',route_version='1',
             entrypoint='tools/m2f5_summary.py',status='PASS' if row['hero'] else 'NOT_EVALUABLE',
             code_commit=code,inputs={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs if p.is_file()},
             outputs={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in outputs if p.is_file()},
             hero_count=row['hero'],a2b_count=row['a2b'])
  with path.open('a') as stream:stream.write(json.dumps(event,sort_keys=True)+'\n')
print('cad',len(rows),'multi',len(multi),'groups',len(gg),'pipeline',len(ps))
