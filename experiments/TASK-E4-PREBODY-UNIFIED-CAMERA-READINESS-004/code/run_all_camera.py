import subprocess, sys
from pathlib import Path
T = Path(__file__).resolve().parents[1]
inst = [(g, v) for g in ('G01', 'G02', 'G03', 'G05', 'G06') for v in ('004', '005')]
for n in (8, 16, 22):
    for g, v in inst:
        r = subprocess.run([sys.executable, str(T / 'code/run_camera.py'), g, v, str(n)],
                           capture_output=True, text=True, cwd=str(T))
        out = (r.stdout or '').strip().splitlines()
        print(f'[{n}] {g}/{v}: ' + (out[-2] if len(out) > 1 else (out[-1] if out else 'no output')), flush=True)
