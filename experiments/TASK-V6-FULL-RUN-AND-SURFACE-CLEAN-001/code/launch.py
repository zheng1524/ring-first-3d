"""Freeze only the committed execution code and start a detached, logged queue."""
from pathlib import Path
import subprocess,tarfile,io,json,hashlib,os,time
wt=Path(__file__).resolve().parents[3];B=Path('/home/liu/ring_first_3d_workspace/runs/v6_full_run_001');head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=wt,text=True).strip();snap=B/'snapshots'/head
snap.mkdir(parents=True,exist_ok=False)
paths=['src/ring_first_3d/v6_raw','src/ring_first_3d/__init__.py','experiments/TASK-V6-RAW-TO-HERO-MAINLINE-001/evidence/KERNEL_LOCK.json','experiments/TASK-V6-FULL-RUN-AND-SURFACE-CLEAN-001/config/FULL_RUN.json','experiments/TASK-V6-FULL-RUN-AND-SURFACE-CLEAN-001/evidence/DATASET_MANIFEST.json']
archive=subprocess.check_output(['git','archive',head,*paths],cwd=wt);tarfile.open(fileobj=io.BytesIO(archive)).extractall(snap)
config=snap/'experiments/TASK-V6-FULL-RUN-AND-SURFACE-CLEAN-001/config/FULL_RUN.json';c=json.loads(config.read_text());c['manifest']=str(snap/'experiments/TASK-V6-FULL-RUN-AND-SURFACE-CLEAN-001/evidence/DATASET_MANIFEST.json');config.write_text(json.dumps(c,indent=2))
(snap/'experiments/TASK-V6-FULL-RUN-AND-SURFACE-CLEAN-001/figures').mkdir(exist_ok=True)
receipt=dict(execution_commit=head,snapshot=str(snap),config=str(config),files={str(p.relative_to(snap)):hashlib.sha256(p.read_bytes()).hexdigest() for p in snap.rglob('*') if p.is_file()},baseline_readonly_files={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path('/home/liu/.config/superpowers/worktrees/ring_first_3d_workspace/TASK-V6-RAW-TO-HERO-001/src/ring_first_3d/v6_raw/route.py'),Path('/home/liu/.config/superpowers/worktrees/ring_first_3d_workspace/TASK-V6-RAW-TO-HERO-001/src/ring_first_3d/v6_raw/policy.py')]})
(B/'SNAPSHOT.json').write_text(json.dumps(receipt,indent=2));(wt/'experiments/TASK-V6-FULL-RUN-AND-SURFACE-CLEAN-001/evidence/EXECUTION_SNAPSHOT.json').write_text(json.dumps(receipt,indent=2))
for p in snap.rglob('*'):
 if p.is_file():p.chmod(0o444)
script=f'''#!/bin/bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH='{snap}/src:/home/liu/ring_first_3d_workspace/.runtime/extra_packages:/home/liu/polyp_research/ring_anchor_3d/experiments/surface_fusion_v3/vendor'
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 V6_EXECUTION_COMMIT={head}
cd '{snap}'
python3 - <<'CHECK'
import json,hashlib
from pathlib import Path
r=json.loads(Path('{B}/SNAPSHOT.json').read_text())
for p,h in list(r['baseline_readonly_files'].items())+[(str(Path(r['snapshot'])/p),h) for p,h in r['files'].items()]:
 assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,'SNAPSHOT_DRIFT '+p
CHECK
exec /home/liu/polyp_research/ring_anchor_3d/.venv/bin/python -u -m ring_first_3d.v6_raw.full_run run --config '{config}'
'''
(B/'start.sh').write_text(script);(B/'start.sh').chmod(0o755)
if (B/'PAUSE_REQUESTED').exists():(B/'PAUSE_REQUESTED').unlink()
log=open(B/'runner.log','ab');p=subprocess.Popen(['bash',str(B/'start.sh')],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);rec=dict(pid=p.pid,epoch=time.time(),command=['bash',str(B/'start.sh')],persistent='setsid detached process, stdin DEVNULL, logfile redirection',snapshot=head)
(B/'LAUNCH.json').write_text(json.dumps(rec,indent=2));print(json.dumps(rec))
