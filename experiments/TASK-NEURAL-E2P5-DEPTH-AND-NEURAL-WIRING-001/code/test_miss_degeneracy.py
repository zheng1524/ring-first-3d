"""Fixed real observations: loss-selection counterexample + actual neural SDF perturbations.

No Sphere, training or parameter update. Output offsets are explicit diagnostic
inputs. Hit-count interventions are nondifferentiable diagnostics, never a loss.
"""
from common import *
import torch
ROWS=[];SELECTION=[];STABILITY=[]


def stable_log_mask(adapter,b,cells):
    """Same finite opacity BCE, evaluated in log optical-depth coordinates.

    log sigma(f>=0)=-log(2 beta)-f/beta;
    log sigma(f<0)=-log(beta)+log(1-.5 exp(f/beta)).
    log tau=logsumexp(log sigma+log delta); positive BCE=-log(1-exp(-tau));
    negative BCE=tau. For log tau<-20 use log opacity≈log tau (error<1.1e-9).
    Counts do not enter the derivative. Candidate only, not a formal loss change.
    """
    ix=np.flatnonzero(b['valid']&(b['mask_weight']>0));o=torch.tensor(b['origin'][ix]);d=torch.tensor(b['direction'][ix])
    a=torch.tensor(b['start'][ix]);end=torch.tensor(b['end'][ix]);u=(torch.arange(cells,dtype=torch.float64)+.5)/cells
    t=a[:,None]+(end-a)[:,None]*u;P=o[:,None]+d[:,None]*t[:,:,None]
    sdf=adapter.raw_outputs(P.reshape(-1,3))['sdf_mm'].reshape(len(ix),cells);beta=adapter.beta*adapter.scale
    positive=-torch.log(2*beta)-sdf/beta
    negative=-torch.log(beta)+torch.log1p(-.5*torch.exp(torch.clamp_max(sdf/beta,0)))
    log_sigma=torch.where(sdf>=0,positive,negative)
    log_tau=torch.logsumexp(log_sigma+torch.log((end-a)/cells)[:,None],1)
    safe_tau=torch.exp(log_tau.clamp_min(-20));log_opacity=torch.where(log_tau<-20,log_tau,torch.log(-torch.expm1(-safe_tau)))
    y=torch.tensor(b['mask_target'][ix],dtype=sdf.dtype);w=torch.tensor(b['mask_weight'][ix],dtype=sdf.dtype);value=(-y*log_opacity+(1-y)*torch.exp(log_tau))*w
    return value.sum()/w.sum()


def deriv(value,delta):
    if value is None:return None
    g=torch.autograd.grad(value,delta,retain_graph=True,allow_unused=True)[0]
    return None if g is None else float(g.detach())


def run_degeneracy(model,domain,packets,scene,cfg,params):
    from official_sdf_cpu_adapter import AuthorizedFiniteCPU,proposals,per_view_terms,legacy
    spec=load(R/'config/MISS_DEGENERACY_PREREG.json');base_predictions=None
    class OffsetRaw:
        def __init__(self,delta):self.delta=delta
        def forward(self,x):
            out=model.implicit_network.forward(x)
            return torch.cat([out[:,:1]+self.delta/domain['mm_per_unit'],out[:,1:]],1)
    for fraction in spec['geometric_output_offset_ROI_fractions']:
        delta=torch.tensor(fraction*domain['ROI_radius_mm'],dtype=torch.float64,requires_grad=True)
        adapter=AuthorizedFiniteCPU(model,domain,OffsetRaw(delta));adapter.current_ref=None
        predictions=[];old_masks=[];stable_masks=[];rgb=[];depth=[];counts=[]
        for j,b in enumerate(packets):
            p=adapter.render(b,proposals(b,domain['mm_per_unit'],cfg['sample_cells']),j);predictions.append(p)
            terms,c=per_view_terms(p,b);counts.append(c);old_masks.append(terms['mask']);stable_masks.append(stable_log_mask(adapter,b,cfg['sample_cells']))
            if terms['depth'] is not None:depth.append(terms['depth'])
            if terms['rgb'] is not None:rgb.append(terms['rgb'])
        mask=torch.stack(old_masks).mean();stable=torch.stack(stable_masks).mean()
        dl=torch.stack(depth).mean() if depth else None;rl=torch.stack(rgb).mean() if rgb else None
        partial=.1*mask+(.1*dl if dl is not None else 0)+(rl if rl is not None else 0)
        alternative=.1*stable+(.1*dl if dl is not None else 0)+(rl if rl is not None else 0)
        valid=all(c['hit_N']>0 and c['RGB_N']>0 for c in counts)
        observed=sum(c['observed_N'] for c in counts);hits=sum(c['hit_N'] for c in counts)
        row=dict(scene=scene,kind='ACTUAL_OFFICIAL_NEURAL_RAW_OFFSET',condition='ROI_START_INSIDE_FIELD' if fraction<0 else 'DECLARED_OFFSET_'+str(fraction),
            diagnostic_offset_mm=float(delta.detach()),observed_N=observed,hit_N=hits,miss_N=observed-hits,hit_coverage=hits/observed,
            depth_hit_mean=None if dl is None else float(dl.detach()),Mask_loss=float(mask.detach()),RGB_loss=None if rl is None else float(rl.detach()),
            current_joint_total=float(partial.detach()) if valid else None,joint_status='COMPLETE' if valid else 'REJECTED_INCOMPLETE_REFERENCE',
            partial_known_terms_sum=float(partial.detach()),stable_Mask_candidate=float(stable.detach()),
            current_Mask_dLoss_dOffset=deriv(mask,delta),stable_Mask_dLoss_dOffset=deriv(stable,delta),
            depth_dLoss_dOffset=deriv(dl,delta),current_known_terms_dLoss_dOffset=deriv(partial,delta),
            stable_known_terms_dLoss_dOffset=deriv(alternative,delta),
            gradient_direction_note='positive derivative: descent reduces positive SDF offset and tends to expand/recover; not a hit-count gradient',
            missing_depth_encoded_as_zero=False,model_parameters_modified=False,formal_new_loss_adopted=False)
        ROWS.append(row)
        if fraction==0:
            base_predictions=[dict(depth=p['axial_depth_mm'].detach().numpy(),hit=p['render_hit'].copy(),opacity=p['opacity'].detach().numpy()) for p in predictions]
            # Compare stable log evaluation with old epsilon-clamped formula only
            # in their shared non-saturated domain, using real network rays.
            for b,p in zip(packets,predictions):
                prob=p['opacity'].detach().numpy();inside=(prob>1e-6)&(prob<1-1e-6)&(b['mask_weight']>0)
                if inside.any():
                    small={k:v[inside] if isinstance(v,np.ndarray)and v.ndim>0 and len(v)==len(prob) else v for k,v in b.items()}
                    expected=opacity.masked_opacity_loss(dict(opacity=p['opacity'][inside]),dict(mask_weight=small['mask_weight'],mask_target=small['mask_target']))
                    actual=stable_log_mask(adapter,small,cfg['sample_cells']);error=abs(float((actual-expected).detach()))
                    STABILITY.append(dict(scene=scene,source=b['source'],non_saturated_ray_N=int(inside.sum()),BCE_equivalence_abs_error=error,
                        pass_=error<1e-5,approximation_error_bound=1.1e-9))
        print('MISS_DIAGNOSTIC',scene,'offset fraction',fraction,'hit',hits,'/',observed,'Mask offset gradient',row['current_Mask_dLoss_dOffset'],'stable',row['stable_Mask_dLoss_dOffset'],flush=True)
        table('metrics/DEGENERACY_TESTS.csv',ROWS);table('metrics/STABLE_MASK_NUMERICAL_CHECKS.csv',STABILITY)
    # Selection-only counterexample. Keep the SAME model outputs/opacity/RGB and
    # remove highest source-HERO errors from the rendered-hit selection. This
    # proves objective sensitivity; it is not a physically certified field or
    # differentiable intervention and is never used to select model parameters.
    for condition,fraction in zip(spec['conditions'],spec['adversarial_hit_keep_fractions']):
        terms=[];observed=0;hits=0;fixed_contribution=0.;fixed_weight=0.;per_source=[]
        for b,p in zip(packets,base_predictions):
            obs=(b['depth_weight']>0)&np.isfinite(b['target_Z'])&(b['target_Z']>0);observed+=int(obs.sum())
            valid=obs&p['hit'];idx=np.flatnonzero(valid);err=abs(p['depth'][idx]-b['target_Z'][idx]);h=np.where(err<=.5,err**2,err-.25)
            order=np.argsort(h);keep=int(np.ceil(len(idx)*fraction)) if fraction>0 else 0;ix=order[:keep]
            w=b['depth_weight'][idx[ix]];value=float((h[ix]*w).sum()/w.sum()) if len(ix) else None
            if value is not None:terms.append(value)
            hits+=keep;fixed_contribution+=float((h[ix]*w).sum());fixed_weight+=float(b['depth_weight'][obs].sum())
            per_source.append(dict(source=b['source'],observed_N=int(obs.sum()),kept_hit_N=keep))
        SELECTION.append(dict(scene=scene,kind='ADVERSARIAL_SELECTION_ONLY_NOT_FIELD_PREDICTION',condition=condition,
            observed_N=observed,hit_N=hits,hit_coverage=hits/observed,depth_hit_mean=float(np.mean(terms)) if terms else None,
            hit_error_contribution_over_fixed_observed_weight=fixed_contribution/fixed_weight,
            fixed_denominator_warning='zero missing contribution is not full-depth accuracy; display coverage and NaN misses',
            Mask_loss='UNCHANGED_BY_SELECTION_INTERVENTION',RGB_loss='UNCHANGED_BY_SELECTION_INTERVENTION',
            joint_gate='REJECTED' if any(x['kept_hit_N']==0 for x in per_source) else 'MAY_PASS_WITH_PARTIAL_COVERAGE',
            gradient='NOT_DEFINED_FOR_DISCRETE_HIT_GATE; actual geometry gradients in DEGENERACY_TESTS.csv',per_source=per_source,
            observations_changed=False,model_parameters_modified=False))
    table('metrics/DEGENERACY_SELECTION_COUNTEREXAMPLE.csv',SELECTION)
    save('metrics/MISS_DEGENERACY_GATE.json',dict(status='POTENTIAL_COVERAGE_ERROR_TRADEOFF_IDENTIFIED',
        hit_conditional_mean_can_fall_when_hard_rays_disappear=True,all_miss_reference_rejected_by_current_joint_gate=True,
        partial_miss_risk_eliminated=False,Mask_clamp_can_cut_off_recovery_gradient=True,
        stable_log_BCE_candidate='diagnostic only; same math probability, avoids epsilon clamp; no scientific adoption',
        stable_mask_checks_pass=all(x['pass_'] for x in STABILITY),fixed_observed_denominators=True,
        formal_new_loss_adopted=False,GPU='NOT_AUTHORIZED',optimizer_step_N=0))


def legacy_selection_control(cfg,packets_by_scene):
    """Use the SAME preregistered legacy control in both scenes, not best-model selection."""
    out=[];gradient_rows=list(csv.DictReader((R/'metrics/NEURAL_PER_REFERENCE_GRADIENTS.csv').open()))
    for scene,packets in packets_by_scene.items():
        candidate='A_LEGACY_INIT_CONTROL';eik=float(next(x['value'] for x in gradient_rows if x['scene']==scene and x['candidate']==candidate and x['loss']=='eikonal'))
        for condition,fraction in zip(['NORMAL','PARTIAL_REMOVAL','HEAVY_REMOVAL','ALL_REMOVED'],[1.,.75,.25,0.]):
            depths=[];rgbs=[];masks=[];observed=0;hits=0;per_source=[];fixed_sum=0.;fixed_weight=0.
            for b in packets:
                p=np.load(R/f'local_results/neural/{scene}_{candidate}_{b["source"]}.npz');obs=p['observed'];idx=np.flatnonzero(obs&p['render_hit'])
                err=abs(p['depth_mm'][idx]-b['target_Z'][idx]);h=np.where(err<=.5,err**2,err-.25);keep=int(np.ceil(len(idx)*fraction)) if fraction>0 else 0
                order=np.argsort(h)[:keep];chosen=idx[order];w=b['depth_weight'][chosen]
                if keep:depths.append(float((h[order]*w).sum()/w.sum()))
                fixed_sum+=float((h[order]*w).sum());fixed_weight+=float(b['depth_weight'][obs].sum())
                selected=np.zeros(len(obs),bool);selected[chosen]=True
                rgbvalid=(b['sampling_class']==0)&selected&(b['mask_weight']>0)
                if rgbvalid.any():
                    e=p['RGB'][rgbvalid]-b['RGB'][rgbvalid];a=abs(e);hu=np.where(a<=.05,.5*e**2/.05,a-.025).mean(1);rw=b['mask_weight'][rgbvalid]
                    rgbs.append(float((hu*rw).sum()/rw.sum()))
                mask=float(next(x['value'] for x in gradient_rows if x['scene']==scene and x['candidate']==candidate and x['source']==b['source'] and x['loss']=='mask'))
                masks.append(mask);observed+=int(obs.sum());hits+=keep
                per_source.append(dict(source=b['source'],observed_N=int(obs.sum()),hit_N=keep))
            valid=len(depths)==len(rgbs)==3;dl=float(np.mean(depths)) if depths else None;rgb=float(np.mean(rgbs)) if rgbs else None;mask=float(np.mean(masks))
            total=rgb+.1*dl+.1*mask+.1*eik if valid else None
            out.append(dict(scene=scene,candidate=candidate,condition=condition,kind='DISCRETE_SELECTION_COUNTEREXAMPLE_NOT_A_REAL_FIELD',
                observed_N=observed,hit_N=hits,miss_N=observed-hits,hit_coverage=hits/observed,Depth_loss=dl,Mask_loss=mask,RGB_loss=rgb,
                current_joint_total=total,partial_error_contribution_over_fixed_observed_weight=fixed_sum/fixed_weight,
                joint_status='COMPLETE_BUT_PARTIAL_COVERAGE' if valid else 'REJECTED_INCOMPLETE_REFERENCE',
                gradient='NOT_DIFFERENTIABLE_INTERVENTION; actual-neural continuous perturbation reported separately',
                per_source=per_source,Mask_opacity_unchanged=True,observations_unchanged=True,model_parameters_unchanged=True))
    table('metrics/DEGENERACY_SELECTION_COUNTEREXAMPLE.csv',out)


def replay_corrected_diagnostic():
    from official_sdf_cpu_adapter import construct_official,model_config,packets_for,parameter_hash
    cfg=load(R/'config/PREREGISTERED.json');domains=load(E2/'config/SDF_INITIALIZATION_CANDIDATE.json')['scenes']
    old=load(R/'metrics/OFFICIAL_SDF_CPU_RUNS.json');receipts=[];packets={}
    freeze('STABLE_MASK_FIX_BEFORE_IDENTICAL_REPLAY.json',dict(new_initialization_candidates=0,optimizer_steps=0))
    for scene,refs in selected().items():
        packets[scene]=packets_for(scene,refs,cfg);torch.random.default_generator.manual_seed(cfg['seed'])
        model,ports=construct_official(model_config(domains[scene],'B_SOURCE_ROI_PHYSICAL',cfg));before=parameter_hash(model)
        expected=next(x['parameter_SHA_before'] for x in old if x['scene']==scene and x['candidate']=='B_SOURCE_ROI_PHYSICAL')
        assert before==expected,'replay must reproduce exactly the original untrained parameters'
        run_degeneracy(model,domains[scene],packets[scene],scene,cfg,list(model.named_parameters()))
        assert parameter_hash(model)==before
        receipts.append(dict(scene=scene,replayed_identical_parameter_SHA256=before,parameters_unchanged=True,new_candidate=False))
    legacy_selection_control(cfg,packets)
    save('provenance/IDENTICAL_NETWORK_DIAGNOSTIC_REPLAY.json',dict(replays=receipts,total_network_constructions_first_pass=4,additional_identical_replays=2,
        unique_scene_candidate_models=4,initialization_candidate_N=2,original_neural_gate_not_changed=True,optimizer_step_N=0))
    print('CORRECTED_STABLE_MASK_DIAGNOSTIC_COMPLETE; two exact seeded replays; neural gate unchanged')


if __name__=='__main__':replay_corrected_diagnostic()
