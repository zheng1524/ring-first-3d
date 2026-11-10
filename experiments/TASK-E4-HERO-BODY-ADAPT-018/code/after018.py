"""Wait for this task's serial training only, then freeze and run independent evaluation."""
from common import *
import subprocess

def main():
 log=R/'runtime/SERIAL_R2.log'
 while not log.exists()or'ALL_FORMAL_ARMS_ATTEMPTED'not in log.read_text():time.sleep(5)
 jobs=[('freeze018.py',R),('evaluate018.py',R/'evaluation'),('conflicts018.py',R),('figures018.py',R),('summarize018.py',R)]
 for script,root in jobs:
  print('POSTPROCESS_START',script,flush=True);env=dict(os.environ,E4_RUN_DIR=str(root));p=R/'runtime'/(script.removesuffix('.py')+'.log')
  with p.open('w')as f:a=subprocess.run([sys.executable,'-B',str(R/'code'/script)],env=env,stdout=f,stderr=subprocess.STDOUT)
  if a.returncode:print('POSTPROCESS_ENGINEERING_FAILURE',script,a.returncode,str(p),flush=True);return
  print('POSTPROCESS_DONE',script,flush=True)
 save('runtime/ALL_COMPUTATION_AND_FIGURES_DONE.json',dict(epoch=time.time(),optimization=True,evaluation=True,actual_mesh_figures=True,stopped_after_task=True));print('ALL_COMPUTATION_AND_FIGURES_DONE',flush=True)
if __name__=='__main__':main()
