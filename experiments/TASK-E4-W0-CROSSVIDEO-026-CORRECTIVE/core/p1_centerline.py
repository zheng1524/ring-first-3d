#!/usr/bin/env python3
"""P1: regenerate Ring observations with the REAL DXY centerline (same routine 019 used).

Historical path (verified): 019/ring019.py -> dxy_mid._engine.ring_component.recover(labels, RGB, 10.)
  -> ring/<view>.npz {inner,outer} + ring/<view>.json {inner,outer,centerline,...}
026 replaced this with 011 DXY_OBSERVATIONS and wrongly set centerline=inner.
This script reruns the HISTORICAL routine (unmodified) in a new namespace ring_corrective/.
"""
import importlib, json, sys, types
from pathlib import Path
import numpy as np
WS = Path('/home/liu/ring_first_3d_workspace')
K = WS/'experiments/TASK-E4-W0-CROSSVIDEO-026-CORRECTIVE'
R26 = WS/'experiments/TASK-E4-W0-CROSSVIDEO-026-RING-GEOMETRY-AND-UNCERTAINTY/replay_020/runs'
DXY = Path('/home/liu/new-polyp-dxy/src/dxy_mid')


def mod():
    pkg = types.ModuleType('dxy_mid'); pkg.__path__ = [str(DXY)]; sys.modules.setdefault('dxy_mid', pkg)
    return importlib.import_module('dxy_mid._engine.ring_component')


def main():
    recover = mod().recover
    views = json.loads((R26/'config'/'VIEWS.json').read_text())
    out = K/'replay'/'ring_corrective'; out.mkdir(parents=True, exist_ok=True)
    rows = []
    for v in views:
        a = np.load(v['cache'])
        rep, pay = recover(a['labels'], a['RGB'][:, :, ::-1], 10.)
        np.savez_compressed(out/(v['id']+'.npz'),
                            inner=pay.get('inner_points', np.empty((0, 2))),
                            outer=pay.get('outer_points', np.empty((0, 2))),
                            rejected=pay.get('rejected_points', np.empty((0, 2))))
        (out/(v['id']+'.json')).write_text(json.dumps(rep))
        ci, cc = rep.get('inner'), rep.get('centerline')
        same = bool(ci == cc) if ci is not None and cc is not None else None
        rows.append(dict(view=v['id'], video=v['video'], role=v['role'], valid=rep.get('valid'),
                         has_centerline=cc is not None, centerline_equals_inner=same,
                         inner=ci, outer=rep.get('outer'), centerline=cc,
                         inner_N=len(pay.get('inner_points', [])), outer_N=len(pay.get('outer_points', []))))
        print('CL', v['id'], rep.get('valid'), 'centerline', 'MISSING' if cc is None else ('SAME_AS_INNER' if same else 'DISTINCT'), flush=True)
    (K/'runs/G03/CENTERLINE_AUDIT.json').write_text(json.dumps(rows, indent=1))
    import pandas as pd
    pd.DataFrame([{k: r[k] for k in ('view','video','role','valid','has_centerline','centerline_equals_inner','inner_N','outer_N')} for r in rows]).to_csv(K/'runs/G03/CENTERLINE_AUDIT.csv', index=False)
    n = sum(1 for r in rows if r['centerline_equals_inner'] is False)
    print('views', len(rows), 'centerline distinct:', n, 'missing:', sum(1 for r in rows if r['has_centerline'] is False))


if __name__ == '__main__':
    main()
