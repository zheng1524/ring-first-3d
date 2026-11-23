#!/usr/bin/env python3
"""Single formal entry for R4 (stages select experiments; one BA implementation)."""
import argparse, json, os, subprocess, sys
from pathlib import Path
R4 = Path(__file__).resolve().parent
STAGES = {'r4-corrective': [],
          'controlled-error-ablation': [('core/r4_run.py', ['--what', 'baseline']),
                                        ('core/r4_run.py', ['--what', 'leftover']),
                                        ('core/figs_r4.py', [])],
          'full-r4': [('core/r4_run.py', ['--what', 'baseline']),
                      ('core/r4_run.py', ['--what', 'leftover']),
                      ('core/figs_r4.py', [])]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--group', required=True)
    ap.add_argument('--config', default=str(R4/'config'/'R4_PROTOCOL.json'))
    ap.add_argument('--stage', default='controlled-error-ablation', choices=sorted(STAGES))
    a = ap.parse_args()
    cfg = json.loads(Path(a.config).read_text())
    assert cfg['algo'] == 'w0-crossvideo-027-corrective-r4', cfg['algo']
    print('PROTOCOL', cfg['algo'], 'group', a.group, 'stage', a.stage, 'status', cfg['status'], flush=True)
    if a.group != 'G03':
        (R4/'runs'/a.group).mkdir(parents=True, exist_ok=True)
        (R4/'runs'/a.group/'RUN_STATE.json').write_text(json.dumps(dict(group=a.group, status='BLOCKED_BY_W0_ADMISSION'), indent=1))
        print('BLOCKED_BY_W0_ADMISSION', flush=True); return
    env = dict(os.environ, CV_CONFIG=str(Path(a.config)))
    env['PYTHONPATH'] = ':'.join([str(R4/'core'), str(R4/'replay'),
                                  '/home/liu/ring_first_3d_workspace/runtime/p3d', '/home/liu/ring_first_3d_workspace/src'])
    for script, extra in STAGES[a.stage]:
        print('RUN', script, extra, flush=True)
        if subprocess.run([sys.executable, str(R4/script)]+extra, env=env).returncode != 0:
            sys.exit(f'STAGE_FAILED {script}')


if __name__ == '__main__':
    main()
