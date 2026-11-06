from pathlib import Path
import subprocess,sys,json,time
r=Path(__file__).resolve().parents[1];rows=[]
for c in json.loads((r/'config/PROTOCOL.json').read_text())['cases']:
 t=time.time()
 with(r/'runtime'/(c+'_TRAIN.log')).open('w')as f:p=subprocess.run([sys.executable,'-B',str(r/'code/train.py'),c],stdout=f,stderr=subprocess.STDOUT)
 result=r/'metrics'/(c+'_RUN.json');row=dict(case=c,returncode=p.returncode,seconds=time.time()-t,result=json.loads(result.read_text())if result.exists()else None);rows.append(row);(r/'runtime/SERIAL_STATUS.json').write_text(json.dumps(rows,indent=2));print(row,flush=True)
 if p.returncode:print((r/'runtime'/(c+'_TRAIN.log')).read_text()[-3000:],flush=True)
print('ALL_NINE_ATTEMPTED')
