"""Resume after declared virtual pixel-grid engineering repair; no repeated real runs."""
from after_real_gpu016 import *
def main():
 assert load(R/'metrics/VIRTUAL_P3D_PROJECTION_GATE.json')['all_pass']
 reg=load(R/'config/VIRTUAL_RUN_REGISTRY.json')
 for x in reg:
  tag=x['tag'];save('runtime/STATUS.json',dict(phase='VIRTUAL_GRID_REPAIRED_CONTROL',tag=tag,epoch=time.time()))
  if not(R/'arms'/tag/'metrics/VIRTUAL_INITIAL_PROBE.json').exists():command('virtual_probe_grid016.py',tag)
  if not Path(x['final']).exists():command(x['script'],tag,[x['case']])
  print('VIRTUAL_COMPLETE',tag,flush=True)
 save('provenance/VIRTUAL_PREDICTIONS_FROZEN.json',dict(epoch=time.time(),files=[asset(Path(x['final']))for x in reg],GT_used_for_fitting=False,grid_repair_provenance='VIRTUAL_GRID_REPAIR_AMENDMENT.json'))
 old=REPO/'experiments/TASK-E4-MULTIVIEW-INIT-STALK-015'
 for n in ['G03','G01']:
  jobs=[(old/'arms/Stalk-B/local_results'/n/'MECHANISM_0001.npz','OLD_B_FIRST'),(R/'arms/MECH_COHERENT/local_results'/n/'MECHANISM_0001.npz','NEW_FIRST')]
  if n=='G03':jobs.extend([(old/'arms/Stalk-B/local_results'/n/'MECHANISM_0040.npz','OLD_B_LAST'),(R/'arms/MECH_COHERENT/local_results'/n/'MECHANISM_0040.npz','NEW_LAST'),(old/'arms/Stalk-A/local_results'/n/'REJECTED_RING_WORSENING.npz','OLD_A_REJECTED')])
  for p,label in jobs:command('actual_trace016.py','DIAGNOSTIC',[n,str(p),label])
 save('runtime/STATUS.json',dict(phase='ALL_UPDATES_AND_CAUSAL_TAPES_COMPLETE',epoch=time.time()));print('GPU_WORK_AND_TAPES_COMPLETE',flush=True)
if __name__=='__main__':main()
