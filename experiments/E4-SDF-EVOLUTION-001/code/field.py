"""Metric scalar level set, trilinear sparse basis; no vertex optimization."""
from inputs import *
from scipy import sparse
from skimage.measure import marching_cubes

class Field:
    def __init__(self,origin,shape,h=.25):
        self.origin=np.asarray(origin,float);self.shape=tuple(shape);self.h=h
        self.points=np.stack(np.meshgrid(*[self.origin[k]+np.arange(self.shape[k])*h for k in range(3)],indexing='ij'),-1).reshape(-1,3)
        self.N=len(self.points)
    def basis(self,X):
        t=(np.asarray(X)-self.origin)/self.h;i=np.floor(t).astype(int)
        valid=((i>=0)&(i<np.array(self.shape)-1)).all(1)
        i=np.clip(i,0,np.array(self.shape)-2);f=np.clip(t-i,0,1);cols=[];vals=[]
        for a in [0,1]:
            for b in [0,1]:
                for c in [0,1]:
                    off=np.array([a,b,c]);cols.append(np.ravel_multi_index((i+off).T,self.shape));vals.append(np.prod(np.where(off,f,1-f),axis=1))
        return sparse.csr_matrix((np.stack(vals,1).ravel(),(np.repeat(np.arange(len(X)),8),np.stack(cols,1).ravel())),shape=(len(X),self.N)),valid
    def value(self,phi,X):
        B,v=self.basis(X);a=B@phi;a[~v]=np.nan;return a
    def gradient(self,phi):return np.stack(np.gradient(phi.reshape(self.shape),self.h,edge_order=2),-1).reshape(-1,3)
    def query_gradient(self,phi,X):
        """Exact derivative of the selected trilinear cell, not interpolated nodal FD gradients.

        At grid planes a C0 field has two one-sided derivatives. Choose the
        positive-side cell deterministically; no claim of a unique C1 normal.
        """
        t=(np.asarray(X)-self.origin)/self.h;i=np.floor(t).astype(int);i=np.clip(i,0,np.array(self.shape)-2);f=np.clip(t-i,0,1);out=np.zeros((len(X),3))
        for a in [0,1]:
            for b in [0,1]:
                for c in [0,1]:
                    off=np.array([a,b,c]);q=phi[np.ravel_multi_index((i+off).T,self.shape)];w=np.where(off,f,1-f)
                    for k in range(3):out[:,k]+=q*(1 if off[k]else-1)*np.prod(np.delete(w,k,axis=1),axis=1)/self.h
        return out
    def mesh(self,phi):
        V,F,_,_=marching_cubes(phi.reshape(self.shape).astype(np.float32),0.,spacing=(self.h,)*3,gradient_direction='ascent',allow_degenerate=False)
        V=V+self.origin;F=F.astype(np.int32)
        if trimesh.Trimesh(V,F,process=False).volume<0:F=F[:,[0,2,1]]
        return np.asarray(V,float),F
    def differences(self,active):
        """Three forward derivatives on the full grid; inactive increments are zero."""
        idx=np.arange(self.N).reshape(self.shape);out=[]
        for axis in range(3):
            lo=[slice(None)]*3;hi=lo.copy();lo[axis]=slice(None,-1);hi[axis]=slice(1,None)
            a=idx[tuple(lo)].ravel();b=idx[tuple(hi)].ravel();sel=active[a]|active[b];a=a[sel];b=b[sel];nr=len(a)
            D=sparse.csr_matrix((np.tile([-1.,1.],nr)/self.h,(np.repeat(np.arange(nr),2),np.c_[a,b].ravel())),shape=(nr,self.N));out.append(D)
        return out
    def centered(self,active):
        ij=np.stack(np.unravel_index(np.flatnonzero(active),self.shape),1);good=((ij>0)&(ij<np.array(self.shape)-1)).all(1);ij=ij[good];cent=np.ravel_multi_index(ij.T,self.shape);out=[]
        for axis in range(3):
            d=np.eye(3,dtype=int)[axis];a=np.ravel_multi_index((ij-d).T,self.shape);b=np.ravel_multi_index((ij+d).T,self.shape);nr=len(a)
            out.append(sparse.csr_matrix((np.tile([-.5,.5],nr)/self.h,(np.repeat(np.arange(nr),2),np.c_[a,b].ravel())),shape=(nr,self.N)))
        return cent,out

def signed(rt,P):return rt.compute_signed_distance(o3d.core.Tensor(np.asarray(P,np.float32)),nsamples=3).numpy().astype(float)
def volume(V,F):return float(trimesh.Trimesh(V,F,process=False).volume)
def project_jacobian(P,K,T):
    x=(P-T[:3,3])@T[:3,:3];q=x@K.T
    J=(K[None,:2,:]*q[:,2,None,None]-q[:,:2,None]*K[None,2:3,:])/q[:,2,None,None]**2
    return J@T[:3,:3].T
def snapshot(name,grid,phi,**meta):
    V,F=grid.mesh(phi);p=R/'local_results'/name;p.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(p/'FIELD.npz',origin=grid.origin,shape=grid.shape,h=grid.h,phi=phi,V=V,F=F)
    m=trimesh.Trimesh(V,F,process=False);m.export(p/'BODY_mm.ply');mm=m.copy();mm.vertices*=.001;mm.export(p/'BODY_m.glb')
    save('local_results/'+name+'/META.json',meta);return V,F
