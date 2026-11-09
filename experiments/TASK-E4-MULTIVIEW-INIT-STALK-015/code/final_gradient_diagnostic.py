"""Read-only weighted component gradients at the actual final parameters.
No reseeding, reinitialization, optimizer step, GT access or result selection.
"""
from stalk import *
import argparse

def main():
 ap=argparse.ArgumentParser();ap.add_argument('case');a=ap.parse_args();guard_optimizer();cfg=load(R/'config/ARM.json');c=Case(a.case);ch=StalkChart(c)if cfg['tag']=='Stalk-C'else FreeVertices(c);z=np.load(R/'local_results'/a.case/'FINAL.npz');q=tensor(z['parameters'],torch.float64).detach().clone().requires_grad_(True);obj=MultiObjective(c,ch,cfg['loss']);obj.attempt=int(z['attempt']);names=['silhouette','missing','extra','contour','absolute','relative','prior'];GG={k:torch.zeros_like(q)for k in names};values={k:0. for k in names};obj.depth.begin(ch.mesh(q));ramp=.25+.75*min(1.,obj.attempt/40.)
 def collect(k,t):
  values[k]+=float(t.detach());d=torch.autograd.grad(t,q,retain_graph=True,allow_unused=True)[0]
  if d is not None:GG[k]+=d.detach()
 for cid in c.fit:
  m=ch.mesh(q);fr=c.fragments(m,cid);base,alpha,w,*_=c.aware(fr,cid,True);target=c.views[cid]['target'];fg=((1-alpha)**2*target).sum()/target.sum().clamp_min(1);known=w*(1-target);fp=(alpha**2*known).sum()/known.sum().clamp_min(1);cd,_=obj.contour(ch.vertices(q),cid);ww=obj.w[cid]
  for k,t in [('silhouette',ww*base),('missing',ww*ramp*.05*fg),('extra',ww*ramp*.05*fp),('contour',ww*ramp*.01*cd)]:collect(k,t)
  if cid in obj.depth.obs:
   ab,rel,_,_=obj.depth.terms(m,cid,'E3');collect('absolute',obj.dw[cid]*.01*ab);collect('relative',obj.dw[cid]*.01*rel)
 collect('prior',relative_total(obj.prior(ch.mesh(q))));total=sum(GG.values());obj.compute(q,True);image=sum(GG[k]for k in ['silhouette','missing','extra','contour']);depth=GG['absolute']+GG['relative'];cos=lambda p,d:float((p*d).sum()/(p.norm()*d.norm()).clamp_min(1e-30));rows=[dict(component=k,weighted_value=values[k],gradient_norm=float(g.norm()),finite=bool(torch.isfinite(g).all()))for k,g in GG.items()];err=float((total-q.grad).norm()/q.grad.norm().clamp_min(1e-20));rec=dict(case=a.case,arm=cfg['tag'],rows=rows,actual_attempt=obj.attempt,gradient_units='objective_per_chart_coordinate; all mm for A/B, mixed curve/residual coordinates for C; do not compare raw C norm to A/B',image_depth_gradient_cosine=cos(image,depth),image_prior_gradient_cosine=cos(image,GG['prior']),additivity_relative_error=err,additivity_threshold=1e-4,additivity_pass=err<1e-4,optimizer_updates=0,GT_read=False,frozen_prediction=asset(R/'local_results'/a.case/'FINAL.npz'));save('metrics/'+a.case+'_FINAL_COMPONENT_GRADIENTS.json',rec);np.savez_compressed(R/'metrics'/(a.case+'_FINAL_COMPONENT_GRADIENTS.npz'),parameters=q.detach().cpu().numpy(),V=z['V'],F=z['F'],**{k:g.cpu().numpy()for k,g in GG.items()});assert all(row['finite']for row in rows);print('FINAL_COMPONENT_GRADIENTS',a.case,cfg['tag'],rec['image_prior_gradient_cosine'],flush=True)
if __name__=='__main__':main()
