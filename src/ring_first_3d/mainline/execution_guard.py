"""Reject execution from any former experiment workspace; data may stay external."""
import sys
from pathlib import Path
from .paths import ROOT
EXECUTED=set()
def install():
    def guard(event,args):
        if event!='exec':return
        name=args[0].co_filename
        if name.startswith('<'):return
        p=Path(name).resolve()
        if str(p).startswith('/home/liu/ring_first_3d')or p.is_relative_to(Path('/home/liu/ring-first-hero-core')):
            if not p.is_relative_to(ROOT):raise RuntimeError('OLD_EXPERIMENT_EXECUTION_FORBIDDEN: '+str(p))
        if p.is_relative_to(ROOT):EXECUTED.add(str(p.relative_to(ROOT)))
    sys.addaudithook(guard)
