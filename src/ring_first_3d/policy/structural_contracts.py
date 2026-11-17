"""Schema9: C0-only structural proof precedes any real/GT-free HERO execution."""
import copy,json
from pathlib import Path
from .contracts import ROOT,MODULES,STAGES,require,fields,validate_v1,verify_task,freeze_identity
from ..contracts.identities import sha256
TASK_ID='TASK-E4-MULTIVIEW-STRUCTURAL-UPDATE-001'
BASELINE='418c96f87ba06458be5bb082813cad6e20127a19'
STRUCTURAL_STAGES=('preflight','contracts','structural_regression','G0_initialization','G1_C0_update','G2_C0_evaluate','G3_C0_visualize','G4_C0_gate','G5_real_update','G6_hero_relocate','G7_real_evaluate','G4_visualize','artifacts')
MODULE_FILES={'SU01':'body_update.py','SU02':'data_adapter.py','SU03':'hero_relocation.py','SU04':'experiment.py','SU05':'figures.py'}

def legacy(t):
    d=copy.deepcopy({k:v for k,v in t.items() if k!='structural'});d.update(schema=1,modules=list(MODULES));d['authorization']['stages']=list(STAGES);d['acceptance']['required_stages']=list(STAGES);d['split'].update(GT=[],access='verification_only_no_GT');return d


def validate(t,path):
    fields(t,'schema task_id goal modules variables inputs split authorization acceptance budget stop output_root structural','Structural TASK')
    require(t['schema']==9 and t['task_id']==TASK_ID,'SCIENCE_SCOPE',TASK_ID);b=validate_v1(legacy(t),path);c=t['structural']
    require(c['baseline_commit']==BASELINE and c['initialization']=='EXACT_013_INPUT_MESH_V_F_SOLID_CAP','INITIALIZATION_LINEAGE','Same exact013 both domains')
    require(set(t['modules'])==set(MODULES)|set(MODULE_FILES),'MODULE','Existing contracts plus SU01-SU05')
    require(c['real_cases']==['G01','G03','G05'] and c['simulation_conditions']==['C0'],'SCIENCE_SCOPE','Ideal C0 then three real groups only')
    require(c['camera_optimization'] is False and c['Body_uses_HERO'] is False and c['HERO_updates_Body'] is False and c['GT_selects_prediction'] is False,'GT_LEAK','Strict role boundaries')
    require(c['Body_arms']==['DEFORM_ONLY','DEFORM_GROW'],'FROZEN_PROTOCOL','Explicit structural control')
    require(c['update']['growth_min_views']>=3 and c['update']['growth_min_videos']==2,'MULTIVIEW_SUPPORT','No single-view growth')
    require(c['C0_gate']==dict(require_GT_Chamfer_improvement=True,require_HOLDOUT_IoU_nonworsening=True,require_accepted_growth=True,require_growth_over_deform_GT_gain=True,require_no_geometry_worsening=True),'ACCEPTANCE','Predeclared scientific gate')
    require(t['authorization']['stages']==list(STRUCTURAL_STAGES) and t['acceptance']['required_stages']==list(STRUCTURAL_STAGES),'AUTHORIZATION','C0 must precede real')
    for k in ('inputs','variables','output_root'):t[k]=b[k]
    f=path.with_name('TASK_FREEZE.json')
    if f.exists():require(sha256(path)==json.loads(f.read_text())['task_sha256'],'TASK_DRIFT','Frozen protocol cannot be rewritten')
    return t


def verify(t):
    c=t['structural'];assets=c['assets'];code=json.loads(Path(assets['code_lock']['path']).read_text())
    bound=json.loads(Path(assets['input_manifest']['path']).read_text())['files']
    for r in list(assets.values())+code['files']+bound:
        p=Path(r['path']);require(p.is_file() and sha256(p)==r['sha256'],'SOURCE_SHA',str(p))
    info=verify_task(legacy(t));contracts=dict(info['module_contracts'])
    for mid,file in MODULE_FILES.items():contracts[mid]=dict(path=str(ROOT/'experiments'/TASK_ID/'code'/file),sha256=sha256(ROOT/'experiments'/TASK_ID/'code'/file))
    require(all(any(r['path']==contracts[m]['path'] and r['sha256']==contracts[m]['sha256'] for r in code['files']) for m in MODULE_FILES),'SOURCE_SHA','Actually executing experiment code must be locked')
    return freeze_identity(t,contracts,info['verified_assets']+len(bound))


def permissions(t,stage,root):
    c=t['structural'];src=json.loads(Path(c['assets']['real_sources']['path']).read_text());gt=[Path(c['assets']['virtual_gt']['path']).resolve()]+[Path(r['GT']['path']).resolve() for r in src['cases'] if r.get('GT')]
    role='evaluator' if stage in {'G2_C0_evaluate','G7_real_evaluate','G3_C0_visualize','G4_visualize'} else 'predictor' if stage in {'G1_C0_update','G5_real_update','G6_hero_relocate'} else 'verification'
    denied=[]
    if role=='predictor':
        denied=[Path(r['legacy_aligned_directory']) for r in src['cases']]
        if stage in {'G1_C0_update','G5_real_update'}:
            denied +=[Path(r['path']).resolve() for x in src['cases'] for r in x['depth'].values()]
            denied +=[Path(v['cache']['path']).resolve() for r in src['cases'] for v in r['HOLDOUT']]
            denied +=[Path(c['simulation_public'])/'observations'/(v['view_id']+'.npz') for v in json.loads(Path(c['assets']['simulation_views']['path']).read_text())['HOLDOUT']]
    return dict(stage=stage,role=role,allow_GT=role=='evaluator',gt_paths=gt,run_root=Path(root).resolve(),denied_read_prefixes=denied)


def dispatch(stage,t,attempt):
    import sys
    sys.path.insert(0,str(ROOT/'experiments'/TASK_ID/'code'))
    from experiment import dispatch as handler
    return handler(stage,t,attempt)
