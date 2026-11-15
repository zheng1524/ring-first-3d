from body_multi import *
import hero_objective018 as legacy

def main():
 # Exact 018 configuration switch: original source weights, original fixed miss cost, no new point/face terms.
 c=Case('G06');configure(c);ch=FreeVertices(c);q=torch.zeros((ch.N,3),device=device,dtype=torch.float64,requires_grad=True);legacy.ROOT=REPO/'experiments/TASK-E4-HERO-BODY-ADAPT-018';old=legacy.Objective018(c,ch,'TRUSTED');old.attempt=40;L,p=old.compute(q,True);g=q.grad.detach().clone()
 ss=[Source(s)for s in load(R/'config/SOURCES.json')if s['group']=='G06'and s['origin']=='018'];new=JointObjective(c,ch,ss)
 for s in ss:s.w=old.hero.w[s.rec['view_id']];new.native.obs[s.id]['miss']=old.hero.obs[s.rec['view_id']]['miss_cost']
 # All added geometry terms exactly disabled (empty correspondences).
 new.bind={s.id:dict(face=tensor([],torch.int64),weak=np.empty((0,2),int),denominator=1)for s in ss}
 ll,pp=new.compute(q,True);delta=float((q.grad-g).abs().max());ok=abs(L-ll)<1e-7 and delta<1e-7;save('metrics/BASELINE_REPRODUCTION.json',dict(PASS=ok,original_objective=L,reused_objective=ll,max_gradient_error=delta,original_sources=len(ss),new_modules_disabled=True,original_miss_cost=True,original_source_weights=True,official_raster_barycentric_native_depth=True));print('BASELINE',L,ll,delta,ok,flush=True);assert ok
if __name__=='__main__':main()
