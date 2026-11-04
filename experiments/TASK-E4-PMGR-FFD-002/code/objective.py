"""Fixed-pixel differentiable silhouette, native relative depth and soft XYZ.
No per-source veto and no prediction-dependent Mask denominator.
"""
from inputs import *
from renderer import Renderer,tensor
from data import Data
from collision import Collision
import torch
import torch.nn.functional as TF

def pseudo(x):return torch.sqrt(1+x*x)-1
class Objective:
    def __init__(self,scene,body,data=None):
        self.scene=scene;self.body=body;self.data=Data(scene)if data is None else data;self.renderer=Renderer(scene);self.col=Collision(scene)
        self.V0=body.vertices(body.p);mesh=trimesh.Trimesh(self.V0,body.F,process=False);self.edges=mesh.edges_unique;self.adj=mesh.face_adjacency;self.neighbors=[np.unique(self.edges[(self.edges==i).any(1)])for i in range(len(self.V0))]
        L=np.eye(len(self.V0))
        for i,nb in enumerate(self.neighbors):
            nb=nb[nb!=i];L[i,nb]=-1/len(nb)
        self.L=tensor(L);self.ix=torch.as_tensor(self.edges,device='cuda',dtype=torch.long);self.F=torch.as_tensor(body.F,device='cuda',dtype=torch.long)
        self.ring_points=self.col.sample;rt=mesh_scene(self.V0,body.F);sd=rt.compute_signed_distance(o3d.core.Tensor(self.ring_points.astype(np.float32))).numpy();self.barrier_indices=np.flatnonzero(sd<.5)
    def native_terms(self,V,Vnp,rt,cid):
        d=self.data.views[cid];o=d['o'];rays=d['rays'];hit=rt.cast_rays(o3d.core.Tensor(rays.astype(np.float32)));fid=hit['primitive_ids'].numpy().astype(int);safe=np.clip(fid,0,len(self.body.F)-1);valid=np.isfinite(hit['t_hit'].numpy())&(hit['t_hit'].numpy()>0)&(hit['t_hit'].numpy()<=o['cad']+.05)
        tri=V[torch.as_tensor(self.body.F[safe],device=V.device)];normal=torch.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0],dim=1);direc=tensor(rays[:,3:]);den=(normal*direc).sum(1);den=torch.where(abs(den)>1e-8,den,torch.ones_like(den));z=(normal*(tri[:,0]-tensor(rays[:,:3]))).sum(1)/den
        pp=o['pairs'];good=valid[pp].all(1);p=torch.as_tensor(pp[good],device=V.device);delta=tensor(o['delta'][good]);er=(z[p[:,0]]-z[p[:,1]]-delta)/.25;depth=pseudo(er).sum()/len(pp)
        cp=rt.compute_closest_points(o3d.core.Tensor(o['X'].astype(np.float32)));fi=cp['primitive_ids'].numpy().astype(int);b=cp['primitive_uvs'].numpy();w=tensor(np.c_[1-b.sum(1),b]);P=(V[torch.as_tensor(self.body.F[fi],device=V.device)]*w[:,:,None]).sum(1);ds=((P-tensor(o['X']))**2).sum(1)/.5**2;hero=torch.log1p(ds).mean()
        return depth,hero,dict(native_fixed_N=512,native_hit_N=int(valid.sum()),native_miss_N=int((~valid).sum()),relative_fixed_pair_N=256,relative_hit_pair_N=int(good.sum()),relative_depth_mm=stats(er.detach().cpu().numpy()*.25))
    def evaluate(self,q,stage='P2',gradient=True,aa=True,mask_only=False,return_images=False,source_subset=None):
        t=torch.tensor(q,dtype=torch.float32,device='cuda',requires_grad=gradient);V=self.body.vertices(t);Vnp=self.body.vertices(np.array(q));rt=mesh_scene(Vnp,self.body.F);terms=[];weights=[];per=[];images={}
        for cid in (self.data.ids if source_subset is None else source_subset):
            d=self.data.views[cid];out=self.renderer.render(V,self.body.F,d['K'],d['s']['T'],aa=aa);a=out['alpha'];y=d['target'];w=d['weight'];known=d['known'];prob=.001+.998*a
            bce=(-(y*torch.log(prob)+(1-y)*torch.log1p(-prob))*w).sum();dice=1-(2*(a*y*known).sum()+1)/((a*known).sum()+(y*known).sum()+1);distance=((a-y)*d['sdf']*w).sum();mask=bce+.5*dice+.1*distance
            if mask_only:depth=V.sum()*0;hero=V.sum()*0;diag={}
            else:depth,hero,diag=self.native_terms(V,Vnp,rt,cid)
            view=mask+.3*depth+.05*hero;tau=1. if GATE[cid]['qualification']=='CONDITIONAL_USABLE'else .5;soft=.2*view+.8*tau*torch.log1p(view/tau)
            weight=self.data.weights[cid]*(1. if stage!='P1'or cid in protocol()['scenes'][self.scene]['P1']else .5);terms.append(soft);weights.append(weight)
            hard=out['hard'].detach().cpu().numpy();kn=d['known_np'];tar=d['target_np'];per.append(dict(source=cid,Mask=float(mask.detach()),BCE=float(bce.detach()),Dice=float(dice.detach()),distance=float(distance.detach()),Depth=float(depth.detach()),HERO=float(hero.detach()),raw_objective=float(view.detach()),retreat_derivative=float((.2+.8/(1+view/tau)).detach()),fixed_known_N=int(kn.sum()),fixed_foreground_N=int((tar&kn).sum()),fixed_Mask_hit_N=int((hard&tar&kn).sum()),fixed_Mask_miss_N=int((tar&~hard&kn).sum()),outside_N=int((hard&~tar&kn).sum()),IoU=float((hard&tar&kn).sum()/max(1,((hard|tar)&kn).sum())),**diag))
            if return_images:images[cid]=dict(alpha=a.detach().cpu().numpy(),hard=hard,z=out['z'].detach().cpu().numpy(),target=tar,known=kn)
        E=sum(v*w for v,w in zip(terms,weights))/sum(weights);dataE=E;regular=V.sum()*0;barrier=V.sum()*0
        if not mask_only:
            base=self.body.vertices(torch.cat([t[:9],torch.zeros_like(t[9:])]))if len(t)>9 else V;disp=V-base;lap=(self.L@disp).square().mean();edge=torch.linalg.norm(V[self.ix[:,1]]-V[self.ix[:,0]],dim=1);eref=tensor(np.linalg.norm(self.V0[self.edges[:,1]]-self.V0[self.edges[:,0]],axis=1));strain=((edge/eref-1)**2).mean();pose=((t[:9]-tensor(self.body.p))/tensor([10,10,10,.5,.5,.5,.3,.3,.3])).square().mean();regular=.02*lap+.01*strain+.0005*pose
            if len(t)>9:regular=regular+.002*t[9:].square().sum()/96
            if len(self.barrier_indices):
                pts=self.ring_points[self.barrier_indices];cp=rt.compute_closest_points(o3d.core.Tensor(pts.astype(np.float32)));fi=cp['primitive_ids'].numpy().astype(int);b=cp['primitive_uvs'].numpy();w=tensor(np.c_[1-b.sum(1),b]);P=(V[torch.as_tensor(self.body.F[fi],device=V.device)]*w[:,:,None]).sum(1);sign=np.sign(rt.compute_signed_distance(o3d.core.Tensor(pts.astype(np.float32))).numpy());dist=torch.sqrt((P-tensor(pts)).square().sum(1)+1e-12)*tensor(sign);barrier=.0005*TF.softplus((.08-dist)/.03).square().mean()
            E=E+regular+barrier
        g=None
        if gradient:
            E.backward();g=t.grad.detach().cpu().double().numpy()
        return dict(E=float(E.detach()),data_E=float(dataE.detach()),reg=float(regular.detach()),barrier=float(barrier.detach()),g=g,V=Vnp,per_view=per,images=images,finite=bool(torch.isfinite(E).item()and(g is None or np.isfinite(g).all())))
