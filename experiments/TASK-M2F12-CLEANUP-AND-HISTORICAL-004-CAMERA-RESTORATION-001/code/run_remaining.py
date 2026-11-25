"""Sequential fixed-denominator runner. Failures retained; no fallback inputs."""
import json,os,subprocess,sys,time
from pathlib import Path
from historical_io import W,sha
from source_lock import verify
HERE=Path(__file__).resolve().parent
rows=json.loads((HERE.parent/'evidence/INPUT_REGISTRY.json').read_text())
BASE=W/'runs/m2f12_historical004/H004_RAW_BASELINE'
first=BASE/'GP_Ip_12.0mm_closed_R10_single_refY_004'
assert json.loads((first/'STAGE_recover.json').read_text())['status']=='COMPLETED'
commands=[]
for row in rows:
 case=row['case'];R=BASE/case
 if R==first:continue
 for stage,script in [('prepare','historical004.py'),('seed','historical004.py'),('recover','recover004.py')]:
  state=R/f'STAGE_{stage}.json'
  if state.exists() and json.loads(state.read_text())['status']=='COMPLETED':continue
  log=R/'logs'/f'{stage}.log';log.parent.mkdir(exist_ok=True)
  cmd=[sys.executable,str(HERE/script)]+([stage]if script=='historical004.py'else[])+[case]
  lock_receipt=verify();start=time.time();print('START',case,stage,flush=True)
  with log.open('w')as f:rc=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,env=os.environ.copy()).returncode
  commands.append(dict(case=case,stage=stage,argv=cmd,exit_code=rc,seconds=time.time()-start,log=str(log),script_sha256=sha(HERE/script),source_lock=lock_receipt))
  (BASE.parent/'BATCH_COMMANDS.json').write_text(json.dumps(commands,indent=2))
  print('END',case,stage,rc,round(time.time()-start,2),flush=True)
  if rc:
   (R/'PIPELINE_FAILURE.json').write_text(json.dumps(commands[-1],indent=2));break
print('FIXED_TEN_VIDEO_RUN_FINISHED',flush=True)
