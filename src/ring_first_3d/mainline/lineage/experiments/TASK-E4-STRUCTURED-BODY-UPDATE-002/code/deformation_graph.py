"""Deterministic intrinsic graph, SO(3) node transforms; no free vertex parameters."""
import numpy as np
import torch
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra

def so3(w):
    x,y,z=w.unbind(-1);o=torch.zeros_like(x)
    K=torch.stack([o,-z,y,z,o,-x,-y,x,o],-1).reshape(*w.shape[:-1],3,3)
    return torch.matrix_exp(K)

class DeformationGraph:
    def __init__(self,V,F,nodes=32,neighbors=4,device='cpu'):
        V=np.asarray(V,float);F=np.asarray(F,int);edges=np.unique(np.sort(np.r_[F[:,[0,1]],F[:,[1,2]],F[:,[2,0]]],1),axis=0)
        length=np.linalg.norm(V[edges[:,0]]-V[edges[:,1]],axis=1)
        G=coo_matrix((np.r_[length,length],(np.r_[edges[:,0],edges[:,1]],np.r_[edges[:,1],edges[:,0]])),shape=(len(V),len(V))).tocsr()
        active=np.unique(F);chosen=[int(active[0])];dist=dijkstra(G,indices=chosen[0]);D=[dist]
        for _ in range(min(nodes,len(active))-1):
            j=int(active[np.argmax(dist[active])]);chosen.append(j);row=dijkstra(G,indices=j);D.append(row);dist=np.minimum(dist,row)
        D=np.asarray(D);assert np.isfinite(D[:,active]).all(),'Disconnected initial graph'
        ids=np.argsort(D,axis=0)[:neighbors].T;ds=np.take_along_axis(D.T,ids,axis=1)
        # Inactive retained vertices inherit nearest physical node deterministically.
        bad=~np.isfinite(ds).all(1)
        if bad.any():
            eu=np.linalg.norm(V[bad,None]-V[np.array(chosen)][None],axis=2);ids[bad]=np.argsort(eu,axis=1)[:neighbors];ds[bad]=np.take_along_axis(eu,ids[bad],axis=1)
        scale=np.maximum(ds[:,-1:]*1.01,1e-8);weights=np.maximum(0,1-ds/scale)**2;weights/=weights.sum(1,keepdims=True)
        self.node_ids=np.array(chosen);self.weights_np=weights;self.vertex_nodes_np=ids
        dn=D[:,chosen];links=np.argsort(dn,axis=1)[:,1:neighbors+1];edge=np.unique(np.sort(np.c_[np.repeat(np.arange(len(chosen)),neighbors),links.ravel()],1),axis=0)
        self.edges_np=edge;self.device=device
        self.V=torch.as_tensor(V,dtype=torch.float64,device=device);self.g=self.V[self.node_ids]
        self.ids=torch.as_tensor(ids,device=device);self.weights=torch.as_tensor(weights,device=device)
        self.edges=torch.as_tensor(edge,device=device)
    def mesh(self,w,t):
        R=so3(w);g=self.g[self.ids];local=self.V[:,None]-g
        return (self.weights[...,None]*(torch.einsum('nkij,nkj->nki',R[self.ids],local)+g+t[self.ids])).sum(1)
    def energy(self,w,t):
        R=so3(w);a,b=self.edges.T
        e=torch.einsum('nij,nj->ni',R[a],self.g[b]-self.g[a])+self.g[a]+t[a]-self.g[b]-t[b]
        return (e*e).sum(1).mean()
