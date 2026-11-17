from common import *
import subprocess,ast
def main():
 gate=load(R/'metrics/P3D_HERO_PROJECTION_GRADIENT_GATE.json');assert gate['all29_passed'];assert all(x['ready']for x in load(R/'config/GROUP_READY.json').values());plan=load(R/'config/ARM_PLAN.json')
 # Freeze final algorithms/configurations before a single formal update.
 if not(R/'provenance/FORMAL_OPTIMIZATION_R2_FREEZE.json').exists():save('provenance/FORMAL_OPTIMIZATION_R2_FREEZE.json',dict(epoch=time.time(),code=[asset(p)for p in sorted((R/'code').glob('*.py'))],config=[asset(p)for p in sorted((R/'config').glob('*.json'))],gate=asset(R/'metrics/P3D_HERO_PROJECTION_GRADIENT_GATE.json'),data=asset(R/'provenance/PRE_OPTIMIZATION_ASSETS_R2.json'),HOLDOUT='no optimizer image/mask/depth access',GT=False))
 for a in plan:
  folder=Path(a['path']);case=a['group'];out=folder/'local_results'/case/'FINAL.npz'
  if out.exists():continue
  save('arms/'+a['arm']+'/config/ARM.json',dict(tag=a['arm'],kind=a['kind'],HERO_views=a['HERO_views'],loss='NEW_HERO_REPLACES_OLD_D2'if a['kind']!='OLD'else'OLD_D2_ON_NEW_HOLDOUT_FREE_HERO',mode=a.get('proposal_mode','STANDARD_016'),budget=a['budget']))
  env=dict(os.environ,E4_RUN_DIR=str(folder));log=R/'runtime'/(case+'_'+a['arm']+'.log');print('START_FORMAL',case,a['arm'],flush=True)
  resume=any(out.parent.glob('*.pt'));cmd=[sys.executable,'-B',str(R/'code/train018.py'),case]+(['--resume']if resume else[])
  with log.open('a'if resume else'w')as f:ret=subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT)
  save('runtime/PIPELINE_STATE.json',dict(last_group=case,last_arm=a['arm'],returncode=ret.returncode,epoch=time.time(),log=str(log)))
  if ret.returncode:print('ARM_ENGINEERING_FAILURE',case,a['arm'],log,flush=True)
  else:print('DONE_FORMAL',case,a['arm'],load(folder/'metrics'/(case+'_RUN.json')),flush=True)
 print('ALL_FORMAL_ARMS_ATTEMPTED',flush=True)
if __name__=='__main__':main()
