#!/usr/bin/env python3
"""Single formal entry for cross-video landmark identity + consistency (all groups).

    python run_cross_video_registration.py --group G03 --config config/CROSS_VIDEO_PROTOCOL.json
"""
import argparse, json, sys
from pathlib import Path
M = Path(__file__).resolve().parent
sys.path.insert(0, str(M/'core')); sys.path.insert(0, str(M/'replay_019_020/code'))
import p1_pipeline as P1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--group', required=True)
    ap.add_argument('--config', default=str(M/'config'/'CROSS_VIDEO_PROTOCOL.json'))
    a = ap.parse_args()
    cfg = json.loads(Path(a.config).read_text())
    print('PROTOCOL', cfg['algo'], 'group', a.group, flush=True)
    sys.argv = [sys.argv[0], '--group', a.group]
    P1.main()


if __name__ == '__main__':
    main()
