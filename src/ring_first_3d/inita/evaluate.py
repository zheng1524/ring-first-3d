"""Frozen world predictions → exact historical multistart rigid evaluation copies."""
import ast,json,csv,itertools,hashlib
from pathlib import Path
import numpy as np
import open3d as o3d
import trimesh
from scipy.spatial.transform import Rotation
from scipy.stats import qmc
from ..policy.contracts import ROOT,require
from ..contracts.identities import sha256
from ..synthetic.io import fetch,save_json,outputs
from ..multisurface.geometry import scene
from ..multisurface.evaluate import fixed_stats
from .train import sources,projection_rows
from .hero import evaluate as hero_evaluate

def legacy_namespace(task):
 folder=ROOT/'experiments'/task['task_id']/'legacy015';ns=dict(np=np,o3d=o3d,trimesh=trimesh,itertools=itertools,Rotation=Rotation,qmc=qmc,scene=scene);receipts=[]
 for file,names in [('evaluate.py',['area_samples','distance','occupied']),('best_rigid015.py',['frames','pca','apply','rigid','interpolate','align']),('safe_geometry.py',['dense_face_distance','self_intersections'])]:
  p=folder/file;nodes=[n for n in ast.parse(p.read_text()).body if isinstance(n,ast.FunctionDef)and n.name in names];require({n.name for n in nodes}==set(names),'SOURCE_CONTRACT',file);exec(compile(ast.Module(body=nodes,type_ignores=[]),str(p),'exec'),ns)
  receipts.extend(dict(file=file,function=n.name,AST_sha256=hashlib.sha256(ast.dump(n,include_attributes=False).encode()).hexdigest(),mathematics_modified=False)for n in nodes)
 ns['reuse_receipts']=receipts;return ns

def geometry(mesh,initial,ring,ns):
 V,F=mesh['V'],mesh.get('F_solid',mesh['F']);V0=initial['V'];rs=scene(ring['V'],ring['F']);d=ns['dense_face_distance'](rs,V,F,ring['V'],64,ring['F']);si=ns['self_intersections'](V,F);m=trimesh.Trimesh(V,F,process=False);e=np.unique(np.sort(np.r_[F[:,[0,1]],F[:,[1,2]],F[:,[2,0]]],axis=1),axis=0);before=np.linalg.norm(V0[e[:,0]]-V0[e[:,1]],axis=1);after=np.linalg.norm(V[e[:,0]]-V[e[:,1]],axis=1);tri=V[F];t0=V0[F];normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);n0=np.cross(t0[:,1]-t0[:,0],t0[:,2]-t0[:,0]);ratio=np.linalg.norm(normal,axis=1)/np.maximum(1e-20,np.linalg.norm(n0,axis=1));dot=(normal*n0).sum(1)
 return dict(volume_positive=bool(m.is_volume),watertight=bool(m.is_watertight),winding_consistent=bool(m.is_winding_consistent),self_intersections=si['intersections'],ring_min_dense64_mm=float(d.min()),ring_negative_dense_face_N=int((d<0).sum()),ring_penetration_max_mm=float(max(0,-d.min())),area_ratio_min=float(ratio.min()),normal_against_initial_nonpositive_N=int((dot<=0).sum()),edge_ratio=fixed_stats(after/np.maximum(before,1e-20)),displacement_from013_mm=fixed_stats(np.linalg.norm(V-V0,axis=1)),inferred_base=bool(mesh.get('inferred_base_faces',np.zeros(1,bool)).any()),components=int(len(m.split(only_watertight=False))))

def shape_evaluate(task,attempt,smoke=False):
 root=attempt.parents[1];stage='G1_smoke_train'if smoke else'G1_all_train';pred=json.loads(fetch(root,stage,'BODY_PREDICTIONS_FROZEN.json').read_text())['records'];by={c['case']:c for c in sources(task)['cases']};ns=legacy_namespace(task);allrows=[];transforms=[];metadata=json.loads(Path(task['inita']['assets']['GT_metadata']['path']).read_text());gtmeta={r['case']:r for r in metadata}
 save_json(attempt/'GT_FIRST_ACCESS.json',dict(prediction_freeze_sha256=sha256(fetch(root,stage,'BODY_PREDICTIONS_FROZEN.json')),applicable_predictions_frozen=True,scale_fixed=1,training_changes_after_GT=False));save_json(attempt/'LEGACY_REUSE_RECEIPTS.json',ns['reuse_receipts'])
 for name in dict.fromkeys(r['case']for r in pred):
  row=by[name];group=[r for r in pred if r['case']==name];out=attempt/'evaluation_only'/name;out.mkdir(parents=True);gt=dict(np.load(row['GT']['path']));GV,GF=gt['V'],gt['F'];gr=scene(GV,GF);GTmesh=trimesh.Trimesh(GV,GF,process=False);GTsi=ns['self_intersections'](GV,GF)['intersections'];G=ns['area_samples'](GV,GF,8192);initial=dict(np.load(row['resolved013_initial']['path']));ring=dict(np.load(row['static']['RING.npz']['path']));D=5. if row['ring']=='R5'else 10.;aligned={};records={};world_digests={}
  for r in group:
   arm=r['arm'];item=dict(case=name,morphology=row['morphology'],arm=arm,status=r['status'],IoU_3D=None,IoU_3D_status='NOT_EVALUABLE_NO_PREDICTION',conditional_occupancy_IoU=None,Chamfer_MAE_mm=None,GT_alignment_scale=1.)
   if r['status']!='NUMERIC':item['reason']=r.get('reason');records[arm]=item;continue
   path=fetch(root,stage,r['world_mesh_relative']);world_digests[arm]=sha256(path);m=dict(np.load(path));V,F=m['V'],m['F'];T,trials=ns['align'](V,F,GV,GF,D);require(np.allclose(T[:3,:3].T@T[:3,:3],np.eye(3),atol=1e-6)and np.linalg.det(T[:3,:3])>.999999,'GT_SE3','Scale1 proper rotation');AV=ns['apply'](V,T);np.savez_compressed(out/(arm+'_ALIGNED.npz'),**dict(m,V=AV,T=T));trimesh.Trimesh(AV,m['F_solid'],process=False).export(out/(arm+'_ALIGNED_mm.ply'));save_json(out/(arm+'_RIGID_STARTS.json'),trials);aligned[arm]=dict(m,V=AV);ps=ns['area_samples'](AV,F,8192);dp=ns['distance'](gr,ps);dg=ns['distance'](scene(AV,F),G);s=fixed_stats(np.r_[dp,dg]);ge=geometry(m,initial,ring,ns);proj=projection_rows(m,row,np.asarray(r['shared_005_D'])if 'shared_005_D'in r else None);save_json(out/(arm+'_WORLD_PROJECTION.json'),proj);precision=float((dp<=.5).mean());recall=float((dg<=.5).mean());diag=float(np.linalg.norm(np.ptp(GV,axis=0)));item.update(status='NUMERIC',Chamfer_MAE_mm=s['MAE'],Chamfer_P95_mm=s['p95'],Chamfer_median_mm=s['median'],Chamfer_max_mm=s['maximum'],median_absolute_relative_surface_error_to_GT_diagonal=s['median']/diag,pred_to_GT_mm=fixed_stats(dp),GT_to_pred_mm=fixed_stats(dg),GT_coverage_0p5mm=recall,Fscore_0p5mm=2*precision*recall/max(1e-20,precision+recall),GT_geometry=dict(watertight=bool(GTmesh.is_watertight),winding_consistent=bool(GTmesh.is_winding_consistent),self_intersections=GTsi),world_geometry=ge,projection=proj,world_prediction_sha256=world_digests[arm],aligned_mesh_relative=str((out/(arm+'_ALIGNED.npz')).relative_to(attempt)),alignment=T.tolist(),alignment_best_score_mm=trials['best']['score_mm'],alignment_global_optimum_certified=False,GT_used_for_training=False,GT_aligned_HERO=False)
   records[arm]=item;transforms.append(dict(case=name,arm=arm,T=T.tolist(),scale=1.,world_source_sha256=world_digests[arm],only_evaluation_copy_modified=True));print('INIT_A_GT_ALIGNED',name,arm,item['Chamfer_MAE_mm'],flush=True)
  # One fixed 3D population and bounds per case for all frozen aligned arms.
  bounds=np.concatenate([GV]+[m['V']for m in aligned.values()]);lo=bounds.min(0)-.5;hi=bounds.max(0)+.5;Q=lo+(hi-lo)*qmc.Sobol(3,scramble=True,seed=task['inita']['occupancy_seed']).random_base2(task['inita']['occupancy_Sobol_power']);og=ns['occupied'](gr,Q);save_json(out/'COMMON_OCCUPANCY_DOMAIN.json',dict(lo_mm=lo,hi_mm=hi,N=len(Q),seed=task['inita']['occupancy_seed'],all_arms_share_points=True,domain='Union of all frozen aligned predictions and GT +0.5mm; metric only, no prediction cropping or model selection'))
  for arm,m in aligned.items():
   item=records[arm];op=ns['occupied'](scene(m['V'],m['F_solid']),Q);intersection=int((op&og).sum());union=int((op|og).sum());value=intersection/max(1,union);pg=item['world_geometry'];valid=pg['volume_positive']and GTmesh.is_volume and pg['watertight']and pg['winding_consistent']and pg['self_intersections']==0 and GTmesh.is_watertight and GTmesh.is_winding_consistent and GTsi==0
   item.update(conditional_occupancy_IoU=value,occupancy_N=len(Q),occupancy_intersection_N=intersection,occupancy_union_N=union,conditional_occupancy_status='CLOSED_ENTITY_WITH_INFERRED_BASE'if valid else'RAY_PARITY_DIAGNOSTIC_ENTITY_INVALID',conditional_occupancy_not_strict_IoU=True)
   strict=valid and not pg['inferred_base']and gtmeta.get(name,{}).get('GT_geometry_complete',False)
   item['IoU_3D']=value if strict else None;item['IoU_3D_status']='VALID_SOLID_SOBOL_ESTIMATE'if strict else'NOT_EVALUABLE_STRICT_INFERRED_OR_UNCERTAIN_BASE'if valid else'NOT_EVALUABLE_ENTITY_VALIDITY'
   r=next(r for r in group if r['arm']==arm);require(sha256(fetch(root,stage,r['world_mesh_relative']))==world_digests[arm],'GT_COPY_ISOLATION',name+'/'+arm)
  allrows.extend(records.values());save_json(attempt/'BODY_SHAPE_METRICS_PARTIAL.json',dict(rows=allrows,target_physical_cases=11))
 save_json(attempt/'BODY_SHAPE_METRICS.json',dict(rows=allrows,target_physical_cases=11,scale_fixed=1,actual_best_rigid_alignment=True,world_models_unchanged=True));save_json(attempt/'GT_RIGID_TRANSFORMS.json',transforms)
 with(attempt/'BODY_SHAPE_METRICS.csv').open('w',newline='')as f:
  keys=['case','morphology','arm','status','IoU_3D','IoU_3D_status','conditional_occupancy_IoU','conditional_occupancy_status','Chamfer_MAE_mm','Chamfer_P95_mm','Chamfer_median_mm','Chamfer_max_mm','median_absolute_relative_surface_error_to_GT_diagonal','GT_coverage_0p5mm','Fscore_0p5mm'];w=csv.DictWriter(f,keys,extrasaction='ignore',lineterminator='\n');w.writeheader();w.writerows(allrows)
 return allrows

def run(task,attempt,smoke=False):
 body=shape_evaluate(task,attempt,smoke);hero=hero_evaluate(task,attempt,smoke);failures=[]
 for r in body:
  if r['status']!='NUMERIC':failures.append(dict(case=r['case'],arm=r['arm'],category='incomplete_evaluation',reason=r.get('reason'),evidence='BODY_SHAPE_METRICS.json'))
  elif r['IoU_3D']is None:failures.append(dict(case=r['case'],arm=r['arm'],category='scientific_negative',reason=r['IoU_3D_status'],conditional_occupancy_IoU=r['conditional_occupancy_IoU'],evidence='BODY_SHAPE_METRICS.json'))
 for g in hero:
  if g['status']!='NUMERIC':failures.append(dict(case=g['case'],category='incomplete_evaluation',reason=g['reason'],evidence='HERO_METRICS.json'))
 paired=[]
 for g in task['inita']['cases']:
  by={r['arm']:r for r in body if r['case']==g}
  if all(by.get(a,{}).get('status')=='NUMERIC'for a in ['A1','A2']):paired.append(dict(case=g,conditional_IoU_delta_A2_minus_A1=by['A2']['conditional_occupancy_IoU']-by['A1']['conditional_occupancy_IoU'],Chamfer_delta_A2_minus_A1_mm=by['A2']['Chamfer_MAE_mm']-by['A1']['Chamfer_MAE_mm'],strict_IoU_pair_valid=by['A1']['IoU_3D']is not None and by['A2']['IoU_3D']is not None))
 save_json(attempt/'PAIRED_COMPARISONS.json',dict(body=paired,physical_denominator=11,no_post_GT_winner_selection=True));save_json(attempt/'FAILURE_LEDGER.json',dict(failures=failures,scientific_accuracy_not_execution_gate=True));return outputs(attempt,dict(status='PASS',body_rows=len(body),body_numeric=sum(r['status']=='NUMERIC'for r in body),HERO_target_groups=len(hero),GT_read_by_evaluator=True,scale_fixed=1.))
