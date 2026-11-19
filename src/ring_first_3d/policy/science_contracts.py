"""Explicit G0–G1 extension. Schema 1 and its no-GT contract remain unchanged."""
import copy
import json
from pathlib import Path
from .contracts import fields,require,validate_v1,MODULES,STAGES,verify_task,freeze_identity,ROOT
from ..contracts.identities import sha256

TASK_ID="TASK-E4-SYNTHETIC-BODY-PIXEL-CORRESPONDENCE-001"
SCIENCE_STAGES=("preflight","contracts","research_regression","G0_prepare","C0_smoke_predict","C0_smoke_evaluate",
                "C0_predict","C0_evaluate","C1_predict","C1_evaluate","C3_predict","C3_evaluate","G1_visualize","artifacts")
ROLES={s:("generator" if s=="G0_prepare" else "evaluator" if s.endswith("evaluate") or s=="G1_visualize" else "predictor" if s.endswith("predict") else "verification")for s in SCIENCE_STAGES}
SCIENCE_MODULES={
 "S01":dict(file="synthetic/scene.py",role="generator",description="Real G01 source and frozen synthetic camera frame"),
 "S02":dict(file="synthetic/raster.py",role="generator/predictor",description="T24 camera convention and hard Pixel-to-Face raster"),
 "S03":dict(file="synthetic/correspondence.py",role="predictor",description="3D closest surface, pixel barycentric point and Ring visibility"),
 "S04":dict(file="synthetic/evaluate.py",role="evaluator",description="Frozen predictions, independent true points and Oracle diagnostics"),
 "S05":dict(file="synthetic/visualize.py",role="evaluator",description="Actual data figures and offline evidence gallery")}


def legacy_task(task):
    base=copy.deepcopy({k:v for k,v in task.items()if k!="science"})
    base["schema"]=1;base["modules"]=[m for m in base["modules"]if m in MODULES]
    base["split"]["GT"]=[];base["split"]["access"]="verification_only_no_GT"
    base["authorization"]["stages"]=list(STAGES);base["acceptance"]["required_stages"]=list(STAGES)
    return base


def validate(task,path):
    fields(task,"schema task_id goal modules variables inputs split authorization acceptance budget stop output_root science","science TASK")
    require(type(task["schema"])is int and task["task_id"]==TASK_ID,"SCIENCE_SCOPE","This extension authorizes only the named G0–G1 task")
    require(type(task["modules"])is list and len(set(task["modules"]))==len(task["modules"]) and set(task["modules"])==set(MODULES)|set(SCIENCE_MODULES),"MODULE","Exact declared legacy + science modules required")
    base=validate_v1(legacy_task(task),path)
    original_auth=task["authorization"]["stages"];original_accept=task["acceptance"]["required_stages"]
    require(original_auth and original_auth==list(SCIENCE_STAGES[:len(original_auth)]),"AUTHORIZATION","Ordered G0–G1 prefix only; no G2 or optimization")
    require(original_accept==list(SCIENCE_STAGES),"ACCEPTANCE","All G0–G1 stages required")
    require(task["split"]["access"]=="synthetic_generator_predictor_evaluator" and task["split"]["GT"]==["G01_original_blender"],"GT_LEAK","Explicit synthetic GT role split required")
    sc=task["science"]
    fields(sc,"assets camera_ids condition_order conditions resolution native_resolution canonical_from_blender unit_to_mm body_initialization projection_tolerance_mm heatmap_max_mm scope","science")
    require(sc["scope"]=="G0-G1_correspondences_only" and sc["condition_order"]==["C0","C1","C3"],"SCIENCE_SCOPE","Frozen representative cases only")
    require(sc["conditions"]=={"C0":{"depth_bias_mm":0.,"rotation_y_deg":0.,"translation_x_mm":0.},"C1":{"depth_bias_mm":1.,"rotation_y_deg":0.,"translation_x_mm":0.},"C3":{"depth_bias_mm":0.,"rotation_y_deg":2.,"translation_x_mm":.5}},"INJECTION_PROTOCOL","Do not enlarge/retune perturbations")
    require(sc["resolution"]==[320,180] and sc["native_resolution"]==[640,360] and sc["unit_to_mm"]==1000.,"COORDINATES","Frozen scale and half-pixel resolution")
    require(sc["canonical_from_blender"]==[[1.,0.,0.,0.],[0.,1.,0.,0.],[0.,0.,1.,0.],[0.,0.,0.,1.]],"COORDINATES","Explicit synthetic canonical placement, not recovered deployment pose")
    require(sc["body_initialization"]=="exact_real_G01_mesh_for_controlled_correspondence_only","SCIENCE_SCOPE","No historical prediction or fabricated G01 initialization")
    require(sc["camera_ids"]==["G01_004_ref08","G01_004_ref13","G01_004_ref03","G01_004_growth_r04"],"DATA_ISOLATION","Frozen three FIT plus one HOLDOUT")
    require(sc["projection_tolerance_mm"]==.001 and sc["heatmap_max_mm"]==2.,"FROZEN_PROTOCOL","Fixed tolerances and comparable color scale")
    require(set(sc["assets"])=={"blend","gt_cache","gt_extraction","identity_lock","ring","blender_binary","export_source"},"SOURCE_IDENTITY","All genuine sources required")
    for name,rec in sc["assets"].items():
        fields(rec,"path sha256","science asset "+name)
        require(isinstance(rec["path"],str) and isinstance(rec["sha256"],str) and len(rec["sha256"])==64,"SOURCE_SHA",name)
        rec["path"]=str((path.parent/rec["path"]).resolve())
    for key in ["inputs","output_root","variables"]:task[key]=base[key]
    task["split"]["manifest"]=base["split"]["manifest"]
    return task


def verify(task):
    for name,rec in task["science"]["assets"].items():
        require(Path(rec["path"]).is_file(),"NOT_EVALUABLE","Missing genuine source: "+name)
        require(sha256(rec["path"])==rec["sha256"],"SOURCE_SHA",name)
    info=verify_task(legacy_task(task))
    a=task["science"]["assets"]
    identity=next(x for x in json.loads(Path(a["identity_lock"]["path"]).read_text())if x["case"]=="G01")
    extraction=json.loads(Path(a["gt_extraction"]["path"]).read_text())
    require(identity["sha256"]==a["blend"]["sha256"]==extraction["source_sha256"] and identity["physical_specimen"]=="spec_01p-12-" and extraction["scene_unit_system"]=="METRIC" and extraction["scene_scale_length"]==1. and extraction["unit_to_mm"]==1000.,"SOURCE_IDENTITY","Real G01 identity/Blender units")
    contracts=dict(info["module_contracts"])
    for mid,rec in SCIENCE_MODULES.items():
        p=ROOT/"src/ring_first_3d"/rec["file"]
        require(p.is_file(),"MODULE",mid)
        contracts[mid]=dict(rec,sha256=sha256(p))
    return freeze_identity(task,contracts,info["verified_assets"]+len(a))


def permissions(task,stage,run_root):
    require(stage in ROLES,"UNAUTHORIZED_STAGE",stage)
    role=ROLES[stage]
    gt_paths=[Path(rec["path"]).resolve()for key,rec in task["science"]["assets"].items()if key in {"blend","gt_cache","gt_extraction","identity_lock"}]
    if role=="predictor":
        for key in ("fixture","support"):
            metadata=json.loads(Path(task["inputs"][key]["path"]).read_text())
            gt_paths.extend(Path(p).resolve()for p in metadata["assets"])
    return dict(role=role,gt_paths=gt_paths,run_root=Path(run_root).resolve(),allow_GT=role in {"generator","evaluator"})
