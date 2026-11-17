"""Schema11: two actual rejected candidates, fixed Body, isolated GT evaluation."""
import copy,json
from pathlib import Path
from .contracts import ROOT,MODULES,STAGES,require,fields,validate_v1,verify_task,freeze_identity
from ..contracts.identities import sha256
TASK_ID='TASK-E4-G01-G03-GROWTH-RECOVERY-001'
RECOVERY_STAGES=('preflight','contracts','recovery_regression','G0_recovery_audit','G1_G01','G1_G03','G2_evaluate','G4_visualize','artifacts')
FILES=('recover','lengths','embedded_sweep','boolean_blender','union_mesh','geometry_gate','ring_gate','projection','optimize','pipeline','evaluate','visualize','io_utils')
NEW_MODULES={'GR'+str(i+1).zfill(2):f+'.py'for i,f in enumerate(FILES)}
def legacy(t):
    d=copy.deepcopy({k:v for k,v in t.items()if k!='recovery'});d.update(schema=1,modules=list(MODULES));d['authorization']['stages']=list(STAGES);d['acceptance']['required_stages']=list(STAGES);d['split'].update(GT=[],access='verification_only_no_GT');return d
def validate(t,path):
    fields(t,'schema task_id goal modules variables inputs split authorization acceptance budget stop output_root recovery','Recovery task')
    require(t['schema']==11 and t['task_id']==TASK_ID,'SCIENCE_SCOPE',TASK_ID);b=validate_v1(legacy(t),path);c=t['recovery']
    require(c['baseline_commit']=='238c2da1cd842c0eba710a4ec44db5f437bff8e4'and c['cases']==['G01','G03'],'LINEAGE','Audited HEAD and only G01/G03')
    require(c['arm']=='DEFORM_SWEEP_RECOVERY'and c['iteration']==24 and c['max_candidates_per_case']==1,'SCIENCE_SCOPE','Only the saved preferred actual candidate')
    require(c['Body_fixed']and not c['camera_optimization']and not c['HERO_read']and not c['GT_selects_prediction'],'GT_LEAK','Only local recovered spline optimization')
    require(c['update']['continuation_fractions']==[.35,.7,1.]and c['update']['iterations_per_stage']==8,'FROZEN_PROTOCOL','Bounded three-stage continuation, no36-round Body retraining')
    require(c['update']['projection']==dict(max_distance_px=40.,mutual_radius_px=0.,normal_cos_min=.5,max_tangent_px=8.),'FROZEN_PROTOCOL','Inherited correspondence contract')
    require(set(t['modules'])==set(MODULES)|set(NEW_MODULES),'MODULE','Existing harness and recovery modules')
    require(t['authorization']['stages']==list(RECOVERY_STAGES)and t['acceptance']['required_stages']==list(RECOVERY_STAGES),'STAGE','Tests, both predictions, then GT')
    for k in ['inputs','variables','output_root']:t[k]=b[k]
    freeze=path.with_name('TASK_FREEZE.json')
    if freeze.exists():require(sha256(path)==json.loads(freeze.read_text())['task_sha256'],'TASK_DRIFT','No silent protocol edits')
    return t
def verify(t):
    c=t['recovery'];code=json.loads(Path(c['code_lock']['path']).read_text())['files'];bound=json.loads(Path(c['input_manifest']['path']).read_text())['files']
    if 'resume_valid_stage'in c:
        r=c['resume_valid_stage'];require(sha256(r['path'])==r['sha256'],'SOURCE_SHA','Resume manifest')
        m=json.loads(Path(r['path']).read_text())
        require(m['case']=='G03' and m['stage']=='G1_G03' and m['source_commit']=='62c56097916e32da6dde3a3d9018912f76c69378','RESUME_IDENTITY','Only the completed same-task G03 stage')
        require(m['update']==c['update'] and m['configuration_sha256']==c['configuration']['sha256'],'FROZEN_PROTOCOL','Resume must preserve all scientific parameters')
        bound=bound+m['files']+[m['source_result']]
    for r in code+bound+[c['code_lock'],c['input_manifest'],c['configuration']]:
        require(Path(r['path']).is_file()and sha256(r['path'])==r['sha256'],'SOURCE_SHA',r['path'])
    info=verify_task(legacy(t));contracts=dict(info['module_contracts'])
    for mid,file in NEW_MODULES.items():
        p=ROOT/'experiments'/TASK_ID/'code'/file;contracts[mid]=dict(path=str(p),sha256=sha256(p));require(any(r==contracts[mid]for r in code),'SOURCE_SHA','Actually executing source locked')
    return freeze_identity(t,contracts,info['verified_assets']+len(bound))
def permissions(t,stage,root):
    src=json.loads(Path(t['recovery']['sources']).read_text());rows=[r for r in src['cases']if r['case']in ['G01','G03']]
    gt=[Path(r['GT']['path']).resolve()for r in rows]
    predictor=stage.startswith('G1_');evaluator=stage in ['G2_evaluate','G4_visualize'];denied=[]
    if predictor:
        denied +=[Path(v['cache']['path']).resolve()for r in rows for v in r['HOLDOUT']]
        denied +=[Path(a['path']).resolve()for r in rows for a in r['depth'].values()]
        denied +=[Path(r['legacy_aligned_directory'])for r in rows]
        denied +=[Path(t['recovery']['baseline_root'])/'experiments/TASK-E4-STRUCTURED-BODY-UPDATE-002/review_assets']
    return dict(stage=stage,role='predictor'if predictor else'evaluator'if evaluator else'verification',allow_GT=evaluator,gt_paths=gt,run_root=Path(root).resolve(),denied_read_prefixes=denied,
        recovery_boolean_binary=t['recovery']['blender_binary']['path'],recovery_boolean_script=str(ROOT/'experiments'/TASK_ID/'code/boolean_blender.py'))
def dispatch(stage,t,attempt):
    import sys
    sys.path.insert(0,str(ROOT/'experiments'/TASK_ID/'code'))
    from pipeline import dispatch as handler
    return handler(stage,t,attempt)
