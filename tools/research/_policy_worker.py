"""Private allowlisted worker; public entry is policy.py, never arbitrary shell."""
from _bootstrap import ROOT
import argparse
import json
import os
from pathlib import Path
import sys


def install_io_guard(attempt,science=None):
    """Python I/O guard for trusted existing handlers, not an OS sandbox."""
    from ring_first_3d.policy.contracts import PolicyError
    def resolve_at(value,dir_fd=None):
        p=Path(os.fsdecode(value))
        if not p.is_absolute() and dir_fd is not None and dir_fd!=-1:
            p=Path(os.readlink(f"/proc/self/fd/{dir_fd}"))/p
        return p.resolve()
    def guard(event,args):
        if event == "open" and isinstance(args[0],(str,bytes,os.PathLike)):
            p=Path(os.fsdecode(args[0])).resolve();mode=args[1]if isinstance(args[1],str)else"";flags=args[2]if isinstance(args[2],int)else 0
            writing=any(x in mode for x in "wax+") or bool(flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC))
            if writing and p != Path("/dev/null") and not p.is_relative_to(attempt):raise PolicyError("WRITE_ISOLATION",str(p))
            gt_like=p.suffix.lower()==".blend" or any(x.lower()in {"audit_only","evaluation_only","ground_truth","gt","private"}for x in p.parts) or "NATIVE_CAD_GT" in p.name
            if science and p in science["gt_paths"]:gt_like=True
            if science and not writing and any(p.is_relative_to(x)for x in science.get('denied_read_prefixes',[])):
                raise PolicyError('CLEAN_POSE_LEAK',str(p))
            if science and science["role"]=="predictor" and any("_evaluate-" in part or "_visualize-" in part for part in p.parts):gt_like=True
            if not writing and gt_like:
                allowed=science and science["allow_GT"] and (p in science["gt_paths"] or p.is_relative_to(science["run_root"]))
                if not allowed:raise PolicyError("GT_LEAK",str(p))
        elif event in ("os.mkdir","os.remove","os.rmdir") and isinstance(args[0],(str,bytes)):
            fd=args[2]if event=="os.mkdir"else args[1]
            p=resolve_at(args[0],fd)
            if not p.is_relative_to(attempt):raise PolicyError("WRITE_ISOLATION",str(p))
        elif event in ("os.rename","os.link"):
            for value,fd in [(args[0],args[2]),(args[1],args[3])]:
                if not resolve_at(value,fd).is_relative_to(attempt):raise PolicyError("WRITE_ISOLATION",str(value))
        elif event=="os.symlink":
            if not resolve_at(args[1],args[2]).is_relative_to(attempt):raise PolicyError("WRITE_ISOLATION",str(args[1]))
        elif event == "subprocess.Popen":
            command=args[1]
            if science and science.get("stage")in {"G1_visualize","G0_scene_audit","G4_visualize","G4_smoke_visualize"} and isinstance(command,(list,tuple)) and Path(str(command[0])).name=="fc-list" and len(command)==2 and (command[1]=="--help"or str(command[1]).startswith("--format=")):return
            if science and science.get("stage")in {"research_regression","dualvideo_regression","sim_regression","fusion_regression","stress_regression","inita_regression","contour_regression"} and isinstance(command,(list,tuple)) and str(command[0])==sys.executable:return
            if science and science.get("stage")in {"G1_smoke_train","G1_all_train"} and isinstance(command,(list,tuple)) and str(command[0])==sys.executable and len(command)>=3 and Path(str(command[1])).resolve()in {(ROOT/"tools/research/_init_a_train.py").resolve(),(ROOT/"tools/research/_contour_train.py").resolve()}:return
            if science and science["role"]=="generator" and isinstance(command,(list,tuple)) and str(command[0])==science.get("blender_binary"):
                if "--disable-autoexec" in command and "--factory-startup" in command:return
            if not isinstance(command,(list,tuple)) or Path(str(command[0])).name not in {"git","uname","lscpu"}:
                raise PolicyError("COMMAND_DENIED",str(command))
            if Path(str(command[0])).name=="git" and not (len(command)>=4 and command[1]=="-C" and command[3]in {"show","rev-parse"}):
                raise PolicyError("COMMAND_DENIED",str(command))
            if Path(str(command[0])).name=="lscpu" and len(command)!=1:raise PolicyError("COMMAND_DENIED",str(command))
        elif event in ("os.system","os.exec","os.posix_spawn"):
            raise PolicyError("COMMAND_DENIED",event)
    sys.addaudithook(guard)


def main():
    p=argparse.ArgumentParser();p.add_argument("--stage",required=True);p.add_argument("--freeze",type=Path,required=True);p.add_argument("--attempt",type=Path,required=True);a=p.parse_args()
    task=json.loads(a.freeze.read_text())["fingerprint"]["task"]
    attempt=a.attempt.resolve()
    science=None
    if task.get("schema")==8:
        from ring_first_3d.policy.contour_contracts import permissions
        science=permissions(task,a.stage,attempt.parents[1])
    if task.get("schema")==7:
        from ring_first_3d.policy.inita_contracts import permissions
        science=permissions(task,a.stage,attempt.parents[1])
    if task.get("schema")==6:
        from ring_first_3d.policy.stress_contracts import permissions
        science=permissions(task,a.stage,attempt.parents[1])
    if task.get("schema")==5:
        from ring_first_3d.policy.fusion_contracts import permissions
        science=permissions(task,a.stage,attempt.parents[1])
    if task.get("schema")==4:
        from ring_first_3d.policy.sim_contracts import permissions
        science=permissions(task,a.stage,attempt.parents[1])
    if task.get("schema")==3:
        from ring_first_3d.policy.dualvideo_contracts import permissions
        science=permissions(task,a.stage,attempt.parents[1])
    if task.get("schema")==2:
        from ring_first_3d.policy.science_contracts import permissions
        science=permissions(task,a.stage,attempt.parents[1])
        science["stage"]=a.stage
        science["blender_binary"]=task["science"]["assets"]["blender_binary"]["path"]
    install_io_guard(attempt,science)
    sys.path.insert(0,str(ROOT/"tools/research"))
    if task.get("schema")==8 and a.stage not in ("preflight","contracts"):
        from ring_first_3d.contour_guided.experiment import dispatch
        result=dispatch(a.stage,task,attempt)
    elif task.get("schema")==7 and a.stage not in ("preflight","contracts"):
        from ring_first_3d.inita.handlers import dispatch
        result=dispatch(a.stage,task,attempt)
    elif task.get("schema")==6 and a.stage not in ("preflight","contracts"):
        from ring_first_3d.stress.handlers import dispatch
        result=dispatch(a.stage,task,attempt)
    elif task.get("schema")==5 and a.stage not in ("preflight","contracts"):
        from ring_first_3d.multisurface.handlers import dispatch
        result=dispatch(a.stage,task,attempt)
    elif task.get("schema")==4 and a.stage not in ("preflight","contracts"):
        from ring_first_3d.sim.handlers import dispatch
        result=dispatch(a.stage,task,attempt)
    elif task.get("schema")==3 and a.stage not in ("preflight","contracts"):
        from ring_first_3d.dualvideo.audit import dispatch
        result=dispatch(a.stage,task,attempt)
    elif task.get("schema")==2 and a.stage not in ("preflight","contracts"):
        from ring_first_3d.synthetic.handlers import dispatch
        result=dispatch(a.stage,task,attempt)
    elif a.stage=="preflight":
        from preflight import run
        result=run(task["inputs"]["fixture"]["path"],task["inputs"]["dxy_root"])
    elif a.stage=="contracts":
        from validate_contracts import run
        result=run()
    elif a.stage=="smoke":
        from smoke import run
        result=run(task["inputs"]["fixture"]["path"],task["inputs"]["dxy_root"])
    else:raise ValueError("Unknown allowlisted worker stage")
    from ring_first_3d.evaluation.validation import clean
    (attempt/"payload.json").write_text(json.dumps(clean(result),indent=2,allow_nan=False)+"\n")
    print(json.dumps(dict(stage=a.stage,status=result["status"])))


if __name__=="__main__":main()
