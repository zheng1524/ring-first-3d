"""Freeze the separately approved simulation protocol; never overwrite a TASK."""
from _bootstrap import ROOT
from policy import make_task
from pathlib import Path
import json,hashlib,subprocess,datetime,yaml
from ring_first_3d.policy.sim_contracts import TASK_ID,SIM_STAGES,EXTRA,CONDITIONS
from ring_first_3d.contracts.identities import sha256


def main():
    td=ROOT/'experiments'/TASK_ID
    if(td/'TASK.yaml').exists():raise FileExistsError('Frozen revision already exists')
    td.mkdir(parents=True,exist_ok=True)
    old=ROOT/'experiments/TASK-E4-G01-DUALVIDEO-BODY-ANCHORED-REGISTRATION-001'
    (td/'inputs').mkdir();manifest=td/'inputs/G01_DUALVIDEO_SOURCES.json';manifest.write_bytes((old/'inputs/G01_DUALVIDEO_SOURCES.json').read_bytes())
    paths={'models':'experiments/TASK-E4-A1-COARSE-BODY-001/code/models.py','common':'experiments/TASK-E4-A1-ELLIPSE-VS-FULLMASK-001/code/common.py','losses':'experiments/TASK-E4-A1-ELLIPSE-VS-FULLMASK-001/code/losses.py','solver':'experiments/TASK-E4-A1-ELLIPSE-VS-FULLMASK-001/code/fitting.py','current':'experiments/TASK-E4-BODY-GUIDED-HERO-DXY-REPAIR-001/code/fitting.py'}
    sources={}
    for key,path in paths.items():
        raw=subprocess.check_output(['git','-C',str(ROOT),'show','5636aaebd61a3d53b69f528692c4c7095df46508:'+path]);sources[key]=dict(path=path,commit='5636aaebd61a3d53b69f528692c4c7095df46508',sha256=hashlib.sha256(raw).hexdigest())
    lock=td/'inputs/SIM_SOURCE_LOCK.json';lock.write_text(json.dumps(dict(sources=sources,modules={mid:sources[k]for mid,k in [('T05','models'),('T06','losses'),('T07','losses'),('T08','solver'),('T09','current')]}),indent=2)+'\n')
    make_task(TASK_ID,td/'TASK.yaml');t=yaml.safe_load((td/'TASK.yaml').read_text());t['schema']=4;t['modules']+=list(EXTRA)
    oldtask=yaml.safe_load((old/'TASK.yaml').read_text());assets=oldtask['dualvideo']['assets'].copy()
    rec=lambda p:dict(path=str(p.resolve()),sha256=sha256(p))
    assets['source_manifest']=rec(manifest);assets['reuse_lock']=rec(lock)
    assets['previous_report']=rec(old/'TECHNICAL_REPORT.md');assets['previous_failure_registry']=rec(old/'FAILURE_REGISTRY.json');assets['previous_task_freeze']=rec(old/'TASK_FREEZE.json')
    t['goal']='SIM_PROTOCOL_REV1: execute G01-like simulation, independent nine-parameter Body, mediated mapping and genuine full-surface shared-SE3 registration'
    t['authorization']['reference']='User explicitly approved SIM_PROTOCOL_REV1: realism is quality only; complete G1-G4 with strict internal contracts'
    t['authorization']['stages']=list(SIM_STAGES);t['acceptance']['required_stages']=list(SIM_STAGES)
    t['split']['GT']=['G01_generator_and_postfreeze_evaluator_only'];t['split']['access']='simulation_generator_predictor_evaluator'
    t['budget']=dict(max_seconds=7200,stage_timeout_seconds=1800,max_attempts_per_stage=2,max_output_bytes=800000000)
    t['sim']=dict(label='G01_LIKE_SIMULATION',proxy='SYNTHETIC_HERO_PROXY',assets=assets,
      condition_order=list(CONDITIONS),conditions=CONDITIONS,error_transforms={'I':[0.,0.],'A':[2.,.5],'B':[3.,.3]},
      error_axis=[0.,1.,0.],translation_axis=[1.,0.,0.],rotation_center_mm=[0.,0.,0.],action='left_world_SE3',seed=20261116,
      family_by_condition={s:'camera_local'if s=='L1'else'video_world'for s in CONDITIONS},
      placement_candidates_mm=[[0.,0.,0.],[0.,0.,-2.],[0.,0.,-4.],[0.,1.,-2.]],placement_selection='Lowest mean FIT-only synthetic-vs-real visible mask symmetric contour error; shared translation only, original geometry unchanged',
      realism_is_blocking=False,internal_geometry_is_blocking=True,body_frozen_during_registration=True,GT_selects_predictor=False,
      methods=['M0','M1','M2','RING_ONLY','M2_DIRECT','M2_RING'],initialization_order=['E1','E2','E1_PROXY'],
      initialization_views_per_video=4,initialization_starts=3,model_base=[0.,0.,-2.,0.,0.,0.,1.6094379124341003,1.6094379124341003,1.0986122886681098],
      mapping_radial_shrink=.97,mapping_samples_per_frame=96,registration_surface_samples=400,
      weights=dict(geometry=1.,mediated_anchors=.2,contour=.02,ring=10.),registration_outer_iterations=3,registration_max_nfev=60,
      registration_bounds_rotation_deg=8.,registration_bounds_translation_mm=2.,ICP_threshold_mm=1.5,ICP_iterations=60,
      image_wh=[640,360],surface_evaluation_threshold_mm=.1,relative_success_rotation_deg=.5,relative_success_translation_mm=.2,
      scientific_negative_does_not_stop=True)
    (td/'TASK.yaml').write_text(yaml.safe_dump(t,sort_keys=False,allow_unicode=True))
    receipt=dict(protocol='SIM_PROTOCOL_REV1',task_sha256=sha256(td/'TASK.yaml'),previous_delivery_commit='009112d0ceca23e968ef7a97de33ea6989c24b15',
      previous_TASK_sha256=sha256(old/'TASK.yaml'),previous_report_sha256=sha256(old/'TECHNICAL_REPORT.md'),frozen_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
      approved_revision='Realism no longer a blocking condition. Static shared rigid placement permitted; no scale changes. Primary S0-S4 revised by user; L1 separate.')
    (td/'TASK_FREEZE.json').write_text(json.dumps(receipt,indent=2)+'\n');print(td/'TASK.yaml')


if __name__=='__main__':main()
