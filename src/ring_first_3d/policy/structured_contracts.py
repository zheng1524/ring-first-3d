"""Schema10 additive task contract: structured real-only body pilot, no HERO/C0."""
import copy,json
from pathlib import Path
from .contracts import ROOT,MODULES,STAGES,require,fields,validate_v1,verify_task,freeze_identity
from ..contracts.identities import sha256
TASK_ID='TASK-E4-STRUCTURED-BODY-UPDATE-002'
STRUCTURED_STAGES=('preflight','contracts','structured_regression','G0_source_audit','G1_G01','G1_G03','G1_G05','G2_evaluate','G4_visualize','artifacts')
FILES=('projection_gate','deformation_graph','smooth_arap','bspline_sweep','rmf','ring_collision_gate','optimizer','pipeline','common','growth_evidence','figures')
NEW_MODULES={'SB'+str(i+1).zfill(2):f+'.py'for i,f in enumerate(FILES)}
def legacy(t):
    d=copy.deepcopy({k:v for k,v in t.items()if k!='structured'});d.update(schema=1,modules=list(MODULES));d['authorization']['stages']=list(STAGES);d['acceptance']['required_stages']=list(STAGES);d['split'].update(GT=[],access='verification_only_no_GT');return d

def validate(t,path):
    fields(t,'schema task_id goal modules variables inputs split authorization acceptance budget stop output_root structured','Structured task')
    require(t['schema']==10 and t['task_id']==TASK_ID,'SCIENCE_SCOPE',TASK_ID);b=validate_v1(legacy(t),path);c=t['structured']
    require(c['baseline_commit']=='7c471701f38f1577ba506bc8ed1e38774f99dabe'and c['cases']==['G01','G03','G05'],'LINEAGE','Exact prior baseline, all3 groups')
    require(c['arms']==['DEFORM_ONLY','DEFORM_SWEEP']and c['update']['iterations']==36,'FROZEN_PROTOCOL','Matched two-arm fixed budget')
    require(c['camera_optimization']is False and c['HERO_read']is False and c['GT_selects_prediction']is False,'GT_LEAK','No camera/HERO/GT training')
    require(c['update']['sarap_lambda']==.7 and c['update']['graph_nodes']==32,'FROZEN_PROTOCOL','32-node SARAP lambda0.7')
    require(c['update']['projection']['max_distance_px']==40. and c['protection']==dict(initial_IoU_min=.8,max_IoU_drop=.01,max_boundary_increase_px=1.),'FROZEN_PROTOCOL','Local pairs and fixed per-view protection')
    require(set(t['modules'])==set(MODULES)|set(NEW_MODULES),'MODULE','Existing harness and structured modules')
    require(t['authorization']['stages']==list(STRUCTURED_STAGES)and t['acceptance']['required_stages']==list(STRUCTURED_STAGES),'STAGE','Required tests precede real, GT follows all freezes')
    for k in ['inputs','variables','output_root']:t[k]=b[k]
    freeze=path.with_name('TASK_FREEZE.json')
    if freeze.exists():require(sha256(path)==json.loads(freeze.read_text())['task_sha256'],'TASK_DRIFT','Preserve historical protocol')
    return t

def verify(t):
    c=t['structured'];code=json.loads(Path(c['code_lock']['path']).read_text())['files'];bound=json.loads(Path(c['input_manifest']['path']).read_text())['files']
    for r in code+bound+[c['code_lock'],c['input_manifest']]:require(Path(r['path']).is_file()and sha256(r['path'])==r['sha256'],'SOURCE_SHA',r['path'])
    info=verify_task(legacy(t));contracts=dict(info['module_contracts'])
    for mid,file in NEW_MODULES.items():
        p=ROOT/'experiments'/TASK_ID/'code'/file;contracts[mid]=dict(path=str(p),sha256=sha256(p));require(any(r==contracts[mid]for r in code),'SOURCE_SHA','Actually executing source locked')
    return freeze_identity(t,contracts,info['verified_assets']+len(bound))

def permissions(t,stage,root):
    src=json.loads(Path(t['structured']['sources']).read_text());cases=[r for r in src['cases']if r['case']in t['structured']['cases']]
    gt=[Path(r['GT']['path']).resolve()for r in cases];role='predictor'if stage.startswith('G1_')else'evaluator'if stage in ['G2_evaluate','G4_visualize']else'verification'
    denied=[]
    if role=='predictor':
        denied=[Path('/home/liu/ring_first_3d_structural_update/experiments/TASK-E4-MULTIVIEW-STRUCTURAL-UPDATE-001/runs')]
        denied +=[Path(r['legacy_aligned_directory'])for r in cases]
        denied +=[Path(a['path']).resolve()for r in cases for a in r['depth'].values()]
        denied +=[Path(v['cache']['path']).resolve()for r in cases for v in r['HOLDOUT']]
    return dict(stage=stage,role=role,allow_GT=role=='evaluator',gt_paths=gt,run_root=Path(root).resolve(),denied_read_prefixes=denied)

def dispatch(stage,t,attempt):
    import sys
    sys.path.insert(0,str(ROOT/'experiments'/TASK_ID/'code'))
    from pipeline import dispatch as handle
    return handle(stage,t,attempt)
