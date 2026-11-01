"""Exactly two serial bounded Adam arms, with fixed monitoring and hard stops."""
from common import *
from gpu_model_adapter import initialized_model,checkpoint
from fixed_renderer import render,terms,data_loss,eikonal
from evaluate import probe,safety

def append_table(name,new):
    path=R/name;old=list(csv.DictReader(path.open())) if path.exists() else [];table(name,old+new)
def state_cpu(model):return {k:v.detach().cpu().clone() for k,v in model.state_dict().items()}
def update_norm(model,initial):
    delta=0.;base=0.
    for name,t in model.state_dict().items():
        diff=t.detach().cpu().double()-initial[name].double();delta+=float((diff*diff).sum());base+=float((initial[name].double()**2).sum())
    return delta**.5,(delta/max(base,1e-30))**.5

def run(arm):
    assert load(R/'metrics/GPU_PARITY.json')['pass_'],'PREFLIGHT_BLOCKED_NO_OPTIMIZER_STEPS'
    if (R/f'metrics/{arm}_RUN.json').exists():raise RuntimeError('ARM_ALREADY_EXECUTED_NO_RESTART_WITHOUT_ENGINEERING_FAILURE')
    check_gpu();cells=load(R/'config/SELECTED_SAMPLING.json')['cells'];model,meta=initialized_model('cuda:0')
    assert meta['FP32_SHA256']==load(R/'provenance/INITIAL_MODEL.json')['FP32_SHA256']
    initial=state_cpu(model);lastsafe=initial;lastsafe_step=0;start=time.monotonic();torch.cuda.reset_peak_memory_stats()
    opt=torch.optim.Adam([dict(params=model.implicit_network.parameters(),lr=1e-4),dict(params=model.rendering_network.parameters(),lr=1e-4),dict(params=model.density.parameters(),lr=1e-5)],betas=(.9,.999),weight_decay=0)
    checkpoint(model,arm,0);freeze('BEFORE_ARM_'+arm+'.json',dict(initial_model=meta,step_budget=100,optimizer_step_N=0,small_never_updates=True))
    rows,curve=probe(model,arm,0,cells);curve.update(elapsed_seconds=time.monotonic()-start,parameter_update_L2=0.,parameter_update_relative=0.)
    append_table('metrics/PER_REFERENCE_METRICS.csv',rows);append_table('metrics/TRAINING_CURVES.csv',[curve]);append_table('metrics/COVERAGE_HISTORY.csv',[{k:r[k] for k in ['arm','step','source','split','observed_N','front_hit_N','miss_N','coverage','status']} for r in rows])
    persist={(ref,sp):0 for ref in REFS for sp in ['extra','small']};reason=None;step=0;updates=0;engineering=False
    extra_checkpoints=set()
    if arm=='B'and(R/'metrics/A_RUN.json').exists():extra_checkpoints.add(load(R/'metrics/A_RUN.json')['last_safe_step'])
    try:
        sr,cr,reason=safety(model,arm,0,cells)
        if reason:raise RuntimeError('INITIAL_'+reason)
        for step in range(1,101):
            if time.monotonic()-start>=1800:reason='WALL_TIME_LIMIT';break
            opt.zero_grad(set_to_none=True)
            for ref in REFS:
                b=packet(ref,'extra');p=render(model,b,cells,REFS.index(ref));t=terms(model,b,p,include_anchor=(arm=='B'));loss=data_loss(t,cfg()['arms'][arm]['anchor'])/3
                if not bool(torch.isfinite(loss)):raise FloatingPointError('NONFINITE_TRAIN_LOSS')
                loss.backward();del b,p,t,loss
            e=.1*eikonal(model)
            if not bool(torch.isfinite(e)):raise FloatingPointError('NONFINITE_EIKONAL')
            e.backward();del e
            if not all(p.grad is None or bool(torch.isfinite(p.grad).all()) for p in model.parameters()):raise FloatingPointError('NONFINITE_TRAIN_GRADIENT')
            memory_guard();opt.step();updates+=1
            if not all(bool(torch.isfinite(p).all()) for p in model.parameters()):raise FloatingPointError('NONFINITE_PARAMETERS')
            sr,cr,reason=safety(model,arm,step,cells);append_table('metrics/SAFETY_EVERY_STEP.csv',sr)
            isprobe=step%5==0 or reason is not None
            if isprobe:
                rr,curve=probe(model,arm,step,cells);u,ur=update_norm(model,initial);curve.update(elapsed_seconds=time.monotonic()-start,parameter_update_L2=u,parameter_update_relative=ur)
                append_table('metrics/PER_REFERENCE_METRICS.csv',rr);append_table('metrics/TRAINING_CURVES.csv',[curve]);append_table('metrics/COVERAGE_HISTORY.csv',[{k:r[k] for k in ['arm','step','source','split','observed_N','front_hit_N','miss_N','coverage','status']} for r in rr])
                if step%5==0:
                    for r in rr:
                        key=(r['source'],r['split']);drop=r['baseline_coverage']-r['coverage'];persist[key]=persist[key]+1 if drop>.10+1e-12 else 0
                    if any(v>=3 for v in persist.values()):reason=reason or 'COVERAGE_DROP_OVER10PP_THREE_FIXED_PROBES'
                print('ARM_PROBE',arm,step,'coverage',[(r['source'],r['split'],r['front_hit_N'],r['observed_N']) for r in rr],'loss',curve['total_loss'],'stop',reason,flush=True)
            if time.monotonic()-start>=1800:reason=reason or 'WALL_TIME_LIMIT'
            memory_guard()
            if reason:
                checkpoint(model,arm,step,'STOP_UNSAFE');break
            lastsafe=state_cpu(model);lastsafe_step=step
            if step in cfg()['checkpoint_steps']or step in extra_checkpoints:checkpoint(model,arm,step)
        if reason is None:reason='COMPLETED100'
    except torch.cuda.OutOfMemoryError as exc:
        reason='GPU_OUT_OF_MEMORY_ENGINEERING';engineering=True;save('metrics/'+arm+'_EXCEPTION.json',dict(type=type(exc).__name__,message=str(exc)))
    except (FloatingPointError,RuntimeError)as exc:
        reason=str(exc);engineering=isinstance(exc,FloatingPointError)or not any(x in reason for x in ['MISSING_RGB_OR_DEPTH','MISSING_REFERENCE_DATA_TERM','INITIAL_'])
        save('metrics/'+arm+'_EXCEPTION.json',dict(type=type(exc).__name__,message=str(exc)))
    stopped=reason!='COMPLETED100'
    if stopped:
        model.load_state_dict(lastsafe);final=checkpoint(model,arm,lastsafe_step,'FINAL_LAST_SAFE')
        # Retain actual last safe source/geometry evidence even off the5-step schedule.
        if lastsafe_step%5:
            rr,cv=probe(model,arm,lastsafe_step,cells);u,ur=update_norm(model,initial);cv.update(elapsed_seconds=time.monotonic()-start,parameter_update_L2=u,parameter_update_relative=ur)
            append_table('metrics/PER_REFERENCE_METRICS.csv',rr);append_table('metrics/TRAINING_CURVES.csv',[cv]);append_table('metrics/COVERAGE_HISTORY.csv',[{k:r[k] for k in ['arm','step','source','split','observed_N','front_hit_N','miss_N','coverage','status']} for r in rr])
    else:final=checkpoint(model,arm,100,'FINAL')
    u,ur=update_norm(model,initial);record=dict(arm=arm,status='TRAINING_STOPPED' if stopped else 'COMPLETED100',reason=reason,engineering_error=engineering,
        optimizer_step_N=updates,last_safe_step=lastsafe_step,final_checkpoint=final,elapsed_seconds=time.monotonic()-start,
        initial_FP32_SHA256=meta['FP32_SHA256'],final_parameter_SHA256=parameter_hash(model),parameter_update_L2=u,parameter_update_relative=ur,
        selected_cells=cells,peak_allocated_bytes=memory_guard(),source_view_N=3,train_rays_per_step=192,monitor_never_used_for_training=True)
    save('metrics/'+arm+'_RUN.json',record);print('ARM_FINAL',record,flush=True)
    del opt,model,lastsafe,initial;gc.collect();torch.cuda.empty_cache()
    if engineering:raise SystemExit(3)

if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1] in ['A','B'];run(sys.argv[1])
