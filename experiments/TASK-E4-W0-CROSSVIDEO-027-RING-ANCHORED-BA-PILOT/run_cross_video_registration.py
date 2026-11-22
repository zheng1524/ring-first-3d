#!/usr/bin/env python3
"""Single formal entry (027). Stages: prerequisite-validation | ba-controlled | shared-H-baseline | ba-real | full-027."""
import argparse, json, os, subprocess, sys
from pathlib import Path
B = Path(__file__).resolve().parent
STAGES = {'prerequisite-validation': ['core/p0_paired.py'],
          'ba-controlled': ['core/p3_controlled.py'],
          'shared-H-baseline': ['core/p4_real.py'],
          'ba-real': ['core/p4_real.py'],
          'full-027': ['core/p0_paired.py', 'core/p3_controlled.py', 'core/p4_real.py', 'core/p6_figures.py']}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--group', required=True)
    ap.add_argument('--config', default=str(B/'config'/'BA_PROTOCOL.json'))
    ap.add_argument('--stage', default='full-027', choices=sorted(STAGES))
    a = ap.parse_args()
    cfg = json.loads(Path(a.config).read_text())          # parsed and passed down
    assert cfg['algo'] == 'w0-crossvideo-027-ba-pilot', cfg['algo']
    print('PROTOCOL', cfg['algo'], 'group', a.group, 'stage', a.stage,
          'ring_lambda', cfg['weights']['ring_lambda'], flush=True)
    if a.group != 'G03':
        (B/'runs'/a.group).mkdir(parents=True, exist_ok=True)
        (B/'runs'/a.group/'RUN_STATE.json').write_text(json.dumps(dict(group=a.group, status='BLOCKED_BY_W0_ADMISSION'), indent=1))
        print('BLOCKED_BY_W0_ADMISSION', flush=True); return
    env = dict(os.environ, CV_CONFIG=str(Path(a.config)))
    env['PYTHONPATH'] = ':'.join([str(B/'core'), str(B/'replay'), str(B),
                                  '/home/liu/ring_first_3d_workspace/runtime/p3d', '/home/liu/ring_first_3d_workspace/src'])
    for s in STAGES[a.stage]:
        print('RUN', s, flush=True)
        if subprocess.run([sys.executable, str(B/s)], env=env).returncode != 0:
            sys.exit(f'STAGE_FAILED {s}')


if __name__ == '__main__':
    main()
