#!/usr/bin/env python3
"""M2A B1/C1 recovery runner.

B1: for Ring-insufficient videos, keep frames with observe(labels).q_train >= 20.
C1: for pose-graph-disconnected videos, keep all frames but try all frame pairs.
All camera solving is delegated to the frozen M1 W0 entry.
"""
import argparse
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

WS = Path('/home/liu/ring_first_3d_workspace')
M1 = WS / 'runs/m1_final_39'
OUT = WS / 'runs/m2a_w0_recovery'
PREP = M1 / 'prepared'
W0 = WS / 'tools/run_w0_camera.py'
PY = sys.executable

sys.path.insert(0, str(WS / 'src'))


def make_subset(g, v, keep, root):
    src = PREP / f'{g}_{v}' / 'PREPARED.json'
    meta = json.loads(src.read_text())
    out = Path(root) / f'{g}_{v}'
    out.mkdir(parents=True, exist_ok=True)
    views = [q for q in meta['views'] if q['view'] in set(keep)]
    if not views:
        return None
    m2 = dict(meta)
    m2['views'] = views
    m2['subset_of'] = str(src)
    m2['excluded_frames'] = [q['view'] for q in meta['views'] if q['view'] not in set(keep)]
    m2['selection_reason'] = 'M2A_B1_QTRAIN_GE20'
    (out / 'PREPARED.json').write_text(json.dumps(m2, indent=1))
    return out


def run_one(g, v, prepared_root, method, out_root, work_root, pair_offsets):
    out = Path(out_root) / g / v
    work = Path(work_root) / g / v
    out.mkdir(parents=True, exist_ok=True); work.mkdir(parents=True, exist_ok=True)
    cmd = [PY, str(W0), '--group', g, '--video', v, '--stage', 'all',
           '--prepared-root', str(prepared_root), '--output', str(out), '--workdir', str(work),
           '--pair-offsets', ','.join(str(x) for x in pair_offsets)]
    env = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1',
               MKL_NUM_THREADS='1', NUMEXPR_NUM_THREADS='1')
    r = subprocess.run(cmd, cwd=WS, capture_output=True, text=True, env=env)
    (out / 'stdout.log').write_text(r.stdout); (out / 'stderr.log').write_text(r.stderr)
    st = {}
    if (out / 'STATUS.json').exists():
        st = json.loads((out / 'STATUS.json').read_text())
    q = {}
    if (out / 'quality_summary.json').exists():
        q = json.loads((out / 'quality_summary.json').read_text())
    return dict(group_id=g, video_id=v, method=method, returncode=r.returncode,
                execution_status=st.get('status'), failure_stage=st.get('stage'),
                failure_reason=st.get('reason'), n_w0_poses=q.get('n_w0_poses'),
                n_accept=q.get('n_accept'), n_quarantine=q.get('n_quarantine'),
                n_insufficient=q.get('n_insufficient_evidence'), n_reject=q.get('n_reject'),
                ring_mae=q.get('ring_mae_mean_px'), held_median=q.get('held_median_px'),
                held_p95=q.get('held_p95_px'), output_path=str(out))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--workers', type=int, default=4)
    args = ap.parse_args()
    ring = pd.read_csv(OUT / 'RING_FRAME_DIAGNOSTICS.csv')
    graph = pd.read_csv(OUT / 'POSE_GRAPH_DIAGNOSTICS.csv')
    b1 = []
    for (g, v), sub in ring.groupby(['group_id', 'video_id']):
        v = f'{int(v):03d}'
        keep = sub[sub.q_train_count >= 20].frame_id.tolist()
        if keep:
            root = OUT / 'prepared_b1'
            make_subset(g, v, keep, root)
            b1.append((g, v, len(keep), len(sub)))
    c1 = sorted({(r.group_id, f'{int(r.video_id):03d}') for _, r in graph.iterrows() if r.stage == 'C1'})
    jobs = [(g, v, OUT / 'prepared_b1', 'B1', nkeep, total)
            for g, v, nkeep, total in b1] + [(g, v, PREP, 'C1', 10, 10) for g, v in c1]
    rows = []
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
        futs = {}
        for g, v, prep, method, nkeep, total in jobs:
            out_root = OUT / 'recovery' / method
            work_root = OUT / 'work' / method
            po = list(range(1, int(nkeep)))
            futs[ex.submit(run_one, g, v, prep, method, out_root, work_root, po)] = (g, v, method)
        for f in as_completed(futs):
            g, v, method = futs[f]
            try:
                r = f.result()
            except Exception as e:
                r = dict(group_id=g, video_id=v, method=method, returncode=-1,
                         execution_status='IMPLEMENTATION_ERROR', failure_stage='runner',
                         failure_reason=f'{type(e).__name__}: {e}', n_w0_poses=None,
                         n_accept=None, n_quarantine=None, n_insufficient=None, n_reject=None,
                         ring_mae=None, held_median=None, held_p95=None, output_path=None)
            rows.append(r)
            print('RECOVER', method, g, v, r['execution_status'], 'n', r['n_w0_poses'], flush=True)
    pd.DataFrame(rows).to_csv(OUT / 'RECOVERY_RESULTS.csv', index=False)
    print(pd.DataFrame(rows)[['method','group_id','video_id','execution_status','n_w0_poses','n_accept']].to_string(index=False))


if __name__ == '__main__':
    main()
