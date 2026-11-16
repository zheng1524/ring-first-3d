"""Freeze exact sources, view selection and complete protocol before simulation."""
from _bootstrap import ROOT
from policy import make_task
import json,datetime,yaml,shutil
from pathlib import Path
import numpy as np
from ring_first_3d.contracts.identities import sha256
from ring_first_3d.policy.fusion_contracts import TASK_ID,FUSION_STAGES,MODULE_FILES,CONDITIONS,REUSED


def main():
    td=ROOT/'experiments'/TASK_ID
    if(td/'TASK.yaml').exists():raise FileExistsError('Never overwrite frozen task')
    td.mkdir(parents=True,exist_ok=True);inp=td/'inputs';inp.mkdir()
    parent=Path('/home/liu/ring_first_3d_g01_sim_rev1/experiments/TASK-E4-G01-DUALVIDEO-BODY-ANCHORED-REGISTRATION-001-SIM-PROTOCOL-REV1/runs/SIM_REV1_001')
    from ring_first_3d.synthetic.io import fetch
    bodyfreeze=json.loads(fetch(parent,'G1_initialize','BODY_FREEZE.json').read_text());old=ROOT/'experiments/TASK-E4-G01-DUALVIDEO-BODY-ANCHORED-REGISTRATION-001-SIM-PROTOCOL-REV1'
    original=json.loads((old/'inputs/G01_DUALVIDEO_SOURCES.json').read_text());selected=[]
    for video in ['004','005']:
        pool=sorted([r for r in original['rows']if r['video']==video and r['role']=='FIT'],key=lambda r:r['view_id'])
        chosen=[i for i,r in enumerate(pool)if r['view_id']in bodyfreeze['fit_ids']]
        directions=np.array([np.asarray(r['Camera_to_Ring'])[:3,3]for r in pool]);directions/=np.linalg.norm(directions,axis=1)[:,None]
        while len(chosen)<8:
            scores=[-1 if i in chosen else min(np.arccos(np.clip(directions[i]@directions[j],-1,1))for j in chosen)for i in range(len(pool))]
            chosen.append(int(np.argmax(scores)))
        selected.extend(pool[i]for i in sorted(chosen))
    held=[r for r in original['rows']if r['role']=='HOLDOUT']
    manifest=inp/'VIEW_SOURCES.json';manifest.write_text(json.dumps(dict(selected=selected,HOLDOUT=held,selection='Keep all parent Body FIT references, then angular farthest-point in native camera-to-Ring directions; no GT selection',parent_body_fit_ids=bodyfreeze['fit_ids'],GT_shape_reused_only_by_generator=True),indent=2)+'\n')
    for arm in ['E1','E2']:shutil.copyfile(fetch(parent,'G1_initialize',arm+'_body.npz'),inp/(arm+'_INITIALIZER.npz'))
    for name in ['BODY_FREEZE.json','IMAGE_FITS.json','REUSE_RECEIPTS.json']:shutil.copyfile(fetch(parent,'G1_initialize',name),inp/name)
    shutil.copyfile(old/'inputs/SIM_SOURCE_LOCK.json',inp/'SIM_SOURCE_LOCK.json')
    rec=lambda p:dict(path=str(Path(p).resolve()),sha256=sha256(p))
    assets=dict(source_manifest=rec(manifest),virtual_gt=rec(fetch(parent,'G0_simulate','private/virtual_GT.npz')),
        ring=rec(fetch(parent,'G0_simulate','public/canonical_ring.npz')),E1_initializer=rec(inp/'E1_INITIALIZER.npz'),E2_initializer=rec(inp/'E2_INITIALIZER.npz'),
        body_freeze=rec(inp/'BODY_FREEZE.json'),image_fits=rec(inp/'IMAGE_FITS.json'),reuse_lock=rec(inp/'SIM_SOURCE_LOCK.json'),reuse_receipts=rec(inp/'REUSE_RECEIPTS.json'),
        parent_freeze=rec(parent/'FREEZE.json'),parent_failure_registry=rec(old/'FAILURE_REGISTRY.json'))
    make_task(TASK_ID,td/'TASK.yaml');t=yaml.safe_load((td/'TASK.yaml').read_text());t['schema']=5;t['modules']+=list(REUSED)+list(MODULE_FILES)
    t['goal']='Independent depth-grid multisurfaces with video bias/frame noise; Body-mediated localization and owned geometry fusion, no GT fitting'
    t['authorization']['reference']='Explicit user TASK-E4-G01-MULTISURFACE-BODY-FUSION-001; independently triangulated per-view proxy, hierarchical surface corrections, exact mesh sections first'
    t['authorization']['stages']=list(FUSION_STAGES);t['acceptance']['required_stages']=list(FUSION_STAGES);t['split']['GT']=['generator_and_postfreeze_evaluation_only'];t['split']['access']='multisurface_generator_predictor_evaluator'
    t['budget']=dict(max_seconds=7200,stage_timeout_seconds=1800,max_attempts_per_stage=2,max_output_bytes=900000000)
    t['fusion']=dict(assets=assets,parent_run=str(parent),label='G01_LIKE_SIMULATION',proxy='INDEPENDENT_DEPTH_GRID_SYNTHETIC_HERO_PROXY',condition_order=list(CONDITIONS),conditions=CONDITIONS,
      pose_model='VideoBias @ TruePose @ FrameNoise',seed=20261117,bias_parameters={'I':[0.,0.],'A':[2.,.5],'B':[3.,.3]},bias_axis='positive_world_Y; translation_positive_world_X; pivot_Ring_origin',
      noise_model='Gaussian local rotvec_xyz_deg and translation_xyz_mm, centered per video, common random numbers across sigma levels',
      body_arms=['E1','E2'],methods=['M0','ICP','BODY_VIDEO','BODY_HIER'],tolerance_mm=.5,tolerance_ablation_mm=[0.,1.],
      camera_optimization=False,physical_Ring_fixed=True,body_frozen=True,GT_selects_predictor=False,GT_face_union_prohibited=True,
      mesh_builder='native_axial_depth_grid_triangles',mesh_stride_px=2,mesh_edge_limit_mm=1.,
      sections=[dict(axis=0,offset_mm=0.),dict(axis=1,offset_mm=0.),dict(axis=2,offset_mm=-2.),dict(axis=2,offset_mm=-6.)],
      registration_outer_iterations=3,registration_nfev=25,registration_samples_per_view=96,overlap_samples_per_edge=96,
      pair_max_distance_mm=1.5,normal_agreement_min=.4,candidate_reject_distance_mm=2.5,candidate_confidence_min=.15,
      weights=dict(overlap=1.,body_region=.15,frame_prior=.01,frame_mean=.2,video_prior=.001),
      residual_sigma_bound=3.,video_rotation_bound_deg=8.,video_translation_bound_mm=2.,
      ICP_iterations=30,ICP_outer_iterations=2,ICP_distance_mm=1.5,
      fusion_consensus_mm=.25,fusion_min_support=2,fusion_max_seam_jump_mm=.8,fusion_min_incidence=.15,
      evaluation_GT_samples=12000,evaluation_model_samples=12000,overlap_evaluation_samples_per_pair=160,
      coverage_threshold_mm=.2,material_success_threshold_mm=.2,main_figure_condition='C3',main_figure_arm='E1',main_figure_method='BODY_HIER')
    (td/'TASK.yaml').write_text(yaml.safe_dump(t,sort_keys=False,allow_unicode=True));(td/'TASK_FREEZE.json').write_text(json.dumps(dict(task_sha256=sha256(td/'TASK.yaml'),source_manifest_sha256=sha256(manifest),baseline_commit='0a3fe96bb1d91e5719f8e21bcf232e0967dd233f',UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),Body_initializer_reuse='Explicitly approved GT-free 2D initializers; not historical measurement fallback',DXY_new_calls=0),indent=2)+'\n');print(td/'TASK.yaml')


if __name__=='__main__':main()
