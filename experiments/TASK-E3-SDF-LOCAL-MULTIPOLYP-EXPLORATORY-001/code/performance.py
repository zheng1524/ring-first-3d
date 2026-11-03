"""Full real M1 gradients for resource timing, with zero optimizer updates."""
from official_adapter import *
import gc


def main():
    torch.set_num_threads(2);torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
    torch.cuda.reset_peak_memory_stats();model=make_model();loss=ProjectLoss('M1');events=instrument(model)
    initial={k:v.detach().clone()for k,v in model.state_dict().items()};records=[]
    for j,cid in enumerate(SOURCES):
        data,batch=packet(cid,100+j);model.zero_grad(set_to_none=True);torch.cuda.synchronize();start=time.monotonic()
        out,terms=forward_and_loss(model,loss,data,batch);assert torch.isfinite(terms['loss']);terms['loss'].backward()
        assert all(v.grad is None or torch.isfinite(v.grad).all()for v in model.parameters())
        torch.cuda.synchronize();seconds=time.monotonic()-start
        assert all(torch.equal(initial[k],v)for k,v in model.state_dict().items())
        records.append(dict(source=cid,forward_backward_seconds=seconds,optimizer_updates=0,
            peak_allocated_MiB=torch.cuda.max_memory_allocated()/2**20,
            batch_rays=1024,loss=float(terms['loss'].detach()),parameter_changes=0))
        del data,batch,out,terms;gc.collect();torch.cuda.empty_cache()
    table('metrics/PERFORMANCE.csv',records)
    save('metrics/PERFORMANCE.json',dict(scene=SCENE,records=records,full_official_chain_calls=events,
        formal_updates=0,unchanged=True,mean_seconds=float(np.mean([r['forward_backward_seconds']for r in records])),
        planning='add20-60percent CPU/input/checkpoint/extraction and Adam allowance; no convergence inference',GT=False))
    print('PERFORMANCE',SCENE,clean(records),flush=True)


if __name__=='__main__':main()
