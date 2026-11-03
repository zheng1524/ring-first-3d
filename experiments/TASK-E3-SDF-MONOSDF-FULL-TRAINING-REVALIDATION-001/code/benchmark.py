"""Disposable resource measurement; never interpreted as sufficiently trained geometry."""
from official_adapter import *
import argparse,traceback,gc
def main(stage,arm):
    key=stage+'_'+arm;assert not (R/f'metrics/BENCHMARK_{key}.json').exists(),'DO_NOT_REPEAT_RESOURCE_ARM'
    p=protocol();torch.set_num_threads(2);torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False;torch.cuda.reset_peak_memory_stats();model=make_model();loss=ProjectLoss(arm);events=instrument(model);opt=torch.optim.Adam(model.parameters(),lr=5e-4,betas=(.9,.999),eps=1e-8);sources=p['stages'][stage]
    warm=p['resource_benchmark']['warmup_updates'];timed=p['resource_benchmark']['timed_updates'];rr=[];start=time.monotonic();updates=0;status='COMPLETED_RESOURCE_ONLY'
    save(f'provenance/BEFORE_BENCHMARK_{key}.json',dict(protocol=asset(R/'config/PREREGISTERED.json'),code=[asset(x)for x in(R/'code').glob('*.py')],source_inputs=load(R/'provenance/INPUT_FREEZE.json'),formal_training_updates=0,disposable_seed=p['seed']))
    try:
        for step in range(1,warm+timed+1):
            cid=sources[(step-1)%len(sources)];data,batch=packet(cid,step);opt.param_groups[0]['lr']=5e-4*min(1.,step/1000)*.1**(step/200000)
            torch.cuda.synchronize();t=time.monotonic();opt.zero_grad(set_to_none=True);output,terms=forward_and_loss(model,loss,data,batch);assert torch.isfinite(terms['loss']),'NONFINITE_LOSS';terms['loss'].backward()
            assert all(a.grad is None or torch.isfinite(a.grad).all()for a in model.parameters()),'NONFINITE_GRADIENT';opt.step();updates+=1;torch.cuda.synchronize();elapsed=time.monotonic()-t
            assert torch.isfinite(output['sdf']).all();assert (output['z_vals']>=batch['near']-1e-5).all()and(output['z_vals']<=batch['far']+1e-5).all(),'SAMPLER_LEFT_LEGAL_VISIBLE_INTERVAL'
            row=dict(stage=stage,arm=arm,step=step,source=cid,resource_only=True,timed=step>warm,step_seconds=elapsed,samples_per_ray=output['z_vals'].shape[1],loss=float(terms['loss'].detach()),lr=opt.param_groups[0]['lr'],beta_mm=float(model.density.get_beta().detach())*p['geometry']['mm_per_model_unit'],peak_allocated_MiB=torch.cuda.max_memory_allocated()/2**20,peak_reserved_MiB=torch.cuda.max_memory_reserved()/2**20)
            rr.append(row);table(f'metrics/BENCHMARK_{key}_STEPS.csv',rr);print('RESOURCE_STEP',key,step,'sec',round(elapsed,3),'MiB',round(row['peak_allocated_MiB'],1),flush=True);del output,terms,data,batch
    except (torch.cuda.OutOfMemoryError,AssertionError,RuntimeError)as e:
        status='ENGINEERING_INTERRUPTION_RESOURCE_ONLY';save(f'metrics/BENCHMARK_{key}_EXCEPTION.json',dict(error=type(e).__name__,message=str(e),traceback=traceback.format_exc(),updates=updates));print('BENCHMARK_INTERRUPTED',key,type(e).__name__,str(e),flush=True)
    values=[r['step_seconds']for r in rr if r['timed']];record=dict(stage=stage,arm=arm,status=status,formal_training_updates=0,resource_benchmark_updates=updates,observed_step_seconds=stats(values),elapsed_seconds=time.monotonic()-start,peak_allocated_MiB=torch.cuda.max_memory_allocated()/2**20,peak_reserved_MiB=torch.cuda.max_memory_reserved()/2**20,official_chain_calls=events,parameter_N=sum(a.numel()for a in model.parameters()),observed_complete_batch_rays=1024,scientific_conclusion='NOT_EVALUABLE_RESOURCE_TEST_ONLY',source_order=sources,CUDA_GPU=torch.cuda.get_device_name(),torch=torch.__version__,GT=False,read_files=sorted(ACCESSED),denials=DENIALS)
    save(f'metrics/BENCHMARK_{key}.json',record);print('RESOURCE_DONE',key,status,'median',record['observed_step_seconds']['median'],flush=True);del model,opt;gc.collect();torch.cuda.empty_cache()
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['single','three_CORE']);parser.add_argument('arm',choices=['M0','M1']);a=parser.parse_args();main(a.stage,a.arm)
