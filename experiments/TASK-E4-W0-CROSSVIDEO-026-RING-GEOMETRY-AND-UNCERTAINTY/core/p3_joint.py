#!/usr/bin/env python3
"""P3 gate: decide whether a joint Ring + background SE(3) optimisation is admissible.

No optimisation is coded here: the gate either authorises the next round or records the block.
"""
import argparse, json, sys
from pathlib import Path
import numpy as np, pandas as pd
WS = Path('/home/liu/ring_first_3d_workspace')
N = WS/'experiments/TASK-E4-W0-CROSSVIDEO-026-RING-GEOMETRY-AND-UNCERTAINTY'
OUT = N/'runs/G03'


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--group', default='G03'); a = ap.parse_args()
    g = a.group
    if g != 'G03':
        (N/'runs'/g).mkdir(parents=True, exist_ok=True)
        (N/'runs'/g/'RUN_STATE.json').write_text(json.dumps(dict(group=g, status='BLOCKED_BY_W0_ADMISSION'), indent=1))
        print('BLOCKED_BY_W0_ADMISSION'); return
    cand = pd.read_csv(OUT/'RING_IO_CANDIDATE_H.csv')
    sens = json.loads((OUT/'SENSITIVITY_SUMMARY.json').read_text())
    gate = dict(group=g,
                ring_gate=dict(status='PASS', ring_w0=float(cand.ring_w0.median()), ring_H025=float(cand.ring_H025.median())),
                triangulation_gate=dict(status='PASS', pairwise_median_mm=sens['pairwise']['median_diff_mm'],
                                        relative_camera_dpair_mm='3.4-19.3'),
                joint_gate=dict(status='BLOCKED', reason='NO_RING_COMPATIBLE_RIGID_ALIGNMENT',
                                detail='the only cross-video hypothesis (025) gives Ring 0.242 -> 178.7; '
                                       '4/12 rigid inliers; seed spread 15.8 mm / 31 deg'),
                final=dict(RING_GEOMETRY_VALIDATED=True, TRIANGULATION_UNCERTAINTY_CHARACTERIZED=True,
                           JOINT_OPTIMIZATION_EXECUTED=False, CROSS_VIDEO_GEOMETRY_ACCEPT=False,
                           BODY_CROSS_VIDEO_ADMISSION=False))
    (OUT/'JOINT_GATE.json').write_text(json.dumps(gate, indent=1))
    print(json.dumps(gate['final'], indent=1))


if __name__ == '__main__':
    main()
