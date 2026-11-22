#!/usr/bin/env python3
"""Rebuild SUMMARY.csv from ALL independent run directories (never overwritten by a new run)."""
import glob, json
from pathlib import Path
import pandas as pd
R3 = Path('/home/liu/ring_first_3d_workspace/experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R3')
CT = R3/'runs/controlled'
rows = []
for f in sorted(glob.glob(str(CT/'*'/'METRICS.json'))):
    d = json.loads(open(f).read())
    rows.append({k: v for k, v in d.items() if k not in ('stage1',)})
pd.DataFrame(rows).to_csv(CT/'SUMMARY_ALL_RUNS.csv', index=False)
print('aggregated', len(rows), 'runs')
