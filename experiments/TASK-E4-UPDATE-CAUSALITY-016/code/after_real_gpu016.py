"""Serial continuation after real training, no simultaneous GPU subprocesses."""
from common import *
import subprocess
PY='/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python'
def command(script,tag=None,args=None):
 env=dict(os.environ)
 if tag:env['E4_RUN_DIR']=str(R/'arms'/tag)
 else:env.pop('E4_RUN_DIR',None)
 with(R/'runtime'/(script+'_'+str(tag)+'.log')).open('a')as f:rc=subprocess.call([PY,'-B',str(R/'code'/script)]+(args or[]),env=env,stdout=f,stderr=subprocess.STDOUT)
 if rc:raise RuntimeError('Preserve failed-stage evidence: '+script+' '+str(tag))
def main():
 start=time.time();pid=load(R/'runtime/PID.json')['pid']
 while not(R/'provenance/REAL_PREDICTIONS_FROZEN.json').exists():
  state=Path('/proc')/str(pid)/'stat'
  if not state.exists()or state.read_text().split()[2]=='Z':raise RuntimeError('Real GPU queue failed; do not bypass prerequisite')
  if time.time()-start>2400:raise RuntimeError('Bounded prerequisite wait expired')
  time.sleep(5)
 save('runtime/STATUS.json',dict(phase='NUMERIC_VISIBILITY_BRANCH_ISOLATION',epoch=time.time()));command('raster_branch016.py','DIAGNOSTIC');command('virtual_gate016.py')
 registry=load(R/'config/VIRTUAL_RUN_REGISTRY.json')
 for x in registry:
  tag=x['tag'];save('runtime/STATUS.json',dict(phase='VIRTUAL_CONTROL',tag=tag,epoch=time.time()))
  if not(R/'arms'/tag/'metrics/VIRTUAL_INITIAL_PROBE.json').exists():command('virtual_probe016.py',tag)
  if not Path(x['final']).exists():command(x['script'],tag,[x['case']])
  print('VIRTUAL_COMPLETE',tag,flush=True)
 save('provenance/VIRTUAL_PREDICTIONS_FROZEN.json',dict(epoch=time.time(),files=[asset(Path(x['final']))for x in registry],GT_used_for_fitting=False));save('runtime/STATUS.json',dict(phase='ALL_OPTIMIZATION_COMPLETE',epoch=time.time()));print('ALL_GPU_WORK_COMPLETE',flush=True)
if __name__=='__main__':main()
