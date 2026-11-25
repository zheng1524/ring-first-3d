"""PMGR cotan spectrum + base-preserving low-dimensional surface chart."""
from p3d import *
from pmgr_spectrum import laplace
from scipy.sparse.linalg import eigsh
from scipy import sparse

class Chart:
 def __init__(self,c):
  self.c=c;self.initial=np.array(c.V);self.F=c.F;self.Fs=c.F_solid;self.cap=bool(c.inferred.any());self.V0=tensor(c.V,torch.float64);self.n=np.array(trimesh.Trimesh(c.V,c.F,process=False).vertex_normals,copy=True);used=np.unique(c.F);cached=R/'inputs'/c.name/'CHART_BASIS.npz'
  if cached.exists():
   cache=np.load(cached);full=cache['Phi'];eigenvalues=cache['eigenvalues']
  else:
   mapping=np.full(len(c.V),-1,int);mapping[used]=np.arange(len(used));Lu,mass,areas=laplace(c.V[used],mapping[c.F]);eig,phi=eigsh(Lu,k=49,M=sparse.diags(mass),sigma=-1e-8,which='LM',v0=np.linspace(1,2,len(used)),tol=1e-9);order=np.argsort(eig);phi=phi[:,order[1:49]];phi/=np.max(abs(phi),axis=0);full=np.zeros((len(c.V),48));full[used]=phi;eigenvalues=eig[order[1:49]]
  self.Phi=tensor(full,torch.float64);self.D=float(np.ptp(c.V[used],axis=0).max());self.tau=float(np.clip(.0125*self.D,.075,.2));self.meta=None
  self.model=load(R/'inputs'/c.name/'C_INITIAL_MODEL.json');self.bs=load(R/'inputs'/c.name/'BASE_SELECTION.json');self.plane=np.asarray(self.bs['selected_plane']);self.origin=np.array(c.V[-1])if self.cap else c.V.mean(0)
  if self.cap:
   self.Q=np.asarray(self.model['meta']['base_Q']);self.Q[:,2]=self.plane[:3];q0=(c.V-self.origin)@self.Q;q0[:,2]=np.maximum(0,q0[:,2]);self.q0=tensor(q0,torch.float64);self.QT=tensor(self.Q.T,torch.float64);self.nl=tensor(self.n@self.Q,torch.float64);self.H=max(.1,float(np.quantile(q0[used,2],.95)));self.envelope=tensor(np.clip(q0[:,2]/self.H,0,1),torch.float64);lo=np.r_[-.1*self.D,-.1*self.D,-.15,-.15,-.15,-.1,np.full(48,-.5*self.H)];hi=-lo;self.units=np.r_[self.D,self.D,.1,.1,.1,.1,np.full(48,self.H)]
  else:
   self.H=self.D;self.nT=tensor(self.n,torch.float64);self.C=tensor(self.origin,torch.float64);lo=np.r_[np.full(3,-.1*self.D),np.full(3,-.15),np.full(48,-.5*self.D)];hi=-lo;self.units=np.r_[np.full(3,self.D),np.full(3,.1),np.full(48,self.D)]
  self.lo=lo;self.hi=hi;self.eigenvalues=eigenvalues
  if not cached.exists():save('inputs/'+c.name+'/CHART.json',dict(cap=self.cap,D_mm=self.D,H_mm=self.H,tau_mm=self.tau,eigenvalues=self.eigenvalues,parameter_lower=lo,parameter_upper=hi,modes=48,type_dispatch=False));np.savez_compressed(cached,Phi=full,eigenvalues=eigenvalues,normal=self.n,origin=self.origin,Q=self.Q if self.cap else np.eye(3))
 def vertices(self,q):
  a=self.Phi@q[6:]
  if self.cap:
   xy=(self.q0[:,:2]+a[:,None]*self.envelope[:,None]*self.nl[:,:2])*q[2:4].exp();cs=torch.cos(q[5]);sn=torch.sin(q[5]);rot=torch.stack([torch.stack([cs,sn]),torch.stack([-sn,cs])]);xy=xy@rot+q[:2];z=self.q0[:,2]*torch.exp(q[4]+a*self.nl[:,2]/self.H);local=torch.cat([xy,z[:,None]],1);return self.V0+(local-self.q0)@self.QT
  return self.V0+(self.V0-self.C)*(q[3:6].exp()-1)+q[:3]+self.nT*a[:,None]
 def mesh(self,q):return mesh((self.vertices(q)-tensor(self.c.center,torch.float64))/self.c.scale,self.F)
