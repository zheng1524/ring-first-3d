"""Schema 7: exact 015/013 lineage, isolated GT copies, no per-frame camera fit."""
import copy,json
from pathlib import Path
from .contracts import ROOT,MODULES,STAGES,require,fields,validate_v1,verify_task,freeze_identity
from ..contracts.identities import sha256
TASK_ID='TASK-E4-MULTIVIDEO-INIT-A-HERO-ALIGN-001'
BASELINE='b1f8fb433f37677b93ac52ac5719afd902c1fa11';LEGACY='905e2a9b3615a5f429553837a05e5d53826cef03'
INIT_STAGES=('preflight','contracts','inita_regression','G0_sources','G1_smoke_train','G2_smoke_hero','G3_smoke_evaluate','G4_smoke_visualize','G1_all_train','G2_all_hero','G3_all_evaluate','G4_visualize','artifacts')
MODULE_FILES={'IA01':'train.py','IA02':'hero.py','IA03':'evaluate.py','IA04':'visualize.py','IA05':'handlers.py'}
def legacy(task):
 t=copy.deepcopy({k:v for k,v in task.items()if k!='inita'});t['schema']=1;t['modules']=[m for m in t['modules']if m in MODULES];t['authorization']['stages']=list(STAGES);t['acceptance']['required_stages']=list(STAGES);t['split']['GT']=[];t['split']['access']='verification_only_no_GT';return t

def validate(task,path):
 fields(task,'schema task_id goal modules variables inputs split authorization acceptance budget stop output_root inita','Init-A TASK');require(task['schema']==7 and task['task_id']==TASK_ID,'SCIENCE_SCOPE','Registered Init-A task only');b=validate_v1(legacy(task),path);c=task['inita']
 require(set(task['modules'])==set(MODULES)|set(MODULE_FILES),'MODULE','Existing harness and explicit Init-A adapters')
 require(c['legacy_commit']==LEGACY and c['parent_commit']==BASELINE and c['initialization']=='EXACT_013_INPUT_MESH_V_F_SOLID_CAP','INITIALIZATION_LINEAGE','No E1/E2/Init-B/Init-C substitute')
 require(c['arms']==['A0','A1','A2']and c['training_budget']==dict(max_proposals=80,max_accepted=40,consecutive_rejection_stop=30),'FROZEN_PROTOCOL','Exact historical budget, final accepted Mesh, no checkpoint selection')
 require(c['smoke_cases']==['G01','G03','G05']and len(c['cases'])==11 and len(set(c['cases']))==11,'DATA_ISOLATION','All eleven physical groups')
 require(c['GT_alignment_scope']=='EVALUATION_COPIES_ONLY_SCALE1'and c['HERO_uses_GT_aligned_Body']is False and c['train_uses_GT']is False,'GT_LEAK','GT cannot change world predictions')
 require(c['camera_parameters']=='004_FIXED; optionally_one_shared_005_SE3; no_per_frame'and c['shared_trigger']==dict(delta_FIT_IoU=.10,absolute_005_FIT_IoU=.5),'CAMERA_SCOPE','GT-free trigger, separately reported A2S')
 require(task['authorization']['stages']==list(INIT_STAGES)and task['acceptance']['required_stages']==list(INIT_STAGES),'AUTHORIZATION','Both smoke parts before full matrix')
 require(task['split']['access']=='inita_train_hero_evaluation_isolation'and task['split']['GT']==['independent_shape_evaluator_only'],'GT_LEAK','Explicit isolation')
 for key in ['inputs','variables','output_root']:task[key]=b[key]
 task['split']['manifest']=b['split']['manifest'];freeze=path.with_name('TASK_FREEZE.json')
 if freeze.exists():require(sha256(path)==json.loads(freeze.read_text())['task_sha256'],'TASK_DRIFT','Do not edit frozen protocol')
 return task

def verify(task):
 c=task['inita'];source=json.loads(Path(c['assets']['sources']['path']).read_text());lock=json.loads(Path(c['assets']['code_lock']['path']).read_text())
 for rec in list(c['assets'].values())+lock['files']+source['frozen_assets']:
  p=Path(rec['path']);require(p.is_file()and sha256(p)==rec['sha256'],'SOURCE_SHA',str(p))
 require(lock['commit']==LEGACY,'SOURCE_SHA','Legacy commit identity')
 info=verify_task(legacy(task));contracts=dict(info['module_contracts'])
 for mid,file in MODULE_FILES.items():contracts[mid]=dict(path='inita/'+file,sha256=sha256(ROOT/'src/ring_first_3d/inita'/file))
 return freeze_identity(task,contracts,info['verified_assets']+len(lock['files'])+len(source['frozen_assets']))

def permissions(task,stage,root):
 require(stage in INIT_STAGES,'UNAUTHORIZED_STAGE',stage)
 role='evaluator'if stage.startswith(('G3_','G4_'))else'predictor'if stage.startswith(('G1_','G2_'))else'verification'
 source=json.loads(Path(task['inita']['assets']['sources']['path']).read_text());gt=[Path(r['GT']['path']).resolve()for r in source['cases']if r.get('GT')]+[Path(task['inita']['assets']['GT_metadata']['path']).resolve()]
 denied=[]
 if role=='predictor':
  denied=[s/'visualization'for s in (Path(root)/'snapshots').glob('*')];denied+=[Path(r['legacy_aligned_directory'])for r in source['cases']]
 return dict(role=role,allow_GT=role=='evaluator',gt_paths=gt,run_root=Path(root).resolve(),stage=stage,denied_read_prefixes=denied)
