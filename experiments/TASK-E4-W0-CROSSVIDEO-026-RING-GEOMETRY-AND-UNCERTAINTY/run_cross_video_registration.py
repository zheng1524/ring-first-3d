#!/usr/bin/env python3
"""Single formal entry for 026 (same CLI as 025, extended stages).

    python run_cross_video_registration.py --group G03 --config config/CROSS_VIDEO_PROTOCOL.json \
        --stage ring-validation|triangulation-sensitivity|joint-registration|full-026
"""
import argparse, json, os, subprocess, sys
from pathlib import Path
N = Path(__file__).resolve().parent
STAGES = {
    'ring-validation': ['core/p1_ring_io.py'],
    'triangulation-sensitivity': ['core/p1_ring_io.py', 'core/p2_sensitivity.py', 'core/p2_relative.py'],
    'joint-registration': ['core/p3_joint.py'],
    'full-026': ['core/p1_ring_io.py', 'core/p2_sensitivity.py', 'core/p2_relative.py',
                 'core/p3_joint.py', 'core/p4_figures.py'],
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--group', required=True)
    ap.add_argument('--config', default=str(N/'config'/'CROSS_VIDEO_PROTOCOL.json'))
    ap.add_argument('--stage', default='full-026', choices=sorted(STAGES))
    a = ap.parse_args()
    cfg_path = Path(a.config)
    if not cfg_path.exists():
        sys.exit(f'MISSING_CONFIG {cfg_path}')
    cfg = json.loads(cfg_path.read_text())
    assert cfg['algo'] == 'w0-crossvideo-026', cfg['algo']
    print('PROTOCOL', cfg['algo'], 'group', a.group, 'stage', a.stage, flush=True)
    env = dict(os.environ, CV_CONFIG=str(cfg_path))
    env['PYTHONPATH'] = ':'.join([str(N/'core'), str(N/'replay_020/code'),
                                  '/home/liu/ring_first_3d_workspace/runtime/p3d',
                                  '/home/liu/ring_first_3d_workspace/src'])
    for script in STAGES[a.stage]:
        print('RUN', script, flush=True)
        r = subprocess.run([sys.executable, str(N/script), '--group', a.group], env=env)
        if r.returncode != 0:
            sys.exit(f'STAGE_FAILED {script} rc={r.returncode}')


if __name__ == '__main__':
    main()
