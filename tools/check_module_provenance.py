#!/usr/bin/env python3
"""Fail if the running task silently imports a same-named module from an older experiment."""
import sys, json
from pathlib import Path
TASK = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd().resolve()
ALLOW = {TASK/'code'}
ALLOW_PREFIX = ('ring_first_3d', 'unified_camera')
bad = []
for name, mod in list(sys.modules.items()):
    f = getattr(mod, '__file__', None)
    if not f or 'experiments' not in str(f): continue
    p = Path(f).resolve()
    if name.split('.')[0] in ALLOW_PREFIX: continue
    if not any(str(p).startswith(str(a)) for a in ALLOW):
        bad.append(dict(module=name, file=str(p)))
print(json.dumps(dict(task=str(TASK), violations=bad), indent=1))
sys.exit(1 if bad else 0)
