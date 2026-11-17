"""Freeze every actual prediction before any independent HOLDOUT performance reading."""
from common import *
def main():
 plan=load(R/'config/ARM_PLAN.json');records=[]
 for a in plan:
  p=Path(a['path']);run=p/'metrics'/(a['group']+'_RUN.json');f=p/'local_results'/a['group']/'FINAL.npz'
  assert f.exists()and run.exists(),(a['group'],a['arm'],'not yet complete')
  rec=load(run);assert rec['GT_read']is False;records.append(dict(group=a['group'],arm=a['arm'],result=asset(f),mesh=asset(f.with_name('FINAL_mm.ply')),status=asset(run),scale=asset(R/'inputs'/a['group']/'NORMALIZATION.json'),Ring=asset(R/'inputs'/a['group']/'RING.npz'),optimizer_reads=asset(p/'provenance'/(a['group']+'_OPTIMIZER_READS.json'))))
 dest=R/'provenance/ALL_OPTIMIZED_PREDICTIONS_FROZEN.json'
 if dest.exists():
  for x in load(dest)['records']:assert sha(x['result']['path'])==x['result']['sha256']
 else:save('provenance/ALL_OPTIMIZED_PREDICTIONS_FROZEN.json',dict(epoch=time.time(),records=records,all_formal_arms_attempted=True,formal_routes=14,groups=4,GT_used=False,holdout_performance_used_for_training=False,initialization_ancestry_caveat='historical016 initialized before this protected-update experiment; no whole-pipeline independence claimed'))
 print('ALL14_PREDICTIONS_AND_SCALES_FROZEN_BEFORE_INDEPENDENT_HOLDOUT_EVALUATION',flush=True)
if __name__=='__main__':main()
