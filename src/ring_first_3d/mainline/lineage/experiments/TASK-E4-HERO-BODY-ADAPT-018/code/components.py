"""Thin additions to the inherited renderer: P0-relative priors and audited axial-depth term."""
from p3d import *
from evaluate import pointcast
import open3d as o3d

class RelativePrior:
    def __init__(self,c):
        self.c=c;self.v0=c.base.verts_packed().detach();self.edges=c.base.edges_packed();self.length0=(self.v0[self.edges[:,0]]-self.v0[self.edges[:,1]]).norm(dim=1).detach()
        self.L=c.base.laplacian_packed().detach();self.lap0=torch.sparse.mm(self.L,self.v0).detach()
        supported=np.zeros(len(c.V),bool);body=scene(c.V,c.F);cad=scene(c.ringV,c.ringF)
        for cid in c.fit:
            d=c.views[cid];uv,z,cz=pointcast(cad,c.V,d['K'],d['T']);_,_,bz=pointcast(body,c.V,d['K'],d['T']);px=np.clip(np.rint(uv).astype(int),[0,0],[639,359]);inside=(z>0)&(uv[:,0]>=0)&(uv[:,0]<640)&(uv[:,1]>=0)&(uv[:,1]<360)
            supported|=inside&(d['labels'][px[:,1],px[:,0]]==1)&(z<cz)&(abs(bz-z)<.05)
        self.unknown=tensor(~supported,torch.bool)
        np.savez_compressed(R/'local_results'/(c.name+'_P0_SUPPORT.npz'),supported=supported,unknown=~supported,vertex_id=np.arange(len(supported)))
    def __call__(self,m):
        v=m.verts_packed();e=(v[self.edges[:,0]]-v[self.edges[:,1]]).norm(dim=1)
        return dict(edge=((e-self.length0)**2).mean(),laplacian=((torch.sparse.mm(self.L,v)-self.lap0)**2).sum(1).mean(),normal=mesh_normal_consistency(m),unsupported=((v[self.unknown]-self.v0[self.unknown])**2).sum(1).mean()if self.unknown.any()else v.sum()*0.)

class Depth:
    def __init__(self,c):
        self.c=c;self.obs={};self.cfg=load(R/'config/PROTOCOL.json')['depth'];self.rt=None
        ring=scene(c.ringV,c.ringF)
        for cid in c.fit:
            if not (R/'depth_observations'/(cid+'.npz')).exists():continue
            a=dict(np.load(R/'depth_observations'/(cid+'.npz')));K=a['K'];T=a['T'];ray=np.c_[a['uv'],np.ones(len(a['uv']))]@np.linalg.inv(K).T
            X=(ray*a['z'][:,None])@T[:3,:3].T+T[:3,3];_,_,cad=pointcast(ring,X,K,T)
            self.obs[cid]=dict(a,ray=ray,ray_t=tensor(ray,torch.float64),z_t=tensor(a['z'],torch.float64),w_t=tensor(a['weight'],torch.float64),cad=cad)
    def begin(self,m):
        self.m=m;V,F=self.c.mm(m);self.rt=scene(V,F)
    def loss(self,m,cid):
        a=self.obs[cid];T=a['T'];ray=a['ray'];rays=np.c_[np.broadcast_to(T[:3,3],ray.shape),ray@T[:3,:3].T].astype(np.float32)
        hit=self.rt.cast_rays(o3d.core.Tensor(rays));z0=hit['t_hit'].numpy().astype(float);fid=hit['primitive_ids'].numpy().astype(np.int64);valid=(fid<len(self.c.F))&np.isfinite(z0)&(z0>0)&(z0<a['cad']-.05)
        ids=tensor(np.clip(fid,0,len(self.c.F)-1),torch.int64);world=m.verts_packed().double()*self.c.scale+tensor(self.c.center,torch.float64);cam=(world-tensor(T[:3,3],torch.float64))@tensor(T[:3,:3],torch.float64);tri=cam[tensor(self.c.F,torch.int64)[ids]]
        n=torch.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0],dim=1);den=(n*a['ray_t']).sum(1);cos=den.abs()/(n.norm(dim=1)*a['ray_t'].norm(dim=1)).clamp_min(1e-30);stable=(cos.detach()>.001)&(n.norm(dim=1).detach()>2e-14)
        active=tensor(valid,torch.bool)&stable;safe=torch.where(stable,den,torch.ones_like(den));z=(n*tri[:,0]).sum(1)/safe
        r=(z-a['z_t'])/.5;ab=r.abs();h=torch.where(ab<1.,.5*r*r,ab-.5).clamp(max=9.5);terms=torch.where(active,h,torch.full_like(h,9.5));loss=(terms*a['w_t']).sum()/a['w_t'].sum().clamp_min(1e-12)
        info=dict(source=cid,fixed_N=len(fid),mesh_first_hit_N=int(valid.sum()),active_N=int(active.sum()),miss_or_occluded_N=int((~valid).sum()),grazing_or_degenerate_N=int((tensor(valid,torch.bool)&~stable).sum()),capped_active_N=int((active&(ab.detach()>=10)).sum()),depth_loss=float(loss.detach()),active_depth_MAE_mm=float((z[active]-a['z_t'][active]).abs().mean().detach())if active.any()else None,O3D_axial_agreement_max_mm=float((z[active].detach()-tensor(z0[valid&stable.cpu().numpy()],torch.float64)).abs().max())if active.any()else None)
        return loss,info

def relative_total(pr):return pr['edge']+pr['laplacian']+.01*pr['normal']+.01*pr['unsupported']
