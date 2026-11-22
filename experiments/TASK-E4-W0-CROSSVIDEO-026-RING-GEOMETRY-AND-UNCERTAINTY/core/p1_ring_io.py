#!/usr/bin/env python3
"""P1: historical ring020 RingRenderer (patched copy) on current G03 W0 cameras -> M/I/C/O per view."""
import json, os, sys
from pathlib import Path
import numpy as np, pandas as pd, torch
WS = Path('/home/liu/ring_first_3d_workspace')
N = WS/'experiments/TASK-E4-W0-CROSSVIDEO-026-RING-GEOMETRY-AND-UNCERTAINTY'
RUN = N/'replay_020/runs'
sys.path.insert(0, str(N/'replay_020/code')); sys.path.insert(0, str(WS/'src'))
os.environ['E4_RUN_DIR'] = str(RUN)
os.environ['RING_CAD'] = str(WS/'assets/retained_sources/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-HERO-BODY-ADAPT-018/inputs/G03/RING.npz')
os.environ['RING_NORM'] = str(WS/'assets/retained_sources/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/FREE_VERTEX_013/inputs/G03/NORMALIZATION.json')
from ring020_026 import RingRenderer, tensor


def main():
    ids = [v['id'] for v in json.loads((RUN/'config'/'VIEWS.json').read_text())]
    rr = RingRenderer(ids)
    rows = []
    for cid in ids:
        L, aux, _ = rr.losses(tensor(np.eye(4), torch.float64), cid)
        row = dict(view=cid, M=float(L['M']), I=float(L['I']), C=float(L['C']), O=float(L['O']),
                   ring=0.25*float(L['M'])+0.35*float(L['I'])+0.05*float(L['C'])+0.35*float(L['O']))
        for k in ('M','I','C','O'):
            a = aux.get(k, {})
            row[f'{k}_N'] = a.get('N') if isinstance(a, dict) else None
        rows.append(row)
        print('RINGIO', cid, round(row['I'], 3), round(row['O'], 3), round(row['ring'], 3), flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(N/'runs/G03'/'RING_IO_PER_VIEW.csv', index=False)
    print(json.dumps(dict(n=len(df), I_median=float(df.I.median()), O_median=float(df.O.median()),
                          M_median=float(df.M.median()), C_median=float(df.C.median()),
                          ring_median=float(df.ring.median())), indent=1))


if __name__ == '__main__':
    main()
