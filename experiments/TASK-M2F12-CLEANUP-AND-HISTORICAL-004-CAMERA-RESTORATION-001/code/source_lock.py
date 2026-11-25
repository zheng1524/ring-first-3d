"""Freeze actual stage sources, verify before execution; no solved asset access."""
import json,sys
from pathlib import Path
from historical_io import E,H,SOURCES,sha
HERE=Path(__file__).resolve().parent
LOCK=HERE.parent/'evidence/RESTORATION_SOURCE_LOCK.json'
def dependencies():
 paths=set(SOURCES.values())|set(HERE.glob('*.py'))
 paths.update((E/'ring_first_v5_real_validation/scripts').glob('*.py'))
 paths.update((E/'ring_first_v3_static_ba/scripts').glob('*.py'))
 paths.update((E/'ring_first_v4_synthetic_audit/scripts').glob('*.py'))
 paths.update((H/'TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001/code').glob('*.py'))
 paths.update(Path('/home/liu/ring-first-hero-core/src/ring_first_hero').glob('*.py'))
 paths.add(E/'ring_first_v2_real_ba/runs/continuous16/scripts/decode_segment.py')
 return sorted(paths)
def verify():
 lock=json.loads(LOCK.read_text());bad=[p for p,h in lock['files'].items()if sha(p)!=h]
 if bad:raise RuntimeError('FROZEN_SOURCE_CHANGED:'+str(bad))
 return dict(lock_path=str(LOCK),lock_sha256=sha(LOCK),files=len(lock['files']))
if __name__=='__main__':
 if sys.argv[1]=='freeze':
  assert not LOCK.exists(),'Never overwrite an existing source lock'
  LOCK.write_text(json.dumps(dict(files={str(p):sha(p)for p in dependencies()},scope='restoration source closure before batch; Ip12 pilot earlier per-stage snapshots preserved'),indent=2))
 print(verify())
