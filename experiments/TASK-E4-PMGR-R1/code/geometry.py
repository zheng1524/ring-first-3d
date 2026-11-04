"""Live nine-parameter ellipsoid plus transported fixed spectral detail."""
from inputs import *
import torch
from scipy.linalg import eigh,null_space
from legacy_mesh import laplace
torch.set_num_threads(2)
def torch_vertices(q,unit,R0,a0,n0,phi):
    c=q[:3];v=q[3:6];z=v[0]*0;K=torch.stack([z,-v[2],v[1],v[2],z,-v[0],-v[1],v[0],z]).reshape(3,3);Q=R0@torch.matrix_exp(K);a=torch.exp(q[6:9]);local=unit*a
    if len(q)>9:local=local+n0*(phi@q[9:])[:,None]*(a/a0)
    return local@Q.T+c
class Model:
    def __init__(self,row,basis=None):
        self.historical=row;self.R0=np.array(row['R0']);mesh=trimesh.creation.icosphere(subdivisions=3);self.unit=np.asarray(mesh.vertices);self.F=np.asarray(mesh.faces);self.reference=np.array(row['p']);self.a0=np.exp(self.reference[6:9]);self.n0=self.unit/self.a0;self.n0/=np.linalg.norm(self.n0,axis=1)[:,None];self.phi=np.zeros((len(self.unit),0))if basis is None else basis
    def set_reference(self,p,phi):
        self.reference=np.array(p);self.a0=np.exp(self.reference[6:9]);self.n0=self.unit/self.a0;self.n0/=np.linalg.norm(self.n0,axis=1)[:,None];self.phi=phi
    def vertices(self,q,jac=False):
        d=len(q)-9;args=[torch.as_tensor(a,dtype=torch.float64)for a in [self.unit,self.R0,self.a0,self.n0,self.phi[:,:d]]];t=torch.as_tensor(q,dtype=torch.float64)
        fn=lambda x:torch_vertices(x,*args)
        V=fn(t).detach().numpy()
        if not jac:return V
        J=torch.func.jacfwd(fn)(t).detach().numpy();return V,J
    def build_basis(self,p,n=32):
        V,J=self.vertices(p,True);L,m,_=laplace(V,self.F);c,Q,a=decode(p,self.R0);norm=(self.unit/a)@Q.T;norm/=np.linalg.norm(norm,axis=1)[:,None];g=(J*norm[:,:,None]).sum(1);U,s,_=np.linalg.svd(np.sqrt(m)[:,None]*g,full_matrices=False);old=U[:,s>s[0]*1e-8];Z=null_space(old.T);A=(L.toarray()/np.sqrt(m)[:,None])/np.sqrt(m)[None,:];val,vec=eigh(Z.T@A@Z,subset_by_index=[0,n-1]);phi=(Z@vec)/np.sqrt(m)[:,None]
        for k in range(n):
            if phi[np.argmax(abs(phi[:,k])),k]<0:phi[:,k]*=-1
        phi/=abs(phi).max(0);self.set_reference(p,phi);self.frequency=val;return dict(phi=phi,frequency=val,mass=m,V_reference=V,n_reference=norm,F=self.F,geometric_tangent_rank=old.shape[1],projected_constraint_eigensolve=True)
