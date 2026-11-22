#!/usr/bin/env python3
"""Single formal entry (025): historical 020 identity build + validation + visualisation.

    python run_cross_video_registration.py --group G03 \
        --config config/CROSS_VIDEO_PROTOCOL.json --stage identity-validation
"""
import argparse, json, subprocess, sys
from pathlib import Path
N = Path(__file__).resolve().parent
STAGES = {'identity-validation': ['core/p1_020_chain.py', 'core/p2_validate.py'],
          'identity-and-visuals': ['core/p1_020_chain.py', 'core/p2_validate.py', 'core/p6_visuals.py']}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--group', required=True)
    ap.add_argument('--config', default=str(N/'config'/'CROSS_VIDEO_PROTOCOL.json'))
    ap.add_argument('--stage', default='identity-validation', choices=sorted(STAGES))
    a = ap.parse_args()
    cfg_path = Path(a.config)
    if not cfg_path.exists():
        sys.exit(f'MISSING_CONFIG {cfg_path}')
    cfg = json.loads(cfg_path.read_text())          # config is parsed and passed down via env
    assert cfg['algo'] == 'w0-crossvideo-025', cfg['algo']
    print('PROTOCOL', cfg['algo'], 'group', a.group, 'stage', a.stage, flush=True)
    import os
    os.environ['CV_CONFIG'] = str(cfg_path)
    for script in STAGES[a.stage]:
        cmd = [sys.executable, str(N/script), '--group', a.group]
        print('RUN', script, flush=True)
        r = subprocess.run(cmd, env=os.environ)
        if r.returncode != 0:
            sys.exit(f'STAGE_FAILED {script} rc={r.returncode}')


if __name__ == '__main__':
    main()
