from pathlib import Path
import subprocess,sys,json,time
r=Path(__file__).resolve().parents[1];cfg=json.loads((r/'config/PROTOCOL.json').read_text());rows=[]
for c in cfg['cases']:
 for a in cfg['arms']:
  if a=='B'and c in cfg['reuse_B']:continue
  log=r/'runtime'/(c+'_'+a+'.log');start=time.time()
  with log.open('w')as f:p=subprocess.run([sys.executable,'-B',str(r/'code/train.py'),c,a],stdout=f,stderr=subprocess.STDOUT)
  row=dict(case=c,arm=a,returncode=p.returncode,elapsed=time.time()-start);rows.append(row);(r/'runtime/SERIAL_STATUS.json').write_text(json.dumps(rows,indent=2));print(row,flush=True)
  if p.returncode:print(log.read_text()[-3000:],flush=True);break
print('SERIAL_DONE',flush=True)
