"""Same frozen solver/config, three independent CPU jobs within each ordered group."""
from resection import *
from concurrent.futures import ProcessPoolExecutor
import multiprocessing

def worker(job):
 rec,b=job;guard_optimizer();g=rec['group'];folder=R/'local_results'/g/b/rec['id'];done=folder/'CANDIDATES_FROZEN.json'
 if not done.exists():
  try:
   a=np.load(R/'local_results'/g/(b+'.npz'));run_source(rec,b,a['V'],a['F'],folder=folder)
  except Exception as e:
   import traceback
   save(str(done.relative_to(R)),dict(source=rec['id'],group=g,Body=b,status='ENGINEERING_FAILURE',chosen=None,error=repr(e),traceback=traceback.format_exc()));print('FAILED',g,b,rec['id'],repr(e),flush=True)
 return dict(group=g,source=rec['id'],Body=b,result=asset(done))
def main():
 assert (R/'controls/EVALUATION_COMPLETED.json').exists();old=load(R/'provenance/REAL_SOLVER_CODE_FREEZE.json')
 for a in old['code']:assert sha(a['path'])==a['sha256']
 save('provenance/CPU_SCHEDULING.json',dict(epoch=time.time(),workers=3,group_order=['G03','G05','G01','G06'],algorithm_changes=False,interrupted_single_worker='only CPU scheduling; incomplete source replay same frozen seeds/budget',runner=asset(Path(__file__))))
 rows=[]
 for g in ['G03','G05','G01','G06']:
  jobs=[(s,b)for s in load(R/'config/REAL_SOURCES.json')if s['group']==g for b in ['Body-E','Body-U']]
  with ProcessPoolExecutor(max_workers=3,mp_context=multiprocessing.get_context('spawn'))as pool:rows.extend(pool.map(worker,jobs))
 save('provenance/ALL_REAL_PREDICTIONS_FROZEN.json',dict(epoch=time.time(),results=rows,selection='FIT only',real_GT_access=False,all_bodies_fixed=True));print('REAL_ALL_FROZEN',len(rows),flush=True)
if __name__=='__main__':main()
