"""Resolve a failed component-sum Adam check with exact original FP32 accumulation."""
from common import *
from gpu_model_adapter import initialized_model
from fixed_renderer import render,terms,data_loss,eikonal

def main():
    records=[];components=load(R/'metrics/FIRST_STEP_DIAGNOSIS.json')
    # Retain the original failed2e-7 check; do not relax its criterion.
    if not (R/'provenance/COMPONENT_SUM_ADAM_CHECK.json').exists():save('provenance/COMPONENT_SUM_ADAM_CHECK.json',components)
    for arm in ['A','B']:
        model,_=initialized_model('cuda:0');before=parameter_hash(model)
        for p in model.parameters():p.grad=None
        for ref in REFS:
            b=packet(ref,'extra');p=render(model,b,load(R/'config/SELECTED_SAMPLING.json')['cells'],REFS.index(ref));t=terms(model,b,p,include_anchor=arm=='B')
            (data_loss(t,cfg()['arms'][arm]['anchor'])/3).backward();del b,p,t
        e=.1*eikonal(model);e.backward();del e
        actual=torch.load(R/f'checkpoints/{arm}/STOP_UNSAFE_step001.pt',map_location='cpu',weights_only=True);maxerr=0.;N=0;errrows=[]
        for name,p in model.named_parameters():
            lr=1e-5 if name.startswith('density.') else 1e-4
            expected=p.detach()-lr*p.grad/(p.grad.abs()+1e-8);delta=abs(expected-actual[name].to(p.device));err=float(delta.max());maxerr=max(maxerr,err);N+=p.numel()
            errrows.append(dict(arm=arm,name=name,max_abs_parameter_error=err,finite=bool(torch.isfinite(p.grad).all())))
        assert parameter_hash(model)==before
        records.append(dict(arm=arm,complete_parameter_N=N,exact_training_backward_accumulation_max_error=maxerr,
            pass_same_original_tolerance=maxerr<2e-7,unchanged_tolerance=2e-7,all_gradient_finite=all(r['finite']for r in errrows),
            original_component_sum_max_error=next(r['independent_first_Adam_formula_max_abs_error']for r in components['rows']if r['arm']==arm),
            no_optimizer_created=True,no_parameter_update=True))
        table('metrics/EXACT_ACCUMULATION_PARAMETER_CHECKS_'+arm+'.csv',errrows)
        del model;gc.collect();torch.cuda.empty_cache()
    save('metrics/EXACT_ACCUMULATION_VERIFICATION.json',dict(rows=records,all_exact_checks_pass=all(r['pass_same_original_tolerance']for r in records),
        original_failed_check_retained=True,explanation='linear component-gradient sums round differently from per-view FP32 loss.backward; coordinatewise first-step Adam can amplify cancellation near eps',
        additional_optimizer_steps=0))
    print('EXACT_ACCUMULATION_CHECK_COMPLETE',records,flush=True)
if __name__=='__main__':main()
