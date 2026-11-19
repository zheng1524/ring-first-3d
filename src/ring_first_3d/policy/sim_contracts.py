"""Explicit human-approved simulation revision; historical schemas are unchanged."""
import copy,json
from pathlib import Path
from .contracts import ROOT,MODULES,STAGES,fields,require,validate_v1,verify_task,freeze_identity
from ..contracts.identities import sha256

TASK_ID='TASK-E4-G01-DUALVIDEO-BODY-ANCHORED-REGISTRATION-001-SIM-PROTOCOL-REV1'
SIM_STAGES=('preflight','contracts','sim_regression','G0_simulate','G1_initialize','G1_evaluate','G2_mapping','G2_evaluate','G3_smoke_predict','G3_smoke_evaluate','G3_matrix_predict','G4_evaluate','G4_visualize','artifacts')
EXTRA=('T05','T06','T07','T08','T09','DV02','DV03','DV04','DV05','DV06','DV07')
CONDITIONS={'S0':{'004':'I','005':'I'},'S1':{'004':'I','005':'A'},'S2':{'004':'I','005':'B'},'S3':{'004':'A','005':'B'},'S4':{'004':'A','005':'A'},'L1':{'004':'I','005':'A'}}


def legacy(task):
    b=copy.deepcopy({k:v for k,v in task.items()if k!='sim'})
    b['schema']=1;b['modules']=[m for m in b['modules']if m in MODULES]
    b['split']['GT']=[];b['split']['access']='verification_only_no_GT'
    b['authorization']['stages']=list(STAGES);b['acceptance']['required_stages']=list(STAGES)
    return b


def validate(task,path):
    fields(task,'schema task_id goal modules variables inputs split authorization acceptance budget stop output_root sim','SIM_PROTOCOL_REV1')
    require(task['schema']==4 and task['task_id']==TASK_ID,'SCIENCE_SCOPE','Explicit simulation revision only')
    b=validate_v1(legacy(task),path)
    require(len(task['modules'])==len(set(task['modules']))and set(task['modules'])==set(MODULES)|set(EXTRA),'MODULE','Declared reused sources and new simulation adapters')
    require(task['authorization']['stages']==list(SIM_STAGES)and task['acceptance']['required_stages']==list(SIM_STAGES),'AUTHORIZATION','No bypass of Smoke or prediction freeze')
    require(task['split']['access']=='simulation_generator_predictor_evaluator'and task['split']['GT']==['G01_generator_and_postfreeze_evaluator_only'],'GT_LEAK','Strict simulation roles')
    sc=task['sim']
    require(sc['label']=='G01_LIKE_SIMULATION'and sc['proxy']=='SYNTHETIC_HERO_PROXY','SCIENCE_SCOPE','No claim of genuine deployment or HERO inference')
    require(sc['conditions']==CONDITIONS and sc['condition_order']==list(CONDITIONS),'INJECTION_PROTOCOL','Approved world matrix plus independent L1')
    require(sc['error_transforms']=={'I':[0.,0.],'A':[2.,.5],'B':[3.,.3]}and sc['error_axis']==[0.,1.,0.]and sc['translation_axis']==[1.,0.,0.]and sc['rotation_center_mm']==[0.,0.,0.]and sc['action']=='left_world_SE3'and sc['seed']==20261116,'INJECTION_PROTOCOL','Frozen axis/direction/center/side/seed')
    require(sc['body_frozen_during_registration']is True and sc['GT_selects_predictor']is False,'GT_LEAK','No GT substitution or selection')
    require(sc['placement_candidates_mm']==[[0.,0.,0.],[0.,0.,-2.],[0.,0.,-4.],[0.,1.,-2.]],'FROZEN_PROTOCOL','Shared rigid placement only; no resizing')
    require(sc['realism_is_blocking']is False and sc['internal_geometry_is_blocking']is True,'SCENE_GATE','Human-approved realism quality metric; internal geometry still blocking')
    require(sc['methods']==['M0','M1','M2','RING_ONLY','M2_DIRECT','M2_RING'],'SCIENCE_SCOPE','Frozen independent comparisons')
    for k in ['inputs','variables','output_root']:task[k]=b[k]
    task['split']['manifest']=b['split']['manifest']
    for rec in sc['assets'].values():
        fields(rec,'path sha256','sim asset');rec['path']=str((path.parent/rec['path']).resolve())
    freeze=path.with_name('TASK_FREEZE.json')
    if freeze.exists():require(sha256(path)==json.loads(freeze.read_text())['task_sha256'],'TASK_DRIFT','New revision requires new config, never overwrite freeze')
    return task


def verify(task):
    sc=task['sim']
    # The public manifest is checked first, including inside restricted tests.
    for name in ['source_manifest']+[k for k in sc['assets']if k!='source_manifest']:
        rec=sc['assets'][name]
        require(Path(rec['path']).is_file(),'NOT_EVALUABLE',name)
        require(sha256(rec['path'])==rec['sha256'],'SOURCE_SHA',name)
    info=verify_task(legacy(task))
    m=json.loads(Path(sc['assets']['source_manifest']['path']).read_text())
    require(len(m['rows'])==33 and len({r['view_id']for r in m['rows']})==33,'SOURCE_IDENTITY','Original 33 distinct frames')
    require(sum(r['role']=='FIT'for r in m['rows'])==25 and sum(r['role']=='HOLDOUT'for r in m['rows'])==8,'DATA_ISOLATION','Original disjoint 25/8 partition')
    source_lock=json.loads(Path(sc['assets']['reuse_lock']['path']).read_text())
    contracts=dict(info['module_contracts'])
    for mid in ['T05','T06','T07','T08','T09']:contracts[mid]=source_lock['modules'][mid]
    for mid,file in zip(EXTRA[5:],['scene.py','initialize.py','mapping.py','registration.py','evaluate.py','visualize.py']):
        contracts[mid]=dict(path='sim/'+file,sha256=sha256(ROOT/'src/ring_first_3d/sim'/file))
    return freeze_identity(task,contracts,info['verified_assets']+len(sc['assets']))


def permissions(task,stage,root):
    require(stage in SIM_STAGES,'UNAUTHORIZED_STAGE',stage)
    role='generator'if stage=='G0_simulate'else'evaluator'if stage.endswith('evaluate')or stage=='G4_visualize'else'predictor'if stage in {'G1_initialize','G2_mapping','G3_smoke_predict','G3_matrix_predict'}else'verification'
    gt=[Path(v['path']).resolve()for k,v in task['sim']['assets'].items()if k in {'blend','gt_cache','gt_extraction'}]
    denied=[]
    if stage in {'G3_smoke_predict','G3_matrix_predict'}:
        for a in (Path(root)/'attempts').glob('*-G0_simulate-*'):denied.append(a/'public/initialization')
        # Diagnostic G2 mappings contain clean-frame anchors. Registration must
        # recompute with the actually corrupted cameras, never reuse those XYZs.
        for a in (Path(root)/'attempts').glob('*-G2_mapping-*'):denied.append(a)
    return dict(role=role,allow_GT=role in {'generator','evaluator'},gt_paths=gt,run_root=Path(root).resolve(),stage=stage,
        denied_read_prefixes=denied,blender_binary=task['sim']['assets']['blender_binary']['path'])
