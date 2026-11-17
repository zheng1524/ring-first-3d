"""Free world-mm vertices; only the cap rim normal and inferred center are constrained."""
from p3d import *
from components import RelativePrior,relative_total
from depth_terms import D2Depth
from safe_geometry import GeometryGuard
import copy

class FreeVertices:
 def __init__(self,c):
  self.c=c;self.V0=tensor(c.V,torch.float64);self.N=len(c.V);self.cap=bool(c.inferred.any());self.plane=np.asarray(load(R/'inputs'/c.name/'BASE_SELECTION.json')['selected_plane']);self.D=float(load(R/'inputs'/c.name/'CHART.json')['D_mm']);self.tau=float(load(R/'inputs'/c.name/'CHART.json')['tau_mm']);self.rim=tensor(c.boundary,torch.bool);self.n=tensor(self.plane[:3],torch.float64);self.used=np.unique(c.F);self.unused=np.setdiff1d(np.arange(self.N),self.used)
 def vertices(self,q):
  delta=q.reshape(self.N,3)
  if self.cap:
   delta=delta-torch.where(self.rim[:,None],(delta@self.n)[:,None]*self.n,torch.zeros_like(delta));V=self.V0+delta
   # The original closing center is inferred bookkeeping, not an observed degree of freedom.
   keep=torch.ones(self.N,device=device,dtype=torch.float64);keep[tensor(self.unused,torch.int64)]=0;center=(V[self.rim]-self.V0[self.rim]).mean(0);V=V*keep[:,None]+(self.V0+center)*(1-keep[:,None]);return V
  return self.V0+delta
 def mesh(self,q):return mesh((self.vertices(q)-tensor(self.c.center,torch.float64))/self.c.scale,self.c.F)

class FrozenPrior(RelativePrior):
 def __init__(self,c):
  path=R/'local_results'/(c.name+'_P0_SUPPORT.npz')
  if not path.exists():super().__init__(c);return
  self.c=c;self.v0=c.base.verts_packed().detach();self.edges=c.base.edges_packed();self.length0=(self.v0[self.edges[:,0]]-self.v0[self.edges[:,1]]).norm(dim=1).detach();self.L=c.base.laplacian_packed().detach();self.lap0=torch.sparse.mm(self.L,self.v0).detach();z=np.load(path);assert np.array_equal(z['vertex_id'],np.arange(len(c.V)));self.unknown=tensor(z['unknown'],torch.bool)

class Objective:
 def __init__(self,c,chart):self.c=c;self.chart=chart;self.prior=FrozenPrior(c);self.depth=D2Depth(c)
 def __call__(self,q):
  m=self.chart.mesh(q);sil=sum(self.c.loss(m,cid,'RingAware')for cid in self.c.fit)/len(self.c.fit);reg=relative_total(self.prior(m));ab=sil*0;rel=sil*0;info=[];self.depth.begin(m)
  for cid in self.c.fit:
   if cid not in self.depth.obs:continue
   a,b,rec,_=self.depth.terms(m,cid,'E3');ab+=a/len(self.c.fit);rel+=b/len(self.c.fit);info.append(rec)
  L=sil+reg+.01*ab+.01*rel
  return L,dict(silhouette=float(sil.detach()),absolute=float(ab.detach()),relative=float(rel.detach()),prior=float(reg.detach()),total=float(L.detach()),depth=info)

def state_equal(a,b):
 if isinstance(a,dict):return a.keys()==b.keys()and all(state_equal(a[k],b[k])for k in a)
 if isinstance(a,(tuple,list)):return len(a)==len(b)and all(state_equal(x,y)for x,y in zip(a,b))
 if torch.is_tensor(a):return torch.equal(a,b)
 return a==b
