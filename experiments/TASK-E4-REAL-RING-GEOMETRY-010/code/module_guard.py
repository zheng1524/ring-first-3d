"""Refuse to run if a same-named module is imported from an older experiment dir."""
import sys, json
from pathlib import Path
T = Path(__file__).resolve().parents[1]
ALLOWED = {T/'code'}
ALLOW_EXTERNAL = {'unified_camera', 'ring_first_3d'}


def check():
    bad = []
    for name, mod in list(sys.modules.items()):
        f = getattr(mod, '__file__', None)
        if not f:
            continue
        p = Path(f).resolve()
        if 'experiments' not in str(p):
            continue
        if name.split('.')[0] in ALLOW_EXTERNAL:
            continue
        if not any(str(p).startswith(str(a)) for a in ALLOWED):
            bad.append(dict(module=name, file=str(p)))
    if bad:
        raise RuntimeError('MODULE_PROVENANCE VIOLATION: ' + json.dumps(bad))
    return [dict(module=n, file=str(getattr(m, '__file__', ''))) for n, m in sorted(sys.modules.items())
            if getattr(m, '__file__', None) and str(T) in str(getattr(m, '__file__', ''))]
