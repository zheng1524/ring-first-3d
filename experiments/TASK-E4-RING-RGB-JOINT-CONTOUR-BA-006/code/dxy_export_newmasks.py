"""Re-export DXY geometry for the newly prepared (frozen-INIT) masks. Read-only DXY."""
import json, sys
from pathlib import Path
import numpy as np
T = Path(__file__).resolve().parents[1]
PREP = Path('/home/liu/ring_first_3d_workspace/experiments/TASK-E4-UNIFIED-RING-CONTOUR-REFINEMENT-005/runs/prepared')
OUT = T/'metrics/DXY_OBSERVATIONS'; OUT.mkdir(parents=True, exist_ok=True)
from dxy_mid._engine import ring_component as RC

rows = []
for d in sorted(PREP.glob('G*_*')):
    if not (d/'PREPARED.json').exists(): continue
    meta = json.loads((d/'PREPARED.json').read_text())
    for v in meta['views']:
        cid = v['view']
        p = OUT/(cid+'.json')
        if p.exists():
            rows.append(dict(view=cid, reused=True)); continue
        c = np.load(v['cache'])
        base, _ = RC.recover(c['labels'], c['RGB'][:,:,::-1].copy(), 10.0)
        rec = dict(view=cid, group=meta['group'], video=meta['video'], valid=bool(base.get('valid')),
                   reason=base.get('reason'), branch=base.get('branch'), inner=base.get('inner'),
                   outer=base.get('outer'), centerline=base.get('centerline'),
                   diagnostics=base.get('diagnostics'), mask_source=v['cache'],
                   mask_sha=None)
        p.write_text(json.dumps(rec, indent=1))
        rows.append(dict(view=cid, valid=rec['valid']))
print('exported', len(rows), 'valid', sum(1 for r in rows if r.get('valid')))
