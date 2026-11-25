"""Validate retained bytes, evidence claims, source locks and Git publication scope."""
import argparse,json,subprocess,re
from pathlib import Path
import numpy as np
from pilot import TASK,REPO,sha
from snapshot import load_snapshot
p=argparse.ArgumentParser();p.add_argument('--staged',action='store_true');args=p.parse_args()
retained=json.loads((TASK/'evidence/RETAIN_DEPENDENCIES.json').read_text())['files']
for r in retained:assert sha(r['retained'])==r['sha256'],r['retained']
row=json.loads((TASK/'fixtures/SOURCE_G01.json').read_text());fit={r['meta']['id']for r in row['FIT']};held={r['meta']['id']for r in row['HOLDOUT']};assert not fit&held
s=load_snapshot();a=np.load(TASK/'fixtures/G01/INITIAL.npz');assert int(a['step'])==300 and int(a['accepted'])==18
run=TASK/'runs/PILOT_002';receipt=json.loads((run/'RUN_RECEIPT.json').read_text());u=json.loads((run/'UPDATES.json').read_text())
assert len(u['iterations'])==3 and sum(len(x['gradient_norms']) for x in u['iterations'])==9
assert receipt['initialization_status']=='HISTORICAL_011_FINAL_AS_013_INITIAL_NOT_PRISTINE_INITIAL'
assert sha(run/'FINAL.npz')==receipt['final_sha256'];assert sum(x['accepted']for x in u['iterations'])==3
for name,n in [('final_historical_tests.log',26),('final_boundary_tests.log',4)]:
 log=(TASK/'logs'/name).read_text();assert f'Ran {n} tests' in log and log.rstrip().endswith('OK')
for name in ['HISTORICAL_REPLAY.json','DEPTH_REPLAY.json','RIGID_CONTROL.json']:
 d=json.loads((TASK/'evidence'/name).read_text());assert d
# Preserve full source file hashes; no claim that reports alone lock source behavior.
sources=set(TASK.glob('code/*.py'))|set((REPO/'src/ring_first_3d/mainline/lineage/experiments/TASK-E4-STRUCTURED-BODY-UPDATE-002/code').glob('*.py'))
for rel in ['src/ring_first_3d/mainline/lineage/experiments/TASK-E4-MULTIVIEW-STRUCTURAL-UPDATE-001/code/body_update.py','src/ring_first_3d/contour_guided/correspondence.py','src/ring_first_3d/synthetic/raster.py','src/ring_first_3d/sim/geometry.py','src/ring_first_3d/contracts/coordinates.py','src/ring_first_3d/_legacy.py','src/ring_first_3d/source_lock.json']:
 sources.add(REPO/rel)
freeze=[dict(path=str(q.relative_to(REPO)),sha256=sha(q)) for q in sorted(sources)]
(TASK/'evidence/SOURCE_FREEZE.json').write_text(json.dumps(freeze,indent=2)+'\n')
links=re.findall(r'\]\(([^)]+)\)',(TASK/'TECHNICAL_REPORT.md').read_text());missing=[x for x in links if not (TASK/x).exists() and x!='evidence/VALIDATION.json'];assert not missing,missing
staged=[]
if args.staged:
 staged=subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=REPO).decode().split('\0');staged=[x for x in staged if x]
 tracked=set(subprocess.check_output(['git','ls-files','-z'],cwd=REPO).decode().split('\0'))
 for r in retained:assert str(Path(r['retained']).relative_to(REPO)) in tracked,r
 assert all(not any(k in x for k in ['/.runtime/','/runtime/','_PAIRS/','/PAIRS/']) for x in staged)
 assert all((REPO/x).stat().st_size<5_000_000 for x in staged)
result=dict(status='PASS',task='TASK-DOWNSTREAM-CORE-ASSET-RECOVERY-AND-PILOT-001',base_commit='000f5f2998ad2a29ca454e8380b587b26ba9f21c',retained_file_records=len(retained),source_freeze_records=len(freeze),historical_tests=26,boundary_tests=4,physical_groups=1,FIT=len(fit),HOLDOUT=len(held),new_pilot=dict(outer_iterations=3,adam_steps=9,accepted=3),total_adam_including_failed_attempt=18,original_initializer='NOT_RECOVERED',real_crossvideo_registration='NOT_EVALUABLE',GT_current='NOT_EVALUATED',staged_checked=args.staged,staged_files=len(staged),staged_bytes=sum((REPO/x).stat().st_size for x in staged),report_links_checked=len(links),remote_upload='VERIFY_SEPARATELY_AFTER_COMMIT')
(TASK/'evidence/VALIDATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
