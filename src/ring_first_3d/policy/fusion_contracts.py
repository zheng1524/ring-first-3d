"""Human-approved independent depth-grid multisurface fusion task profile."""
import copy,json
from pathlib import Path
from .contracts import ROOT,MODULES,STAGES,require,fields,validate_v1,verify_task,freeze_identity
from ..contracts.identities import sha256

TASK_ID='TASK-E4-G01-MULTISURFACE-BODY-FUSION-001'
FUSION_STAGES=('preflight','contracts','fusion_regression','G0_views_noise','G1_body','G2_candidates','G3_smoke_predict','G3_smoke_evaluate','G3_all_predict','G4_fusion_predict','G4_evaluate','G4_visualize','artifacts')
MODULE_FILES={'MF01':'scene.py','MF02':'registration.py','MF03':'fusion.py','MF04':'evaluate.py','MF05':'visualize.py'}
REUSED=('T05','T06','T07','T08','T09')
CONDITIONS={
 'C0':dict(bias={'004':'I','005':'I'},sigma={'004':[0.,0.],'005':[0.,0.]}),
 'C1':dict(bias={'004':'I','005':'A'},sigma={'004':[0.,0.],'005':[.3,.10]}),
 'C2':dict(bias={'004':'I','005':'B'},sigma={'004':[0.,0.],'005':[0.,0.]}),
 'C3':dict(bias={'004':'A','005':'B'},sigma={'004':[.3,.10],'005':[.3,.10]}),
 'C4':dict(bias={'004':'A','005':'B'},sigma={'004':[.7,.20],'005':[.7,.20]}),
 'C5':dict(bias={'004':'I','005':'I'},sigma={'004':[.3,.10],'005':[.3,.10]})}


def legacy(task):
    b=copy.deepcopy({k:v for k,v in task.items()if k!='fusion'});b['schema']=1;b['modules']=[m for m in b['modules']if m in MODULES]
    b['split']['GT']=[];b['split']['access']='verification_only_no_GT';b['authorization']['stages']=list(STAGES);b['acceptance']['required_stages']=list(STAGES);return b


def validate(task,path):
    fields(task,'schema task_id goal modules variables inputs split authorization acceptance budget stop output_root fusion','multisurface TASK')
    require(type(task['schema'])is int and task['schema']==5 and task['task_id']==TASK_ID,'SCIENCE_SCOPE','Registered multisurface task only')
    b=validate_v1(legacy(task),path)
    require(set(task['modules'])==set(MODULES)|set(MODULE_FILES)|set(REUSED)and len(task['modules'])==len(set(task['modules'])),'MODULE','Existing API plus explicit MF modules')
    require(task['authorization']['stages']==list(FUSION_STAGES)and task['acceptance']['required_stages']==list(FUSION_STAGES),'AUTHORIZATION','Smoke and freeze gates required')
    require(task['split']['access']=='multisurface_generator_predictor_evaluator'and task['split']['GT']==['generator_and_postfreeze_evaluation_only'],'GT_LEAK','No GT to surface/fusion predictors')
    f=task['fusion'];require(f['conditions']==CONDITIONS and f['condition_order']==list(CONDITIONS),'INJECTION_PROTOCOL','Predeclared systematic/noise controls')
    require(f['pose_model']=='VideoBias @ TruePose @ FrameNoise'and f['seed']==20261117 and f['bias_parameters']=={'I':[0.,0.],'A':[2.,.5],'B':[3.,.3]},'INJECTION_PROTOCOL','Fixed side/axis seed')
    require(f['bias_axis']=='positive_world_Y; translation_positive_world_X; pivot_Ring_origin'and f['noise_model']=='Gaussian local rotvec_xyz_deg and translation_xyz_mm, centered per video, common random numbers across sigma levels','INJECTION_PROTOCOL','Explicit covariance convention')
    require(f['body_arms']==['E1','E2']and f['methods']==['M0','ICP','BODY_VIDEO','BODY_HIER']and f['tolerance_mm']==.5 and f['tolerance_ablation_mm']==[0.,1.],'FROZEN_PROTOCOL','Both Body controls, tolerance and methods')
    require(f['camera_optimization']is False and f['physical_Ring_fixed']is True and f['body_frozen']is True and f['GT_selects_predictor']is False,'GT_LEAK','Surfaces only, no camera/Body update or oracle choice')
    require(f['mesh_builder']=='native_axial_depth_grid_triangles'and f['mesh_stride_px']==2 and f['GT_face_union_prohibited']is True,'MESH_SOURCE','Independent per-image observations required')
    require(f['sections']==[{'axis':0,'offset_mm':0.},{'axis':1,'offset_mm':0.},{'axis':2,'offset_mm':-2.},{'axis':2,'offset_mm':-6.}],'FROZEN_PROTOCOL','Two longitudinal/two transverse exact mesh cuts')
    for k in ['inputs','variables','output_root']:task[k]=b[k]
    task['split']['manifest']=b['split']['manifest']
    for rec in f['assets'].values():fields(rec,'path sha256','fusion asset');rec['path']=str((path.parent/rec['path']).resolve())
    freeze=path.with_name('TASK_FREEZE.json')
    if freeze.exists():require(sha256(path)==json.loads(freeze.read_text())['task_sha256'],'TASK_DRIFT','Preserve frozen TASK')
    return task


def verify(task):
    f=task['fusion']
    for key in ['source_manifest']+[k for k in f['assets']if k!='source_manifest']:
        rec=f['assets'][key];require(Path(rec['path']).is_file(),'NOT_EVALUABLE',key);require(sha256(rec['path'])==rec['sha256'],'SOURCE_SHA',key)
    m=json.loads(Path(f['assets']['source_manifest']['path']).read_text());views=m['selected']
    require(len(views)==16 and len({r['view_id']for r in views})==16 and all(r['role']=='FIT'for r in views),'DATA_ISOLATION','Sixteen distinct FIT views')
    require(all(sum(r['video']==v for r in views)==8 for v in ['004','005']),'SOURCE_IDENTITY','Eight independent camera sources each')
    info=verify_task(legacy(task));contracts=dict(info['module_contracts'])
    reuse=json.loads(Path(f['assets']['reuse_lock']['path']).read_text())
    for mid in REUSED:contracts[mid]=reuse['modules'][mid]
    for mid,file in MODULE_FILES.items():contracts[mid]=dict(path='multisurface/'+file,sha256=sha256(ROOT/'src/ring_first_3d/multisurface'/file))
    return freeze_identity(task,contracts,info['verified_assets']+len(f['assets']))


def permissions(task,stage,root):
    require(stage in FUSION_STAGES,'UNAUTHORIZED_STAGE',stage)
    role='generator'if stage=='G0_views_noise'else'evaluator'if stage.endswith('evaluate')or stage=='G4_visualize'else'predictor'if stage in {'G1_body','G2_candidates','G3_smoke_predict','G3_all_predict','G4_fusion_predict'}else'verification'
    gt=[Path(v['path']).resolve()for k,v in task['fusion']['assets'].items()if k in {'virtual_gt'}]
    denied=[]
    if role=='predictor':
        denied=[Path(task['fusion']['parent_run']).resolve(),Path(task['fusion']['assets']['source_manifest']['path']).resolve()]
        for snapshot in (Path(root)/'snapshots').glob('*'):denied.append(snapshot/'visualization')
    return dict(role=role,allow_GT=role in {'generator','evaluator'},gt_paths=gt,run_root=Path(root).resolve(),stage=stage,denied_read_prefixes=denied)
