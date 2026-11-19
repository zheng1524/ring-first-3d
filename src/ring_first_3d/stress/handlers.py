"""Small execution adapters; inherited scientific algorithms are not edited."""
import copy,io,json,time,unittest
import numpy as np
from ..policy.contracts import ROOT,require,PolicyError
from ..synthetic.io import fetch,outputs,save_json
from ..contracts.identities import sha256

def regression(attempt):
 loader=unittest.defaultTestLoader;base=unittest.TestSuite([loader.discover(str(ROOT/'tests'),pattern=p)for p in ['test_harness_contracts.py','test_policy_bootstrap.py']]);n=base.countTestCases()
 suite=unittest.TestSuite([base]+[loader.discover(str(ROOT/'tests'),pattern=p)for p in ['test_synthetic_correspondence.py','test_dualvideo_gate.py','test_sim_rev1.py','test_multisurface.py','test_stress.py']]);stream=io.StringIO();r=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite);(attempt/'regression_log.txt').write_text(stream.getvalue());return outputs(attempt,dict(status='PASS'if r.wasSuccessful()and n==35 else'FAIL',baseline_tests=n,tests=r.testsRun,failures=len(r.failures),errors=len(r.errors)))

def diagnostic(task,data,body,fits,X,ns):
 from ..multisurface.registration import mapping_constraints,pair_constraints,graph
 maps=mapping_constraints(task,data,body,fits,X,ns);pairs=pair_constraints(task,data,X,graph(data))
 return maps,dict(body=[{k:a[k]for k in ['i','target_N','accepted_N','contact_unknown_N']}for a in maps],pairs=[{k:a[k]for k in ['i','j','target_N','accepted_N']}for a in pairs],body_rate=sum(a['accepted_N']for a in maps)/max(1,sum(a['target_N']for a in maps)),pair_rate=sum(a['accepted_N']for a in pairs)/max(1,sum(a['target_N']for a in pairs)))

def ctf_eligible(task,diag):
 c=task['stress']['ctf'];return any(a['accepted_N']/max(1,a['target_N'])<c['trigger_body_acceptance_below']for a in diag['body'])or diag['pair_rate']<c['trigger_pair_acceptance_below']

def coarse_to_fine(task,data,body,fits,ns):
 from ..multisurface.registration import optimize
 from ..multisurface.geometry import transform
 X=[np.eye(4)for _ in data];traces=[];maps=[]
 for lev in task['stress']['ctf']['levels']:
  t=copy.deepcopy(task);t['fusion'].update(lev,registration_outer_iterations=task['stress']['ctf']['outer_iterations_per_level'])
  chart=[dict(d,V=transform(d['V'],T),C=T@d['C'],normals=d['normals']@T[:3,:3].T)for d,T in zip(data,X)]
  delta,details,maps=optimize(t,chart,body,fits,True,t['fusion']['tolerance_mm'],ns);X=[a@b for a,b in zip(delta,X)];traces.append(dict(thresholds=lev,details=details))
 return X,dict(optimizer_success=all(t['details']['optimizer_success']for t in traces),ctf_levels=traces,independent_ablation=True,prior_semantics=task['stress']['ctf']['prior'],camera_optimization=False),maps

def predict(task,attempt,smoke=False):
 from ..multisurface.registration import model_namespace,load_case,optimize,icp
 from ..multisurface.geometry import transform
 root=attempt.parents[1];cfg=task['fusion'];ns=model_namespace(task);fits={r['id']:r for r in json.loads(fetch(root,'G1_body','IMAGE_FITS.json').read_text())};rows=[];elig=[];cache={}
 for cond in task['stress']['smoke_conditions']if smoke else cfg['condition_order']:
  data=load_case(root,cond)
  for arm in ['E1']if smoke else cfg['body_arms']:
   body=dict(np.load(fetch(root,'G1_body',arm+'_BODY.npz')));digest=sha256(fetch(root,'G1_body',arm+'_BODY.npz'));initial,diag0=diagnostic(task,data,body,fits,[np.eye(4)for _ in data],ns)
   trigger=cond in task['stress']['ctf']['eligible_conditions']and ctf_eligible(task,diag0);elig.append(dict(condition=cond,arm=arm,triggered=trigger,initial_correspondence=diag0,GT_used=False))
   variants=list(cfg['methods'])+(['BODY_HIER_CTF']if trigger and not smoke else[])
   for method in variants:
    key=f'{cond}__{arm}__{method}__tol0.5';out=attempt/key;out.mkdir();started=time.monotonic()
    try:
     if method=='M0':X=[np.eye(4)for _ in data];details=dict(optimizer_success=True)
     elif method=='ICP':
      if cond not in cache:cache[cond]=icp(task,data)
      X,details=cache[cond]
     elif method=='BODY_HIER_CTF':X,details,_=coarse_to_fine(task,data,body,fits,ns)
     else:X,details,_=optimize(task,data,body,fits,method=='BODY_HIER',cfg['tolerance_mm'],ns)
     final,diag1=diagnostic(task,data,body,fits,X,ns);matrices={};motions={}
     for i,d in enumerate(data):
      V=transform(d['V'],X[i]);F=d['F'];e=F[:,[0,1]];require(np.max(abs(np.linalg.norm(V[e[:,0]]-V[e[:,1]],axis=1)-np.linalg.norm(d['V'][e[:,0]]-d['V'][e[:,1]],axis=1)))<1e-8,'MESH_RIGIDITY',d['id'])
      np.savez_compressed(out/(d['id']+'.npz'),V=V,F=F);matrices[d['id']]=X[i].tolist();motions[d['id']]=float(np.linalg.norm(V-d['V'],axis=1).max())
      np.savez_compressed(out/(d['id']+'_FINAL_CANDIDATES.npz'),**{k:v for k,v in final[i].items()if isinstance(v,np.ndarray)})
     rec=dict(key=key,condition=cond,arm=arm,method=method,kind='COARSE_TO_FINE_ABLATION'if method.endswith('CTF')else'MAIN',tolerance_mm=.5,status='NUMERIC',surface_corrections=matrices,maximum_surface_motion_mm=motions,details=details,correspondence_before=diag0,correspondence_after=diag1,body_sha256=digest,Body_frozen=True,camera_optimization=False,vertices_replaced_by_Body=False)
    except PolicyError:raise
    except(ValueError,RuntimeError,np.linalg.LinAlgError)as e:rec=dict(key=key,condition=cond,arm=arm,method=method,kind='MAIN',tolerance_mm=.5,status='FAILED_NAN',reason=str(e),surface_corrections=None)
    rec['seconds']=time.monotonic()-started;save_json(out/'PREDICTION.json',rec);rows.append(rec);print('STRESS',key,rec['status'],flush=True)
   require(sha256(fetch(root,'G1_body',arm+'_BODY.npz'))==digest,'BODY_IMMUTABLE',arm)
 save_json(attempt/'CTF_ELIGIBILITY.json',elig);save_json(attempt/'PREDICTIONS_FROZEN.json',dict(rows=rows,GT_read_by_predictor=False,smoke=smoke,history_measurement_fallback=0))
 return outputs(attempt,dict(status='PASS',models=len(rows),numeric=sum(r['status']=='NUMERIC'for r in rows),GT_read_by_predictor=False))

def smoke(task,attempt):
 from ..multisurface.evaluate import check_injection,registration_metrics
 root=attempt.parents[1];checks,truth=check_injection(task,root,task['stress']['smoke_conditions']);rows,pred=registration_metrics(task,root,'G3_smoke_predict')
 require(all(f['actual_vertex_displacement_max_mm']==0 for v in truth['C0'].values()for f in v['frames']),'C0_GATE','C0 has no injection')
 require(max(f['actual_vertex_displacement_max_mm']for v in truth['C6'].values()for f in v['frames'])>1,'SMOKE_INJECTION','Actual high-variance Mesh layers')
 require(any(r['condition']=='C6'and r['method']=='BODY_HIER'and r['status']=='NUMERIC'and max(r['maximum_surface_motion_mm'].values())>.01 for r in pred['rows']),'SMOKE_OPTIMIZATION','Full meshes actually move')
 save_json(attempt/'SMOKE_METRICS.json',dict(rows=rows,injection_checks=checks,actual_mesh_motion=True,accuracy_is_not_gate=True));return outputs(attempt,dict(status='PASS',conditions=task['stress']['smoke_conditions'],actual_mesh_motion=True))

def dispatch(stage,task,attempt):
 if stage=='stress_regression':return regression(attempt)
 if stage in {'G0_real_audit','real_predict','real_evaluate'}:
  from .real import audit,predict as real_predict,evaluate
  return {'G0_real_audit':audit,'real_predict':real_predict,'real_evaluate':evaluate}[stage](task,attempt)
 if stage in {'G0_views_noise','G1_body'}:
  from ..multisurface.scene import generate,body
  return (generate if stage=='G0_views_noise'else body)(task,attempt)
 if stage=='G2_candidates':
  from ..multisurface.registration import candidates_stage
  return candidates_stage(task,attempt)
 if stage in {'G3_smoke_predict','G3_all_predict'}:return predict(task,attempt,stage=='G3_smoke_predict')
 if stage=='G3_smoke_evaluate':return smoke(task,attempt)
 if stage=='G4_fusion_predict':
  from ..multisurface.fusion import run
  return run(task,attempt)
 if stage=='G4_evaluate':
  from .evaluate import run
  return run(task,attempt)
 if stage=='G4_visualize':
  from .visualize import run
  return run(task,attempt)
 raise ValueError('Unregistered stress stage '+stage)
