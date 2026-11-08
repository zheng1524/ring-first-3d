"""Same official PyTorch3D/RingAware renderer, memory-bounded exact view sum."""
from contour_objective import ContourDistance
from free_model import *

def weights(c,ids):
 videos={c.views[i]['meta']['video']for i in ids};out={}
 for vid in videos:
  vv=[i for i in ids if c.views[i]['meta']['video']==vid];blocks={c.views[i]['meta'].get('direction_block',0)for i in vv}
  for b in blocks:
   ii=[i for i in vv if c.views[i]['meta'].get('direction_block',0)==b]
   for i in ii:out[i]=1/len(videos)/len(blocks)/len(ii)
 return out

class MultiObjective:
 def __init__(self,c,ch,arm='D0_013'):
  self.c=c;self.ch=ch;self.arm=arm;self.attempt=0;self.prior=FrozenPrior(c);self.depth=D2Depth(c);self.contour=ContourDistance(c);self.w=weights(c,c.fit);self.dw={i:1/len(self.depth.obs)for i in self.depth.obs}
 def compute(self,q,gradient=False):
  if gradient:q.grad=None
  parts=dict(silhouette=0.,missing=0.,extra=0.,contour=0.,absolute=0.,relative=0.,prior=0.,total=0.);ramp=.25+.75*min(1.,self.attempt/40.)
  m=self.ch.mesh(q);self.depth.begin(m)
  # Each backward builds a fresh Mesh graph. This is the exact weighted sum,
  # without retaining all raster graphs or changing ray/image counts.
  for cid in self.c.fit:
   m=self.ch.mesh(q);fr=self.c.fragments(m,cid);base,alpha,w,*_=self.c.aware(fr,cid,True);t=self.c.views[cid]['target'];fg=((1-alpha)**2*t).sum()/t.sum().clamp_min(1);known=w*(1-t);fp=(alpha**2*known).sum()/known.sum().clamp_min(1);cd,_=self.contour(self.ch.vertices(q),cid)
   fpcoef=.1 if self.arm in ['D1_split','D3_combo']else .05;cdcoef=.02 if self.arm in ['D2_bidir','D3_combo']else .01
   loss=self.w[cid]*(base+ramp*(.05*fg+fpcoef*fp+cdcoef*cd))
   for k,z in [('silhouette',base),('missing',fg),('extra',fp),('contour',cd)]:parts[k]+=self.w[cid]*float(z.detach())
   if cid in self.depth.obs:
    a,b,_,_=self.depth.terms(m,cid,'E3');loss+=self.dw[cid]*(.01*a+.01*b);parts['absolute']+=self.dw[cid]*float(a.detach());parts['relative']+=self.dw[cid]*float(b.detach())
   parts['total']+=float(loss.detach())
   if gradient:loss.backward()
  reg=relative_total(self.prior(self.ch.mesh(q)));parts['prior']=float(reg.detach());parts['total']+=parts['prior']
  if gradient:reg.backward()
  return parts['total'],parts
