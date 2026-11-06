from pathlib import Path
import json,subprocess,sys,time
r=Path(__file__).resolve().parents[1];rows=[]
for c in json.loads((r/'config/PROTOCOL.json').read_text())['cases']:
 t=time.time()
 with(r/'runtime'/(c+'_FIT.log')).open('w')as f:p=subprocess.run([sys.executable,'-B',str(r/'code/fit_body.py'),c],stdout=f,stderr=subprocess.STDOUT)
 rows.append(dict(case=c,returncode=p.returncode,seconds=time.time()-t));(r/'runtime/SERIAL_STATUS.json').write_text(json.dumps(rows,indent=2));print(rows[-1],flush=True)
 if p.returncode:print((r/'runtime'/(c+'_FIT.log')).read_text()[-5000:],flush=True);break
print('SERIAL_STOPPED_OR_DONE',flush=True)
