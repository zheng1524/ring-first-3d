"""Native-mask bidirectional distance to genuinely moving apparent-contour edges.
Discrete edge/visibility and nearest-neighbour assignments are recomputed, detached.
Only world vertices and their projected coordinates carry derivatives.
"""
from free_model import Objective as OriginalObjective
from free_model import *
from scipy.ndimage import distance_transform_edt
import torch.nn.functional as tf

class ContourDistance:
 def __init__(self,c):
  self.c=c;F=c.F;edges=np.sort(np.concatenate([F[:,[0,1]],F[:,[1,2]],F[:,[2,0]]]),axis=1);faces=np.tile(np.arange(len(F)),3);u,inv=np.unique(edges,axis=0,return_inverse=True);adj=np.full((len(u),2),-1,int)
  for i,k in enumerate(inv):adj[k,0 if adj[k,0]<0 else 1]=faces[i]
  self.edges=u;self.adj=adj;self.data={};self.last={}
  for cid in c.fit:
   d=c.views[cid];target=d['labels']==1;ct=contour(target);cm=np.ones(target.shape,bool);xy=np.rint(ct).astype(int);cm[xy[:,1],xy[:,0]]=False;dt=distance_transform_edt(cm);ids=np.linspace(0,len(ct)-1,min(256,len(ct))).astype(int);self.data[cid]=(tensor(dt[None,None],torch.float64),tensor(ct[ids],torch.float64))
 def __call__(self,V,cid):
  c=self.c;d=c.views[cid];T=d['T'];W=V.detach().cpu().numpy();tri=W[c.F];n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);front=(n*(T[:3,3]-tri.mean(1))).sum(1)>0;ad=self.adj;take=(ad[:,1]<0)|(front[ad[:,0]]!=front[np.maximum(ad[:,1],0)]);ed=self.edges[take]
  if not len(ed):return V.sum()*0,dict(contour_samples=0)
  eid=np.repeat(ed,3,axis=0);tt=np.tile([.2,.5,.8],len(ed));P=V[tensor(eid[:,0],torch.int64)]*(1-tensor(tt,torch.float64))[:,None]+V[tensor(eid[:,1],torch.int64)]*tensor(tt,torch.float64)[:,None]
  cam=(P-tensor(T[:3,3],torch.float64))@tensor(T[:3,:3],torch.float64);pix=cam@tensor(d['K'].T,torch.float64);uv=pix[:,:2]/pix[:,2:].clamp_min(1e-8);un=uv.detach().cpu().numpy();z=cam[:,2].detach().cpu().numpy();h,w=d['labels'].shape;ok=(z>0)&(un[:,0]>=0)&(un[:,0]<w-1)&(un[:,1]>=0)&(un[:,1]<h-1)
  # First actual body/CAD intersection along the true source camera ray.
  rays=np.c_[np.broadcast_to(T[:3,3],(len(P),3)),(P.detach().cpu().numpy()-T[:3,3])/np.maximum(z[:,None],1e-12)].astype(np.float32)
  import open3d as o3d
  rt=scene(W,c.F);rs=scene(c.ringV,c.ringF);zs=rt.cast_rays(o3d.core.Tensor(rays))['t_hit'].numpy();zr=rs.cast_rays(o3d.core.Tensor(rays))['t_hit'].numpy();tol=max(.02,.002*np.ptp(W,axis=0).max());ok&=(~np.isfinite(zs)|(zs>=z-tol))&(zr>=z-.05)
  # Existing Ring uncertainty excludes ambiguous negative target-boundary evidence.
  small=np.clip(np.rint((un+.5)*.5-.5).astype(int),[0,0],[319,179]);classes=d['classes'].detach().cpu().numpy()[small[:,1],small[:,0]];native=np.clip(np.rint(un).astype(int),[0,0],[w-1,h-1]);ok&=~(np.isin(classes,[1,2,4])&(d['labels'][native[:,1],native[:,0]]!=1))
  ids=np.flatnonzero(ok);ids=ids[np.linspace(0,len(ids)-1,min(512,len(ids))).astype(int)]if len(ids)else ids
  if not len(ids):return V.sum()*0,dict(contour_samples=0)
  uv=uv[tensor(ids,torch.int64)];dt,ct=self.data[cid];grid=torch.stack([2*uv[:,0]/(w-1)-1,2*uv[:,1]/(h-1)-1],1)[None,None];forward=tf.grid_sample(dt,grid,align_corners=True,padding_mode='border').reshape(-1).double();nn=cKDTree(uv.detach().cpu().numpy()).query(ct.cpu().numpy())[1];reverse=(ct-uv[tensor(nn,torch.int64)]).norm(dim=1)
  self.last[cid]=dict(eid=eid[ids],t=tt[ids],nn=nn)
  def hub(x):x=x/20.;return torch.where(x<1,.5*x*x,x-.5)
  loss=.5*(hub(forward).mean()+hub(reverse).mean());return loss,dict(contour_samples=len(ids),forward_native_px=float(forward.mean().detach()),reverse_native_px=float(reverse.mean().detach()))

class Objective(OriginalObjective):
 def __init__(self,c,ch):
  super().__init__(c,ch);self.cfg=load(R/'config/PROTOCOL.json');self.arm=self.cfg.get('loss_arm','A0');self.attempt=0;self.contour=ContourDistance(c)if self.arm in ['A2','A3']else None
 def __call__(self,q):
  L,parts=super().__call__(q)
  if self.arm=='A0':return L,parts
  m=self.chart.mesh(q);fg=L*0;bg=L*0;dist=L*0;info=[]
  for cid in self.c.fit:
   d=self.c.views[cid];fr=self.c.fragments(m,cid);_,alpha,w,*_=self.c.aware(fr,cid,True);t=d['target'];fg+=((1-alpha)**2*t).sum()/t.sum().clamp_min(1)/len(self.c.fit);known=w*(1-t);bg+=(alpha**2*known).sum()/known.sum().clamp_min(1)/len(self.c.fit)
   if self.contour is not None:
    v,rec=self.contour(self.chart.vertices(q),cid);dist+=v/len(self.c.fit);info.append(dict(source=cid,**rec))
  ramp=.25+.75*min(1.,self.attempt/40.)if self.arm=='A3'else 1.;extra=L*0
  if self.arm in ['A1','A3']:extra+=ramp*.05*(fg+bg)
  if self.arm in ['A2','A3']:extra+=ramp*.01*dist
  L=L+extra;parts.update(foreground_miss=float(fg.detach()),background_false=float(bg.detach()),contour_distance=float(dist.detach()),contour_info=info,added_loss=float(extra.detach()),loss_ramp=ramp,total=float(L.detach()));return L,parts
