"""In an independent copied task directory, replay frozen47 inputs without refitting.
Usage: python code/reproduce_frozen_inference.py --parent /original/task/root
Requires the same validated official loader/weights, or matching private assets.
"""
from infer import *
import argparse
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--parent',type=Path,required=True);args=parser.parse_args();parent=args.parent.resolve();assert parent!=N.resolve(),'Refuse to overwrite frozen scientific outputs; copy code to a new experiments/task directory first';assert not(N/'hero_fit').exists()or not list((N/'hero_fit').glob('*/SOURCE.json')),'Output is not empty';(N/'hero_fit').mkdir(exist_ok=True);plans=[]
 for g in GROUPS:plans+=load(parent/'selection_verified'/(g+'_HERO_PLAN.json'))
 # Exact package includes all selected native RGB/Mask/K caches, not olddepth.
 idx={r['id']:r for r in load(parent/'assets_index/FROZEN_HERO_INPUT_CACHES.json')}
 for r in plans:
  for v in [r['target']]+r['support_views']:
   pp=parent/'local_results/selected_inputs'/(v['id']+'.npz');assert sha(pp)==idx[v['id']]['cache']['sha256'];v['cache']=str(pp)
 torch.manual_seed(20261115);torch.set_num_threads(4);model=loader();mf=meshfn();rr=[one(model,r,mf)for r in plans];save('metrics/HERO_INFERENCE_RESULTS.json',rr);print('INDEPENDENT_FROZEN_INPUT_REPLAY_COMPLETE',len(rr),sum(r['success']for r in rr),flush=True)
