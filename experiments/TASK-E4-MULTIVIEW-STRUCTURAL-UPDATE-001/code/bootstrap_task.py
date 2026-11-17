"""Bind pre-existing sources and parameters. Run once before any scientific trial."""
from pathlib import Path
import sys,json,copy
import yaml
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'src'))
from ring_first_3d.contracts.identities import sha256
from ring_first_3d.policy.structural_contracts import STRUCTURAL_STAGES,MODULE_FILES
TD=Path(__file__).resolve().parents[1]
def rec(p):
    p=Path(p).resolve();return dict(path=str(p),sha256=sha256(p))
def write(path,val):
    with path.open('x') as f:json.dump(val,f,indent=2);f.write('\n')
parent=ROOT/'experiments/TASK-E4-2D-CONTOUR-GUIDED-INIT-A-HERO-001';old=yaml.safe_load((parent/'TASK.yaml').read_text());src=json.loads((parent/'inputs/SOURCES.json').read_text());fusion=yaml.safe_load((ROOT/'experiments/TASK-E4-G01-MULTISURFACE-BODY-FUSION-001/TASK.yaml').read_text())['fusion']
simpublic=Path('/home/liu/ring_first_3d_g01_multisurface/experiments/TASK-E4-G01-MULTISURFACE-BODY-FUSION-001/runs/MULTISURFACE_001/attempts/0004-G0_views_noise-3ab770b4/public')
assets=dict(real_sources=rec(parent/'inputs/SOURCES.json'),legacy_geometry=rec(parent/'legacy015/safe_geometry.py'),legacy_multiview=rec(parent/'legacy015/multiview.py'),
            simulation_views=fusion['assets']['source_manifest'],ring=fusion['assets']['ring'],virtual_gt=fusion['assets']['virtual_gt'],E1_initializer=fusion['assets']['E1_initializer'],E2_initializer=fusion['assets']['E2_initializer'],
            upstream_TASK=rec(parent/'TASK.yaml'),upstream_failure=rec(parent/'FAILURE_REGISTRY.json'))
files=list(src['frozen_assets'])
for p in simpublic.rglob('*'):
    if p.is_file() and (p.parent.name=='observations' or p.name=='FRAME_INDEX.json'):files.append(rec(p))
views=json.loads(Path(assets['simulation_views']['path']).read_text())
for v in views['selected']+views['HOLDOUT']:
    for key in ('cache','pose_origin','RGB_source','Mask_source'):files.append(v[key])
# Legacy source namespace used by the evaluator and the exact geometry functions.
files +=[rec(p) for p in (parent/'legacy015').glob('*.py')]
unique={r['path']:dict(path=r['path'],sha256=r['sha256']) for r in files};write(TD/'inputs/INPUT_MANIFEST.json',dict(files=list(unique.values()),purpose='identity only; no GT values/old predictions used by updater'))
assets['input_manifest']=rec(TD/'inputs/INPUT_MANIFEST.json')
code=[rec(p) for p in (TD/'code').glob('*.py') if p.name!='bootstrap_task.py'];write(TD/'inputs/CODE_LOCK.json',dict(files=code));assets['code_lock']=rec(TD/'inputs/CODE_LOCK.json')
t=copy.deepcopy({k:v for k,v in old.items() if k not in {'contour','inita'}});t.update(schema=9,task_id=TD.name,goal='One exact013 Init-A, FIT-only shared multiview deformation and evidence-gated topology growth; C0 proof before real G01/G03/G05 and pixel-identity HERO relocation',modules=old['modules'][:10]+list(MODULE_FILES),output_root=str(TD/'runs'))
for k in ('fixture','support','reference','source_lock','evidence'):t['inputs'][k]=rec(ROOT/Path(t['inputs'][k]['path']).relative_to('/home/liu/ring_first_3d_contour_guided_init_a'))
t['authorization'].update(reference='User explicit TASK-E4-MULTIVIEW-STRUCTURAL-UPDATE-001',stages=list(STRUCTURAL_STAGES));t['acceptance']['required_stages']=list(STRUCTURAL_STAGES)
t['budget']=dict(max_seconds=14400,stage_timeout_seconds=5400,max_attempts_per_stage=2,max_output_bytes=4000000000)
t['structural']=dict(baseline_commit='418c96f87ba06458be5bb082813cad6e20127a19',initialization='EXACT_013_INPUT_MESH_V_F_SOLID_CAP',real_cases=['G01','G03','G05'],simulation_conditions=['C0'],Body_arms=['DEFORM_ONLY','DEFORM_GROW'],
    camera_optimization=False,Body_uses_HERO=False,HERO_updates_Body=False,GT_selects_prediction=False,assets=assets,simulation_public=str(simpublic),
    update=dict(iterations=36,learning_rate_mm=.02,line_search_steps=8,samples_per_direction=384,negative_samples=256,ring_unknown_px=3,capture_px=120.,pixel_loss_scale=20.,lambda_lap=.03,lambda_edge=.02,lambda_prior=.002,
                growth_iterations=[12,24],growth_min_gap_px=6.,growth_min_views=3,growth_min_videos=2,growth_patch_rings=2,growth_max_patch_faces=80,growth_min_singular_ratio=.02,growth_max_inconsistency=.5,growth_min_mm=.1,growth_max_mm=.8,growth_candidates=3,growth_min_FIT_IoU_gain=.0001),
    C0_gate=dict(require_GT_Chamfer_improvement=True,require_HOLDOUT_IoU_nonworsening=True,require_accepted_growth=True,require_growth_over_deform_GT_gain=True,require_no_geometry_worsening=True),
    hero=dict(capture_mm=3.,samples=384,tolerance_mm=.5,video_offset_bound_mm=2.,frame_prior=[.01,.1,.1,.1],frame_bounds=[.03,.3,.3,.3],outer_iterations=3,max_nfev=40))
with (TD/'TASK.yaml').open('x') as f:yaml.safe_dump(t,f,sort_keys=False,allow_unicode=True)
write(TD/'TASK_FREEZE.json',dict(task_sha256=sha256(TD/'TASK.yaml'),baseline=t['structural']['baseline_commit'],configuration_sha256=sha256(TD/'TASK.yaml'),code_lock_sha256=sha256(TD/'inputs/CODE_LOCK.json'),purpose='Pre-execution freeze; no GT outcome examined'))
print(TD/'TASK.yaml')
