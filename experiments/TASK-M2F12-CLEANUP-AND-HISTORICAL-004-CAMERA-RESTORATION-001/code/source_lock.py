"""Freeze actual stage sources, verify before execution; no solved asset access."""
import json,sys
from pathlib import Path
from historical_io import E,H,SOURCES,sha
HERE=Path(__file__).resolve().parent
LOCK=HERE.parent/'evidence/RESTORATION_SOURCE_LOCK.json'
LOCK2=HERE.parent/'evidence/RESTORATION_SOURCE_LOCK_R2.json'
LOCK3=HERE.parent/'evidence/RESTORATION_SOURCE_LOCK_R3.json'
def dependencies():
 paths=set(SOURCES.values())|{HERE/name for name in ['historical004.py','historical_io.py','recover004.py','frame_identity.py','run_remaining.py','source_lock.py','freeze_inputs.py']}
 paths.update((E/'ring_first_v5_real_validation/scripts').glob('*.py'))
 paths.update((E/'ring_first_v3_static_ba/scripts').glob('*.py'))
 paths.update((E/'ring_first_v4_synthetic_audit/scripts').glob('*.py'))
 paths.update((H/'TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001/code').glob('*.py'))
 paths.update(Path('/home/liu/ring-first-hero-core/src/ring_first_hero').glob('*.py'))
 paths.add(E/'ring_first_v2_real_ba/runs/continuous16/scripts/decode_segment.py')
 paths.add(E.parent/'scripts/geometry.py')
 paths.add(E/'ring_pose_contact_v1/scripts/recover.py')
 paths.update(Path('/home/liu/new-polyp-dxy/src/dxy_mid').rglob('*.py'))
 paths.update(Path('/home/liu/polyp_research/experiments/v8_5_cross_ring_pipeline_audit_20261014/freeze/model').glob('*.py'))
 return sorted(paths)
def verify():
 chosen=LOCK3 if LOCK3.exists()else LOCK2 if LOCK2.exists()else LOCK;lock=json.loads(chosen.read_text());bad=[p for p,h in lock['files'].items()if sha(p)!=h]
 if bad:raise RuntimeError('FROZEN_SOURCE_CHANGED:'+str(bad))
 return dict(lock_path=str(chosen),lock_sha256=sha(chosen),files=len(lock['files']))
if __name__=='__main__':
 if sys.argv[1]in ['freeze','freeze-r2','freeze-r3']:
  chosen=LOCK3 if sys.argv[1]=='freeze-r3'else LOCK2 if sys.argv[1]=='freeze-r2'else LOCK
  assert not chosen.exists(),'Never overwrite an existing source lock'
  chosen.write_text(json.dumps(dict(files={str(p):sha(p)for p in dependencies()},scope='Lossless image hash + decoder PTS identity IO repair, complete source closure; prior locks preserved; no solver change'),indent=2))
 print(verify())
