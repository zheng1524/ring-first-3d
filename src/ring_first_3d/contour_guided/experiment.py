"""Policy stages composing frozen Init-A, native HERO, rigid evaluation and PNG export."""
from pathlib import Path
import json,os,sys,subprocess,shutil,types,io,unittest,time
import numpy as np
from ..policy.contracts import ROOT,require,PolicyError
from ..contracts.identities import sha256
from ..synthetic.io import save_json,fetch,outputs
from ..inita.train import sources,copy_tree,projection_rows
from ..inita import hero as oldhero
from ..multisurface import registration
from ..multisurface.geometry import transform
from ..stress.real import validate_view,load_view
from . import hero as meshhero

def regression(attempt):
 loader=unittest.defaultTestLoader;patterns=['test_harness_contracts.py','test_policy_bootstrap.py','test_synthetic_correspondence.py','test_dualvideo_gate.py','test_sim_rev1.py','test_multisurface.py','test_stress.py','test_inita.py','test_contour_guided.py'];suites=[loader.discover(str(ROOT/'tests'),pattern=p)for p in patterns];base=suites[0].countTestCases()+suites[1].countTestCases();suite=unittest.TestSuite(suites);stream=io.StringIO();r=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite);(attempt/'regression_log.txt').write_text(stream.getvalue());return outputs(attempt,dict(status='PASS'if r.wasSuccessful()and base==35 else'FAIL',baseline_tests=base,tests=r.testsRun,failures=len(r.failures),errors=len(r.errors)))

def audit(task,attempt):
 from ..inita.handlers import audit as inherited_audit
 result=inherited_audit(task,attempt);receipt=[]
 for r in sources(task)['cases']:
  g=r['case'];baseline=task['contour']['baseline_meshes'][g]
  for arm,rec in baseline.items():require(sha256(Path(rec['path']))==rec['sha256'],'SOURCE_SHA',g+'/'+arm)
  receipt.append(dict(case=g,A3_initial=r['resolved013_initial'],baseline=baseline,original_FIT=[v['meta']['id']for v in r['FIT']],original_HOLDOUT=[v['meta']['id']for v in r['HOLDOUT']],new_view_selection=False,cameras_changed=False))
 save_json(attempt/'CONTOUR_SOURCE_LOCK.json',receipt);return outputs(attempt,dict(status='PASS',cases=11,frozen_views=True,original_013=True,GT_read=False))

def prepare(task,row,arm,out):
 inp=out/'inputs'/row['case'];inp.mkdir(parents=True);views=[]
 for key,r in row['static'].items():
  if key=='INITIAL.npz':shutil.copyfile(r['path'],inp/key)
  else:(inp/key).symlink_to(r['path'])
 for vv in row['FIT']+row['HOLDOUT']:
  m=dict(vv['meta']);m['role']='FIT'if vv in row['FIT']else'UPDATE_HOLDOUT';views.append(m);(inp/(m['id']+'.npz')).symlink_to(vv['cache']['path']);(inp/(m['id']+'_SIDES.npz')).symlink_to(vv['sides']['path'])
 save_json(inp/'CASE.json',dict(row['meta'],views=views));save_json(out/'config/ARM.json',dict(tag=arm,loss=arm,budget=task['inita']['training_budget']));save_json(out/'config/CONTOUR.json',task['contour']['pairing']);save_json(out/'config/PROTOCOL.json',dict(depth_disabled=True,reason='A3 and A2D are 2D-only; no HERO depth assets linked'))
 require(not(out/'depth_observations').exists(),'DEPTH_LEAK','No depth loader in 2D objective');return out

def train(task,attempt,smoke=False):
 root=attempt.parents[1];rows=[];selected=[r for r in sources(task)['cases']if not smoke or r['case']in task['contour']['smoke_cases']]
 for row in selected:
  g=row['case'];out=attempt/g;out.mkdir()
  if not smoke and g in task['contour']['smoke_cases']:
   copy_tree(fetch(root,'G1_smoke_train',g+'/CASE_PREDICTIONS_FROZEN.json').parent,out);rows.extend(json.loads((out/'CASE_PREDICTIONS_FROZEN.json').read_text())['records']);continue
  records=[]
  for arm in ['A0','A2']:
   rec=task['contour']['baseline_meshes'][g].get(arm)
   if rec:
    target=out/(arm+'_WORLD.npz');shutil.copyfile(rec['path'],target);records.append(dict(case=g,arm=arm,status='NUMERIC',world_mesh_relative=str(target.relative_to(attempt)),world_sha256=sha256(target),frozen_baseline=True,GT_read=False))
   else:records.append(dict(case=g,arm=arm,status='NOT_EVALUABLE',world_mesh_relative=None,reason='Inherited A2 unavailable: no004; no substituted views'))
  for arm in ['A2D','A3']:
   if row['status']!='READY':records.append(dict(case=g,arm=arm,status='NOT_EVALUABLE',world_mesh_relative=None,reason=row['status']));continue
   ar=prepare(task,row,arm,out/arm);env=dict(os.environ,E4_RUN_DIR=str(ar),CONTOUR_POLICY_FREEZE=str(root/'FREEZE.json'),CONTOUR_POLICY_RUN=str(root));start=time.monotonic()
   with(ar/'TRAIN_STDOUT.txt').open('w')as f:code=subprocess.call([sys.executable,str(ROOT/'tools/research/_contour_train.py'),g],env=env,stdout=f,stderr=subprocess.STDOUT)
   final=ar/'local_results'/g/'FINAL.npz'
   if code or not final.is_file():records.append(dict(case=g,arm=arm,status='FAILED_NAN',reason='Historical optimizer adapter returned '+str(code),world_mesh_relative=None,log=str((ar/'TRAIN_STDOUT.txt').relative_to(attempt))));continue
   target=out/(arm+'_WORLD.npz');shutil.copyfile(final,target);m=dict(np.load(target));initial=np.load(row['resolved013_initial']['path']);require(np.array_equal(m['F'],initial['F'])and np.array_equal(m['F_solid'],initial['F_solid']),'TOPOLOGY','Same actual triangles');info=json.loads((ar/'metrics'/(g+'_RUN.json')).read_text());score=projection_rows(m,row);initialscore=projection_rows(dict(initial),row);save_json(out/(arm+'_PROJECTION.json'),dict(before=initialscore,after=score));records.append(dict(case=g,arm=arm,status='NUMERIC',world_mesh_relative=str(target.relative_to(attempt)),world_sha256=sha256(target),training=info,projection=score,initial_projection=initialscore,depth_loss=False,GT_read=False,seconds=time.monotonic()-start));print('CONTOUR_BODY',g,arm,info['accepted'],info['maximum_displacement_mm'],flush=True)
  save_json(out/'CASE_PREDICTIONS_FROZEN.json',dict(records=records,FIT_only=True,GT_read=False));rows.extend(records)
 save_json(attempt/'BODY_PREDICTIONS_FROZEN.json',dict(records=rows,initialization='EXACT_013_MESH',GT_read=False,no_HERO_training_depth=True));return outputs(attempt,dict(status='PASS',records=len(rows),numeric=sum(r['status']=='NUMERIC'for r in rows),failures_retained=True))

def predict(task,attempt,smoke=False):
 root=attempt.parents[1];stage='G1_smoke_train'if smoke else'G1_all_train';by={(r['case'],r['arm']):r for r in json.loads(fetch(root,stage,'BODY_PREDICTIONS_FROZEN.json').read_text())['records']};cohort=task['contour']['smoke_cases']if smoke else task['inita']['cases'];cfg=oldhero.parameters(task);cfg['contour']=task['contour']['pairing'];rows=[]
 for group in sources(task)['real_groups']:
  g=group['group']
  if g not in cohort:continue
  out=attempt/g;out.mkdir()
  if not smoke and g in task['contour']['smoke_cases']:
   copy_tree(fetch(root,'G2_smoke_hero',g+'/HERO_PREDICTIONS_FROZEN.json').parent,out);rows.append(json.loads((out/'HERO_PREDICTIONS_FROZEN.json').read_text()));continue
  fit=[v for v in group['views']if v['role']=='FIT'];record=dict(case=g,FIT_views=len(fit),videos=sorted({v['video']for v in fit}),records=[],absolute_accuracy='NOT_EVALUABLE_NO_INDEPENDENT_GT')
  if len(fit)<2:
   record.update(status='NOT_EVALUABLE',reason='Inherited interface has no >=2 source-bound complete HERO Meshes; raw inventories retained');save_json(out/'HERO_PREDICTIONS_FROZEN.json',record);rows.append(record);continue
  for r in group['views']:validate_view(r)
  data=[load_view(r,task['inita']['HERO_frame_prior_deg_mm'])for r in fit];fits={d['id']:d['fit']for d in data};ring=dict(np.load(group['assets']['ring']['path']))
  for d in data:np.savez_compressed(out/(d['id']+'_ORIGINAL.npz'),V=d['V'],F=d['F'])
  for method in task['contour']['HERO_methods']:
   arm='A3'if method in ['H2','H4']else'A2';mo=out/method;mo.mkdir();brec=by.get((g,arm),{});start=time.monotonic()
   if brec.get('status')!='NUMERIC':rr=dict(method=method,status='NOT_EVALUABLE',reason='Body '+arm+' unavailable')
   else:
    bpath=fetch(root,stage,brec['world_mesh_relative']);digest=sha256(bpath);body=dict(np.load(bpath));body['ring']=ring;provider=meshhero.mapping_constraints if method in ['H3','H4']else oldhero.mapping_constraints
    try:
     if method=='M0':X=[np.eye(4)for _ in data];details=dict(optimizer_success=True)
     elif method=='ICP':X,details=registration.icp(cfg,data)
     else:X,details,_=meshhero.optimizer(provider)(cfg,data,body,fits,True,.5,None)
     final=provider(cfg,data,body,fits,X,None);pairs=registration.pair_constraints(cfg,data,X,registration.graph(data));diagnostic=dict(body_rate=sum(a['accepted_N']for a in final)/max(1,sum(a['target_N']for a in final)),pair_rate=sum(a['accepted_N']for a in pairs)/max(1,sum(a['target_N']for a in pairs)),per_view=[{k:a[k]for k in ['i','target_N','accepted_N','contact_unknown_N']}for a in final]);motions=[]
     for d,T,mapping in zip(data,X,final):
      V=transform(d['V'],T);F=d['F'];edges=F[:,[0,1]];preserve=float(abs(np.linalg.norm(V[edges[:,0]]-V[edges[:,1]],axis=1)-np.linalg.norm(d['V'][edges[:,0]]-d['V'][edges[:,1]],axis=1)).max());require(preserve<1e-8,'MESH_RIGIDITY',d['id']);np.savez_compressed(mo/(d['id']+'.npz'),V=V,F=F);np.savez_compressed(mo/(d['id']+'_CANDIDATES.npz'),**{k:v for k,v in mapping.items()if isinstance(v,np.ndarray)});motions.append(dict(id=d['id'],maximum_motion_mm=float(np.linalg.norm(V-d['V'],axis=1).max()),mean_motion_mm=float(np.linalg.norm(V-d['V'],axis=1).mean()),edge_change_max_mm=preserve))
     rr=dict(method=method,status='NUMERIC',body_arm=arm,body_world_sha256=digest,corrections={d['id']:T.tolist()for d,T in zip(data,X)},details=details,correspondence=diagnostic,motions=motions,GT_aligned_Body_used=False)
    except PolicyError:raise
    except(ValueError,RuntimeError,np.linalg.LinAlgError)as e:rr=dict(method=method,status='FAILED_NAN',reason=str(e))
    require(sha256(bpath)==digest,'BODY_IMMUTABLE',g)
   rr['seconds']=time.monotonic()-start;record['records'].append(rr);save_json(mo/'PREDICTION.json',rr);print('CONTOUR_HERO',g,method,rr['status'],flush=True)
  record['status']='NUMERIC';save_json(out/'HERO_PREDICTIONS_FROZEN.json',record);rows.append(record)
 save_json(attempt/'ALL_HERO_PREDICTIONS_FROZEN.json',dict(groups=rows,Body_frozen=True,camera_optimized=False,GT_read=False));return outputs(attempt,dict(status='PASS',groups=len(rows),numeric_groups=sum(r['status']=='NUMERIC'for r in rows)))

def evaluate(task,attempt,smoke=False):
 from ..inita.evaluate import shape_evaluate
 body=shape_evaluate(task,attempt,smoke);hero=oldhero.evaluate(task,attempt,smoke);pairs=[];failures=[]
 for g in task['inita']['cases']:
  b={r['arm']:r for r in body if r['case']==g}
  if not b:continue
  for r in b.values():
   if r['status']!='NUMERIC'or r['IoU_3D']is None:failures.append(dict(case=g,arm=r['arm'],category='incomplete_evaluation'if r['status']!='NUMERIC'else'scientific_negative',reason=r.get('reason',r['IoU_3D_status']),evidence='BODY_SHAPE_METRICS.json'))
  for reference in ['A2','A2D']:
   if b.get('A3',{}).get('status')==b.get(reference,{}).get('status')=='NUMERIC':
    p=dict(case=g,reference=reference,conditional_IoU_delta=b['A3']['conditional_occupancy_IoU']-b[reference]['conditional_occupancy_IoU'],Chamfer_delta_mm=b['A3']['Chamfer_MAE_mm']-b[reference]['Chamfer_MAE_mm'],strict_IoU_delta=b['A3']['IoU_3D']-b[reference]['IoU_3D']if b['A3']['IoU_3D']is not None and b[reference]['IoU_3D']is not None else None)
    for role in ['FIT','HOLDOUT']:
     for video in ['004','005']:
      def mean(r):
       z=[v['IoU']for v in r['projection']if v['role']==role and v['video']==video];return float(np.mean(z))if z else None
      x,y=mean(b['A3']),mean(b[reference]);p[role+'_'+video+'_IoU_delta']=x-y if x is not None and y is not None else None
    pairs.append(p)
 for g in hero:
  if g['status']!='NUMERIC':failures.append(dict(case=g['case'],category='incomplete_evaluation',reason=g['reason'],evidence='HERO_METRICS.json'))
  else:
   for r in g['methods']:
    if r['status']!='NUMERIC':failures.append(dict(case=g['case'],method=r['method'],category='scientific_negative',reason=r.get('reason'),evidence='HERO_METRICS.json'))
 save_json(attempt/'PAIRED_COMPARISONS.json',dict(body=pairs,denominator=11,no_GT_selection=True));save_json(attempt/'FAILURE_LEDGER.json',dict(failures=failures,scientific_failure_not_gate=True));return outputs(attempt,dict(status='PASS',body_rows=len(body),hero_groups=len(hero),GT_read_by_evaluator=True))

def dispatch(stage,task,attempt):
 if stage=='contour_regression':return regression(attempt)
 if stage=='G0_sources':return audit(task,attempt)
 for prefix,fn in [('G1_',train),('G2_',predict),('G3_',evaluate)]:
  if stage.startswith(prefix):return fn(task,attempt,'smoke'in stage)
 if stage.startswith('G4_'):
  from .visualize import run
  return run(task,attempt,'smoke'in stage)
 raise ValueError(stage)
