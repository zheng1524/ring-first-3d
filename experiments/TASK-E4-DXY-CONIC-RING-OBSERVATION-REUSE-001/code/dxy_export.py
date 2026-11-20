"""Step 2: export DXY V9.1 ring geometry for every frozen FIT view.

Run with an interpreter that has scikit-image (DXY dependency):
    PYTHONPATH=/home/liu/new-polyp-dxy/src /usr/bin/python3 dxy_export.py

DXY is used read-only as an upstream 2-D observation source. Its algorithm is
not modified, re-implemented or re-fitted here.
"""
import json
from pathlib import Path
import numpy as np

WS = Path('/home/liu/ring_first_3d_workspace')
T005 = WS / 'experiments/TASK-E4-UNIFIED-RING-RGB-CAMERA-MAINLINE-005'
TASK = WS / 'experiments/TASK-E4-DXY-CONIC-RING-OBSERVATION-REUSE-001'
OUT = TASK / 'metrics/DXY_OBSERVATIONS'
OUT.mkdir(parents=True, exist_ok=True)

from dxy_mid._engine import ring_component as RC  # noqa: E402


def main():
    V = json.loads((WS / 'experiments/TASK-E4-UNIFIED-PIPELINE-COMPLETION-002/audit/SELECTED_VIEWS.json').read_text())
    inner_mm = 10.0  # DXY V9.1 frozen R10 inner diameter used by the mainline
    rows = []
    for x in V:
        if x['meta']['role'] != 'FIT':
            continue
        cid = x['meta']['id']
        d = np.load(x['cache']['path'])
        labels, rgb = d['labels'], d['RGB']
        base, payload = RC.recover(labels, rgb[:, :, ::-1].copy(), inner_mm)
        rec = dict(id=cid, group=x['meta']['case'], video=x['meta']['video'],
                   cache=x['cache']['path'], valid=bool(base.get('valid')),
                   reason=base.get('reason'), branch=base.get('branch'),
                   inner=base.get('inner'), outer=base.get('outer'),
                   centerline=base.get('centerline'),
                   diagnostics=base.get('diagnostics'))
        (OUT / (cid + '.json')).write_text(json.dumps(rec, indent=1))
        rows.append(dict(id=cid, group=rec['group'], video=rec['video'],
                         valid=rec['valid'], reason=rec['reason'], branch=rec['branch']))
        print('DXY', cid, rec['valid'], rec['branch'], flush=True)
    (OUT / 'INDEX.json').write_text(json.dumps(dict(count=len(rows), views=rows), indent=1))
    print('exported', len(rows))


if __name__ == '__main__':
    main()
