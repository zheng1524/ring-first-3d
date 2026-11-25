"""Post-output evaluation only: original CAD/reprojection kernels and all directed depth pairs."""
import ast,inspect,sys
import numpy as np
from .route import W,WT,T,B,CORE,read,save,sha,environment
from pathlib import Path
LOADED_SOURCE_SHA=sha(__file__)
P12=Path('/home/liu/.config/superpowers/worktrees/ring_first_3d_workspace/TASK-M2F12/experiments/TASK-M2F12-CLEANUP-AND-HISTORICAL-004-CAMERA-RESTORATION-001')

def depth_diagnostic(a,b,visible):
 common=visible&np.isfinite(a)&np.isfinite(b)&(a>0)&(b>0);d=a[common]-b[common];v=abs(d)
 return dict(status='EVALUABLE'if len(d)else'NOT_EVALUABLE',common_pixels=int(len(d)),MAE_mm=float(v.mean())if len(d)else None,median_signed_mm=float(np.median(d))if len(d)else None,median_absolute_mm=float(np.median(v))if len(d)else None,P95_absolute_mm=float(np.quantile(v,.95))if len(d)else None,max_absolute_mm=float(v.max())if len(d)else None,over_5mm_fraction=float((v>5).mean())if len(d)else None,not_GT=True,visibility='A original mesh z-buffer + CAD; B real tissue occlusion unknown; no error-based rejection')

def scorer():
 environment();sys.path.insert(0,str(P12/'code'));import hero_check as old
 f=ast.parse(inspect.getsource(old.evaluate)).body[0];body=[]
 for node in f.body:
  if isinstance(node,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='m'for t in node.targets):break
  body.append(node)
 f.name='ring_only';f.body=body+ast.parse('return rm,d,np.where(common,abs(depth-cad),np.nan),ns').body;ast.fix_missing_locations(f);ns=dict(old.__dict__);exec(compile(ast.Module(body=[f],type_ignores=[]),str(P12/'code/hero_check.py')+'::ring_prefix','exec'),ns);return old,ns['ring_only']

def evaluate_run(R,out=None,case=None,variant=None):
 import cv2,trimesh
 assert sha(__file__)==LOADED_SOURCE_SHA,'Evaluator changed in memory; use a fresh evaluation process'
 R=Path(R);case=case or R.name;variant=variant or R.parent.name;out=Path(out)if out else B/'evaluation'/variant/case;out.mkdir(parents=True,exist_ok=True)
 files=list((R/'raw').glob('*.npz'))+list((R/'meshes').glob('*_Polyp.ply'))+list((R/'predictions').glob('local005_camera_*.npz'))
 files += [R/p for p in ['config.json','inputs/ledger005.json','inputs/MVS_supported_cases.json','predictions/local005_primary.json','metrics/local_validation.json','metrics/surfaces005.json','metrics/MVS005_supported_runs.json','PLAN_FROZEN.json']if(R/p).exists()]
 for row in read(R/'inputs/ledger005.json'):files += [Path(row['RGB_path']),Path(row['Mask_path'])]
 files += [Path(__file__),P12/'code/hero_check.py',W/'src/ring_first_3d/sim/geometry.py',W/'src/ring_first_3d/mainline/lineage/experiments/TASK-VIEW-OBSERVABILITY-GT-EVAL-001/code/reprojection.py',W/'runs/m2f5_unified/cad'/('R5.npz'if '_R5_'in case else'R10.npz')]
 input_hashes={str(p):sha(p)for p in files}
 if(out/'COMPLETE.json').exists():
  prior=read(out/'COMPLETE.json')
  if prior['inputs']==input_hashes:return read(out/'RESULTS.json')
  # Post-output metrics can be recomputed; never silently reuse changed evaluator inputs.
  save(out/('PREVIOUS_EVALUATION_'+sha(out/'COMPLETE.json')[:12]+'.json'),prior)
 old,ring_only=scorer();L=read(R/'inputs/ledger005.json');primary=read(R/'predictions/local005_primary.json')['primary_version'];cam=np.load(R/f'predictions/local005_camera_{primary}.npz');C=cam['c2w'];cfg=read(R/'config.json');ring_mm=5 if '_R5_'in case else 10
 plan=read(R/'PLAN_FROZEN.json')if(R/'PLAN_FROZEN.json').exists()else None
 cases=plan['legal']if plan else[c for c in read(R/'inputs/MVS_supported_cases.json')if(R/'meshes'/(c['tag']+'_Polyp.ply')).exists()]
 surfaces={r['tag']:r for r in read(R/'metrics/surfaces005.json')}if(R/'metrics/surfaces005.json').exists()else{}
 results=[];loaded={};render_ns=None
 for c in cases:
  tag=c['tag'];native=R/'raw'/(tag+'.npz');mesh=R/'meshes'/(tag+'_Polyp.ply');O=out/tag;O.mkdir(exist_ok=True)
  row=dict(case=case,variant=variant,route='V6',plan=c,v6_root=str(R),ring_inner_mm=ring_mm)
  if not(native.exists()and mesh.exists()):results.append(dict(tag=tag,status='FAILED_OR_MISSING',plan=c,raw_target=L[c['reference']]['raw_frame'],raw_support=[L[i]['raw_frame']for i in c['sources']],native_exists=native.exists(),mesh_exists=mesh.exists(),failure_reason='NATIVE_OR_MESH_MISSING'));continue
  try:
   m=trimesh.load(mesh,process=False)
   if not np.isfinite(C[[c['reference']]+c['sources']]).all()or not hasattr(m,'faces')or not len(m.faces)or not np.isfinite(m.vertices).all():
    results.append(dict(tag=tag,status='NONRENDERABLE',plan=c,raw_target=L[c['reference']]['raw_frame'],raw_support=[L[i]['raw_frame']for i in c['sources']],failure_reason='NONFINITE_CAMERA_OR_VERTEX_OR_EMPTY_FACES'));continue
   fs=old.frames(row);z=np.load(native);np.savez_compressed(O/'HERO_native.npz',depth_mm=z['depth_mm'],K_index_native=z['K_index_native'],reference_pose_mm=C[c['reference']]);rm,d,heat,render_ns=ring_only(row,fs,O);rm.update(max_mm=float(d.max())if len(d)else None,over5_count=int((d>5).sum()),over5_fraction=float((d>5).mean())if len(d)else None)
   m=trimesh.load(mesh,process=False);V=np.asarray(m.vertices);F=np.asarray(m.faces);color=np.asarray(m.visual.vertex_colors)[:,:3]/255.;target=int(c['independent_image_heldout']);bf=L[target];bRGB=cv2.cvtColor(cv2.imread(bf['RGB_path']),cv2.COLOR_BGR2RGB);blab=cv2.imread(bf['Mask_path'],0);pred=render_ns['render'](V,F,color,np.asarray(bf.get('K',cfg['K'])),C[target],np.eye(4),'R5'if ring_mm==5 else'R10');ab,err,common=render_ns['evaluate'](pred,bRGB,blab);ab.update(B_raw_frame=bf['raw_frame'],B_in_HERO=target in [c['reference']]+c['sources'],B_camera_used_RGB_BA=True,full_chain_independent=False)
   np.savez_compressed(O/'DISPLAY.npz',ring_heat=heat,A_RGB=fs[0]['RGB'],A_Mask=fs[0]['labels'],B_RGB=bRGB,A_to_B=pred['RGBA'],A_to_B_error=np.where(common,err,np.nan))
   rec=dict(tag=tag,status='RENDERABLE',case=case,variant=variant,plan=c,raw_target=L[c['reference']]['raw_frame'],raw_support=[L[i]['raw_frame']for i in c['sources']],old_rule_generated=c.get('old_rule_generated',True),rule_version=c.get('rule_version','M2F10'),target_own_old_pass=c.get('target_own_old_pass'),target_own_new_pass=c.get('target_own_new_pass'),ring=rm,noninput_B=ab,sparse_held=surfaces.get(tag,{}).get('heldout_reprojection_px'),mesh_path=str(mesh),mesh_sha256=sha(mesh),native_path=str(native),native_sha256=sha(native),display=str(O/'DISPLAY.npz'),vertices=len(V),faces=len(F),bbox_min=V.min(0),bbox_max=V.max(0))
   results.append(clean_record(rec));loaded[tag]=dict(V=V,F=F,color=color,depth=cv2.resize(z['depth_mm'].astype(float),(640,360),interpolation=cv2.INTER_LINEAR),labels=fs[0]['labels'],K=fs[0]['K'],C=fs[0]['c2w_mm']);save(out/'RESULTS.json',results);print('EVAL_SOURCE',variant,case,tag,rm['MAE_mm'],flush=True)
  except Exception as ex:
   import traceback
   results.append(dict(tag=tag,status="EVALUATION_ERROR",plan=c,raw_target=L[c["reference"]]["raw_frame"],raw_support=[L[i]["raw_frame"]for i in c["sources"]],native_exists=native.exists(),mesh_exists=mesh.exists(),failure_reason=repr(ex),traceback=traceback.format_exc()))
   save(out/"RESULTS.json",results)

 pairs=[]
 for a in results:
  if a['tag']not in loaded:continue
  A=loaded[a['tag']]
  for b in results:
   if a['tag']==b['tag']or b['tag']not in loaded:continue
   D=loaded[b['tag']];pred=render_ns['render'](A['V'],A['F'],A['color'],D['K'],D['C'],np.eye(4),'R5'if ring_mm==5 else'R10');visible=pred['valid']&(D['labels']==1);r=depth_diagnostic(pred['z_mm'],D['depth'],visible);r.update(A=a['tag'],B=b['tag'],A_raw=a['raw_target'],B_raw=b['raw_target'],B_polyp_pixels=int((D['labels']==1).sum()),projected_common_fraction=r['common_pixels']/max(1,int((D['labels']==1).sum())));pairs.append(r)
 save(out/'PAIR_DEPTH_CONSISTENCY.json',pairs)
 directions=np.asarray(next(x['P_estimate_mm']for x in read(R/'metrics/local_validation.json')['coverage']if x['version']==primary))-C[:,:3,3];directions/=np.maximum(np.linalg.norm(directions,axis=1)[:,None],1e-12);angles=np.degrees(np.arccos(np.clip(directions@directions.T,-1,1)));az=np.degrees(np.arctan2(directions[:,1],directions[:,0]));el=np.degrees(np.arcsin(np.clip(directions[:,2],-1,1)));allbins=set(zip(np.floor(az/10).astype(int),np.floor(el/10).astype(int)));targets=[x['plan']['reference']for x in results if x['status']=='RENDERABLE'];targetbins=set((int(np.floor(az[i]/10)),int(np.floor(el[i]/10)))for i in targets)
 summary=dict(case=case,variant=variant,numeric_cameras=len(C),generated=len(targets),old_rule_generated=sum(x.get('old_rule_generated',False)for x in results if x['status']=='RENDERABLE'),added=sum(not x.get('old_rule_generated',True)for x in results if x['status']=='RENDERABLE'),angular_span_deg=float(angles.max()),observed_10deg_bins=len(allbins),generated_10deg_bins=len(targetbins),pair_count=len(pairs),pair_evaluable=sum(x['status']=='EVALUABLE'for x in pairs),ring_MAE_median=median([x['ring']['MAE_mm']for x in results if x['status']=='RENDERABLE']),ring_P95_median=median([x['ring']['p95_mm']for x in results if x['status']=='RENDERABLE']),ring_P95_max=max([x['ring']['p95_mm']for x in results if x['status']=='RENDERABLE'and x['ring']['p95_mm']is not None],default=None),overlap_P95_pair_median=median([x['P95_absolute_mm']for x in pairs]),not_absolute_pose_GT=True)
 if not plan:
  per=next(v['per_frame']for v in read(R/'metrics/local_validation.json')['versions']if v['version']==primary)
  for x in results:
   x['target_own_old_pass']=per[x['plan']['reference']]['status']=='VALIDATED';x['target_own_new_pass']=x['target_own_old_pass']
 runs=read(R/'metrics/MVS005_supported_runs.json')if(R/'metrics/MVS005_supported_runs.json').exists()else[]
 tags={c['tag']for c in cases};attempted=[x for x in runs if x['tag']in tags]
 summary.update(legal_combinations=len(cases),inference_started=len(attempted),inference_success=sum(x['success']for x in attempted),renderable=len(targets),nonrenderable=[x for x in results if x['status']!='RENDERABLE'],failed_or_nonrenderable=sum(x['status']!='RENDERABLE'for x in results),not_admitted_targets=[x for x in plan['all_targets']if len(x['sources'])!=3]if plan else[],old_admitted_cameras=plan['old_cameras']if plan else sum(x['status']=='VALIDATED'for x in next(v['per_frame']for v in read(R/'metrics/local_validation.json')['versions']if v['version']==primary)),new_admitted_cameras=plan['new_cameras']if plan else None,target_own_old_pass=sum(bool(x.get('target_own_old_pass'))for x in results if x['status']=='RENDERABLE'),target_own_new_pass=sum(bool(x.get('target_own_new_pass'))for x in results if x['status']=='RENDERABLE'),sparse_held_source_count=sum(x.get('sparse_held',{}).get('n',0)>0 for x in results if x['status']=='RENDERABLE'and x.get('sparse_held')))
 if plan:
  journal=B/'INFERENCE_STARTS.jsonl';summary['inference_started']=sum(1 for line in journal.read_text().splitlines()if (lambda x:x['case']==case and x['variant']==variant)(__import__('json').loads(line)))if journal.exists()else 0
 summary.update(run_path=str(R),ring_evaluable_sources=sum(x.get('ring',{}).get('MAE_mm')is not None for x in results if x['status']=='RENDERABLE'),ring_observed_pixels=sum(x['ring']['observed_ring_pixels']for x in results if x['status']=='RENDERABLE'),ring_common_pixels=sum(x['ring']['CAD_common_pixels']for x in results if x['status']=='RENDERABLE'),pair_common_pixels=sum(x['common_pixels']for x in pairs))
 save(out/'SUMMARY.json',summary);save(out/'RESULTS.json',results);save(out/'COMPLETE.json',dict(inputs=input_hashes,source_sha256=sha(__file__),original_evaluator_sha256=sha(P12/'code/hero_check.py')));print('EVAL_COMPLETE',summary,flush=True);return results

def clean_record(r):
 from .route import clean
 return clean(r)
def median(xs):
 x=[a for a in xs if a is not None and np.isfinite(a)];return float(np.median(x))if x else None
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('run');p.add_argument('--out');a=p.parse_args();evaluate_run(a.run,a.out)
