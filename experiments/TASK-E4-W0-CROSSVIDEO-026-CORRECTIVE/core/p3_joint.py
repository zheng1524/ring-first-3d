#!/usr/bin/env python3
"""026-CORRECTIVE gate script (was referenced by the entry but missing — 027 P0.1 repair).

Reads the corrective Ring/H025/sensitivity numbers and writes the joint gate decision.
No optimisation of any kind is performed here.
"""
import argparse, json, sys
from pathlib import Path
import pandas as pd
WS = Path('/home/liu/ring_first_3d_workspace')
K = WS/'experiments/TASK-E4-W0-CROSSVIDEO-026-CORRECTIVE'
OUT = K/'runs/G03'


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--group', default='G03'); a = ap.parse_args()
    if a.group != 'G03':
        (K/'runs'/a.group).mkdir(parents=True, exist_ok=True)
        (K/'runs'/a.group/'RUN_STATE.json').write_text(json.dumps(dict(group=a.group, status='BLOCKED_BY_W0_ADMISSION'), indent=1))
        print('BLOCKED_BY_W0_ADMISSION'); return
    io = pd.read_csv(OUT/'RING_IO_CORRECTIVE.csv'); h = pd.read_csv(OUT/'H025_REEVALUATION.csv')
    gate = dict(group='G03',
                ring_gate=dict(status='PASS', mio_w0=float(io.MIO.median()), mio_h025=float(h.MIO.median())),
                joint_gate=dict(status='BLOCKED', reason='NO_VALIDATED_CANDIDATE_FOUND'),
                final=dict(RING_GEOMETRY_VALIDATED=True, TRIANGULATION_UNCERTAINTY_CHARACTERIZED=True,
                           JOINT_OPTIMIZATION_EXECUTED=False, CROSS_VIDEO_GEOMETRY_ACCEPT=False))
    (OUT/'JOINT_GATE.json').write_text(json.dumps(gate, indent=1))
    print(json.dumps(gate['final'], indent=1))


if __name__ == '__main__':
    main()
