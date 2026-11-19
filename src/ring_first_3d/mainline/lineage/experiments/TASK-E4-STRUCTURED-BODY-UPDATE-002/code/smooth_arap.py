"""Oehri et al.2025 Eq(1)-(5): spokes/rims, mixed Voronoi mass, edge-only SVD.
Graph-restricted autograd global step, NOT the original unrestricted linear solve.
"""
import numpy as np
import torch

class SmoothARAP:
    def __init__(self,V,F,lam=.7,device='cpu'):
        V=np.asarray(V,float);F=np.asarray(F,int);tri=V[F]
        double=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1);area=double*.5
        cot=np.stack([np.einsum('ni,ni->n',tri[:,(i+1)%3]-tri[:,i],tri[:,(i+2)%3]-tri[:,i])/np.maximum(double,1e-20)for i in range(3)],1)
        M=np.zeros(len(V));L=np.zeros((len(V),len(V)));roots=[];ea=[];eb=[];ew=[]
        for fi,f in enumerate(F):
            if (cot[fi]<0).any():
                a=np.full(3,area[fi]/4);a[np.argmin(cot[fi])]=area[fi]/2
            else:
                a=np.array([(np.sum((tri[fi,i]-tri[fi,(i+1)%3])**2)*cot[fi,(i+2)%3]+np.sum((tri[fi,i]-tri[fi,(i+2)%3])**2)*cot[fi,(i+1)%3])/8 for i in range(3)])
            M[f]+=a
            for j in range(3):
                x,y=f[(j+1)%3],f[(j+2)%3];c=cot[fi,j]/2
                L[x,x]+=c;L[y,y]+=c;L[x,y]-=c;L[y,x]-=c
                for root in f:roots.append(root);ea.append(x);eb.append(y);ew.append(cot[fi,j])
        self.lam=lam;self.mass=torch.as_tensor(M,dtype=torch.float64,device=device)
        self.L=torch.as_tensor(L,dtype=torch.float64,device=device);self.V=torch.as_tensor(V,dtype=torch.float64,device=device)
        self.root=torch.as_tensor(roots,device=device);self.a=torch.as_tensor(ea,device=device);self.b=torch.as_tensor(eb,device=device);self.w=torch.as_tensor(ew,dtype=torch.float64,device=device)
        self.refedge=self.V[self.b]-self.V[self.a];self.ref_lap=(self.L@self.V)/self.mass.clamp_min(1e-20)[:,None]
    @torch.no_grad()
    def rotations(self,V):
        edge=V[self.b]-V[self.a];cov=torch.zeros((len(V),3,3),dtype=V.dtype,device=V.device)
        cov.index_add_(0,self.root,self.w[:,None,None]*self.refedge[:,:,None]*edge[:,None,:])
        U,_,VH=torch.linalg.svd(cov);W=VH.transpose(-1,-2);fix=torch.ones((len(V),3),dtype=V.dtype,device=V.device);fix[:,-1]=torch.linalg.det(W@U.transpose(-1,-2))
        R=(W*fix[:,None,:])@U.transpose(-1,-2)
        R[self.mass==0]=torch.eye(3,dtype=V.dtype,device=V.device)
        return R.detach()
    def energies(self,V,R):
        edge=V[self.b]-V[self.a];re=torch.einsum('nij,nj->ni',R[self.root],self.refedge)
        arap=(self.w*((edge-re)**2).sum(1)).sum()/3
        lap=(self.L@V)/self.mass.clamp_min(1e-20)[:,None];rl=torch.einsum('nij,nj->ni',R,self.ref_lap)
        smooth=(self.mass*((lap-rl)**2).sum(1)).sum()
        return arap,smooth,(1-self.lam)*arap+self.lam*smooth
