#!/usr/bin/env python3
"""Single formal entry for R3 (same BA modules; stages only select experiments)."""
import argparse, json, os, subprocess, sys
from pathlib import Path
R3 = Path(__file__).resolve().parent
STAGES = {'controlled-L2-diagnostics': [('core/r3_run.py', ['--what', 'h_only_sweep', '--yaws', '0,1,3,6,9,12,18', '--max-nfev', '200']),
                                        ('core/r3_run.py', ['--what', 'compare', '--max-nfev', '60']),
                                        ('core/visibility_jacobian.py', [])],
          'controlled-L3': [('core/r3_run.py', ['--what', 'h_only_sweep', '--yaws', '3', '--max-nfev', '200'])],
          'controlled-L4': [], 'controlled-L5': []}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--group', required=True)
    ap.add_argument('--config', default=str(R3/'config'/'R3_PROTOCOL.json'))
    ap.add_argument('--stage', default='controlled-L2-diagnostics', choices=sorted(STAGES))
    a = ap.parse_args()
    cfg = json.loads(Path(a.config).read_text())
    assert cfg['algo'] == 'w0-crossvideo-027-corrective-r3', cfg['algo']
    print('PROTOCOL', cfg['algo'], 'group', a.group, 'stage', a.stage, 'status', cfg['status'], flush=True)
    if a.group != 'G03':
        (R3/'runs'/a.group).mkdir(parents=True, exist_ok=True)
        (R3/'runs'/a.group/'RUN_STATE.json').write_text(json.dumps(dict(group=a.group, status='BLOCKED_BY_W0_ADMISSION'), indent=1))
        print('BLOCKED_BY_W0_ADMISSION', flush=True); return
    env = dict(os.environ, CV_CONFIG=str(Path(a.config)))
    env['PYTHONPATH'] = ':'.join([str(R3/'core'), str(R3/'replay'),
                                  '/home/liu/ring_first_3d_workspace/runtime/p3d', '/home/liu/ring_first_3d_workspace/src'])
    for script, extra in STAGES[a.stage]:
        print('RUN', script, extra, flush=True)
        if subprocess.run([sys.executable, str(R3/script)]+extra, env=env).returncode != 0:
            sys.exit(f'STAGE_FAILED {script}')


if __name__ == '__main__':
    main()
