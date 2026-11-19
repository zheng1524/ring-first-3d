"""Reject execution from any former experiment workspace; data may stay external."""
import sys,os,json
from pathlib import Path
from .paths import ROOT
EXECUTED=set()
def install():
    bindings=ROOT/'manifests/PATH_BINDINGS.json'
    blocked=tuple(json.loads(bindings.read_text())) if bindings.exists() else ()
    def guard(event,args):
        if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
            p=Path(os.fsdecode(args[0])).absolute()
            if any(str(p)==b or str(p).startswith(b+'/') for b in blocked):
                raise RuntimeError('RETIRED_WORKTREE_READ_FORBIDDEN: '+str(p))
        if event!='exec':return
        name=args[0].co_filename
        if name.startswith('<'):return
        p=Path(name).resolve()
        if str(p).startswith('/home/liu/ring_first_3d')or p.is_relative_to(Path('/home/liu/ring-first-hero-core')):
            if not p.is_relative_to(ROOT):raise RuntimeError('OLD_EXPERIMENT_EXECUTION_FORBIDDEN: '+str(p))
        if p.is_relative_to(ROOT):EXECUTED.add(str(p.relative_to(ROOT)))
    sys.addaudithook(guard)
