from chart import *
from depth_terms import D2Depth
from components import RelativePrior,relative_total
from safe_geometry import GeometryGuard,points
from scipy.optimize import minimize,LinearConstraint,Bounds
import copy
import open3d as o3d

class Objective:
 def __init__(self,c,chart):self.c=c;self.chart=chart;self.prior=RelativePrior(c);self.depth=D2Depth(c)
 def __call__(self,q):
  m=self.chart.mesh(q);sil=sum(self.c.loss(m,cid,'RingAware')for cid in self.c.fit)/len(self.c.fit);pr=self.prior(m);reg=relative_total(pr);ab=sil*0;rel=sil*0;info=[];self.depth.begin(m)
  for cid in self.c.fit:
   if cid not in self.depth.obs:continue
   a,b,rec,_=self.depth.terms(m,cid,'E3');ab+=a/len(self.c.fit);rel+=b/len(self.c.fit);info.append(rec)
  L=sil+reg+.01*ab+.01*rel;return L,dict(silhouette=float(sil.detach()),absolute=float(ab.detach()),relative=float(rel.detach()),prior=float(reg.detach()),total=float(L.detach()),depth=info)

def active_contact_projection(chart,guard,q,delta,active):
 """One linearized feasible-direction QP; exact guard still decides every candidate."""
 V=chart.vertices(q).detach().cpu().numpy();P=points(V,guard.F,guard.edges);d=guard.ring_distance(V);ids=np.flatnonzero(d<chart.tau);ids=ids[np.argsort(d[ids])[:64]]
 if not len(ids):return None,dict(status='NO_ACTIVE_CONTACT_SAMPLES')
 cp=guard.rs.compute_closest_points(o3d.core.Tensor(P[ids].astype(np.float32)));close=cp['points'].numpy();norm=P[ids]-close;norm*=np.where(d[ids]<0,-1.,1.)[:,None];norm/=np.maximum(np.linalg.norm(norm,axis=1)[:,None],1e-12)
 x=q.detach().clone().requires_grad_();v=chart.vertices(x);T=torch.cat([v,v[tensor(guard.F,torch.int64)].mean(1),v[tensor(guard.edges,torch.int64)].mean(1)],0);rows=[]
 for i,n in zip(ids,norm):rows.append(torch.autograd.grad((T[int(i)]*tensor(n,torch.float64)).sum(),x,retain_graph=True)[0].detach().cpu().numpy()[active])
 A=np.array(rows);bound=np.maximum(np.minimum(guard.sd0[ids],0),np.minimum(guard.lastsd[ids],0))-guard.eps-d[ids];bound=np.minimum(bound,0);target=delta[active];units=chart.units[active];lo=chart.lo[active]-q.detach().cpu().numpy()[active];hi=chart.hi[active]-q.detach().cpu().numpy()[active];w=1/np.maximum(units,1e-5)**2
 result=minimize(lambda y:.5*np.sum((y-target)**2*w),np.zeros(len(active)),jac=lambda y:(y-target)*w,bounds=Bounds(lo,hi),constraints=[LinearConstraint(A,bound,np.full(len(bound),np.inf))],method='SLSQP',options=dict(maxiter=50,ftol=1e-12));rec=dict(status='PROJECTED'if result.success else'QP_FAILED',message=result.message,active_contact_N=len(ids),iterations=result.nit,max_linear_violation=float(np.maximum(0,bound-A@result.x).max()))
 if not result.success:return None,rec
 out=np.zeros_like(delta);out[active]=result.x;return out,rec

def state_equal(a,b):
 if isinstance(a,dict):return a.keys()==b.keys()and all(state_equal(a[k],b[k])for k in a)
 if isinstance(a,(list,tuple)):return len(a)==len(b)and all(state_equal(x,y)for x,y in zip(a,b))
 if torch.is_tensor(a):return torch.equal(a,b)
 return a==b
