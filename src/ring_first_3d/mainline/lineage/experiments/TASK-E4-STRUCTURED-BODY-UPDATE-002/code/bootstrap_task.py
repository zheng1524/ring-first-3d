"""One-time pre-experiment source/config lock; refuses to overwrite any freeze."""
from ring_first_3d.mainline.paths import historical_path as _mainline_path
from pathlib import Path
import json,sys,copy,yaml
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'src'))
from ring_first_3d.contracts.identities import sha256
from ring_first_3d.policy.structured_contracts import STRUCTURED_STAGES,NEW_MODULES
from ring_first_3d.policy.contracts import MODULES
TD=Path(__file__).resolve().parents[1];OLD=Path(str(_mainline_path('/home/liu/ring_first_3d_structural_update/experiments/TASK-E4-MULTIVIEW-STRUCTURAL-UPDATE-001')));SOURCE=OLD.parent/'TASK-E4-2D-CONTOUR-GUIDED-INIT-A-HERO-001/inputs/SOURCES.json'
def rec(p):
 p=Path(p).resolve();return dict(path=str(p),sha256=sha256(p))
def write(p,v):
 with p.open('x')as f:json.dump(v,f,indent=2);f.write('\n')
t=copy.deepcopy(yaml.safe_load((OLD/'TASK.yaml').read_text()));t.pop('structural');t.update(schema=10,task_id=TD.name,goal='Real G01/G03/G05 matched graph Smooth-ARAP and evidence-gated B-spline RMF sweep update; no HERO, no C0',modules=list(MODULES)+list(NEW_MODULES),output_root=str(TD/'runs'))
t['inputs']['source_lock']=rec(ROOT/'src/ring_first_3d/source_lock.json')
t['authorization'].update(reference='Explicit user TASK-E4-STRUCTURED-BODY-UPDATE-002',stages=list(STRUCTURED_STAGES));t['acceptance']['required_stages']=list(STRUCTURED_STAGES);t['budget'].update(max_output_bytes=450000000)
files=[rec(SOURCE),rec(OLD/'TASK.yaml'),rec(OLD/'TECHNICAL_REPORT.md'),rec(OLD/'FAILURE_REGISTRY.json')]
src=json.loads(SOURCE.read_text())
for r in src['cases']:
 if r['case']not in ['G01','G03','G05']:continue
 files +=[rec(r['resolved013_initial']['path']),rec(r['GT']['path'])]+[rec(x['path'])for x in r['static'].values()]
 files +=[rec(v['cache']['path'])for v in r['FIT']+r['HOLDOUT']]
 files.append(rec(OLD/f'runs/STRUCTURAL_004/attempts/0009-G5_real_update-842b9067/{r["case"]}/DEFORM_GROW/FINAL.npz'))
for directory in [OLD/'code',SOURCE.parents[1]/'legacy015']:
 files +=[rec(p)for p in directory.glob('*.py')]
files +=[rec(p)for p in (ROOT/'experiments/TASK-E4-2D-CONTOUR-GUIDED-INIT-A-HERO-001/legacy015').glob('*.py')]
files +=[rec(p)for p in [ROOT/'src/ring_first_3d/contour_guided/correspondence.py',ROOT/'src/ring_first_3d/synthetic/raster.py']]
write(TD/'inputs/INPUT_MANIFEST.json',dict(files=list({x['path']:x for x in files}.values()),GT_identity_hash_only_before_prediction=True))
write(TD/'inputs/CODE_LOCK.json',dict(files=[rec(p)for d in ['code','tests']for p in sorted((TD/d).glob('*.py'))]))
t['structured']=dict(baseline_commit='7c471701f38f1577ba506bc8ed1e38774f99dabe',initialization='EXACT_013_INPUT_MESH_V_F_SOLID_CAP',cases=['G01','G03','G05'],arms=['DEFORM_ONLY','DEFORM_SWEEP'],camera_optimization=False,HERO_read=False,GT_selects_prediction=False,sources=str(SOURCE),code_lock=rec(TD/'inputs/CODE_LOCK.json'),input_manifest=rec(TD/'inputs/INPUT_MANIFEST.json'),protection=dict(initial_IoU_min=.8,max_IoU_drop=.01,max_boundary_increase_px=1.),update=dict(iterations=36,inner_steps=3,line_search_steps=8,graph_nodes=32,sarap_lambda=.7,projection=dict(max_distance_px=40.,mutual_radius_px=0.,normal_cos_min=.5,max_tangent_px=8.),rotation_lr_rad=.002,translation_lr_mm=.01,sweep_lr_mm=.01,lambda_graph=.03,lambda_sarap=.01,lambda_prior=.002,lambda_centerline=.01,lambda_radius=.01,lambda_attachment=.01,growth_iterations=[12,24],growth_min_view_IoU=.5,max_sweep_length_mm=6.,max_sweep_radius_mm=3.,min_growth_region_gain=.0001,growth=dict(growth_patch_rings=2,growth_max_patch_faces=80,growth_min_singular_ratio=.02,growth_max_inconsistency=.5,growth_min_mm=.1,growth_candidates=2)))
with (TD/'TASK.yaml').open('x')as f:yaml.safe_dump(t,f,sort_keys=False,allow_unicode=True)
write(TD/'TASK_FREEZE.json',dict(task_sha256=sha256(TD/'TASK.yaml'),code_lock_sha256=sha256(TD/'inputs/CODE_LOCK.json'),baseline=t['structured']['baseline_commit'],purpose='Before real execution and before independent GT evaluation'))
print(TD/'TASK.yaml')
