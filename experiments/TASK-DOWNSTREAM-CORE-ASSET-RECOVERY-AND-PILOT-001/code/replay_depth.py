"""Existing 018 replay, zero optimizer steps; retained external inputs required."""
import argparse
from pathlib import Path
from pilot import TASK
from ring_first_3d.mainline.replays import depth_supervised,save
p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args();out=Path(a.out).resolve()
if not out.is_relative_to(TASK) or out.exists():raise ValueError('New task-local directory required')
out.mkdir(parents=True)
r=depth_supervised(out);save(out/'RECEIPT.json',r);print(r)
if r['status']!='PASS':raise SystemExit(1)
