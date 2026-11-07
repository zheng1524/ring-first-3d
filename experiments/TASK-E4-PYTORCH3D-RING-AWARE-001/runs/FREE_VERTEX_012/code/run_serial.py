from common import *
import subprocess

def main():
 rows=[]
 for name in load(R/'config/PROTOCOL.json')['cases']:
  start=time.time()
  with (R/'runtime'/(name+'_TRAIN.log')).open('w')as f:result=subprocess.run([sys.executable,'-B',str(R/'code/train.py'),name],stdout=f,stderr=subprocess.STDOUT)
  rec=dict(case=name,returncode=result.returncode,seconds=time.time()-start,result=load(R/'metrics'/(name+'_RUN.json'))if(R/'metrics'/(name+'_RUN.json')).exists()else None);rows.append(rec);save('runtime/SERIAL_STATUS.json',rows);print(rec,flush=True)
  if result.returncode!=0:print('ENGINEERING_ERROR_PRESERVED; next case still independently attempted',flush=True)
 print('NINE_ROUTES_ATTEMPTED',flush=True)

if __name__=='__main__':main()
