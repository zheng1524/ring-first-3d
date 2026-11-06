from pathlib import Path
import subprocess,sys,json,time
r=Path(__file__).resolve().parents[1];rows=[]
for c in json.loads((r/'config/PROTOCOL.json').read_text())['cases']:
 for a in['P','S']:
  t=time.time()
  with(r/'runtime'/(c+'_'+a+'_FIT.log')).open('w')as f:p=subprocess.run([sys.executable,'-B',str(r/'code/train.py'),c,a],stdout=f,stderr=subprocess.STDOUT)
  run=r/'metrics'/(c+'_'+a+'_RUN.json');rec=dict(case=c,route=a,returncode=p.returncode,seconds=time.time()-t,run=json.loads(run.read_text())if run.exists()else None);rows.append(rec);(r/'runtime/SERIAL_STATUS.json').write_text(json.dumps(rows,indent=2));print(rec,flush=True)
  # A failed condition remains a failure; other locked conditions still execute.
print('ALL_LOCKED_CONDITIONS_ATTEMPTED',flush=True)
