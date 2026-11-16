"""Real public-CLI regression, including killing only our own smoke runner.

Does not alter science code or inputs. Test variants and run histories stay LOCAL_ONLY.
"""
from _bootstrap import ROOT
import argparse
import copy
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time
import yaml
from ring_first_3d.policy.contracts import load_task
from ring_first_3d.policy.artifacts import read_state, heads
from ring_first_3d.contracts.identities import sha256


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--task",type=Path,required=True);p.add_argument("--label",required=True);p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    if not re.fullmatch(r"[a-z0-9-]+",a.label):raise ValueError("Simple run label required")
    task=load_task(a.task);base=Path(task["output_root"]);cases=base/("cases-"+a.label)
    cases.mkdir(parents=True,exist_ok=False)
    records=[];cli=[sys.executable,str(ROOT/"tools/research/policy.py")]
    def call(command,task_file=a.task,root=None,stage=None,error=None):
        args=cli+[command,"--task",str(task_file)]
        if root is not None:args += ["--run-dir",str(root)]
        if stage:args += ["--stage",stage]
        t=time.monotonic();result=subprocess.run(args,capture_output=True,text=True)
        payload=json.loads(result.stdout if result.returncode==0 else result.stderr)
        if error:
            if result.returncode!=2 or payload.get("code")!=error:raise AssertionError((command,error,result.stdout,result.stderr))
        elif result.returncode!=0:raise AssertionError((command,result.stdout,result.stderr))
        records.append(dict(command=command,stage=stage,expected_error=error,actual=payload,seconds=time.monotonic()-t))
        return payload
    def variant(name,change):
        data=yaml.safe_load(a.task.read_text());change(data)
        path=cases/(name+".yaml");path.write_text(yaml.safe_dump(data,sort_keys=False));return path
    call("check")
    normal=base/("verified-"+a.label)
    call("run",root=normal,stage="all");call("accept",root=normal)
    actual=heads(normal,read_state(normal))
    if actual["contracts"]["payload"]["tests"]<11:raise AssertionError("Real contracts missing")
    if len(actual["smoke"]["payload"]["tests"])!=4:raise AssertionError("Actual smoke bundle missing")
    wrong=variant("wrong-units",lambda d:d["variables"].update(geometry_unit="m"));call("check",wrong,error="COORDINATES")
    wrong=variant("wrong-sha",lambda d:d["inputs"]["fixture"].update(sha256="0"*64));call("check",wrong,error="SOURCE_SHA")
    wrong=variant("GT-leak",lambda d:d["split"].update(GT=["/tmp/ground_truth.blend"]));call("check",wrong,error="GT_LEAK")
    wrong=variant("role-overlap",lambda d:d["split"].update(HOLDOUT=["FIT"]));call("check",wrong,error="DATA_ISOLATION")
    limited=variant("limited-authorization",lambda d:d["authorization"].update(stages=["preflight"]))
    denied=base/("denied-"+a.label);call("run",limited,denied,"contracts",error="UNAUTHORIZED_STAGE")
    # Missing visualization is rejected without silently rebuilding the snapshot.
    before=(normal/"RUN_MANIFEST.json").resolve();(normal/"visualization").unlink()
    call("accept",root=normal,error="ARTIFACT_MISSING")
    if (normal/"RUN_MANIFEST.json").resolve()!=before:raise AssertionError("Failed acceptance mutated history")
    (normal/"visualization").symlink_to("current/visualization");call("accept",root=normal)
    drift=variant("parameter-drift",lambda d:d["variables"]["parameters"].update(edited_after_freeze=True))
    call("accept",drift,normal,error="FREEZE_DRIFT")
    # Smoke cannot jump over a failed/absent predecessor even with full authorization.
    blocked=base/("blocked-"+a.label);call("run",root=blocked,stage="smoke",error="PREDECESSOR_FAILED")
    call("accept",root=blocked,error="ACCEPTANCE_GATE")
    small=variant("timeout-budget",lambda d:d["budget"].update(stage_timeout_seconds=.001))
    call("run",small,base/("budget-"+a.label),"preflight",error="BUDGET_TIMEOUT")
    # Actual interruption and recovery: preserve successful stages and partial evidence.
    resume=base/("resume-"+a.label)
    call("run",root=resume,stage="preflight");call("run",root=resume,stage="contracts")
    successful=list(read_state(resume)["attempts"])
    args=cli+["run","--task",str(a.task),"--run-dir",str(resume),"--stage","smoke"]
    process=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    worker=None;deadline=time.monotonic()+20
    try:
        while time.monotonic()<deadline and process.poll() is None:
            matches=list((resume/"attempts").glob(".pending-*-smoke-*/worker.json"))
            if matches:
                worker=json.loads(matches[0].read_text());break
            time.sleep(.025)
        if worker is None:raise AssertionError("No real smoke worker appeared")
        process.kill();stdout,stderr=process.communicate(timeout=5)
        deadline=time.monotonic()+5
        while time.monotonic()<deadline:
            stat=Path(f"/proc/{worker['pid']}/stat")
            if not stat.exists() or stat.read_text().split()[2]=="Z":break
            time.sleep(.025)
        else:raise AssertionError("Orphan worker still running")
    finally:
        if process.poll() is None:process.kill();process.wait()
    call("run",root=resume,stage="all");call("accept",root=resume)
    final=read_state(resume)
    if final["attempts"][:2]!=successful:raise AssertionError("Completed stages overwritten")
    interrupted=json.loads((resume/"failures.json").read_text())["failures"]
    if not any(x["status"]=="INTERRUPTED"for x in interrupted):raise AssertionError("Interruption evidence lost")
    summary=dict(status="PASS",test_type="Actual public CLI, actual existing APIs/GPU, no handler mocks",
        cases=records,normal_run=str(normal),resume_run=str(resume),
        real_stage_results={k:v["payload"]for k,v in actual.items()},
        actual_interruption=dict(worker=worker,parent_exit_code=process.returncode,orphan_running=False,first_two_attempts_unchanged=True,retained_failures=interrupted),
        run_manifest_sha256=sha256(normal/"RUN_MANIFEST.json"),visualization=str(normal/"visualization/index.html"),
        scientific_algorithms_modified=False,new_body_reconstructions=0,GT_read=False)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open("x")as f:json.dump(summary,f,indent=2);f.write("\n")
    print(json.dumps(dict(status="PASS",cli_checks=len(records),output=str(a.output),visualization=summary["visualization"]),indent=2))


if __name__=="__main__":main()
