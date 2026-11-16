"""Fail-closed authenticity gate; downstream work is conditional on genuine scene proof."""
import copy,json
from pathlib import Path
from .contracts import ROOT,STAGES,MODULES,require,fields,validate_v1,verify_task,freeze_identity
from ..contracts.identities import sha256

TASK_ID='TASK-E4-G01-DUALVIDEO-BODY-ANCHORED-REGISTRATION-001'
DUAL_STAGES=('preflight','contracts','dualvideo_regression','G0_scene_audit','G1_initialize','G2_mapping_predict','G2_mapping_evaluate','G3_register','G4_evaluate','artifacts')


def legacy(task):
    base=copy.deepcopy({k:v for k,v in task.items()if k!='dualvideo'})
    base['schema']=1;base['modules']=[m for m in base['modules']if m in MODULES]
    base['split']['GT']=[];base['split']['access']='verification_only_no_GT'
    base['authorization']['stages']=list(STAGES);base['acceptance']['required_stages']=list(STAGES)
    return base


def validate(task,path):
    fields(task,'schema task_id goal modules variables inputs split authorization acceptance budget stop output_root dualvideo','dual-video TASK')
    require(type(task['schema'])is int and task['task_id']==TASK_ID,'SCIENCE_SCOPE','Only approved dual-video task')
    base=validate_v1(legacy(task),path)
    require(set(task['modules'])==set(MODULES)|{'DV01'},'MODULE','Existing modules + scene gate')
    require(task['authorization']['stages']==list(DUAL_STAGES),'AUTHORIZATION','Exact ordered gated task required')
    require(task['acceptance']['required_stages']==list(DUAL_STAGES),'ACCEPTANCE','Cannot skip scene gate')
    require(task['split']['access']=='dualvideo_scene_gate_then_generator_predictor_evaluator','GT_LEAK','Explicit roles')
    cfg=task['dualvideo']
    fields(cfg,'assets condition_order conditions frame_policy world_injection local_injection Ring_to_Body_policy body_initialization registration gates evaluation source_frame_count','dualvideo')
    expected={'S0':(None,'none',0.,0.),'S1':('004','video_world',2.,.5),'S2':('004','video_world',3.,.3),'S3':('004','camera_to_ring',2.,.5),'S4':('005','camera_to_ring',3.,.3)}
    require(cfg['condition_order']==list(expected),'INJECTION_PROTOCOL','S0–S4 frozen')
    require(set(cfg['conditions'])==set(expected),'INJECTION_PROTOCOL','No extra conditions')
    for name,(video,family,angle,translation)in expected.items():
        require(cfg['conditions'][name]==dict(video=video,family=family,rotation_y_deg=angle,translation_x_mm=translation),'INJECTION_PROTOCOL',name)
    require(cfg['gates']==dict(min_observed_ring_pixels=20,observed_ring_CAD_support_within2px_min=.95,observed_to_full_CAD_boundary_p95_px_max=3.,require_GT_Ring_fixed_pose_certificate=True,require_camera_to_ring_native_binding=True,require_distinct_004_005_trajectories=True),'SCENE_GATE','Cannot weaken frozen gates')
    require(cfg['body_initialization']=='Official DXY E1/full Mask E2 plus nine parameters; GT prohibited; freeze before registration','GT_LEAK','No GT Body substitute')
    for name,rec in cfg['assets'].items():
        fields(rec,'path sha256',name);rec['path']=str((path.parent/rec['path']).resolve())
    for key in ['inputs','variables','output_root']:task[key]=base[key]
    task['split']['manifest']=base['split']['manifest']
    freeze=path.with_name('TASK_FREEZE.json')
    if freeze.exists():require(sha256(path)==json.loads(freeze.read_text())['task_sha256'],'TASK_DRIFT','Immutable TASK.yaml changed')
    return task


def verify(task):
    cfg=task['dualvideo']
    # Validate the public source manifest before touching restricted GT assets.
    rec=cfg['assets']['source_manifest']
    require(Path(rec['path']).is_file(),'NOT_EVALUABLE','source_manifest')
    require(sha256(rec['path'])==rec['sha256'],'SOURCE_SHA','source_manifest')
    for name,rec in cfg['assets'].items():
        require(Path(rec['path']).is_file(),'NOT_EVALUABLE',name)
        require(sha256(rec['path'])==rec['sha256'],'SOURCE_SHA',name)
    info=verify_task(legacy(task))
    manifest=json.loads(Path(cfg['assets']['source_manifest']['path']).read_text())
    require(len(manifest['rows'])==33 and cfg['source_frame_count']=={'004':22,'005':11},'SOURCE_IDENTITY','Frozen 33 distinct source frames')
    require(len({r['source_id']for r in manifest['rows']})==33 and len({r['view_id']for r in manifest['rows']})==33,'DATA_ISOLATION','No duplicated FIT/HOLDOUT')
    require(sum(r['role']=='FIT'for r in manifest['rows'])==25 and sum(r['role']=='HOLDOUT'for r in manifest['rows'])==8,'DATA_ISOLATION','Frozen 25 FIT / 8 HOLDOUT')
    contracts=dict(info['module_contracts']);contracts['DV01']=dict(path='dualvideo/audit.py',sha256=sha256(ROOT/'src/ring_first_3d/dualvideo/audit.py'),status='G0_GATE_ONLY')
    return freeze_identity(task,contracts,info['verified_assets']+len(cfg['assets']))


def permissions(task,stage,root):
    require(stage in DUAL_STAGES,'UNAUTHORIZED_STAGE',stage)
    role='generator'if stage=='G0_scene_audit'else'verification'
    paths=[Path(r['path']).resolve()for k,r in task['dualvideo']['assets'].items()if k in {'blend','gt_cache','gt_extraction'}]
    return dict(role=role,gt_paths=paths,run_root=Path(root).resolve(),allow_GT=role=='generator',stage=stage,blender_binary=task['dualvideo']['assets']['blender_binary']['path'])
