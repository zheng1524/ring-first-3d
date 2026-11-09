"""One common FIT-only stalk method recommendation, before GT is opened."""
from audit_models import *
from publish import link

def main():
 assert(R/'provenance/PHASE_B_PREDICTIONS_FROZEN.json').exists();assert not(R/'provenance/GT_FIRST_ACCESS.json').exists();ips=load(R/'config/PROTOCOL.json')['phase_B']['cases'];rows=[];records=[]
 for n in ips:
  baseline=audit(n,R/'arms/Stalk-A/inputs'/n/'INITIAL.npz')
  for tag in ['Stalk-A','Stalk-B','Stalk-C']:
   p=R/'arms'/tag/'local_results'/n/'FINAL.npz'
   if not p.exists():continue
   sc=load(R/'metrics/scores'/(n+'_'+tag+'_FINAL.json'));g=audit(n,p,baseline);d=fixed_depth(sc);rows.append(dict(case=n,arm=tag,cost=1-sc['mean']['FIT']['IoU']+.02*(d['fixed_cost']if d['fixed_cost']is not None else 9.5),geometry=g,FIT=sc['mean']['FIT'],HERO_FIT=d))
 bad=lambda q:bool(not q['geometry']['dense_nonworsening_vs_common013'])or bool(q['geometry']['self_intersections_N']);basebad=sum(bad(q)for q in rows if q['arm']=='Stalk-A')
 for tag in ['Stalk-A','Stalk-B','Stalk-C']:
  rr=[q for q in rows if q['arm']==tag];badN=sum(bad(q)for q in rr);records.append(dict(arm=tag,N=len(rr),target_N=5,FIT_median_cost=float(np.median([q['cost']for q in rr]))if rr else None,geometry_bad_N=badN,eligible=len(rr)==5 and badN<=basebad))
 chosen=min([q for q in records if q['eligible']],key=lambda q:q['FIT_median_cost'])['arm'];save('config/PHASE_B_SELECTED.json',dict(epoch=time.time(),selected=chosen,rule='same global FIT-only score and relative geometry eligibility as Phase A; common method all5, no percase best',summary=records,GT_used=False,HOLDOUT_used=False));save('metrics/PHASE_B_FIT_ONLY_SELECTION_EVIDENCE.json',rows);choiceA=load(R/'config/PHASE_A_SELECTED.json')['selected'];bodies=[]
 for c in load(R/'config/CASE_LOCK.json'):
  n=c['name'];tag=chosen if n in ips else choiceA;p=R/'arms'/tag/'local_results'/n/'FINAL.npz';link(p,R/'local_results/final_bodies'/n/'BODY_FINAL.npz');link(p.with_name('FINAL_mm.ply'),R/'local_results/final_bodies'/n/'BODY_FINAL_mm.ply');bodies.append(dict(case=n,arm=tag,**asset(p),selection_uses_GT=False))
 save('provenance/FROZEN_FINAL_BODIES_FIT_ONLY.json',dict(epoch=time.time(),bodies=bodies,selection_A=asset(R/'config/PHASE_A_SELECTED.json'),selection_B=asset(R/'config/PHASE_B_SELECTED.json'),GT_read=False));print('STALK_FIT_ONLY_SELECTION',chosen,flush=True)
if __name__=='__main__':main()
