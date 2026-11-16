"""Bind baseline algorithms and real native HERO observations before execution."""
from _bootstrap import ROOT
from pathlib import Path
import json,copy,datetime,yaml
from ring_first_3d.contracts.identities import sha256
from ring_first_3d.policy.stress_contracts import TASK_ID,BASELINE,STRESS_STAGES,STRESS_MODULES,CONDITIONS,CTF
from ring_first_3d.policy.artifacts import read_state,check_artifacts

def main():
 td=ROOT/'experiments'/TASK_ID;td.mkdir(parents=True,exist_ok=True);inp=td/'inputs';inp.mkdir(exist_ok=True)
 if(td/'TASK.yaml').exists():raise FileExistsError('Frozen task exists')
 parent=Path('/home/liu/ring_first_3d_g01_multisurface/experiments/TASK-E4-G01-MULTISURFACE-BODY-FUSION-001');run=parent/'runs/MULTISURFACE_001';state=read_state(run);assert state['accepted'];check_artifacts(run,state)
 p=yaml.safe_load((parent/'TASK.yaml').read_text());(inp/'PARENT_TASK.json').write_text(json.dumps(p,indent=2)+'\n')
 files=[]
 for base in ['multisurface','sim','synthetic','contracts']:
  for f in sorted((ROOT/'src/ring_first_3d'/base).glob('*.py')):files.append(dict(path=str(f.relative_to(ROOT)),sha256=sha256(f)))
 (inp/'ALGORITHM_LOCK.json').write_text(json.dumps(dict(commit=BASELINE,files=files),indent=2)+'\n')
 repo=Path('/home/liu/polyp_research/ring-first-3d/experiments');maxroot=repo/'TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001';repair=repo/'TASK-E4-BODY-GUIDED-HERO-DXY-REPAIR-001';inf=maxroot/'metrics/HERO_INFERENCE_RESULTS.json';rs=json.loads(inf.read_text());conf=json.loads((maxroot/'config/FOUR_GROUP_INPUTS.json').read_text())
 def rec(p):
  p=Path(p);return dict(path=str(p.resolve()),sha256=sha256(p))if p.is_file()else dict(path=str(p),sha256=None,missing=True)
 groups=[]
 for g in ['G01','G03','G05']:
  rows=[r for r in rs if r.get('group')==g and r.get('success') and '_photo'not in r['id']];views=[];excluded=[]
  for video in ['004','005']:
   options=[r for r in rows if '_v'+video+'_'in r['id']or'video'+video+'_'in r['id']]
   for i,r in enumerate(options[:3]):
    dxy=repair/'provenance/dxy_records'/('MAX__'+r['id']+'.json');d=json.loads(dxy.read_text())if dxy.exists()else{}
    assets={k:rec(r[k])for k in ['native','pack','points','mesh']};assets['raw_mesh']=rec(Path(r['native']).parent/'RAW_NATIVE_MESH.npz');assets['dxy']=rec(dxy)
    for k in ['cache','source_RGB','source_Mask']:
     if k in d:assets[k]=rec(d[k]['path'])
    views.append(dict(id=r['id'],group=g,video=video,role='FIT'if i<2 else'HOLDOUT',K=r['K'],C=r['C'],unit=r['unit'],depth_definition=r['depth_definition'],source_ids=r['source_ids'],target_RGB_SHA=r['target_SHA'],assets=assets,qualification='ARCHIVED_RING_FIRST_CAMERA; absolute accuracy NOT_EVALUABLE'))
   excluded.extend(r['id']for r in options[3:])
  c=next(c for c in conf if c['group']==g)
  groups.append(dict(group=g,difficult_group=g=='G03',available_native_views=len(rows),views=views,not_selected=excluded,assets=dict(ring=rec(c['ring']['path'])),world_status='Archived Ring-First world convention, cross-video deployment is not independently certified'))
 (inp/'REAL_SOURCES.json').write_text(json.dumps(dict(groups=groups,inference_ledger=rec(inf),selection='Original inference order within each real video; first two FIT, next one HOLDOUT. No GT, geometry-error ranking or historical measurement fallback.',raw_HERO_only=True),indent=2)+'\n')
 t=copy.deepcopy(p);t['schema']=6;t['task_id']=TASK_ID;t['goal']='Frozen algorithm variance stress and source-bound minimal real HERO adapter pilot; no camera/DXY/HERO training changes';t['modules']+=list(STRESS_MODULES)
 for k in ['fixture','support','reference']:t['inputs'][k]=rec(ROOT/'tools/research'/Path(t['inputs'][k]['path']).name)
 t['inputs']['source_lock']=rec(ROOT/'src/ring_first_3d/source_lock.json');t['inputs']['evidence']=rec(ROOT/'experiments/TASK-RESEARCH-HARNESS-STORAGE-001/figures/REAL_SMOKE_EVIDENCE.png')
 t['authorization']['reference']='User-approved TASK-E4-MULTISURFACE-STRESS-AND-REAL-PILOT-001; retained baseline algorithms, independently named CTF, no GT real accuracy claim';t['authorization']['stages']=list(STRESS_STAGES);t['acceptance']['required_stages']=list(STRESS_STAGES);t['output_root']=str(td/'runs');t['budget']=dict(max_seconds=7200,stage_timeout_seconds=1800,max_attempts_per_stage=2,max_output_bytes=1300000000)
 t['fusion'].update(conditions=CONDITIONS,condition_order=list(CONDITIONS),tolerance_ablation_mm=[],main_figure_condition='C7')
 t['stress']=dict(baseline_commit=BASELINE,parent_multisurface_run=str(run),assets=dict(parent_task_json=rec(inp/'PARENT_TASK.json'),algorithm_lock=rec(inp/'ALGORITHM_LOCK.json'),real_manifest=rec(inp/'REAL_SOURCES.json'),parent_run_freeze=rec(run/'FREEZE.json'),parent_result=rec(parent/'SCIENTIFIC_RESULT.json'),parent_failure_registry=rec(parent/'FAILURE_REGISTRY.json')),ctf=CTF,real_groups=['G01','G03','G05'],real_frame_prior_sigma_deg_mm=[.3,.1],real_max_FIT_per_video=2,real_HOLDOUT_per_video=1,real_initializer='Fresh FIT-only E1 formal ellipse and E2 full-mask nine-parameter fits; E1 primary if all formal candidates exist, otherwise explicit E2',real_initial_base=[0.,0.,-3.5,0.,0.,0.,1.3862943611198906,1.3862943611198906,1.6094379124341003],real_initial_starts=1,real_absolute_GT='NOT_AVAILABLE',smoke_conditions=['C0','C6'])
 (td/'TASK.yaml').write_text(yaml.safe_dump(t,sort_keys=False,allow_unicode=True));(td/'TASK_FREEZE.json').write_text(json.dumps(dict(task_sha256=sha256(td/'TASK.yaml'),baseline_commit=BASELINE,UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),selection_before_metrics=True,history_measurement_fallback=0,GT_algorithm_selection=False),indent=2)+'\n');print(td/'TASK.yaml')
if __name__=='__main__':main()
