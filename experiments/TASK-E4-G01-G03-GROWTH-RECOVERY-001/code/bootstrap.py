"""Create new immutable protocol and source/input locks; never rewrite a freeze."""
import copy,json,sys,yaml
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'src'))
from io_utils import TD,OLD,OLD_ROOT,read,sha,source_folder
from ring_first_3d.policy.recovery_contracts import RECOVERY_STAGES,NEW_MODULES
from ring_first_3d.policy.contracts import MODULES
from union_mesh import BLENDER
def rec(p):
    p=Path(p).resolve();return dict(path=str(p),sha256=sha(p))
def write(p,x):
    with Path(p).open('x')as f:json.dump(x,f,indent=2);f.write('\n')

t=copy.deepcopy(yaml.safe_load((OLD/'TASK.yaml').read_text()));t.pop('structured')
t.update(schema=11,task_id=TD.name,goal='Recover the actual G01/G03 iteration24 rejected sweeps with bounded embedding, exact union, fresh 2D gates and current-only Ring non-worsening; fixed Body, no HERO',modules=list(MODULES)+list(NEW_MODULES),output_root=str(TD/'runs'))
t['inputs']['source_lock']=rec(ROOT/'src/ring_first_3d/source_lock.json')
t['authorization'].update(reference='Explicit user TASK-E4-G01-G03-GROWTH-RECOVERY-001; supplied TASK.md',stages=list(RECOVERY_STAGES));t['acceptance']['required_stages']=list(RECOVERY_STAGES)
t['budget'].update(max_seconds=7200,stage_timeout_seconds=2400,max_attempts_per_stage=2,max_output_bytes=140000000)
source=Path('/home/liu/ring_first_3d_structural_update/experiments/TASK-E4-2D-CONTOUR-GUIDED-INIT-A-HERO-001/inputs/SOURCES.json')
files=[rec(source),rec(OLD/'TASK.yaml'),rec(OLD/'TECHNICAL_REPORT.md'),rec(OLD/'FAILURE_REGISTRY.json'),rec(TD/'TASK.md'),rec(TD/'inputs/RECOVERY_CONFIGURATION.json'),rec(BLENDER)]
for row in read(source)['cases']:
    if row['case']not in ['G01','G03']:continue
    folder=source_folder(row['case'])
    files +=[rec(folder/f)for f in ['INITIAL.npz','STEP_024/BODY.npz','STEP_024/GRAPH.npz','UPDATES.json','GROWTH_PROPOSAL_024/BODY.npz','GROWTH_PROPOSAL_024/SWEEP.npz']]
    files +=[rec(v['cache']['path'])for v in row['FIT']+row['HOLDOUT']]
    files +=[rec(r['path'])for r in row['static'].values()]
    files +=[rec(row['GT']['path'])]
for directory in [OLD/'code',Path('/home/liu/ring_first_3d_structural_update/experiments/TASK-E4-MULTIVIEW-STRUCTURAL-UPDATE-001/code'),ROOT/'experiments/TASK-E4-2D-CONTOUR-GUIDED-INIT-A-HERO-001/legacy015']:
    files +=[rec(p)for p in sorted(directory.glob('*.py'))]
write(TD/'inputs/INPUT_MANIFEST.json',dict(files=list({r['path']:r for r in files}.values()),GT_hash_identity_only_before_prediction=True,cases=['G01','G03']))
write(TD/'inputs/CODE_LOCK.json',dict(files=[rec(p)for d in ['code','tests']for p in sorted((TD/d).glob('*.py'))]))
t['recovery']=dict(baseline_commit='238c2da1cd842c0eba710a4ec44db5f437bff8e4',baseline_root=str(OLD_ROOT),cases=['G01','G03'],arm='DEFORM_SWEEP_RECOVERY',iteration=24,max_candidates_per_case=1,Body_fixed=True,camera_optimization=False,HERO_read=False,GT_selects_prediction=False,sources=str(source),blender_binary=rec(BLENDER),code_lock=rec(TD/'inputs/CODE_LOCK.json'),input_manifest=rec(TD/'inputs/INPUT_MANIFEST.json'),configuration=rec(TD/'inputs/RECOVERY_CONFIGURATION.json'),update=dict(continuation_fractions=[.35,.7,1.],iterations_per_stage=8,backtracks=4,control_lr_mm=.02,radius_lr=.03,control_trust_mm=.35,radius_logit_trust=1.,lambda_clearance=1.,lambda_bend=.01,lambda_radius=.01,lambda_attachment=.01,lambda_embed=1.,min_exposed_mm=.1,max_exposed_mm=6.,projection=dict(max_distance_px=40.,mutual_radius_px=0.,normal_cos_min=.5,max_tangent_px=8.)))
with (TD/'TASK.yaml').open('x')as f:yaml.safe_dump(t,f,sort_keys=False,allow_unicode=True)
write(TD/'TASK_FREEZE.json',dict(task_sha256=sha(TD/'TASK.yaml'),code_lock_sha256=sha(TD/'inputs/CODE_LOCK.json'),baseline=t['recovery']['baseline_commit'],embedding_and_tolerance_before_prediction=True,purpose='Only G01/G03; before local optimization and before independent GT evaluation'))
print(TD/'TASK.yaml')
