from common import *
import subprocess

def main():
 while not(R/'provenance/POSE_PREDICTIONS_FROZEN_BEFORE_HOLDOUT.json').exists():time.sleep(5)
 for script in ['evaluate019.py','feature_evaluate019.py','ring_depth019.py','hero_diagnosis019.py','stability019.py']:
  p=R/(script.removesuffix('.py')+'.log');print('START',script,flush=True)
  with p.open('w')as f:a=subprocess.run([sys.executable,'-B',str(R/'code'/script)],stdout=f,stderr=subprocess.STDOUT)
  if a.returncode:print('FAIL',script,a.returncode,flush=True);return
  print('DONE',script,flush=True)
 save('runtime/P0_P1_DIAGNOSTICS_DONE.json',dict(epoch=time.time(),GT=False));print('P0_P1_DIAGNOSTICS_DONE',flush=True)
if __name__=='__main__':main()
