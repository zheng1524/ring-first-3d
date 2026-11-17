"""One global FIT-only selection. Heldout and GT cannot rank configurations."""
from audit_models import *
def main():
    assert(R/'provenance/PHASE_A_PREDICTIONS_FROZEN.json').exists();rows=[];stability=[];names=[q['name']for q in load(R/'config/CASE_LOCK.json')]
    for n in names:
        base=audit(n,R/'inputs'/n/'INITIAL.npz')
        for arm in ['Init-A','Init-B','Init-C']:
            for stage in ['INITIAL','FINAL']:
                path=R/'initializations'/n/(arm+'.npz')if stage=='INITIAL'else R/'arms'/arm/'local_results'/n/'FINAL.npz';sc=load(R/'metrics/scores'/(n+'_'+arm+'_'+stage+'.json'));depth=fixed_depth(sc);g=audit(n,path,base);rows.append(dict(case=n,arm=arm,stage=stage,geometry=g,FIT=sc['mean']['FIT'],HOLDOUT=sc['mean'].get('UPDATE_HOLDOUT'),HERO_FIT=depth,HERO_HOLDOUT=fixed_depth(sc,'UPDATE_HOLDOUT'),FIT_selection_cost=1-sc['mean']['FIT']['IoU']+.02*(depth['fixed_cost']if depth['fixed_cost']is not None else 9.5)))
            if arm!='Init-A':stability.append(dict(case=n,arm=arm,**compare_surfaces(R/'initializations'/n/(arm+'.npz'),R/'initializations'/n/(arm+'_SUBSET.npz')),subset_rule='remove last selected new FIT view, fixed8nfev from same original parameters; not used for method selection'))
    final=[q for q in rows if q['stage']=='FINAL'];A=[q for q in final if q['arm']=='Init-A'];bad=lambda q:bool(not q['geometry']['dense_nonworsening_vs_common013'])or bool(q['geometry']['self_intersections_N']);a_bad=sum(bad(q)for q in A);summary=[]
    for arm in ['Init-A','Init-B','Init-C']:
        rr=[q for q in final if q['arm']==arm];badN=sum(bad(q)for q in rr);summary.append(dict(arm=arm,target_N=11,numeric_N=len(rr),FIT_median_selection_cost=float(np.median([q['FIT_selection_cost']for q in rr])),geometry_flagged_N=badN,eligible_for_global_selection=len(rr)==11 and badN<=a_bad,selection_uses_only_FIT=True))
    eligible=[q for q in summary if q['eligible_for_global_selection']];chosen=min(eligible,key=lambda q:q['FIT_median_selection_cost'])['arm'];save('metrics/PHASE_A_ALL_METRICS.json',rows);table('metrics/PHASE_A_ALL_METRICS.csv',rows);save('metrics/INITIALIZATION_STABILITY.json',stability);table('metrics/INITIALIZATION_STABILITY.csv',stability);save('config/PHASE_A_SELECTED.json',dict(epoch=time.time(),selected=chosen,all_cases_same_method=True,summary=summary,GT_used=False,HOLDOUT_used=False,no_retraining_or_checkpoint_selection=True));save('provenance/PHASE_A_SELECTION_FREEZE.json',dict(epoch=time.time(),selection=asset(R/'config/PHASE_A_SELECTED.json'),parent_predictions=asset(R/'provenance/PHASE_A_PREDICTIONS_FROZEN.json'),GT_read=False));print('PHASE_A_SELECTED',chosen,summary,flush=True)
if __name__=='__main__':main()
