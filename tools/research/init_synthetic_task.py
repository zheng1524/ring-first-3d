"""Bind the explicitly authorized genuine G01 G0–G1 protocol once, no experiment run."""
from _bootstrap import ROOT
from pathlib import Path
import json
import yaml
from policy import make_task
from ring_first_3d.policy.science_contracts import TASK_ID,SCIENCE_STAGES,SCIENCE_MODULES
from ring_first_3d.policy.contracts import load_task
from ring_first_3d.contracts.identities import sha256


def main():
    taskdir=ROOT/"experiments"/TASK_ID;path=taskdir/"TASK.yaml"
    make_task(TASK_ID,path)
    task=yaml.safe_load(path.read_text());task["schema"]=2
    task["goal"]="G0–G1 controlled real-G01 C0/C1/C3 correspondence comparison; no Body update; stop for human review"
    task["modules"]+=list(SCIENCE_MODULES)
    task["authorization"]["reference"]="User explicitly approved G0–G1 only, after fc63df356a577c61de75912b136f92d7f7b15e9d"
    task["authorization"]["stages"]=list(SCIENCE_STAGES);task["acceptance"]["required_stages"]=list(SCIENCE_STAGES)
    task["split"]["GT"]=["G01_original_blender"];task["split"]["access"]="synthetic_generator_predictor_evaluator"
    task["budget"]=dict(max_seconds=1200,stage_timeout_seconds=180,max_attempts_per_stage=2,max_output_bytes=250000000)
    exp=Path("/home/liu/ring_first_3d_e4_sdf_localization/experiments")
    p14=exp/"TASK-E4-PYTORCH3D-014";p13=exp/"TASK-E4-PYTORCH3D-RING-AWARE-001/runs/FREE_VERTEX_013"
    paths=dict(blend=Path("/home/liu/polyp_research/01p型/01p-12-/息肉.blend"),gt_cache=p14/"evaluation_only/G01/ORIGINAL_BLENDER_GT_MM.npz",
        gt_extraction=p13/"evaluation_only/G01/GT_EXTRACTION.json",identity_lock=p14/"provenance/GT_SOURCE_IDENTITY_LOCK.json",ring=p14/"inputs/G01/RING.npz",
        blender_binary=Path("/home/liu/blender/blender-5.0.1-linux-x64/blender"),export_source=p13/"code/export_blender_gt.py")
    task["science"]=dict(assets={k:dict(path=str(p.resolve()),sha256=sha256(p))for k,p in paths.items()},
        camera_ids=["G01_004_ref08","G01_004_ref13","G01_004_ref03","G01_004_growth_r04"],condition_order=["C0","C1","C3"],
        conditions={"C0":dict(depth_bias_mm=0.,rotation_y_deg=0.,translation_x_mm=0.),"C1":dict(depth_bias_mm=1.,rotation_y_deg=0.,translation_x_mm=0.),"C3":dict(depth_bias_mm=0.,rotation_y_deg=2.,translation_x_mm=.5)},
        resolution=[320,180],native_resolution=[640,360],canonical_from_blender=[[1.,0.,0.,0.],[0.,1.,0.,0.],[0.,0.,1.,0.],[0.,0.,0.,1.]],unit_to_mm=1000.,
        body_initialization="exact_real_G01_mesh_for_controlled_correspondence_only",projection_tolerance_mm=.001,heatmap_max_mm=2.,scope="G0-G1_correspondences_only")
    path.write_text(yaml.safe_dump(task,sort_keys=False,allow_unicode=True));load_task(path)
    print(path)


if __name__=="__main__":main()
