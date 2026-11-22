#!/usr/bin/env python3
"""Single formal entry (027-CORRECTIVE). No second BA pipeline exists."""
import argparse, json, os, subprocess, sys
from pathlib import Path
C = Path(__file__).resolve().parent
STAGES = {'variables': ['core/camvar.py'],
          'ring': ['core/ring_adapter.py'],
          'controlled': ['core/controlled2.py'],
          'audit': ['core/p8_audit.py'],
          'full-corrective': ['core/controlled2.py', 'core/p8_audit.py']}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--group', required=True)
    ap.add_argument('--config', default=str(C/'config'/'BA_PROTOCOL.json'))
    ap.add_argument('--stage', default='full-corrective', choices=sorted(STAGES))
    a = ap.parse_args()
    cfg = json.loads(Path(a.config).read_text())
    assert cfg['algo'] == 'w0-crossvideo-027-corrective', cfg['algo']
    print('PROTOCOL', cfg['algo'], 'group', a.group, 'stage', a.stage,
          'ring_lambda', cfg['weights']['ring_lambda'], flush=True)
    if a.group != 'G03':
        (C/'runs'/a.group).mkdir(parents=True, exist_ok=True)
        (C/'runs'/a.group/'RUN_STATE.json').write_text(json.dumps(dict(group=a.group, status='BLOCKED_BY_W0_ADMISSION'), indent=1))
        print('BLOCKED_BY_W0_ADMISSION', flush=True); return
    env = dict(os.environ, CV_CONFIG=str(Path(a.config)))
    env['PYTHONPATH'] = ':'.join([str(C/'core'), str(C/'replay'),
                                  '/home/liu/ring_first_3d_workspace/runtime/p3d', '/home/liu/ring_first_3d_workspace/src'])
    for s in STAGES[a.stage]:
        print('RUN', s, flush=True)
        if subprocess.run([sys.executable, str(C/s)], env=env).returncode != 0:
            sys.exit(f'STAGE_FAILED {s}')


if __name__ == '__main__':
    main()
