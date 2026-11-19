"""Fixed finite serial GPU queue. Baselines reused explicitly, never fallback."""
from common import *
import subprocess
PY='/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python'

def main():
 assert(R/'provenance/FORMAL_FREEZE.json').exists()
 registry=load(R/'config/RUN_REGISTRY.json');done=[]
 for x in registry:
  if x['kind']=='READ_ONLY_015_BASELINE':continue
  if x.get('scene')=='virtual':continue
  name,tag=x['case'],x['tag'];root=R/'arms'/tag;final=root/'local_results'/name/'FINAL.npz'
  if not final.exists():
   save('runtime/STATUS.json',dict(phase='FORMAL_REAL_RUNS',case=name,tag=tag,completed=done,epoch=time.time()));env=dict(os.environ,E4_RUN_DIR=str(root));log=R/'runtime'/(tag+'_'+name+'.log')
   with log.open('a')as f:rc=subprocess.call([PY,'-B',str(R/'code'/x['script']),name],env=env,stdout=f,stderr=subprocess.STDOUT)
   if rc:raise RuntimeError('Engineering stop; preserve existing outputs: '+str(log))
  done.append(dict(case=name,tag=tag));print('REAL_COMPLETE',name,tag,flush=True)
 files=[asset(Path(x['final']))for x in registry if x['kind']!='READ_ONLY_015_BASELINE'and x.get('scene')!='virtual'];save('provenance/REAL_PREDICTIONS_FROZEN.json',dict(epoch=time.time(),files=files,GT_used_for_selection=False));save('runtime/STATUS.json',dict(phase='REAL_RUNS_COMPLETE',new_real_runs=len(files),epoch=time.time()));print('ALL_REAL_COMPLETE',len(files),flush=True)
if __name__=='__main__':main()
