"""Frozen-prediction native observations, CAD and independent GT evaluation."""
from common import *
from native_score import evaluate
from safe_geometry import dense_face_distance,self_intersections
from evaluate import area_samples,distance
from best_rigid015 import align,feret,apply
from concurrent.futures import ThreadPoolExecutor
import open3d as o3d

OLD15=REPO/'experiments/TASK-E4-MULTIVIEW-INIT-STALK-015'

def initial_for(x):
 if x['tag'].startswith('MECH'):return OLD15/'arms/Init-A/local_results'/x['case']/'FINAL.npz'
 return R/'inputs'/x['case']/'INITIAL.npz'

def depth_stats(sc,role='FIT'):
 rr=[x for x in sc['per_view']if x['role']==role and x.get('fixed_depth_N',0)>0];N=sum(x['fixed_depth_N']for x in rr);hit=sum(x['depth_hit_N']for x in rr)
 return dict(fixed_N=N,hit_N=hit,hit_rate=hit/N if N else None,miss_N=N-hit,source_N=len(rr),source_mean_fixed_cost=float(np.mean([x['fixed_depth_cost']for x in rr]))if rr else None,conditional_depth_MAE_mm=sum(x['depth_MAE_mm']*x['depth_hit_N']for x in rr if x['depth_MAE_mm']is not None)/hit if hit else None)

def geometry(x):
 n=x['case'];z=np.load(x['final']);i=np.load(initial_for(x));V,F=z['V'],z['F_solid'];rg=np.load(R/'inputs'/n/'RING.npz');rs=scene(rg['V'],rg['F']);m=trimesh.Trimesh(V,F,process=False);edges=m.edges_unique;sd=dense_face_distance(rs,V,F,rg['V'],64,rg['F']);si=self_intersections(V,F);e0=np.linalg.norm(i['V'][edges[:,0]]-i['V'][edges[:,1]],axis=1);ef=np.linalg.norm(V[edges[:,0]]-V[edges[:,1]],axis=1);delta=V-i['V'];mag=np.linalg.norm(delta,axis=1);row=dict(Ring_dense64_penetration_mm=max(0.,float(-sd.min())),self_intersections_N=si['intersections'],connected_components=len(m.split(only_watertight=False)),watertight=bool(m.is_watertight),winding_consistent=bool(m.is_winding_consistent),degenerate_faces_N=int((m.area_faces<1e-12).sum()),min_face_area_mm2=float(m.area_faces.min()),maximum_displacement_mm=float(mag.max()),mean_displacement_mm=float(mag.mean()),edge_stretch_p95=float(np.quantile(ef/np.maximum(e0,1e-12),.95)),edge_stretch_max=float((ef/np.maximum(e0,1e-12)).max()),raw_volume_mm3=float(m.volume),volume_not_GT=True)
 moving=mag>max(.05,float(mag.max())*.25)
 if moving.sum()>3:
  s=np.linalg.svd(V[moving]-V[moving].mean(0),compute_uv=False);row.update(high_motion_vertex_N=int(moving.sum()),high_motion_patch_PCA_small_over_large=float(s[-1]/s[0]),patch_flatness_is_proxy_not_anatomy=True)
 return row

def native(x,cache):
 n,t=x['case'],x['tag'];p=Path(x['final']);key=(n,sha(p));ikey=(n,sha(initial_for(x)))
 if key not in cache:cache[key]=evaluate(n,p,True,t)
 if ikey not in cache:cache[ikey]=evaluate(n,initial_for(x),True,'INITIAL')
 sc,initial=cache[key],cache[ikey];save('metrics/native/'+n+'_'+t+'.json',sc);d=depth_stats(sc);di=depth_stats(initial);h=d['hit_rate'];h0=di['hit_rate'];row=dict(case=n,tag=t,kind=x['kind'],scene=x['scene'],source=asset(p),initial_source=asset(initial_for(x)),FIT_common=sc['mean'].get('FIT'),HOLDOUT=sc['mean'].get('UPDATE_HOLDOUT'),COMMON_POOL=sc['mean'].get('COMMON_FIT_EVAL'),depth=d,initial_depth=di,coverage_decreased=h<h0-1e-12 if h is not None and h0 is not None else None,geometry=geometry(x))
 runfile=Path(x['metrics'])if x.get('metrics')else R/'arms'/t/'metrics'/(n+'_RUN.json');row['run']=load(runfile)
 out=R/'review_meshes'/n;out.mkdir(parents=True,exist_ok=True);a=np.load(p);keep={k:a[k]for k in ['V','F','F_solid','inferred_base_faces','boundary_vertex']if k in a};np.savez_compressed(out/(t+'.npz'),**keep);trimesh.Trimesh(a['V'],a['F_solid'],process=False).export(out/(t+'_mm.ply'))
 return row

def evaluate_real_gt(x,sources):
 n,t=x['case'],x['tag'];z=np.load(x['final']);GT=np.load(OLD15/'evaluation_only'/n/'ORIGINAL_BLENDER_GT_MM.npz');src=sources[n]
 if x['kind']=='READ_ONLY_015_BASELINE':
  label='Stalk-B'if t.startswith('MECH')else'Init-A_FINAL';row=dict(next(y for y in load(OLD15/'metrics/BLENDER_GEOMETRIC_METRICS.json')if y['case']==n and y['label']==label));row.update(tag=t,baseline_GT_metric_reused=True,source_GT_metrics=asset(OLD15/'metrics/BLENDER_GEOMETRIC_METRICS.json'));return row
 rg=np.load(R/'inputs'/n/'RING.npz');D=2*float(np.linalg.norm(rg['V'][:,:2],axis=1).min());T,trials=align(z['V'],z['F'],GT['V'],GT['F'],D);V=apply(z['V'],T);P=area_samples(V,z['F'],8192);G=area_samples(GT['V'],GT['F'],8192);dp=distance(scene(GT['V'],GT['F']),P);dg=distance(scene(V,z['F']),G);row=dict(case=n,tag=t,kind=x['kind'],Chamfer_MAE_mm=float(.5*(dp.mean()+dg.mean())),Chamfer_median_mm=float(np.median(np.r_[dp,dg])),Chamfer_p95_mm=float(np.quantile(np.r_[dp,dg],.95)),prediction_to_GT_mm=stats(dp),GT_to_prediction_mm=stats(dg),evaluation='After Ring-based Metric Recovery and Best 6-DoF Rigid Alignment',GT_used_for_selection=False,scale=1.,T=T,best_score_mm=trials['best']['score_mm'],second_score_mm=trials['second']['score_mm'])
 base=src.get('author_base');axis=base['normal']if base else src.get('author_reference_axis')
 if axis is not None:
  dx,gx=feret(V,axis),feret(GT['V'],axis);row.update(Dxy_pred_mm=dx,Dxy_GT_mm=gx,Dxy_AE_mm=abs(dx-gx),Dxy_relative_error=abs(dx-gx)/gx)
 if base:
  axis=np.asarray(axis)/np.linalg.norm(axis);h=V@axis+base['offset_mm'];gh=GT['V']@axis+base['offset_mm'];row.update(height_max_pred_mm=float(h.max()),height_max_GT_mm=float(gh.max()),height_max_AE_mm=float(abs(h.max()-gh.max())),height_status='CONDITIONAL_AUTHOR_BASE_AFTER_ALIGNMENT')
 for tol in [.1,.25,.5,1.]:
  p=float((dp<tol).mean());q=float((dg<tol).mean());row['Fscore_'+str(tol)+'mm']=2*p*q/max(1e-30,p+q)
 folder=R/'local_results/aligned'/n;folder.mkdir(parents=True,exist_ok=True);np.savez_compressed(folder/(t+'.npz'),V=V,F=z['F'],F_solid=z['F_solid'],T=T);save('metrics/alignment/'+n+'_'+t+'.json',trials);return row

def evaluate_virtual(x):
 src=REPO/'experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/BOUNDARY_RELATIVE_DEPTH_D2_001/audit_only/virtual_Ip/GT.npz';g=np.load(src);s=scene(g['V'],g['F']);z=np.load(x['final']);i=np.load(initial_for(x));cp=s.compute_closest_points(o3d.core.Tensor(i['V'].astype(np.float32)))['points'].numpy();desired=cp-i['V'];delta=z['V']-i['V'];dd=distance(s,i['V']);df=distance(s,z['V']);valid=(np.linalg.norm(delta,axis=1)>1e-6)&(dd>.05);cos=np.sum(delta*desired,axis=1)/np.maximum(1e-30,np.linalg.norm(delta,axis=1)*np.linalg.norm(desired,axis=1));rows=[]
 for stage,a in [('INITIAL',i),('FINAL',z)]:
  P=area_samples(a['V'],a['F'],8192);G=area_samples(g['V'],g['F'],8192);dp=distance(s,P);dg=distance(scene(a['V'],a['F']),G);rows.append(dict(stage=stage,Chamfer_mm=stats(np.r_[dp,dg]),prediction_to_GT_mm=stats(dp),GT_to_prediction_mm=stats(dg),highest_world_Z_mm=float(a['V'][:,2].max()),GT_highest_world_Z_mm=float(g['V'][:,2].max())))
 row=dict(tag=x['tag'],scene='virtual',GT_source=asset(src),known_frame_no_ICP=True,stages=rows,direction_evaluable_vertex_N=int(valid.sum()),nearest_GT_direction_cosine_positive_fraction=float((cos[valid]>0).mean())if valid.any()else None,material_vertex_unsigned_GT_distance_change_mm=float((df-dd).mean()),direction_caveat='Closest-surface error-reduction proxy, not authored material correspondence or independent anatomical stalk label',strict_solid_volume_IoU='NOT_EVALUABLE_NATIVE_GT_SELF_INTERSECTIONS',GT_not_in_fit=True);save('metrics/virtual/'+x['tag']+'.json',row);return row

def main():
 assert(R/'provenance/REAL_PREDICTIONS_FROZEN.json').exists()and(R/'provenance/VIRTUAL_PREDICTIONS_FROZEN.json').exists()
 reg=load(R/'config/RUN_REGISTRY.json');vr=load(R/'config/VIRTUAL_RUN_REGISTRY.json');allreg=reg+vr;files=[asset(Path(x['final']))for x in allreg];save('provenance/ALL_PREDICTIONS_AND_SCALE_FROZEN_BEFORE_GT.json',dict(epoch=time.time(),files=files,real_GT_not_read_by_task_until_now=True,virtual_GT_preprojection_exception=True,scale_fixed=1.,no_more_optimizer_updates=True));cache={};native_rows=[]
 for x in allreg:
  native_rows.append(native(x,cache));print('NATIVE_EVALUATED',x['case'],x['tag'],flush=True)
 save('metrics/NATIVE_AND_GEOMETRY.json',native_rows);table('metrics/NATIVE_AND_GEOMETRY.csv',native_rows)
 save('provenance/REAL_GT_FIRST_ACCESS.json',dict(epoch=time.time(),prediction_freeze=asset(R/'provenance/ALL_PREDICTIONS_AND_SCALE_FROZEN_BEFORE_GT.json'),no_selection_by_GT=True));sources={x['case']:x for x in load(OLD15/'evaluation_only/GT_SOURCE_LOCK.json')}
 with ThreadPoolExecutor(max_workers=2)as pool:gg=list(pool.map(lambda x:evaluate_real_gt(x,sources),reg))
 save('metrics/GT_COMPARISONS.json',gg);table('metrics/GT_COMPARISONS.csv',gg);virtual=[evaluate_virtual(x)for x in vr];save('metrics/VIRTUAL_GT_COMPARISONS.json',virtual);print('INDEPENDENT_EVALUATION_COMPLETE',len(native_rows),len(gg),len(virtual),flush=True)
if __name__=='__main__':main()
