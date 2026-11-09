"""Depth-only thin adapter. Same discrete face choice and FP64 ray-plane derivative as prior D."""
from components import *
def robust(r):
 ab=r.abs();return torch.where(ab<1.,.5*r*r,ab-.5).clamp(max=9.5)
class D2Depth(Depth):
 def query(self,m,cid):
  a=self.obs[cid];T=a['T'];ray=a['ray'];rays=np.c_[np.broadcast_to(T[:3,3],ray.shape),ray@T[:3,:3].T].astype(np.float32);hit=self.rt.cast_rays(o3d.core.Tensor(rays));z0=hit['t_hit'].numpy().astype(float);fid=hit['primitive_ids'].numpy().astype(np.int64);valid=(fid<len(self.c.F))&np.isfinite(z0)&(z0>0)&(z0<a['cad']-.05)
  ids=tensor(np.clip(fid,0,len(self.c.F)-1),torch.int64);world=m.verts_packed().double()*self.c.scale+tensor(self.c.center,torch.float64);cam=(world-tensor(T[:3,3],torch.float64))@tensor(T[:3,:3],torch.float64);tri=cam[tensor(self.c.F,torch.int64)[ids]];n=torch.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0],dim=1);den=(n*a['ray_t']).sum(1);cos=den.abs()/(n.norm(dim=1)*a['ray_t'].norm(dim=1)).clamp_min(1e-30);stable=(cos.detach()>.001)&(n.norm(dim=1).detach()>2e-14);active=tensor(valid,torch.bool)&stable;safe=torch.where(stable,den,torch.ones_like(den));z=(n*tri[:,0]).sum(1)/safe
  return z,active,z0,fid
 def terms(self,m,cid,arm):
  a=self.obs[cid];z,active,z0,fid=self.query(m,cid);r=(z-a['z_t'])/.5;h=robust(r);cost=torch.where(active,h,torch.full_like(h,9.5));w=tensor(a['boundary_weight']if arm in['E2','E3']else np.ones(len(z)),torch.float64);absolute=(cost*w).sum()/w.sum().clamp_min(1e-12)
  pair=tensor(a['pairs'],torch.int64);pw=tensor(a['pair_weight'],torch.float64);rel=absolute*0
  if len(pair):
   good=active[pair[:,0]]&active[pair[:,1]];delta=(z[pair[:,0]]-z[pair[:,1]])-(a['z_t'][pair[:,0]]-a['z_t'][pair[:,1]]);rc=robust(delta/.5);rel=(torch.where(good,rc,torch.full_like(rc,9.5))*pw).sum()/pw.sum().clamp_min(1e-12)
  else:good=torch.zeros(0,device=device,dtype=torch.bool);delta=torch.empty(0,device=device,dtype=torch.float64)
  info=dict(source=cid,fixed_N=len(z),active_N=int(active.sum()),fixed_pair_N=len(pair),active_pair_N=int(good.sum()),absolute_loss=float(absolute.detach()),relative_loss=float(rel.detach()),raw_fixed_denominator_cost=float(cost.mean().detach()),weighted_fixed_denominator=float(w.sum()),depth_MAE_active_mm=float((z[active]-a['z_t'][active]).abs().mean().detach())if active.any()else None)
  return absolute,rel,info,dict(z=z,active=active,pair_delta=delta,pair_active=good,face_id=fid,z_O3D=z0)
