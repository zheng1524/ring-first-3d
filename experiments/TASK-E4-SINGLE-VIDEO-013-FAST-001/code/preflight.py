"""Zero optimizer steps: original013 vs view-streamed gradient, then32view VRAM."""
from stream_objective import Objective,Full013
from stream_objective import *
import argparse
def main():
 p=argparse.ArgumentParser();p.add_argument('--memory-only',action='store_true');a=p.parse_args();guard_optimizer();c=Case('G01');ch=FreeVertices(c);ch.total_trust_D=1.;q=torch.zeros((ch.N,3),device=device,dtype=torch.float64,requires_grad=True);stream=Objective(c,ch);stream.attempt=40
 if not a.memory_only:
  original=Full013(c,ch);original.attempt=40;start=time.time();loss,parts=original(q);loss.backward();g=q.grad.detach().clone();v=float(loss.detach());q.grad=None;v2,_=stream.gradient(q);g2=q.grad.detach().clone();diff=float((g-g2).norm()/g.norm().clamp_min(1e-20));cos=float(torch.nn.functional.cosine_similarity(g.ravel(),g2.ravel(),dim=0));value_rel=abs(float(v2)-v)/max(abs(v),1e-20);finite=bool(torch.isfinite(g).all()and torch.isfinite(g2).all());rec=dict(mode='original013_vs_streamed_same_initial_same_FIT',relative_gradient_error=diff,gradient_cosine=cos,relative_objective_error=value_rel,finite=finite,predeclared_relative_gradient_tolerance=1e-3,predeclared_cosine_min=.999999,predeclared_objective_tolerance=1e-5,optimizer_updates=0,GT_used=False,seconds=time.time()-start);rec['pass']=finite and diff<=1e-3 and cos>=.999999 and value_rel<=1e-5;save('metrics/MEMORY_ADAPTER_EQUIVALENCE.json',rec);print(rec,flush=True);assert rec['pass'],'Preserve failed numeric check; do not relax its preregistered tolerance'
 else:
  torch.cuda.reset_peak_memory_stats();start=time.time();v,_=stream.gradient(q);torch.cuda.synchronize();rec=dict(mode='32view_original013_objective_streamed_backward',FIT_N=len(c.fit),finite=bool(torch.isfinite(q.grad).all()and torch.isfinite(v)),gradient_norm=float(q.grad.norm()),peak_allocated_bytes=torch.cuda.max_memory_allocated(),seconds=time.time()-start,optimizer_updates=0,GT_used=False);save('metrics/VRAM_PREFLIGHT.json',rec);print(rec,flush=True);assert rec['finite']
if __name__=='__main__':main()
