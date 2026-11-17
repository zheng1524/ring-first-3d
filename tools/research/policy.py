"""Task Contract + Policy Runner entry; composes existing verification APIs."""
from _bootstrap import ROOT
import argparse
import json
import re
from pathlib import Path
import sys
import yaml
from ring_first_3d.policy.contracts import STAGES, MODULES, PolicyError, load_task, verify_task, require, write_allowed
from ring_first_3d.policy.runner import run_stage, accept
from ring_first_3d.policy.artifacts import read_state, check_artifacts, heads
from ring_first_3d.policy.memory import registry
from ring_first_3d.contracts.identities import sha256
from ring_first_3d.policy.science_contracts import SCIENCE_STAGES
from ring_first_3d.policy.dualvideo_contracts import DUAL_STAGES
from ring_first_3d.policy.sim_contracts import SIM_STAGES
from ring_first_3d.policy.fusion_contracts import FUSION_STAGES
from ring_first_3d.policy.stress_contracts import STRESS_STAGES
from ring_first_3d.policy.inita_contracts import INIT_STAGES
from ring_first_3d.policy.contour_contracts import CONTOUR_STAGES
from ring_first_3d.policy.structural_contracts import STRUCTURAL_STAGES


def make_task(task_id, output):
    """Bind existing registered fixtures, avoiding hand-copied 108 camera IDs."""
    require(bool(re.fullmatch(r"TASK-[A-Z0-9][A-Z0-9-]{2,100}",task_id)),"SCHEMA","Invalid task_id")
    fixture=ROOT/"tools/research/frozen_fixture.json"
    f=json.loads(fixture.read_text());meta=Path(f["real_case_root"])/"inputs"/f["case"]/"CASE.json"
    camera=json.loads(meta.read_text())
    rec=lambda p:dict(path=str(p),sha256=sha256(p))
    task=dict(schema=1,task_id=task_id,goal="Verify the existing frozen harness without new reconstruction or GT access",
        modules=list(MODULES),variables=dict(geometry_unit="mm",pixel_coordinates="native_image_px",camera_transform="opencv_c2w",depth_convention="axial_z",parameters={}),
        inputs=dict(fixture=rec(fixture),support=rec(fixture.with_name("support_fixture.json")),reference=rec(fixture.with_name("frozen_reference.json")),source_lock=rec(ROOT/"src/ring_first_3d/source_lock.json"),dxy_root="/home/liu/new-polyp-dxy",evidence=rec(ROOT/"experiments/TASK-RESEARCH-HARNESS-STORAGE-001/figures/REAL_SMOKE_EVIDENCE.png")),
        split=dict(manifest=rec(meta),FIT=["FIT"],HOLDOUT=sorted({v["role"]for v in camera["views"]if v["role"]!="FIT"}),GT=[],access="verification_only_no_GT"),
        authorization=dict(approved_by="user",reference="User-approved "+task_id,stages=list(STAGES)),
        acceptance=dict(required_stages=list(STAGES),min_contract_tests=11,require_visualization=True,require_failure_log=True),
        budget=dict(max_seconds=300,stage_timeout_seconds=120,max_attempts_per_stage=3,max_output_bytes=64000000),
        stop=["gate_failure","input_drift","budget_exceeded"],output_root=str(ROOT/"experiments"/task_id/"runs"))
    output=write_allowed(output)
    require(not output.exists(),"OUTPUT_EXISTS","Never overwrite TASK.yaml")
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open("x") as stream:yaml.safe_dump(task,stream,sort_keys=False,allow_unicode=True)
    load_task(output)
    return dict(status="CREATED",task=str(output),note="Review goal, authorization and budgets; init does not grant approval")


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest="command",required=True)
    create=sub.add_parser("init",help="Create a bound TASK.yaml from existing frozen cases")
    create.add_argument("--task-id",required=True);create.add_argument("--output",type=Path,required=True)
    sub.add_parser("failures",help="Read structured advisory Failure Memory")
    for name in ["check","run","accept","status"]:
        p=sub.add_parser(name);p.add_argument("--task",type=Path,required=True)
        if name!="check":p.add_argument("--run-dir",type=Path,required=True)
        if name=="run":p.add_argument("--stage",choices=sorted(set(STAGES)|set(SCIENCE_STAGES)|set(DUAL_STAGES)|set(SIM_STAGES)|set(FUSION_STAGES)|set(STRESS_STAGES)|set(INIT_STAGES)|set(CONTOUR_STAGES)|set(STRUCTURAL_STAGES)|{"all"}),required=True)
    a=parser.parse_args(argv)
    try:
        if a.command=="init":result=make_task(a.task_id,a.output)
        elif a.command=="failures":result=dict(status="PASS",registry=registry())
        else:
            task=load_task(a.task)
            if a.command=="check":
                registry();info=verify_task(task)
                result={k:v for k,v in info.items()if k!="fingerprint"}
            elif a.command=="run":
                stages=task["authorization"]["stages"] if a.stage=="all" else [a.stage]
                results=[run_stage(task,a.run_dir,stage)for stage in stages]
                result=dict(status="AUTHORIZED_STAGES_COMPLETE",stages=results,run_dir=str(a.run_dir.resolve()),accepted=False)
            elif a.command=="accept":result=accept(task,a.run_dir)
            else:
                state=read_state(a.run_dir);result=dict(status=state["status"],freeze_sha256=state["freeze_sha256"],stages={k:v["status"]for k,v in heads(a.run_dir,state).items()},attempts=len(state["attempts"]),artifacts=check_artifacts(a.run_dir,state))
        print(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False));return 0
    except (PolicyError,OSError,ValueError,KeyError,TypeError) as e:
        print(json.dumps(dict(status="REJECTED",code=getattr(e,"code","INVALID_INPUT"),reason=str(e)),ensure_ascii=False),file=sys.stderr)
        return 2


if __name__=="__main__":raise SystemExit(main())
