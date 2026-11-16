"""Additive schema 6: inherited algorithms, fixed variance stress and real pilots."""
import copy,json,subprocess
from pathlib import Path
from .contracts import ROOT,MODULES,STAGES,fields,require,validate_v1,verify_task,freeze_identity
from .fusion_contracts import MODULE_FILES,REUSED,legacy,CONDITIONS as BASE
from ..contracts.identities import sha256
TASK_ID='TASK-E4-MULTISURFACE-STRESS-AND-REAL-PILOT-001'
BASELINE='b16a6f813ecf9214958cae3b88d624725a0fa484'
STRESS_STAGES=('preflight','contracts','stress_regression','G0_real_audit','G0_views_noise','G1_body','G2_candidates','G3_smoke_predict','G3_smoke_evaluate','G3_all_predict','G4_fusion_predict','G4_evaluate','real_predict','real_evaluate','G4_visualize','artifacts')
STRESS_MODULES={'SR01':'handlers.py','SR02':'real.py','SR03':'evaluate.py','SR04':'visualize.py'}
CONDITIONS={'C0':copy.deepcopy(BASE['C0']),'C4':copy.deepcopy(BASE['C4']),'C6':dict(bias={'004':'A','005':'B'},sigma={'004':[1.2,.35],'005':[1.2,.35]}),'C7':dict(bias={'004':'A','005':'B'},sigma={'004':[2.,.60],'005':[2.,.60]})}
CTF=dict(eligible_conditions=['C6','C7'],trigger_body_acceptance_below=.25,trigger_pair_acceptance_below=.5,levels=[dict(candidate_reject_distance_mm=5.,pair_max_distance_mm=3.),dict(candidate_reject_distance_mm=3.5,pair_max_distance_mm=2.),dict(candidate_reject_distance_mm=2.5,pair_max_distance_mm=1.5)],outer_iterations_per_level=1,prior='Original optimizer prior restarted at each explicitly separate level; accumulated surface transform, never camera output')

def legacy_task(task):return legacy({k:v for k,v in task.items()if k!='stress'})

def validate(task,path):
 fields(task,'schema task_id goal modules variables inputs split authorization acceptance budget stop output_root fusion stress','stress TASK')
 require(task['schema']==6 and task['task_id']==TASK_ID,'SCIENCE_SCOPE','Registered stress task only')
 b=validate_v1(legacy_task(task),path);f=task['fusion'];s=task['stress']
 require(set(task['modules'])==set(MODULES)|set(REUSED)|set(MODULE_FILES)|set(STRESS_MODULES),'MODULE','Explicit reused and adapter contracts')
 require(task['authorization']['stages']==list(STRESS_STAGES)and task['acceptance']['required_stages']==list(STRESS_STAGES),'AUTHORIZATION','Audit, smoke, freeze and independent evaluation gates required')
 require(f['condition_order']==list(CONDITIONS)and f['conditions']==CONDITIONS,'INJECTION_PROTOCOL','Only C0/C4/C6/C7 variances')
 require(s['baseline_commit']==BASELINE and s['ctf']==CTF,'FROZEN_PROTOCOL','No silent threshold change')
 require(task['split']['access']=='multisurface_generator_predictor_evaluator' and task['split']['GT']==['generator_and_postfreeze_evaluation_only'],'GT_LEAK','No GT predictor access')
 require(f['camera_optimization']is False and f['body_frozen']is True and f['GT_selects_predictor']is False and f['physical_Ring_fixed']is True,'GT_LEAK','Frozen geometry and cameras')
 require(s['real_groups']==['G01','G03','G05']and s['real_frame_prior_sigma_deg_mm']==[.3,.1]and s['real_max_FIT_per_video']==2 and s['real_HOLDOUT_per_video']==1,'FROZEN_PROTOCOL','Small real smoke, explicit heuristic prior')
 for k in ['inputs','variables','output_root']:task[k]=b[k]
 task['split']['manifest']=b['split']['manifest']
 for key,rec in s['assets'].items():fields(rec,'path sha256','stress source');rec['path']=str((path.parent/rec['path']).resolve())
 # Every scientific setting except the declared variance/matrix/figure changes is exact baseline.
 parent=json.loads(Path(s['assets']['parent_task_json']['path']).read_text())['fusion']
 mutable={'conditions','condition_order','tolerance_ablation_mm','main_figure_condition','assets','parent_run'}
 require({k:v for k,v in f.items()if k not in mutable}=={k:v for k,v in parent.items()if k not in mutable},'FROZEN_PROTOCOL','Inherited scientific parameters must stay exact')
 require(f['tolerance_ablation_mm']==[] and f['main_figure_condition']=='C7','FROZEN_PROTOCOL','No new tolerance search')
 freeze=path.with_name('TASK_FREEZE.json')
 if freeze.exists():require(sha256(path)==json.loads(freeze.read_text())['task_sha256'],'TASK_DRIFT','Do not edit frozen task')
 return task

def verify(task):
 s=task['stress'];assets=list(s['assets'].values())+list(task['fusion']['assets'].values())
 for rec in assets:
  p=Path(rec['path']);require(p.is_file()and sha256(p)==rec['sha256'],'SOURCE_SHA',str(p))
 # Inherited algorithm files cannot be adapted silently in this profile.
 locked=json.loads(Path(s['assets']['algorithm_lock']['path']).read_text())
 for r in locked['files']:
  require(sha256(ROOT/r['path'])==r['sha256'],'ALGORITHM_DRIFT',r['path'])
 manifest=json.loads(Path(s['assets']['real_manifest']['path']).read_text())
 for group in manifest['groups']:
  for row in group['views']:
   for rec in row['assets'].values():
    if rec.get('sha256'):
     p=Path(rec['path']);require(p.is_file()and sha256(p)==rec['sha256'],'SOURCE_SHA',str(p))
  for rec in group['assets'].values():
   p=Path(rec['path']);require(p.is_file()and sha256(p)==rec['sha256'],'SOURCE_SHA',str(p))
 info=verify_task(legacy_task(task));contracts=dict(info['module_contracts'])
 for mid,file in MODULE_FILES.items():contracts[mid]=dict(path='multisurface/'+file,sha256=sha256(ROOT/'src/ring_first_3d/multisurface'/file))
 for mid,file in STRESS_MODULES.items():contracts[mid]=dict(path='stress/'+file,sha256=sha256(ROOT/'src/ring_first_3d/stress'/file))
 return freeze_identity(task,contracts,info['verified_assets']+len(assets))

def permissions(task,stage,root):
 require(stage in STRESS_STAGES,'UNAUTHORIZED_STAGE',stage)
 role='generator'if stage=='G0_views_noise'else'evaluator'if stage in {'G3_smoke_evaluate','G4_evaluate','real_evaluate','G4_visualize'}else'predictor'if stage in {'G1_body','G2_candidates','G3_smoke_predict','G3_all_predict','G4_fusion_predict','real_predict'}else'verification'
 gt=[Path(task['fusion']['assets']['virtual_gt']['path']).resolve()]
 denied=[]
 if role=='predictor':
  denied=[Path(task['stress']['parent_multisurface_run']).resolve(),Path(task['fusion']['parent_run']).resolve(),Path(task['fusion']['assets']['source_manifest']['path']).resolve()]
  denied.extend(s/'visualization'for s in (Path(root)/'snapshots').glob('*'))
 return dict(role=role,allow_GT=role in {'generator','evaluator'},gt_paths=gt,run_root=Path(root).resolve(),stage=stage,denied_read_prefixes=denied)
