"""Reject lower coverage even when objective falls; no discrete count gradient."""
from common import *
from stable_losses import packet

def readrows(path):return list(csv.DictReader(Path(path).open()))
def huber(error,delta):
    a=abs(error);return np.where(a<=delta,.5*error**2/delta,a-.5*delta)

def main():
    gate=load(R/'THREE_REFERENCE_NEURAL_GATE.json');neural=readrows(R/'metrics/PER_REFERENCE_NEURAL_SUPERVISION.csv')
    detail=readrows(R/'metrics/PER_REFERENCE_LOSSES_AND_GRADIENTS.csv');old=readrows(E25/'metrics/NEURAL_INITIALIZATION_AND_HITS.csv')
    freeze('P4_COVERAGE_BEFORE_COMPARISON.json',dict(variants=['CURRENT','STABLE_MASK','STABLE_MASK_PLUS_WEAK_ANCHOR'],
        source_denominator='fixed actual observed native HERO; never number of surviving hits',
        lower_coverage_acceptance=False,old_baselines='both A and B, never per-video selected'))
    history=[]
    for x in neural:
        if x['split']!='small':continue
        for candidate in ['A_LEGACY_INIT_CONTROL','B_SOURCE_ROI_PHYSICAL']:
            y=next(y for y in old if y['source']==x['source'] and y['candidate']==candidate)
            baseline=int(y['observed_hit_N'])/int(y['qualified_HERO_N']);current=float(x['hit_fraction'])
            history.append(dict(scene=x['scene'],source=x['source'],split='same_frozen_small',old_candidate=candidate,
                observed_N=int(y['qualified_HERO_N']),old_front_hit_N=int(y['observed_hit_N']),new_front_hit_N=int(x['front_hit_N']),
                old_hit_fraction=baseline,new_hit_fraction=current,coverage_lower=current<baseline-1e-12,
                status='POTENTIAL_FAILURE_LOWER_COVERAGE' if current<baseline-1e-12 else 'NO_COVERAGE_DROP',
                no_per_video_candidate_switch=True,not_a_single_factor_beta_comparison=True))
    table('metrics/HISTORICAL_FIXED_COVERAGE.csv',history)
    results=[]
    for scene,refs in selected().items():
        for split in ['small','extra']:
            bbs=[packet(ref,split) for ref in refs];pps=[np.load(R/f'local_results/neural/{ref}_{split}.npz') for ref in refs]
            source_stats={x['source']:x for x in neural if x['scene']==scene and x['split']==split}
            eik=float(next(x['value'] for x in detail if x['scene']==scene and x['split']==split and x['term']=='eikonal'))
            baseline_by_variant={}
            for condition,keep_fraction in [('NORMAL',1.),('PARTIAL_HIT_REMOVAL',.75),('HEAVY_HIT_REMOVAL',.25),('ALL_HITS_REMOVED',0.)]:
                depth=[];rgb=[];all_counts=[];old_masks=[];stable_masks=[];anchors=[]
                for b,p in zip(bbs,pps):
                    obs=p['observed'];original=p['render_hit'];eligible=np.flatnonzero(obs&original)
                    error=p['depth_mm'][eligible]-b['target_Z'][eligible];hh=huber(error,.5)
                    n=int(np.ceil(len(eligible)*keep_fraction)) if keep_fraction>0 else 0;keep=np.argsort(hh)[:n];hit=original.copy();hit[obs]=False;hit[eligible[keep]]=True
                    valid=obs&hit;w=b['depth_weight'][valid]
                    if valid.any():depth.append(float((huber(p['depth_mm'][valid]-b['target_Z'][valid],.5)*w).sum()/w.sum()))
                    rgb_valid=(b['sampling_class']==0)&hit&(b['mask_weight']>0)
                    if rgb_valid.any():
                        w=b['mask_weight'][rgb_valid];h=huber(p['RGB'][rgb_valid]-b['RGB'][rgb_valid],.05).mean(1)
                        rgb.append(float((h*w).sum()/w.sum()))
                    stats=source_stats[b['source']];old_masks.append(float(stats['old_Mask_loss']));stable_masks.append(float(stats['stable_Mask_loss']));anchors.append(float(stats['weak_anchor_loss']))
                    all_counts.append(dict(source=b['source'],observed_N=int(obs.sum()),baseline_hit_N=int((obs&original).sum()),candidate_hit_N=int(valid.sum()),
                        baseline_coverage=float((obs&original).sum()/obs.sum()),candidate_coverage=float(valid.sum()/obs.sum())))
                complete=len(depth)==len(rgb)==3;dl=float(np.mean(depth)) if depth else None;rl=float(np.mean(rgb)) if rgb else None
                coverage_ok=all(x['candidate_coverage']>=x['baseline_coverage']-1e-12 for x in all_counts)
                observed=sum(x['observed_N'] for x in all_counts);hits=sum(x['candidate_hit_N'] for x in all_counts)
                for variant,mask,anchor in [('CURRENT',np.mean(old_masks),0.),('STABLE_MASK',np.mean(stable_masks),0.),('STABLE_MASK_PLUS_WEAK_ANCHOR',np.mean(stable_masks),np.mean(anchors))]:
                    total=rl+.1*dl+.1*float(mask)+.1*eik+.01*float(anchor) if complete else None
                    if condition=='NORMAL':baseline_by_variant[variant]=total
                    base=baseline_by_variant[variant];lower=total is not None and base is not None and total<base-1e-12
                    results.append(dict(scene=scene,split=split,condition=condition,variant=variant,
                        observed_HERO_N=observed,front_hit_N=hits,miss_N=observed-hits,hit_fraction=hits/observed,
                        Mask_loss=float(mask),Depth_loss=dl,RGB_loss=rl,weak_anchor_loss=float(anchor),total_loss=total,baseline_total_loss=base,
                        coverage_non_decrease_gate=coverage_ok,total_loss_lower=lower,
                        lower_error_with_lower_coverage=lower and not coverage_ok,
                        accepted_as_improvement=complete and coverage_ok and lower,
                        status='POTENTIAL_FAILURE_COVERAGE_LOWER' if not coverage_ok else 'BASELINE_OR_NO_COVERAGE_DROP',
                        fixed_per_reference_observations=all_counts,
                        continuous_model_prediction=False,intervention='loss-selection sensitivity only; raw field/opacity/anchor unchanged',
                        discrete_hit_count_used_as_training_gradient=False))
    table('COVERAGE_DEGENERACY_VALIDATION.csv',results)
    risks=[x for x in results if x['lower_error_with_lower_coverage']]
    save('metrics/COVERAGE_GATE.json',dict(any_loss_variant_structurally_immune=False,
        risk_rows_by_variant={v:sum(x['variant']==v for x in risks) for v in ['CURRENT','STABLE_MASK','STABLE_MASK_PLUS_WEAK_ANCHOR']},
        lower_coverage_rows_rejected=all(not x['accepted_as_improvement'] for x in results if not x['coverage_non_decrease_gate']),
        objective_coverage_tradeoff_risk_still_present=bool(risks),
        weak_anchor_remains_active_on_misses=True,actual_training_coverage_improvement_observed=False,
        historical_A_coverage_drops=sum(x['coverage_lower'] for x in history if x['old_candidate']=='A_LEGACY_INIT_CONTROL'),
        historical_B_coverage_drops=sum(x['coverage_lower'] for x in history if x['old_candidate']=='B_SOURCE_ROI_PHYSICAL'),
        evaluation_fix='any lower fixed-observed per-source coverage is a potential failure, regardless of objective decrease',
        no_gradient_from_hit_counts=True,optimizer_step_N=0,GPU='NOT_AUTHORIZED'))
    print('COVERAGE_VALIDATION_COMPLETE',len(results),'rows;',len(risks),'lower-loss/lower-coverage counterexamples; all rejected by evaluation')

if __name__=='__main__':main()
