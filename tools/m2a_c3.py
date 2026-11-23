#!/usr/bin/env python3
"""M2A C3: recover the largest real connected component of a failed pose graph."""
import ast
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import cv2
import numpy as np
import pandas as pd

WS = Path('/home/liu/ring_first_3d_workspace')
OUT = WS / 'runs/m2a_w0_recovery'
PREP = WS / 'runs/m1_final_39/prepared'
FROZEN = WS / 'experiments/TASK-E4-UNIFIED-PIPELINE-COMPLETION-002/code/frozen_calibration'
sys.path.insert(0, str(WS / 'tools'))
from m2a_recover import make_subset, run_one  # noqa: E402


def pair_graph(work):
    tr = dict(np.load(Path(work) / 'observations/tracks005.npz'))
    pack = dict(np.load(Path(work) / 'observations/pairs005.npz'))
    cfg = json.loads((Path(work) / 'config.json').read_text())
    src = (FROZEN / 'local_ring_sfm.py').read_text()
    node = next(n for n in ast.parse(src).body
                if isinstance(n, ast.FunctionDef) and n.name == 'pair_data')
    ns = dict(np=np, cv2=cv2, cfg=lambda: cfg)
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(FROZEN / 'local_ring_sfm.py'), 'exec'), ns)
    edges = ns['pair_data'](tr, pack)
    n = len(tr['frame_raw'])
    parent = list(range(n))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for e in edges:
        a, b = find(int(e['i'])), find(int(e['j']))
        if a != b: parent[b] = a
    comps = {}
    for i in range(n): comps.setdefault(find(i), []).append(i)
    comps = sorted(comps.values(), key=len, reverse=True)
    return tr, edges, comps


def main():
    ap = __import__('argparse').ArgumentParser(); ap.add_argument('--workers', type=int, default=4)
    args = ap.parse_args()
    graph = pd.read_csv(OUT / 'POSE_GRAPH_DIAGNOSTICS.csv')
    jobs = []
    for (g, v) in sorted({(r.group_id, f'{int(r.video_id):03d}') for _, r in graph.iterrows() if r.stage == 'C1'}):
        c1_status = OUT / 'recovery/C1' / g / v / 'STATUS.json'
        c1 = json.loads(c1_status.read_text())['status'] if c1_status.exists() else None
        if c1 in ('COMPLETED_VALID', 'COMPLETED_LIMITED'):
            continue
        work = OUT / 'work/C1' / g / v
        if not (work / 'observations/tracks005.npz').exists():
            continue
        tr, edges, comps = pair_graph(work)
        biggest = comps[0]
        keep = [str(tr['ids'][i]) for i in biggest]
        if len(keep) < 4:
            print('SKIP_SMALL', g, v, len(keep)); continue
        make_subset(g, v, keep, OUT / 'prepared_c3')
        jobs.append((g, v, len(keep)))
    rows = []
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
        futs = {ex.submit(run_one, g, v, OUT / 'prepared_c3', 'C3', OUT / 'recovery/C3',
                          OUT / 'work/C3', list(range(1, n))) : (g, v, n) for g, v, n in jobs}
        for f in as_completed(futs):
            g, v, n = futs[f]
            try: r = f.result()
            except Exception as e:
                r = dict(group_id=g, video_id=v, method='C3', returncode=-1,
                         execution_status='IMPLEMENTATION_ERROR', failure_stage='runner',
                         failure_reason=f'{type(e).__name__}: {e}', n_w0_poses=None,
                         n_accept=None, n_quarantine=None, n_insufficient=None, n_reject=None,
                         ring_mae=None, held_median=None, held_p95=None, output_path=None)
            rows.append(r); print('C3', g, v, 'frames', n, r['execution_status'], 'n', r['n_w0_poses'], flush=True)
    pd.DataFrame(rows).to_csv(OUT / 'RECOVERY_C3.csv', index=False)
    print(pd.DataFrame(rows)[['group_id','video_id','execution_status','n_w0_poses','n_accept']].to_string(index=False))


if __name__ == '__main__':
    main()
