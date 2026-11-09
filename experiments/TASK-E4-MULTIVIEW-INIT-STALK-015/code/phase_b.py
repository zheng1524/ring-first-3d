"""Serial Phase B only after complete FIT-only Phase A selection."""
from common import *
from publish import arm_case
from phase_a import command
from native_score import evaluate
import shutil

def main():
 assert(R/'provenance/PHASE_A_SELECTION_FREEZE.json').exists();choice=load(R/'config/PHASE_A_SELECTED.json')['selected'];cases=load(R/'config/PROTOCOL.json')['phase_B']['cases'];tags=['Stalk-A','Stalk-B','Stalk-C'];records=[]
 for n in cases:
  initial=R/'arms'/choice/'local_results'/n/'FINAL.npz'
  for tag in tags:arm_case(tag,n,initial,'B')
  probe=R/'arms/Stalk-A/metrics'/(n+'_STALK_PROBE.json')
  if not probe.exists():command('probe_stalk.py',[n],'Stalk-A')
  for tag in ['Stalk-B','Stalk-C']:
   src=R/'arms/Stalk-A/inputs'/n/'STALK_SEED.json';dst=R/'arms'/tag/'inputs'/n/'STALK_SEED.json'
   if not dst.exists():shutil.copyfile(src,dst)
 if not(R/'provenance/PHASE_B_CODE_SEEDS_AND_PROTOCOL_FROZEN.json').exists():save('provenance/PHASE_B_CODE_SEEDS_AND_PROTOCOL_FROZEN.json',dict(epoch=time.time(),chosen_initializer=choice,files=[asset(p)for p in(R/'code').glob('*.py')],seeds=[asset(R/'arms/Stalk-A/inputs'/n/'STALK_SEED.json')for n in cases],inputs=[asset(R/'arms/Stalk-A/inputs'/n/'INITIAL.npz')for n in cases],contract=asset(R/'PHASE_B_ALGORITHM_CONTRACT.md'),recommendation_contract=asset(R/'PHASE_B_FIT_ONLY_RECOMMENDATION.md'),GT_read=False))
 for n in cases:
  for tag in tags:
   root=R/'arms'/tag;folder=root/'local_results'/n;final=folder/'FINAL.npz';seed=load(root/'inputs'/n/'STALK_SEED.json')
   save('runtime/STATUS.json',dict(phase='B_DOWNSTREAM',case=n,arm=tag,completed_stalk=len(records),epoch=time.time()))
   if tag=='Stalk-C'and seed['status']!='RESIDUAL_ASSOCIATION_PROXY':
    records.append(dict(case=n,arm=tag,status='NO_KNOWN_VISIBLE_RESIDUAL_SIGNAL',optimized_result=None,reason=seed.get('reason'),GT_read=False));continue
   if not final.exists():command('train_stalk.py',[n]+(['--resume']if list(folder.glob('*.pt'))else[]),tag)
   run=load(root/'metrics'/(n+'_RUN.json'));records.append(dict(case=n,arm=tag,**run));dest=R/'metrics/scores'/(n+'_'+tag+'_FINAL.json')
   if not dest.exists():save(dest.relative_to(R),evaluate(n,final,True,tag+'_FINAL'))
  save('metrics/PHASE_B_RUNS.json',records);command('preview_stalk.py',[n]);print('PHASE_B_CASE_COMPLETE',n,len(records),flush=True)
 files=[dict(asset(R/'arms'/q['arm']/'local_results'/q['case']/'FINAL.npz'),case=q['case'],arm=q['arm'])for q in records if q.get('optimized_result','OK')is not None];save('provenance/PHASE_B_PREDICTIONS_FROZEN.json',dict(epoch=time.time(),files=files,GT_read=False,missing=[q for q in records if q.get('optimized_result','OK')is None]));save('runtime/STATUS.json',dict(phase='PHASE_B_COMPLETE',completed_stalk=len(records),epoch=time.time()));print('PHASE_B_COMPLETE',len(records),flush=True)
if __name__=='__main__':main()
