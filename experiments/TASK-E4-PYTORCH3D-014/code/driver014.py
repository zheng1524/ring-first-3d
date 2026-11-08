"""Resumable serial GPU stages. Only FIT ranks predeclared methods; no GT imports."""
from setup_arm import *
import subprocess,traceback
from score014 import evaluate
PY='/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python'
CASES=[c['name']for c in load(MASTER/'config/CASE_LOCK.json')]
def run(tag,view,loss,formal=False,start=None,cases=None,budget=None):
 root=setup(tag,view,loss,formal,start,budget);cfg=load(root/'config/ARM.json');used=['common.py','p3d.py','free_model.py','components.py','depth_terms.py','contour_objective.py','strategy.py','normalized_local.py','safe_geometry.py','pmgr_self.py','multiview.py','train014.py'];files=[asset(MASTER/'code'/p)for p in used]+[asset(root/'config/ARM.json')]
 if not(MASTER/'provenance'/(tag+'_PREOPT.json')).exists():save('provenance/'+tag+'_PREOPT.json',dict(epoch=time.time(),files=files,selection_GT=False))
 for n in cases or CASES:
  out=root/'local_results'/n/'FINAL.npz';log=MASTER/'runtime'/(tag+'_'+n+'.log')
  if not out.exists():
   env=dict(os.environ,E4_RUN_DIR=str(root));print('START',tag,n,flush=True)
   save('provenance/'+tag+'_'+n+'_START.json',dict(epoch=time.time(),files=[asset(MASTER/'code'/p)for p in used],input=asset(root/'inputs'/n/'INITIAL.npz'),config=asset(root/'config/ARM.json'),GT_used=False))
   argv=[PY,'-B',str(MASTER/'code/train014.py'),n]
   if list((root/'local_results'/n).glob('ACCEPTED_*.pt')):argv.append('--resume')
   with log.open('a')as f:code=subprocess.call(argv,env=env,stdout=f,stderr=subprocess.STDOUT)
   if code:save('metrics/engineering_failures/'+tag+'_'+n+'.json',dict(tag=tag,case=n,returncode=code,log=str(log)));print('ENGINEERING_FAILURE',tag,n,code,flush=True);continue
  scorep=MASTER/'metrics/scores'/ (tag+'_'+n+'.json')
  if not scorep.exists():d=evaluate(n,out,False,tag);save(scorep.relative_to(MASTER),d)
  print('FINISH',tag,n,load(root/'metrics'/(n+'_RUN.json'))['accepted'],flush=True)
 return root

def select(tags,label):
 values=[];groups=load(MASTER/'config/PROTOCOL.json')['seed_groups_for_method_selection']
 for tag in tags:
  pp=[MASTER/'metrics/scores'/(tag+'_'+n+'.json')for n in groups];vals=[load(p)['mean']['FIT']['selection_score']for p in pp if p.exists()];values.append(dict(tag=tag,group_N=len(vals),mean_FIT_selection_score=float(np.mean(vals))if len(vals)==len(groups)else None))
 good=[v for v in values if v['mean_FIT_selection_score']is not None]
 if not good:raise RuntimeError('No complete FIT-only method candidate: '+label)
 chosen=max(good,key=lambda v:v['mean_FIT_selection_score'])['tag'];target=MASTER/'config'/(label+'_SELECTION.json')
 if target.exists():save('provenance/selection_history/'+label+'_'+sha(target)+'.json',load(target))
 save('config/'+label+'_SELECTION.json',dict(epoch=time.time(),method=chosen,all=values,GT_read=False,HOLDOUT_used_for_selection=False,HOLDOUT_preloaded_by_renderer_but_not_in_loss=True,rule=load(MASTER/'config/PROTOCOL.json')['selection']));return chosen

def main():
 assert not(MASTER/'provenance/ALL_014_PREDICTIONS_AND_SCALE_FROZEN_BEFORE_GT.json').exists(),'Frozen run: no method reselection or training after GT gate'
 ap=argparse.ArgumentParser();ap.add_argument('phase',choices=['C','D']);a=ap.parse_args()
 if a.phase=='C':
  tags=['C0','C1_8','C2_16','C3_32','C4_ALL']
  for tag in tags:run(tag,tag,'D0_013')
  print('C_SELECTED',select(tags,'C'),flush=True)
 else:
  view=load(MASTER/'config/C_SELECTION.json')['method'];tags=[view]
  for loss in ['D1_split','D2_bidir','D3_combo']:
   tag='D_'+loss;run(tag,view,loss);tags.append(tag)
  print('D_SELECTED',select(tags,'D'),flush=True)
if __name__=='__main__':main()
