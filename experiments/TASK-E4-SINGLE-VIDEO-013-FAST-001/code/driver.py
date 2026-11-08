"""Serial full013-budget same-video arms; no GT, no adaptive arm selection."""
from common import *
import subprocess
MASTER=R
PY='/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python'
def main():
 assert not(R/'provenance/ALL_PREDICTIONS_FROZEN_BEFORE_GT.json').exists(),'Do not update a frozen prediction set'
 cfg=load(R/'config/PROTOCOL.json');cases=load(R/'config/CASE_LOCK.json');started=time.time();completed=[]
 for tag in ['S8','S16','S32']:
  root=R/'arms'/tag
  for c in cases:
   n=c['name'];dest=root/'local_results'/n/'FINAL.npz'
   if dest.exists():completed.append(dict(arm=tag,case=n,reused_completed_current_run=True));continue
   log=R/'runtime'/(tag+'_'+n+'.log');argv=[PY,'-B',str(R/'code/train_normalized.py'),n]
   if list((root/'local_results'/n).glob('*.pt')):argv+=['--resume']
   save('runtime/STATUS.json',dict(state='TRAINING',arm=tag,case=n,completed_new_jobs=len(completed),total_new_jobs=33,epoch=time.time()))
   print('START',tag,n,flush=True)
   with log.open('a')as f:code=subprocess.call(argv,env=dict(os.environ,E4_RUN_DIR=str(root)),stdout=f,stderr=subprocess.STDOUT)
   if code:
    save('metrics/ENGINEERING_FAILURE.json',dict(arm=tag,case=n,returncode=code,log=str(log),predictions_not_replaced_with_S0=True));raise RuntimeError('Training interruption; preserve state and diagnose: '+tag+' '+n)
   rec=load(root/'metrics'/(n+'_RUN.json'));completed.append(dict(arm=tag,case=n,accepted=rec['accepted'],attempts=rec['attempts']));print('FINISH',tag,n,rec['accepted'],rec['attempts'],flush=True)
 allfiles=[];scales=[]
 for c in cases:
  n=c['name'];rg=np.load(R/'inputs'/n/'RING.npz');diam=2*np.linalg.norm(rg['V'][:,:2],axis=1).min();true=5. if c['ring']=='R5'else 10.;assert abs(true/diam-1)<1e-6
  scales.append(dict(case=n,known_Ring_inner_mm=true,CAD_inner_mm=float(diam),derived_factor=float(true/diam),applied_factor=1.,scale_locked=True))
  for tag in ['S0','S8','S16','S32']:
   p=R/'arms'/tag/'local_results'/n/'FINAL.npz';assert p.exists();allfiles.append(dict(asset(p),case=n,arm=tag,S0_exact_cache=tag=='S0'))
 save('metrics/RING_SCALE_VALIDATION.json',scales);table('metrics/RING_SCALE_VALIDATION.csv',scales)
 save('provenance/ALL_PREDICTIONS_FROZEN_BEFORE_GT.json',dict(epoch=time.time(),files=allfiles,code=[asset(p)for p in sorted((R/'code').glob('*.py'))],input_freeze=asset(R/'provenance/INPUTS_FROZEN.json'),optimization_freeze=asset(R/'provenance/TRAINING_PROTOCOL_FREEZE.json'),scale=asset(R/'metrics/RING_SCALE_VALIDATION.json'),independent_physical_groups=11,current_new_runs=33,explicit_S0_controls_reused=11,GT_used=False))
 save('runtime/STATUS.json',dict(state='ALL_PREDICTIONS_FROZEN',completed_new_jobs=33,total_models=44,epoch=time.time(),driver_seconds=time.time()-started));print('ALL_44_PREDICTIONS_FROZEN_NO_GT',flush=True)
if __name__=='__main__':main()
