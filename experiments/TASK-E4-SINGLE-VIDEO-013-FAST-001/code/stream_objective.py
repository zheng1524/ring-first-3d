"""Exact013 A3 objective, one-view backward accumulation to bound VRAM.

Keep the original 1/Nfit depth divisor, shared identical raster outputs, frozen
P0 support, A3 ramp and every coefficient. No014 loss, depth normalization,
coarse chart, dense optimization guard, or pose correction.
"""
from contour_objective import Objective as Full013
from contour_objective import *
class Objective(Full013):
 def __call__(self,q):
  assert not torch.is_grad_enabled(),'Use gradient(q) for view-streamed backward'
  return self.compute(q,False)
 def gradient(self,q):return self.compute(q,True)
 def compute(self,q,backward):
  assert self.arm=='A3';N=len(self.c.fit);ramp=.25+.75*min(1.,self.attempt/40.);parts=dict(silhouette=0.,absolute=0.,relative=0.,prior=0.,total=0.,foreground_miss=0.,background_false=0.,contour_distance=0.,added_loss=0.,loss_ramp=ramp,depth=[],contour_info=[]);self.depth.begin(self.chart.mesh(q))
  for cid in self.c.fit:
   m=self.chart.mesh(q);fr=self.c.fragments(m,cid);sil,alpha,w,*_=self.c.aware(fr,cid,True);ab=sil*0;rel=sil*0
   if cid in self.depth.obs:
    ab,rel,rec,_=self.depth.terms(m,cid,'E3');parts['depth'].append(rec)
   t=self.c.views[cid]['target'];fg=((1-alpha)**2*t).sum()/t.sum().clamp_min(1);known=w*(1-t);bg=(alpha**2*known).sum()/known.sum().clamp_min(1);dist,rec=self.contour(self.chart.vertices(q),cid);parts['contour_info'].append(dict(source=cid,**rec));extra=ramp*(.05*(fg+bg)+.01*dist);loss=(sil+.01*ab+.01*rel+extra)/N
   for key,value in [('silhouette',sil),('absolute',ab),('relative',rel),('foreground_miss',fg),('background_false',bg),('contour_distance',dist),('added_loss',extra)]:parts[key]+=float(value.detach())/N
   parts['total']+=float(loss.detach())
   if backward:loss.backward()
  reg=relative_total(self.prior(self.chart.mesh(q)))
  if backward:reg.backward()
  parts['prior']=float(reg.detach());parts['total']+=parts['prior'];return tensor(parts['total'],torch.float64),parts
