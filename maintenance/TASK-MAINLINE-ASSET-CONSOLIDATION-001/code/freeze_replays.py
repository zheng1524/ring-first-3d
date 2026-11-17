"""Bind actual real inputs and historical tolerances before any module replay."""
import json,hashlib,os
from pathlib import Path
R=Path(__file__).resolve().parents[3];T=Path(__file__).resolve().parents[1];M=R/'mainline'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):p.parent.mkdir(exist_ok=True,parents=True);p.write_text(json.dumps(x,indent=2)+'\n')
core=Path('/home/liu/ring-first-hero-core');old018=Path('/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-HERO-BODY-ADAPT-018');view=Path('/home/liu/ring_first_3d_view_eval/experiments/TASK-VIEW-OBSERVABILITY-GT-EVAL-001')
config=json.loads((core/'site_config.local.json').read_text());config['readonly_dependency_paths']=[str(R/'.runtime/extra_packages')if'e4_sdf_evolution'in p else p for p in config['readonly_dependency_paths']]
config.update(controlled_example=str(core/'.local_data/G01_demo'),historical_hero_output=str(core/'outputs/hero'),depth_reference_root=str(old018),depth_arm='B2_TRUSTED_COH16',a_to_b_reference_root=str(view),a_to_b_cases='/home/liu/ring_first_3d_incremental/experiments/TASK-PHASED-INCREMENTAL-FUSION-MULTIGROUP-001/provenance/CASES.json',python='/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python',blender='/home/liu/blender/blender-5.0.1-linux-x64/blender')
save(M/'configs/SITE.local.json',config)
tol=dict(camera_max_abs=1e-10,hero_depth_comparison='BITWISE',initial_mesh_comparison='BITWISE',mesh_vertices_max_mm=1e-5,mesh_faces_comparison='EXACT',projection_IoU_abs=1e-12,boundary_MAE_abs_px=1e-12,a_to_b_valid_and_RGBA='BITWISE',a_to_b_depth='BITWISE',loss_abs=1e-7,gradient_relative_norm=1e-4,
    provenance=dict(camera='ring-first-hero-core/tests/test_real_example.py',hero='same real-example frozen bitwise history comparison',mesh='Growth Recovery exact restoration1e-5mm contract',projection='ProjectionGate existing1e-12 non-regression numerical slack',loss='historical train018 FULL_FIT_OBJECTIVE epsilon1e-7',gradient='historical tape.py additivity_relative_error threshold1e-4'),post_result_relaxation=False)
save(M/'configs/REPLAY_TOLERANCES.json',tol)
sources=json.loads((R/'src/ring_first_3d/mainline/lineage/experiments/TASK-E4-2D-CONTOUR-GUIDED-INIT-A-HERO-001/inputs/SOURCES.json').read_text())
external={}
def add(p,purpose):
    p=Path(p)
    if not p.is_file():return
    if str(p)not in external:external[str(p)]=dict(path=str(p),size_bytes=p.stat().st_size,sha256=sha(p),source='retained real scientific asset / existing official runtime',purpose=purpose,available=True,LOCAL_ONLY=True)
for p in(core/'.local_data/G01_demo').rglob('*'):
    if p.is_file():add(p,'real Ring-First and fresh official HERO fixed-sample replay')
add(config['checkpoint'],'official HERO checkpoint; never copied')
add(config['blender'],'existing exact Boolean backend')
for case in sources['cases']:
    if case['case']not in ['G01','G03']:continue
    for a in case['static'].values():add(a['path'],'frozen shared-body data and Ring CAD')
    for v in case['FIT']+case['HOLDOUT']:add(v['cache']['path'],'frozen camera / RGB / Polyp Mask / Ring Mask / split')
    add(case['resolved013_initial']['path'],'EXACT_013_INPUT_MESH_V_F_SOLID_CAP')
pair=json.loads((view/'provenance/A_TO_B_PAIRS_BEFORE_RENDER.json').read_text())['pairs'][0]
cases=json.loads(Path(config['a_to_b_cases']).read_text());case=next(c for c in cases if c['id']==pair['A'])
for key in ['source_points','pack','RGB','mesh']:add(case[key],'actual frozen A->B source surface')
for key in ['RGB','Mask']:add(pair['B_target'][key],'A->B independent target evaluation only')
add('/home/liu/polyp_research/ring_anchor_3d/experiments/surface_fusion_v2/inputs/R10_ring.obj','A->B exact historical R10 CAD')
reference=view/'local_results/reprojection'/(pair['pair_id']+'.npz');add(reference,'historical frozen A->B output comparison')
save(M/'configs/A_TO_B_SAMPLE.json',dict(pair=pair,source=case,historical_output=str(reference)))
arm=old018/'arms'/config['depth_arm'];armcfg=json.loads((arm/'config/ARM.json').read_text());ref=json.loads((arm/'metrics/G01_INITIAL_GRADIENTS.json').read_text());chosen=next(x for x in ref if x.get('term')=='HERO')
add(arm/'config/ARM.json','fixed historical018 arm; no new training')
for p in(arm/'inputs/G01').iterdir():
    if p.is_file():add(p,'historical native-depth forward and gradient sample inputs')
case_weights=arm/'metrics/G01_HERO_WEIGHTS.json'
ids=json.loads(case_weights.read_text())['ids']
add(case_weights,'actual per-case frozen HERO block identities; shared ARM.json was overwritten by another historical case')
assert all(cid.startswith('G01_')for cid in ids) and chosen['view']in ids
for cid in ids:
    add(old018/'hero_fit'/cid/'OBS_TRUSTED.npz','T30 native observations, distinct from T28')
    add(old018/'hero_fit'/cid/'SOURCE.json','native pixel/face source binding')
add(arm/'local_results/G01/INITIAL_COMPONENT_GRADIENTS.npz','historical gradient array, evaluation reference only')
add(arm/'metrics/G01_INITIAL_GRADIENTS.json','historical loss and gradient scalars')
save(M/'configs/DEPTH_SAMPLE.json',dict(case='G01',arm=config['depth_arm'],view=chosen['view'],HERO_views=ids,history_scalar=chosen,history_gradients=str(arm/'local_results/G01/INITIAL_COMPONENT_GRADIENTS.npz'),history_arm_root=str(arm),root_hero_fit=str(old018)))
save(M/'manifests/EXTERNAL_INPUTS.json',dict(assets=list(external.values()),large_assets_not_copied=True,official_checkpoint_SHA256='00878bab903b1d384cd6bb9ea092e247a9036d429cb8bcc3d6dcbb81f67e556d',DXY_readonly_not_copied=True))
files=[p for d in ['src/ring_first_3d','tools/research','tests','mainline/configs','mainline/results']for p in(R/d).rglob('*')if p.is_file()and p.suffix in ['.py','.json','.yaml','.npz','.csv']]
save(M/'manifests/REPLAY_INPUT_FREEZE.json',dict(before_replays=True,revision=4,source_files=[dict(path=str(p.relative_to(R)),sha256=sha(p))for p in files],external_manifest_sha256=sha(M/'manifests/EXTERNAL_INPUTS.json'),runtime_manifest_sha256=sha(M/'manifests/RUNTIME_FILES.json'),tolerances_sha256=sha(M/'configs/REPLAY_TOLERANCES.json'),scientific_state='ACTIVE_RESEARCH_MAINLINE',GT_optimization=False,parameters_changed=False,engineering_repair='Actual per-case HERO identities and exact013 original container retained; complete shared-source and small frozen-input closure now explicitly locked. Numeric tolerances unchanged.'))
print('Frozen real external assets',len(external),'and',len(files),'source/config files')
