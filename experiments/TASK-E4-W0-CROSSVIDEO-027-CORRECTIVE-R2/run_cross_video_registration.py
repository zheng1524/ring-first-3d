#!/usr/bin/env python3
"""Single formal entry for R2. Stages call the same BA implementation."""
import argparse, json, os, subprocess, sys
from pathlib import Path
R = Path(__file__).resolve().parent
STAGES = {'controlled-level0': ['core/levels.py'],
          'controlled-level1': ['core/levels.py'],
          'controlled-level2': ['core/levels.py'],
          'controlled-r2': ['core/levels.py', 'core/figs_r2.py']}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--group', required=True)
    ap.add_argument('--config', default=str(R/'config'/'R2_PROTOCOL.json'))
    ap.add_argument('--stage', default='controlled-r2', choices=sorted(STAGES))
    ap.add_argument('--levels', default=None)
    ap.add_argument('--yaw', default=None)
    a = ap.parse_args()
    cfg = json.loads(Path(a.config).read_text())
    assert cfg['algo'] == 'w0-crossvideo-027-corrective-r2', cfg['algo']
    print('PROTOCOL', cfg['algo'], 'group', a.group, 'stage', a.stage, 'status', cfg['status'], flush=True)
    if a.group != 'G03':
        (R/'runs'/a.group).mkdir(parents=True, exist_ok=True)
        (R/'runs'/a.group/'RUN_STATE.json').write_text(json.dumps(dict(group=a.group, status='BLOCKED_BY_W0_ADMISSION'), indent=1))
        print('BLOCKED_BY_W0_ADMISSION', flush=True); return
    env = dict(os.environ, CV_CONFIG=str(Path(a.config)))
    env['PYTHONPATH'] = ':'.join([str(R/'core'), str(R/'replay'),
                                  '/home/liu/ring_first_3d_workspace/runtime/p3d', '/home/liu/ring_first_3d_workspace/src'])
    for s in STAGES[a.stage]:
        cmd = [sys.executable, str(R/s)]
        if s.endswith('levels.py'):
            lv = a.levels or {'controlled-level0': '0', 'controlled-level1': '1', 'controlled-level2': '2'}.get(a.stage, '0,1')
            cmd += ['--levels', lv]
            if a.yaw is not None: cmd += ['--yaw', a.yaw]
        print('RUN', s, cmd[2:], flush=True)
        if subprocess.run(cmd, env=env).returncode != 0:
            sys.exit(f'STAGE_FAILED {s}')


if __name__ == '__main__':
    main()
