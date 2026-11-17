"""Schema 8: frozen cameras/views/optimizer; explicit 2D constraints and real Mesh HERO."""
import copy,json
from pathlib import Path
from .contracts import ROOT,MODULES,STAGES,require,fields,validate_v1,verify_task,freeze_identity
from ..contracts.identities import sha256
TASK_ID='TASK-E4-2D-CONTOUR-GUIDED-INIT-A-HERO-001'
BASELINE='13a73f0422be5e5b0e221df4a41407b3b6d6d52c';LEGACY='905e2a9b3615a5f429553837a05e5d53826cef03'
CONTOUR_STAGES=('preflight','contracts','contour_regression','G0_sources','G1_smoke_train','G2_smoke_hero','G3_smoke_evaluate','G4_smoke_visualize','G1_all_train','G2_all_hero','G3_all_evaluate','G4_visualize','artifacts')
MODULE_FILES={'CG01':'correspondence.py','CG02':'objective.py','CG03':'hero.py','CG04':'experiment.py','CG05':'visualize.py'}
def legacy(t):
 d=copy.deepcopy({k:v for k,v in t.items()if k not in ['inita','contour']});d.update(schema=1,modules=list(MODULES));d['authorization']['stages']=list(STAGES);d['acceptance']['required_stages']=list(STAGES);d['split'].update(GT=[],access='verification_only_no_GT');return d

def validate(t,path):
 fields(t,'schema task_id goal modules variables inputs split authorization acceptance budget stop output_root inita contour','Contour TASK');require(t['schema']==8 and t['task_id']==TASK_ID,'SCIENCE_SCOPE',TASK_ID);b=validate_v1(legacy(t),path);c=t['contour'];i=t['inita']
 require(set(t['modules'])==set(MODULES)|set(MODULE_FILES),'MODULE','Explicit contour adapters plus original harness')
 require(c['parent_commit']==BASELINE and i['legacy_commit']==LEGACY and i['initialization']=='EXACT_013_INPUT_MESH_V_F_SOLID_CAP','INITIALIZATION_LINEAGE','Same 013, not trained A2')
 require(c['Body_arms']==['A0','A2','A2D','A3']and c['HERO_methods']==['M0','H1','H2','H3','H4','ICP'],'FROZEN_PROTOCOL','Separate depth-free historical and explicit contour controls')
 require(i['training_budget']==dict(max_proposals=80,max_accepted=40,consecutive_rejection_stop=30),'FROZEN_PROTOCOL','No optimizer budget change')
 require(c['camera_parameters']=='ALL_FIXED'and c['A3_depth_loss']is False and c['HERO_updates_Body']is False,'CAMERA_SCOPE','Only Mesh vertices then surface positions')
 require(c['smoke_cases']==['G01','G05','G11']and len(i['cases'])==11,'DATA_ISOLATION','Original eleven groups')
 require(c['pairing']==dict(max_distance_px=40.,mutual_radius_px=4.,max_tangent_px=8.,normal_cos_min=0.7071067811865476),'FROZEN_PROTOCOL','Predeclared native-pixel matching thresholds')
 require(t['authorization']['stages']==list(CONTOUR_STAGES)and t['acceptance']['required_stages']==list(CONTOUR_STAGES),'AUTHORIZATION','Smoke precedes full cohort')
 require(i['GT_alignment_scope']=='EVALUATION_COPIES_ONLY_SCALE1'and not i['HERO_uses_GT_aligned_Body']and not i['train_uses_GT'],'GT_LEAK','GT evaluation copies only')
 for key in ['inputs','variables','output_root']:t[key]=b[key]
 freeze=path.with_name('TASK_FREEZE.json')
 if freeze.exists():require(sha256(path)==json.loads(freeze.read_text())['task_sha256'],'TASK_DRIFT','Do not overwrite frozen TASK')
 return t

def verify(t):
 i=t['inita'];c=t['contour']
 for key in ['sources','code_lock']:
  r=i['assets'][key];p=Path(r['path']);require(p.is_file()and sha256(p)==r['sha256'],'SOURCE_SHA',str(p))
 s=json.loads(Path(i['assets']['sources']['path']).read_text());lock=json.loads(Path(i['assets']['code_lock']['path']).read_text())
 for r in list(i['assets'].values())+lock['files']+s['frozen_assets']+c['baseline_assets']:
  p=Path(r['path']);require(p.is_file()and sha256(p)==r['sha256'],'SOURCE_SHA',str(p))
 info=verify_task(legacy(t));contracts=dict(info['module_contracts'])
 for mid,name in MODULE_FILES.items():contracts[mid]=dict(path='contour_guided/'+name,sha256=sha256(ROOT/'src/ring_first_3d/contour_guided'/name))
 return freeze_identity(t,contracts,info['verified_assets']+len(s['frozen_assets'])+len(c['baseline_assets']))

def permissions(t,stage,root):
 require(stage in CONTOUR_STAGES,'UNAUTHORIZED_STAGE',stage);role='evaluator'if stage.startswith(('G3_','G4_'))else'predictor'if stage.startswith(('G1_','G2_'))else'verification';s=json.loads(Path(t['inita']['assets']['sources']['path']).read_text());gt=[Path(r['GT']['path']).resolve()for r in s['cases']if r.get('GT')]+[Path(t['inita']['assets']['GT_metadata']['path']).resolve()];denied=[]
 if role=='predictor':
  denied=[p/'visualization'for p in (Path(root)/'snapshots').glob('*')]+[Path(r['legacy_aligned_directory'])for r in s['cases']]
  if stage.startswith('G1_'):denied +=[Path(r['path'])for case in s['cases']for r in case['depth'].values()]
 return dict(stage=stage,role=role,allow_GT=role=='evaluator',gt_paths=gt,run_root=Path(root).resolve(),denied_read_prefixes=denied)
