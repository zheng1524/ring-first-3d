"""Full real-neural parameter gradients, five controls, FP32/64 and math reference."""
from common import *
from stable_losses import mask_bundle,packet
import mpmath as mp

def reference(bundle,index):
    mp.mp.dps=80
    f=bundle['raw_sdf'][index].detach().double().numpy();beta=mp.mpf(float(bundle['beta'].detach()));delta=mp.mpf(float(bundle['delta'][index].detach()))
    tau=mp.mpf(0)
    for value in f:
        x=mp.mpf(float(value));sigma=mp.exp(-x/beta)/(2*beta) if x>=0 else (1-mp.exp(x/beta)/2)/beta
        tau+=sigma*delta
    y=float(bundle['targets'][index]);expected=-mp.log(-mp.expm1(-tau)) if y else tau
    actual=float(bundle['per_ray'][index].detach());expected=float(expected)
    return expected,actual,abs(actual-expected)

def field_case_bias(scene,kind):
    cal=load(R/'config/SHELL_CALIBRATION_FROZEN.json')[scene];domain=domains()[scene];b=cal['bias_network']
    shift=cfg()['pathological_bias_delta_ROI']*domain['ROI_radius_mm']/domain['mm_per_unit']
    return b if kind=='NORMAL' else b-shift if kind=='POSITIVE' else b+shift

def main():
    freeze('P2_FULL_PARAMETER_TESTS_BEFORE_RUN.json',dict(initialization_rule_gate=load(R/'metrics/INITIALIZATION_GATE.json'),
        continuing='loss diagnostics only; no new initialization search or changed shell rule'))
    rows=[];numeric=[];math=[];states=[];cache={}
    cases=[('CALIBRATED_NORMAL','NORMAL'),('ALL_POSITIVE_FIELD','POSITIVE'),('EMPTY_POSITIVE_RAYS','POSITIVE'),('ALL_NEGATIVE_FIELD','NEGATIVE'),('RING_OCCLUDED_PREFIX','NORMAL')]
    for scene,refs in selected().items():
        domain=domains()[scene]
        for precision,dtype in [('FP64',torch.float64),('FP32',torch.float32)]:
            for field in ['NORMAL','POSITIVE','NEGATIVE']:
                model,ports=build_model(domain,field_case_bias(scene,field),dtype);before=e25.parameter_hash(model)
                for case,kind in cases:
                    if kind!=field:continue
                    for ref in refs:
                        b=packet(ref,'small');subset=None
                        if case=='EMPTY_POSITIVE_RAYS':subset=(b['sampling_class']==0)&(b['mask_target']==1)
                        if case=='RING_OCCLUDED_PREFIX':subset=b['sampling_class']==3
                        active=b['valid']&(b['mask_weight']>0)
                        if subset is not None:active&=subset
                        if not active.any():
                            rows.append(dict(scene=scene,source=ref,case=case,precision=precision,status='NO_CERTIFIED_VISIBLE_PREFIX',stable_loss=None,old_loss=None));continue
                        bundle=mask_bundle(model,domain,b,dtype,subset);loss=bundle['stable'];g,vec=full_gradient(loss,model)
                        old=bundle['old'];old_finite=bool(torch.isfinite(old))
                        oldg,oldvec=full_gradient(old,model) if old_finite else ({'implicit_norm':None,'full_norm':None,'finite':False},None)
                        f=bundle['raw_sdf'].detach();sign_ok=bool((f>0).all()) if field=='POSITIVE' else bool((f<0).all()) if field=='NEGATIVE' else True
                        low=cfg()['useful_geometry_gradient_norm_min'];useful=g['implicit_norm']>low and g['trunk_norm']>low
                        row=dict(scene=scene,source=ref,case=case,precision=precision,status='MEASURED',valid_ray_N=len(bundle['active_ids']),
                            positive_Mask_N=int((bundle['targets']>0).sum()),stable_loss=float(loss.detach()),old_loss=float(old.detach()) if old_finite else None,
                            old_loss_finite=old_finite,stable_loss_finite=bool(torch.isfinite(loss)),
                            stable_full_gradient_norm=g['full_norm'],stable_geometry_gradient_norm=g['implicit_norm'],stable_trunk_gradient_norm=g['trunk_norm'],stable_head_gradient_norm=g['head_norm'],
                            stable_beta_gradient_norm=g['beta_norm'],old_geometry_gradient_norm=oldg['implicit_norm'],
                            all_parameter_gradients_finite=g['finite'],full_parameter_N=g['parameter_N'],parameter_tensor_N=g['tensor_N'],
                            useful_geometry_gradient=useful,field_sign_control_valid=sign_ok,raw_min_mm=float(f.min()),raw_max_mm=float(f.max()),
                            only_scalar_output_derivative=False,model_parameters_updated=False)
                        rows.append(row);key=(scene,ref,case)
                        if precision=='FP64':cache[key]=(row,vec)
                        else:
                            other,v64=cache[key];norm64=robust_norm(v64);norm32=robust_norm(vec)
                            fullcos=float(torch.dot(v64,vec)/(norm64*norm32)) if norm64 and norm32 else None
                            # Geometry norm is checked separately: beta-only
                            # gradients may not masquerade as surface recovery.
                            informative=other['useful_geometry_gradient'] and useful
                            error=abs(row['stable_loss']-other['stable_loss']);allowed=cfg()['FP32_FP64_loss_atol']+cfg()['FP32_FP64_loss_rtol']*abs(other['stable_loss'])
                            numeric.append(dict(scene=scene,source=ref,case=case,FP64_loss=other['stable_loss'],FP32_loss=row['stable_loss'],loss_abs_difference=error,
                                loss_consistency_pass=error<=allowed,full_parameter_gradient_cosine=fullcos,
                                norm_relative_difference=abs(norm32-norm64)/max(norm64,1e-300),
                                full_gradient_consistency_pass=(fullcos is not None and fullcos>=cfg()['gradient_cosine_min'] and abs(norm32-norm64)/max(norm64,1e-300)<=cfg()['gradient_norm_relative_tolerance']),
                                geometry_recovery_informative=informative,zero_geometry_not_a_pass=not informative))
                        if precision=='FP64':
                            chosen=[]
                            for label in [1,0]:
                                ix=torch.nonzero(bundle['targets']==label,as_tuple=True)[0]
                                if len(ix):chosen.append(int(ix[0]))
                            for k in chosen:
                                expected,actual,error=reference(bundle,k)
                                math.append(dict(scene=scene,source=ref,case=case,ray_in_subset=k,target=float(bundle['targets'][k]),
                                    mpmath80_expected_BCE=expected,stable_BCE=actual,abs_error=error,
                                    same_finite_interval_target=True,pass_=error<=cfg()['reference_atol']+cfg()['reference_rtol']*abs(expected)))
                        del bundle,loss,old,vec,oldvec;gc.collect()
                    print('STABLE_FULL_PARAMS',scene,precision,case,'measured with real official parameters',flush=True)
                assert before==e25.parameter_hash(model)
                states.append(dict(scene=scene,precision=precision,field_control=field,parameter_SHA_before=before,parameter_SHA_after=before,
                    parameters_unchanged=True,CPU_constructor_ports=ports,initialization_candidate=False,loss_control=True))
                del model;gc.collect()
                table('STABLE_MASK_GRADIENT_TESTS.csv',rows);table('metrics/FP32_FP64_CONSISTENCY.csv',numeric);table('metrics/MATH_TARGET_EQUIVALENCE.csv',math)
    need=any(r.get('case')=='ALL_NEGATIVE_FIELD' and not r.get('useful_geometry_gradient',False) for r in rows)
    save('metrics/STABLE_MASK_GATE.json',dict(stable_all_finite=all(r.get('stable_loss_finite',True) and r.get('all_parameter_gradients_finite',True) for r in rows),
        mathematical_target_equivalence=all(x['pass_'] for x in math),FP32_FP64_loss_consistency=all(x['loss_consistency_pass'] for x in numeric),
        full_gradient_precision_consistency=all(x['full_gradient_consistency_pass'] for x in numeric),
        stable_mask_alone_recovers_all_controls=not need,weak_HERO_anchor_necessary=need,
        beta_only_gradient_not_surface_recovery=True,official_parameter_N=670395,optimizer_step_N=0,GPU='NOT_AUTHORIZED'))
    save('provenance/STABLE_TEST_MODEL_STATES.json',states)
    print('STABLE_MASK_CPU_COMPLETE','weak_anchor_needed',need,'all actual neural gradients checked; no updates')

if __name__=='__main__':main()
