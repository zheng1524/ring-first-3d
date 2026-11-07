from common import *
from fit_score import score
from collections import Counter

def main():
 results=[];traces=[]
 for tag in ['PILOT_A0','PILOT_A1','PILOT_A2','PILOT_A3','PILOT_O1','PILOT_O2','PILOT_O3','PILOT_O4','PILOT_O3N','AMENDED_A3_O3N_1D','COMBINED_VERIFY','REPLAY_012_FULL','FINAL_UNIFORM']:
  arm=R/'arms'/tag
  for p in sorted((arm/'metrics').glob('*_RUN.json')):
   n=p.stem[:-4];run=load(p);h=load(arm/'metrics'/(n+'_TRAINING.json'));cand=load(arm/'metrics'/(n+'_CANDIDATES.json'));counts=Counter(x for t in cand for x in t['reasons']);fs=score(n,arm/'local_results'/n/'FINAL.npz');row=dict(arm=tag,case=n,accepted=run['accepted'],attempts=run['attempts'],max_displacement_mm=run['maximum_displacement_mm'],minimum_lr=min(x['lr']for x in h),max_gradient_norm=max(x['gradient_norm']for x in h),rejected_total_trust=counts['TOTAL_TRUST'],rejected_full_fit=counts['FULL_FIT_OBJECTIVE'],rejected_Ring=counts['RING_WORSENING'],all_rejections=counts,**fs['mean']);results.append(row)
   # Same fixed original missing region for all saved steps, no head/stalk segmentation.
   if n=='G03' or (tag in ['FINAL_UNIFORM','REPLAY_012_FULL'] and n in ['G01','G02','G10','G11']):
    first=None
    for snap in sorted((arm/'local_results'/n).glob('ACCEPTED_*.npz')):
     z=np.load(snap);s=score(n,snap);step=int(z['accepted']);trace=dict(case=n,arm=tag,accepted=step,attempt=int(z['attempt']),**s['mean']);traces.append(trace)
     if first is None and s['mean']['far_recall']>.01:first=step
    row['first_saved_accepted_with_far_recall_over1pct']=first;row['trace_caveat']='First saved checkpoint, not exact first biological-stalk formation; absent far region falls back to total recall per prereg score'
 table('metrics/ALL_ARM_FIT_COMPARISON.csv',results);save('metrics/ALL_ARM_FIT_COMPARISON.json',results);table('metrics/SAVED_STAGE_FAR_COVERAGE.csv',traces);save('metrics/SAVED_STAGE_FAR_COVERAGE.json',traces)
if __name__=='__main__':main()
