"""Only objective/provider adapted; historical optimizer and guards execute verbatim."""
from pathlib import Path
import json
import numpy as np
from .correspondence import ExplicitContour
INSTANCE=None

def objective_class(legacy):
 class Objective:
  def __init__(self,c,ch,arm):
   global INSTANCE
   INSTANCE=self;self.c=c;self.ch=ch;self.attempt=0;self.arm=arm;self.prior=legacy.FrozenPrior(c);self.old=legacy.ContourDistance(c);self.w=legacy.weights(c,c.fit);self.explicit=ExplicitContour(c,self.old,json.loads((legacy.R/'config/CONTOUR.json').read_text()));self.folder=legacy.R/'contour_evidence';self.folder.mkdir();self.prev=None;self.prev_grad={};self.count=0
  def rebuild(self,q):self.explicit.rebuild(self.ch.vertices(q))
  def compute(self,q,gradient=False):
   import torch
   if gradient:q.grad=None;self.rebuild(q);self.count+=1
   elif not self.explicit.generation:self.rebuild(q)
   parts=dict(silhouette=0.,missing=0.,extra=0.,contour=0.,absolute=0.,relative=0.,prior=0.,total=0.,depth_disabled=True,explicit=self.arm=='A3',E_generation=self.explicit.generation);ramp=.25+.75*min(1.,self.attempt/40.);pergrad={};W=self.ch.vertices(q).detach().cpu().numpy()
   for cid in self.c.fit:
    m=self.ch.mesh(q);fr=self.c.fragments(m,cid);base,alpha,w,*_=self.c.aware(fr,cid,True);t=self.c.views[cid]['target'];fg=((1-alpha)**2*t).sum()/t.sum().clamp_min(1);known=w*(1-t);fp=(alpha**2*known).sum()/known.sum().clamp_min(1);V=self.ch.vertices(q);cd=self.explicit(V,cid)if self.arm=='A3'else self.old(V,cid)[0];loss=self.w[cid]*(base+ramp*(.05*fg+.05*fp+.01*cd))
    if gradient:
     cg=torch.autograd.grad(self.w[cid]*ramp*.01*cd,q,retain_graph=True)[0];vg=torch.autograd.grad(loss,q,retain_graph=True)[0];pergrad[cid]=(cg.detach().cpu().numpy(),vg.detach().cpu().numpy());loss.backward()
    for k,z in [('silhouette',base),('missing',fg),('extra',fp),('contour',cd)]:parts[k]+=self.w[cid]*float(z.detach())
    parts['total']+=float(loss.detach())
   reg=legacy.relative_total(self.prior(self.ch.mesh(q)));parts['prior']=float(reg.detach());parts['total']+=parts['prior']
   if gradient:
    reg.backward();self.record(W,pergrad,q);self.prev=W.copy();self.prev_grad=pergrad
   return parts['total'],parts
  def record(self,W,pergrad,q):
   stage=self.folder/('%04d'%self.count);stage.mkdir();np.savez_compressed(stage/'BODY.npz',V=W,F=self.c.F,F_solid=self.c.F_solid,parameters=q.detach().cpu().numpy());delta=np.zeros_like(W)if self.prev is None else W-self.prev;stats=np.linalg.norm(delta,axis=1);summ=[]
   for cid in self.c.fit:
    p=self.explicit.pairs.get(cid);cg,vg=pergrad[cid];previous=self.prev_grad.get(cid,(np.zeros_like(W),np.zeros_like(W)));contribution=-np.einsum('ij,ij->i',previous[0],delta);arrays=dict(contour_gradient=cg,full_view_gradient=vg,actual_shared_vertex_delta=delta,previous_contour_gradient=previous[0],descent_work=contribution)
    if p is not None:arrays.update(p)
    np.savez_compressed(stage/(cid+'.npz'),**arrays);summ.append(dict(id=cid,weight=self.w[cid],**self.explicit.records[cid],contour_gradient_norm=float(np.linalg.norm(cg)),view_gradient_norm=float(np.linalg.norm(vg)),previous_gradient_actual_descent_work=float(contribution.sum())))
   (stage/'SUMMARY.json').write_text(json.dumps(dict(attempt=self.attempt,E_generation=self.explicit.generation,stage=self.count,shared_vertices=True,all_FIT_refreshed=True,actual_previous_shared_step_MAE_mm=float(stats.mean()),actual_previous_shared_step_P95_mm=float(np.quantile(stats,.95)),actual_previous_shared_step_max_mm=float(stats.max()),views=summ),indent=2)+'\n')
  def finalize(self,q):
   self.rebuild(q);self.count+=1;self.record(self.ch.vertices(q).detach().cpu().numpy(),{cid:(np.zeros((self.ch.N,3)),np.zeros((self.ch.N,3)))for cid in self.c.fit},q)
 return Objective
