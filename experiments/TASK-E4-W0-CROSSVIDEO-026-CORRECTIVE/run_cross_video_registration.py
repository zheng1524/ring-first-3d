#!/usr/bin/env python3
"""Single formal entry (026-CORRECTIVE). Same CLI as 026, stage renamed full-corrective."""
import argparse, json, os, subprocess, sys
from pathlib import Path
K = Path(__file__).resolve().parent
STAGES = {'centerline': ['core/p1_centerline.py'],
          'ring-validation': ['core/p1_centerline.py', 'core/p2_se3_ring.py'],
          'triangulation-sensitivity': ['core/p4_tracks.py'],
          'full-corrective': ['core/p1_centerline.py', 'core/p2_se3_ring.py', 'core/p4_tracks.py',
                              'core/p3_joint.py', 'core/p6_figures.py']}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--group', required=True)
    ap.add_argument('--config', default=str(K/'config'/'CROSS_VIDEO_PROTOCOL.json'))
    ap.add_argument('--stage', default='full-corrective', choices=sorted(STAGES))
    a = ap.parse_args()
    cfg = json.loads(Path(a.config).read_text())
    assert cfg['algo'] == 'w0-crossvideo-026-corrective', cfg['algo']
    print('PROTOCOL', cfg['algo'], 'group', a.group, 'stage', a.stage, flush=True)
    if a.group != 'G03':
        (K/'runs'/a.group).mkdir(parents=True, exist_ok=True)
        (K/'runs'/a.group/'RUN_STATE.json').write_text(json.dumps(dict(group=a.group, status='BLOCKED_BY_W0_ADMISSION'), indent=1))
        print('BLOCKED_BY_W0_ADMISSION', flush=True)
        return
    env = dict(os.environ, CV_CONFIG=str(Path(a.config)))
    env['PYTHONPATH'] = ':'.join([str(K/'core'), str(K/'replay'), str(K), '/home/liu/ring_first_3d_workspace/runtime/p3d',
                                  '/home/liu/ring_first_3d_workspace/src'])
    for s in STAGES[a.stage]:
        print('RUN', s, flush=True)
        r = subprocess.run([sys.executable, str(K/s), '--group', a.group], env=env) if s.endswith('p3_joint.py') else subprocess.run([sys.executable, str(K/s)], env=env)
        if r.returncode != 0:
            sys.exit(f'STAGE_FAILED {s} rc={r.returncode}')


if __name__ == '__main__':
    main()
