"""Append-only attempts, frozen identities, enforced order and bounded subprocesses."""
import contextlib
import ctypes
import fcntl
import functools
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import uuid
from .artifacts import write_json, read_state, publish, heads, check_artifacts, load_attempt
from .contracts import ROOT, STAGES, MODULES, PolicyError, require, verify_task, digest, write_allowed, stages_for
from .memory import registry
from ..contracts.identities import sha256


@contextlib.contextmanager
def writer(root):
    with (root / ".writer.lock").open("a+") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as e:
            raise PolicyError("RUN_BUSY", "Another runner owns this run") from e
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def child_setup(parent):
    # Linux parent-death handling prevents orphan GPU jobs on runner SIGKILL.
    libc = ctypes.CDLL(None)
    if libc.prctl(1, signal.SIGKILL) != 0:
        os._exit(125)
    if os.getppid() != parent:
        os.kill(os.getpid(), signal.SIGKILL)


def execute(stage, task, pending, timeout, freeze_path):
    runtime = pending / "runtime"
    runtime.mkdir()
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", TMPDIR=str(runtime),
               MPLCONFIGDIR=str(runtime / "mpl"), XDG_CACHE_HOME=str(runtime / "cache"))
    command = [sys.executable, str(ROOT / "tools/research/_policy_worker.py"),
               "--stage", stage, "--freeze", str(freeze_path), "--attempt", str(pending)]
    with (pending/"stdout.txt").open("x") as stdout, (pending/"stderr.txt").open("x") as stderr:
        process = subprocess.Popen(command, stdout=stdout, stderr=stderr, env=env,
                                   start_new_session=True, preexec_fn=functools.partial(child_setup,os.getpid()))
        write_json(pending/"worker.json",dict(pid=process.pid,runner_pid=os.getpid(),command=command))
        try:
            deadline=time.monotonic()+timeout
            while True:
                remaining=deadline-time.monotonic()
                if remaining<=0:raise subprocess.TimeoutExpired(command,timeout)
                try:
                    code=process.wait(timeout=min(.1,remaining));break
                except subprocess.TimeoutExpired:
                    run_root=pending.parents[1]
                    size=sum(p.stat().st_size for p in run_root.rglob("*")if p.is_file() and not p.is_symlink())
                    if size>task["budget"]["max_output_bytes"]:
                        raise PolicyError("BUDGET_OUTPUT","Output budget exceeded during worker")
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL); process.wait()
            raise PolicyError("BUDGET_TIMEOUT", f"Stage exceeded {timeout:g} seconds")
        except BaseException:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL); process.wait()
            raise
    require(code == 0, "HANDLER_FAILED", (pending/"stderr.txt").read_text()[-3000:])
    payload = json.loads((pending/"payload.json").read_text())
    if stage=='G0_scene_audit':require(payload.get('status')=='PASS','SCENE_AUTHENTICITY_FAILED',payload.get('reason','Unverified dual-video scene'))
    require(payload.get("status") == "PASS", "GATE_FAILED", stage + ": " + str(payload.get("status")))
    if stage == "contracts":
        require(payload["tests"] >= task["acceptance"]["min_contract_tests"] and payload["failures"] == 0 and payload["errors"] == 0, "CONTRACT_COUNT", "Insufficient actual contract tests")
    if stage == "smoke":
        require(len(payload.get("tests", [])) == 4 and all(t["status"] == "PASS" for t in payload["tests"]), "GATE_FAILED", "Real full bundle must pass including compatibility")
    if stage in {"research_regression","dualvideo_regression","sim_regression","fusion_regression","stress_regression","inita_regression","contour_regression","structural_regression","structured_regression"}:
        require(payload.get("baseline_tests")==35 and payload.get("tests",0)>35 and payload.get("failures")==0 and payload.get("errors")==0,"REGRESSION_GATE","Original 35 and new scientific tests required before G0")
    return payload


def _finish(root, task, state, pending, result):
    write_json(pending/"result.json", result)
    final = root/"attempts"/result["attempt_id"]
    pending.rename(final)
    rec = dict(path=str((final/"result.json").relative_to(root)), sha256=sha256(final/"result.json"))
    updated = dict(state, attempts=state["attempts"]+[rec], spent_seconds=state["spent_seconds"]+result["seconds"])
    return publish(root, task, updated)


def _recover(root, task, state):
    # Completed rename before pointer update is recovered from result.json.
    known = {r["path"] for r in state["attempts"]}
    for final in sorted((root/"attempts").glob("*-*")):
        if final.name.startswith("."):continue
        p = final/"result.json"
        if p.is_file() and str(p.relative_to(root)) not in known:
            result=json.loads(p.read_text())
            require(result["freeze_sha256"] == state["freeze_sha256"], "ATTEMPT_IDENTITY", str(p))
            state=dict(state, attempts=state["attempts"]+[dict(path=str(p.relative_to(root)),sha256=sha256(p))],spent_seconds=state["spent_seconds"]+result["seconds"])
            state=publish(root,task,state)
    for pending in sorted((root/"attempts").glob(".pending-*")):
        request_path=pending/"request.json"
        require(request_path.is_file(), "INCOMPLETE_WRITE", "Pending request incomplete; preserve and use a new run")
        req=json.loads(request_path.read_text())
        require(req["freeze_sha256"]==state["freeze_sha256"], "ATTEMPT_IDENTITY", "Pending task changed")
        # A complete result written just before a crash remains authoritative.
        if (pending/"result.json").exists():
            try:
                result=json.loads((pending/"result.json").read_text())
            except (ValueError,TypeError):
                (pending/"result.json").rename(pending/"partial_result.json")
                result=dict(req,status="INTERRUPTED",seconds=float(req["timeout_seconds"]),reason="Partial result preserved; never accept partial PASS")
                state=_finish(root,task,state,pending,result)
                continue
            final=root/"attempts"/req["attempt_id"];pending.rename(final)
            rec=dict(path=str((final/"result.json").relative_to(root)),sha256=sha256(final/"result.json"))
            state=publish(root,task,dict(state,attempts=state["attempts"]+[rec],spent_seconds=state["spent_seconds"]+result["seconds"]))
        else:
            result=dict(req,status="INTERRUPTED",seconds=float(req["timeout_seconds"]),reason="Previous runner interrupted; partial payload never accepted; conservatively charge reserved timeout")
            state=_finish(root,task,state,pending,result)
    return state


def run_stage(task, root, stage):
    stages=stages_for(task)
    root = write_allowed(root)
    require(root.parent == Path(task["output_root"]) and root.name not in ("", ".", ".."), "OUTPUT_SCOPE", "Run must be a direct child of output_root")
    require(stage in stages, "STAGE", stage)
    registry()  # Also validates no unreviewed permanent rule was introduced.
    identity = verify_task(task)
    root.mkdir(parents=True, exist_ok=True)
    with writer(root):
        freeze_path = root/"FREEZE.json"
        if not freeze_path.exists():
            require(not any(p.name != ".writer.lock" for p in root.iterdir()), "OUTPUT_EXISTS", "Never adopt a populated run directory")
            write_json(freeze_path, identity)
            (root/"attempts").mkdir()
            state=publish(root,task,dict(schema=1,freeze_sha256=identity["freeze_sha256"],attempts=[],spent_seconds=0.))
        else:
            frozen=json.loads(freeze_path.read_text())
            require(frozen["freeze_sha256"] == identity["freeze_sha256"] and digest(frozen["fingerprint"]) == identity["freeze_sha256"], "FREEZE_DRIFT", "Task/input/source/environment/version changed; start a new run")
            state=read_state(root)
            require(state["freeze_sha256"] == identity["freeze_sha256"], "FREEZE_DRIFT", "Run manifest drift")
        state=_recover(root,task,state)
        previous=heads(root,state)
        if stage in previous and previous[stage]["status"] == "PASS":
            check_artifacts(root,state)
            return dict(status="PASS",resumed=True,skipped_completed_stage=stage,run_dir=str(root))
        attempt_id=f"{len(state['attempts'])+1:04d}-{stage}-{uuid.uuid4().hex[:8]}"
        pending=root/"attempts"/(".pending-"+attempt_id);pending.mkdir()
        budget=task["budget"]
        timeout=min(budget["stage_timeout_seconds"],max(.001,budget["max_seconds"]-state["spent_seconds"]))
        request=dict(attempt_id=attempt_id,stage=stage,freeze_sha256=state["freeze_sha256"],timeout_seconds=timeout,started_UTC=time.time())
        write_json(pending/"request.json",request)
        start=time.monotonic()
        try:
            require(stage in task["authorization"]["stages"], "UNAUTHORIZED_STAGE", stage)
            if stage in ("preflight", "smoke"):
                require(set(MODULES)<=set(task["modules"]) if task.get("schema")in {2,3,4,5,6,7,8,9,10} else set(task["modules"])==set(MODULES), "BUNDLE_SCOPE", "Declare all modules for existing indivisible Preflight/Smoke bundle")
            for dependency in stages[:stages.index(stage)]:
                require(dependency in previous and previous[dependency]["status"] == "PASS", "PREDECESSOR_FAILED", dependency)
            require(state["spent_seconds"] < budget["max_seconds"], "BUDGET_EXHAUSTED", "Total compute budget")
            require(sum(load_attempt(root,r)["stage"]==stage for r in state["attempts"]) < budget["max_attempts_per_stage"], "BUDGET_ATTEMPTS", stage)
            current_bytes=sum(p.stat().st_size for p in root.rglob("*")if p.is_file() and not p.is_symlink())
            require(current_bytes < budget["max_output_bytes"], "BUDGET_OUTPUT", str(current_bytes))
            if stage == "artifacts":
                payload=check_artifacts(root,state)
            else:
                payload=execute(stage,task,pending,timeout,freeze_path)
            total_bytes=sum(p.stat().st_size for p in root.rglob("*")if p.is_file() and not p.is_symlink())
            require(total_bytes<=budget["max_output_bytes"],"BUDGET_OUTPUT","Output budget exceeded")
            # Check boundaries again after the handler, before accepting results.
            require(verify_task(task)["freeze_sha256"]==identity["freeze_sha256"], "FREEZE_DRIFT", "Input/source modified during stage")
            if stage == "artifacts":
                write_json(pending/"payload.json",payload)
            result=dict(request,status="PASS",seconds=time.monotonic()-start,payload=payload,
                        raw_files={p.name:sha256(p) for p in pending.iterdir()if p.is_file()})
            state=_finish(root,task,state,pending,result)
            return dict(status="PASS",stage=stage,run_dir=str(root),attempt_id=attempt_id)
        except (Exception, KeyboardInterrupt) as e:
            if not pending.exists():
                raise PolicyError("ARTIFACT_PUBLISH_FAILED","Committed attempt retained; current pointer unchanged: "+str(e))from e
            result=dict(request,status="FAIL",seconds=time.monotonic()-start,reason=str(e),
                        raw_files={p.name:sha256(p) for p in pending.iterdir()if p.is_file()})
            _finish(root,task,state,pending,result)
            if isinstance(e,PolicyError):raise
            raise PolicyError("STAGE_ERROR", str(e)) from e


def _accept(task, root):
    identity=verify_task(task);registry();root=Path(root).resolve()
    require(root.parent==Path(task["output_root"]),"OUTPUT_SCOPE",str(root))
    state=read_state(root)
    require(state["freeze_sha256"]==identity["freeze_sha256"],"FREEZE_DRIFT","Cannot accept changed task")
    frozen=json.loads((root/"FREEZE.json").read_text())
    require(digest(frozen["fingerprint"])==state["freeze_sha256"],"FREEZE_DRIFT","Frozen fingerprint modified")
    previous=heads(root,state)
    for stage in task["acceptance"]["required_stages"]:
        require(stage in task["authorization"]["stages"] and stage in previous and previous[stage]["status"]=="PASS","ACCEPTANCE_GATE",stage)
        row=previous[stage]
        attempt=root/"attempts"/row["attempt_id"]
        for name,h in row["raw_files"].items():
            require((attempt/name).is_file() and sha256(attempt/name)==h,"ATTEMPT_SHA",name)
    artifacts=check_artifacts(root,state)
    if not state.get("accepted",False):
        state=publish(root,task,dict(state,accepted=True,accepted_UTC=time.time()))
        artifacts=check_artifacts(root,state)
    return dict(status="PASS",accepted=True,freeze_sha256=state["freeze_sha256"],
                task_id=task["task_id"],run_dir=str(root),artifacts=artifacts,
                retained_attempts=len(state["attempts"]),scientific_acceptance="AWAITING_HUMAN_REVIEW"if task.get("schema")in {2,3,4,5,6,7,8,9,10} else"NOT_APPLICABLE")


def accept(task,root):
    root=write_allowed(root)
    require(root.parent==Path(task["output_root"]) and root.is_dir(),"OUTPUT_SCOPE",str(root))
    with writer(root):return _accept(task,root)
