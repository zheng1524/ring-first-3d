"""Freeze user-clarified scope before any scene measurements or perturbations."""
from _bootstrap import ROOT
from pathlib import Path
import json,subprocess,hashlib,datetime,yaml
from policy import make_task
from ring_first_3d.contracts.identities import sha256


def main():
    tid='TASK-E4-G01-DUALVIDEO-BODY-ANCHORED-REGISTRATION-001';td=ROOT/'experiments'/tid
    if (td/'TASK.yaml').exists():raise FileExistsError('Never overwrite frozen TASK')
    inp=td/'inputs';inp.mkdir(parents=True,exist_ok=True)
    raw=subprocess.check_output(['git','show','5636aaebd61a3d53b69f528692c4c7095df46508:experiments/TASK-E4-BODY-GUIDED-HERO-DXY-REPAIR-001/config/SOURCE_BINDING.json'])
    fit=[x for x in json.loads(raw)if x['group']=='G01'and x['video']in ['004','005']]
    mx=Path('/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001');hp=mx/'config/PROTECTED_HOLDOUT.json'
    held=[x for x in json.loads(hp.read_text())if x.get('case')=='G01'and x.get('video')in ['004','005']]
    def rec(p):
        base,separator,fragment=str(p).partition('#');p=Path(base)
        value=dict(path=str(p.resolve()),sha256=sha256(p),bytes=p.stat().st_size)
        if separator:value['fragment']=fragment
        return value
    rows=[]
    for x in fit:
        rows.append(dict(source_id=x['source_id'],view_id=x['view_id'],video=x['video'],role='FIT',cache=x['cache'],RGB_source=x['RGB_source'],Mask_source=x['Mask_source'],RGB_content_SHA=x['RGB_content_SHA'],Mask_content_SHA=x['Mask_content_SHA'],K=x['K'],Camera_to_Ring=x['C'],pose_origin=x['pose_origin'],ring=x['ring_source'],native_pose_source='Native cache T; never substitute pool_C',pool_pose_delta_mm=x.get('pool_pose_delta_mm')))
    for x in held:
        rows.append(dict(source_id='HELD__'+x['id'],view_id=x['id'],video=x['video'],role='HOLDOUT',cache=rec(x['cache']),RGB_source=rec(x['RGB_source']),Mask_source=rec(x['Mask_source']),RGB_content_SHA=x.get('RGB_content_sha',x.get('RGB_content_SHA256')),Mask_content_SHA=x.get('Mask_content_sha',x.get('Mask_content_SHA256')),K=x['K'],Camera_to_Ring=x.get('RF_native',x['T_original']),pose_origin=rec(x['pose_source']),ring=rec(x['ring_path']),native_pose_source='Protected explicit RF_native/T_original, never corrected T/H0',corrected_camera_metadata=x['T']))
    manifest=inp/'G01_DUALVIDEO_SOURCES.json'
    manifest.write_text(json.dumps(dict(source_commit='5636aaebd61a3d53b69f528692c4c7095df46508',source_binding_sha256=hashlib.sha256(raw).hexdigest(),holdout_manifest=rec(hp),rows=rows,world_frames={'004':'native_Ring_004','005':'native_Ring_005'},shared_world_certified=False),indent=2)+'\n')
    make_task(tid,td/'TASK.yaml');task=yaml.safe_load((td/'TASK.yaml').read_text());task['schema']=3
    task['goal']='G01 authentic dual-video scene gate, then GT-free frozen coarse Body/full local mesh registration only after all gates pass'
    task['modules']+=['DV01'];stages=['preflight','contracts','dualvideo_regression','G0_scene_audit','G1_initialize','G2_mapping_predict','G2_mapping_evaluate','G3_register','G4_evaluate','artifacts']
    task['authorization']['stages']=stages;task['authorization']['reference']='User clarified: S1/S2 world A/B on 004; S3 local A on 004; S4 local B on 005'
    task['acceptance']['required_stages']=list(stages)
    p14=Path('/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-PYTORCH3D-014');p13=Path('/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/FREE_VERTEX_013')
    assets=dict(source_manifest=rec(manifest),blend=rec('/home/liu/polyp_research/01p型/01p-12-/息肉.blend'),gt_cache=rec(p14/'evaluation_only/G01/ORIGINAL_BLENDER_GT_MM.npz'),gt_extraction=rec(p13/'evaluation_only/G01/GT_EXTRACTION.json'),blender_binary=rec('/home/liu/blender/blender-5.0.1-linux-x64/blender'))
    assets={k:{'path':v['path'],'sha256':v['sha256']}for k,v in assets.items()}
    conditions={
      'S0':dict(video=None,family='none',rotation_y_deg=0.,translation_x_mm=0.),
      'S1':dict(video='004',family='video_world',rotation_y_deg=2.,translation_x_mm=.5),
      'S2':dict(video='004',family='video_world',rotation_y_deg=3.,translation_x_mm=.3),
      'S3':dict(video='004',family='camera_to_ring',rotation_y_deg=2.,translation_x_mm=.5),
      'S4':dict(video='005',family='camera_to_ring',rotation_y_deg=3.,translation_x_mm=.3)}
    task['dualvideo']=dict(assets=assets,condition_order=list(conditions),conditions=conditions,
      frame_policy='Independent native Ring frames; no certified common frame assumed',
      world_injection='Left multiply cameras, Ring and full Mesh by same SE3; T_R_C invariant',
      local_injection='Shared Ring-local left SE3 on cameras and observation-derived Mesh; Ring fixed; camera-to-Ring changes; never mix families',
      Ring_to_Body_policy='Require source-supported fixed transform; do not assume Blender author world equals either native Ring frame',
      body_initialization='Official DXY E1/full Mask E2 plus nine parameters; GT prohibited; freeze before registration',
      registration='One shared SE3 per video; unchanged full local triangle meshes; no point-to-Body replacement',
      gates=dict(min_observed_ring_pixels=20,observed_ring_CAD_support_within2px_min=.95,observed_to_full_CAD_boundary_p95_px_max=3.,require_GT_Ring_fixed_pose_certificate=True,require_camera_to_ring_native_binding=True,require_distinct_004_005_trajectories=True),
      evaluation=dict(parameters_selected_using_GT=False,read_GT_only_for_generation_and_postfreeze_evaluation=True,report_all_conditions=True,report_NaN_and_full_denominator=True,freeze_before_GT_evaluation=True),
      source_frame_count={v:sum(x['video']==v for x in rows)for v in ['004','005']})
    task['split']['GT']=['G01_original_blender_scene_audit_only_until_G0_pass'];task['split']['access']='dualvideo_scene_gate_then_generator_predictor_evaluator'
    task['budget']=dict(max_seconds=1800,stage_timeout_seconds=300,max_attempts_per_stage=2,max_output_bytes=300000000)
    p=td/'TASK.yaml';p.write_text(yaml.safe_dump(task,sort_keys=False,allow_unicode=True))
    (td/'TASK_FREEZE.json').write_text(json.dumps(dict(task_sha256=sha256(p),source_manifest_sha256=sha256(manifest),baseline_commit='083ad67ab4b6a8432fb631201b8abafe7df2ee13',frozen_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),condition_clarification='S3=004 local A; S4=005 local B',injection_before_scene_pass=False),indent=2)+'\n')
    print('TASK FROZEN',sha256(p),'frames',task['dualvideo']['source_frame_count'])


if __name__=='__main__':main()
