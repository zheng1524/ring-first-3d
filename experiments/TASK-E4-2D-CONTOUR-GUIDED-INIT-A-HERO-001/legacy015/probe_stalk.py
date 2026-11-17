"""FIT-only seed + exact component gradients at the common frozen Phase A final."""
from stalk import *
import argparse

def main():
 ap=argparse.ArgumentParser();ap.add_argument('case');a=ap.parse_args();guard_optimizer();c=Case(a.case);ch=FreeVertices(c);cfg=load(R/'config/ARM.json');obj=MultiObjective(c,ch,cfg['loss']);obj.attempt=40;q=torch.zeros((ch.N,3),device=device,dtype=torch.float64,requires_grad=True);names=['silhouette','missing','extra','contour','absolute','relative','prior'];GG={k:torch.zeros_like(q)for k in names};values={k:0. for k in names};obj.depth.begin(ch.mesh(q))
 def collect(k,t):
  values[k]+=float(t.detach());g=torch.autograd.grad(t,q,retain_graph=True,allow_unused=True)[0]
  if g is not None:GG[k].add_(g.detach())
 for cid in c.fit:
  m=ch.mesh(q);fr=c.fragments(m,cid);base,alpha,w,*_=c.aware(fr,cid,True);t=c.views[cid]['target'];fg=((1-alpha)**2*t).sum()/t.sum().clamp_min(1);known=w*(1-t);fp=(alpha**2*known).sum()/known.sum().clamp_min(1);cd,_=obj.contour(ch.vertices(q),cid);weight=obj.w[cid]
  for key,term in [('silhouette',weight*base),('missing',weight*.05*fg),('extra',weight*.05*fp),('contour',weight*.01*cd)]:collect(key,term)
  if cid in obj.depth.obs:
   ab,rel,_,_=obj.depth.terms(m,cid,'E3');collect('absolute',obj.dw[cid]*.01*ab);collect('relative',obj.dw[cid]*.01*rel)
 collect('prior',relative_total(obj.prior(ch.mesh(q))));total=sum(GG.values());value,parts=obj.compute(q,True);err=float((total-q.grad).norm()/q.grad.norm().clamp_min(1e-20));far,_=associations(obj,c.V);old=np.zeros(ch.N,bool)
 for _,d in local_normalized(ch,q,total):old|=d.norm(dim=1).detach().cpu().numpy()>0
 _,coverage=expanded_directions(ch,q.detach(),q.grad,obj);seed=make_seed(c,c.V,obj);save('inputs/'+a.case+'/STALK_SEED.json',seed)
 rows=[dict(component=k,weighted_value=values[k],gradient_norm=float(g.norm()),nonzero_vertex_N=int((g.norm(dim=1)>1e-14).sum()),finite=bool(torch.isfinite(g).all()))for k,g in GG.items()]
 rec=dict(case=a.case,rows=rows,source=asset(R/'inputs'/a.case/'INITIAL.npz'),far_associated_N=int(far.sum()),old_local_candidates_cover_far_N=int((far&old).sum()),expanded=coverage,additive_gradient_relative_error=err,additive_gradient_test_pass=err<1e-4,threshold=1e-4,failed_test_not_relabelled=True,seed_status=seed['status'],GT_read=False,optimizer_updates=0,unverified_correspondence=True)
 np.savez_compressed(R/'metrics'/(a.case+'_STALK_GRADIENTS.npz'),V=c.V,F=c.F,F_solid=c.F_solid,far=far,old_candidate=old,full_gradient=q.grad.detach().cpu().numpy(),**{k:g.cpu().numpy()for k,g in GG.items()});save('metrics/'+a.case+'_STALK_PROBE.json',rec)
 assert all(row['finite']for row in rows),'nonfinite component gradients'
 if seed['status']=='RESIDUAL_ASSOCIATION_PROXY':
  sc=StalkChart(c);z=torch.zeros(sc.parameter_shape,device=device,dtype=torch.float64,requires_grad=True);identity=float((sc.vertices(z)-tensor(c.V,torch.float64)).abs().max());derivatives=[]
  for i in range(11):
   dz=z.detach().clone();dz[3*sc.N+i]=.001;move=sc.vertices(dz).detach()-sc.vertices(z).detach();derivatives.append(dict(parameter=i,maximum_mm=float(move.norm(dim=1).max()),nonzero_vertex_N=int((move.norm(dim=1)>1e-12).sum())))
  co=MultiObjective(c,sc,cfg['loss']);co.attempt=40;vv,pp=co.compute(z,True);test=dict(identity_max_mm=identity,perturbation=.001,parameter_derivatives=derivatives,finite_full_gradient=bool(torch.isfinite(z.grad).all()),curve_gradient_norm=float(z.grad[3*sc.N:].norm()),free_residual_gradient_norm=float(z.grad[:3*sc.N].norm()),GT_read=False,optimizer_updates=0);save('metrics/'+a.case+'_CENTERLINE_PREFLIGHT.json',test);assert identity<1e-9 and test['finite_full_gradient'] and all(d['maximum_mm']>0 for d in derivatives),'centerline chart failure'
 print('STALK_PROBE_DONE',a.case,rec['far_associated_N'],rec['old_local_candidates_cover_far_N'],coverage,seed['status'],flush=True)
if __name__=='__main__':main()
