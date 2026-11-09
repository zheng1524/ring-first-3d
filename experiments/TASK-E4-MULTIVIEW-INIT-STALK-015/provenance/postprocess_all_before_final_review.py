"""Independent CPU evaluation only after all real prediction routes are frozen."""
from common import *
from phase_a import command,PY
from concurrent.futures import ThreadPoolExecutor
import subprocess

def evaluate_one(n):
 p=R/'metrics/eval_case'/(n+'_BLENDER_GEOMETRIC_METRICS.json')
 if p.exists():return
 log=R/'runtime'/('best_rigid_'+n+'.log')
 with log.open('a')as f:
  rc=subprocess.call([PY,'-B',str(R/'code/best_rigid015.py'),'--case',n],stdout=f,stderr=subprocess.STDOUT)
 if rc:raise RuntimeError(str(log))

def main():
 if not(R/'provenance/FROZEN_FINAL_BODIES_FIT_ONLY.json').exists():command('select_stalk.py',[])
 for n in load(R/'config/PROTOCOL.json')['phase_B']['cases']:
  for tag in ['Stalk-A','Stalk-B','Stalk-C']:
   if(R/'arms'/tag/'local_results'/n/'FINAL.npz').exists()and not(R/'arms'/tag/'metrics'/(n+'_FINAL_COMPONENT_GRADIENTS.json')).exists():command('final_gradient_diagnostic.py',[n],tag)
 command('prepare_evaluation.py',[]);save('runtime/STATUS.json',dict(phase='FROZEN_PREDICTION_BEST_RIGID_EVALUATION',epoch=time.time(),training_complete=True))
 with ThreadPoolExecutor(max_workers=2)as pool:list(pool.map(evaluate_one,[c['name']for c in load(R/'config/CASE_LOCK.json')]))
 command('summarize_results.py',[]);command('b0_evidence.py',[]);command('final_figures.py',[]);command('six_view_details.py',[]);command('stalk_mechanism_tables.py',[]);command('publish_review_meshes.py',[]);save('runtime/STATUS.json',dict(phase='ALL_CORE_OUTPUTS_READY_FOR_REVIEW',epoch=time.time(),GT_used_for_optimization=False));print('ALL_CORE_OUTPUTS_READY',flush=True)
if __name__=='__main__':main()
