"""Official PyTorch3D raster/barycentric world points; exact fixed native observations."""
from multiview import *
from pytorch3d.ops import interpolate_face_attributes
from pytorch3d.renderer import MeshRasterizer,RasterizationSettings
ROOT=Path(__file__).resolve().parents[1]
def huber018(x):
 a=x.abs();return torch.where(a<1.,.5*x*x,a-.5)
class HeroDepth018:
 def __init__(self,c,ch,kind,ids=None):
  self.c=c;self.ch=ch;self.kind=kind;self.ids=c.fit if ids is None else ids;self.obs={};self.sigma=.5
  for cid in self.ids:
   root=ROOT/'hero_fit'/cid;a=dict(np.load(root/('OBS_'+kind+'.npz')));assert len(a['uv'])>0
   h,w=map(int,a['native_shape']);K=a['K'].copy();K[:2,2]+=.5;T=a['T'];rot=T[:3,:3].T;tv=(rot@c.center-rot@T[:3,3])/c.scale;cam=cameras_from_opencv_projection(tensor(rot[None]),tensor(tv[None]),tensor(K[None]),tensor([[h,w]]));rs=MeshRasterizer(cameras=cam,raster_settings=RasterizationSettings(image_size=(h,w),blur_radius=0.,faces_per_pixel=1,bin_size=0,perspective_correct=True))
   zi=(c.V-T[:3,3])@T[:3,2];worst=np.maximum(abs(zi.min()-a['z']),abs(zi.max()-a['z']))+ch.D;miss=huber018(tensor(worst/.5,torch.float64))+1
   self.obs[cid]=dict(a,cam=cam,raster=rs,index=tensor(a['uv'][:,1]*w+a['uv'][:,0],torch.int64),z_t=tensor(a['z'],torch.float64),weight_t=tensor(a['weight'],torch.float64),cad_t=tensor(a['cad_z'],torch.float64),miss_cost=miss)
  # Fixed block mass, within-block inverse upstream RGB correlation degree.
  parents={cid:{x['sha256']for x in load(ROOT/'hero_fit'/cid/'SOURCE.json')['parent_RGB']}|{sha(c.views[cid]['meta']['RGB_source'])}for cid in self.ids};raw={}
  for cid in self.ids:raw[cid]=1/(1+sum(len(parents[cid]&parents[j])/max(1,len(parents[cid]|parents[j]))for j in self.ids if j!=cid))
  blocks={c.views[cid]['meta'].get('direction_block',0)for cid in self.ids};self.w={}
  for b in blocks:
   ii=[cid for cid in self.ids if c.views[cid]['meta'].get('direction_block',0)==b];s=sum(raw[x]for x in ii)
   for cid in ii:self.w[cid]=raw[cid]/s/len(blocks)
  save('metrics/'+c.name+'_HERO_WEIGHTS.json',dict(kind=kind,raw_correlation_weight=raw,normalized=self.w,fixed_W={cid:float(a['weight'].sum())for cid,a in self.obs.items()},ids=self.ids,scale_mm=c.scale,center=c.center,miss_cost_bound='maximum initial vertex axial range +/-D, fixed per observation Huber+1; guards enforce all accepted vertices within D; losing an individual hit cannot lower its HERO cost'))
 def term(self,m,cid,details=False):
  a=self.obs[cid];fr=a['raster'](m);fid=fr.pix_to_face.reshape(-1,1)[a['index']];bary=fr.bary_coords.reshape(-1,1,3)[a['index']];attr=m.verts_packed()[m.faces_packed()]
  # Interpolate world-normalized vertices; recover metric axial Z explicitly.
  pt=interpolate_face_attributes(fid[None,:,None,:],bary[None,:,None,:,:],attr)[0,:,0,0,:].double()*self.c.scale+tensor(self.c.center,torch.float64)
  T=a['T'];z=(pt-tensor(T[:3,3],torch.float64))@tensor(T[:3,2],torch.float64);hit=fid[:,0]>=0;finite=torch.isfinite(z)&(z>0);occluded=hit&finite&(z>=a['cad_t']-.05);active=hit&finite&~occluded
  h=huber018((z-a['z_t'])/self.sigma);cost=torch.where(active,h,a['miss_cost']);loss=(cost*a['weight_t']).sum()/a['weight_t'].sum()
  info=dict(view=cid,fixed_N=len(z),active_N=int(active.sum()),Ring_occluded_N=int(occluded.sum()),miss_N=int((~hit|~finite).sum()),robust_nonzero_derivative_N=int((active&((z-a['z_t']).abs()>1e-10)).sum()),miss_gradient_supported=False,fixed_W=float(a['weight_t'].sum()),unweighted_loss=float(loss.detach()),depth_MAE_mm=float((z[active]-a['z_t'][active]).abs().mean().detach())if active.any()else None,depth_median_mm=float((z[active]-a['z_t'][active]).abs().median().detach())if active.any()else None,depth_p95_mm=float(torch.quantile((z[active]-a['z_t'][active]).abs(),.95).detach())if active.any()else None,weight=self.w[cid])
  return loss,info,dict(z=z.detach().cpu().numpy(),active=active.detach().cpu().numpy(),face_id=fid[:,0].detach().cpu().numpy(),world_point=pt.detach().cpu().numpy(),uv=a['uv'],z_H=a['z'],miss_cost=a['miss_cost'].detach().cpu().numpy())if details else None
class Objective018:
 def __init__(self,c,ch,kind,ids=None):
  self.c=c;self.ch=ch;self.kind=kind;self.attempt=0;self.prior=FrozenPrior(c);self.contour=ContourDistance(c);self.w=weights(c,c.fit);self.depth=D2Depth(c)if kind=='OLD'else None;self.hero=None if kind=='OLD'else HeroDepth018(c,ch,kind,ids);self.last=[]
 def compute(self,q,gradient=False):
  if gradient:q.grad=None
  parts=dict(silhouette=0.,missing=0.,extra=0.,contour=0.,absolute=0.,relative=0.,hero=0.,prior=0.,Ring_indicator=0.,total=0.);ramp=.25+.75*min(1.,self.attempt/40.);self.last=[]
  if self.depth:self.depth.begin(self.ch.mesh(q))
  for cid in self.c.fit:
   m=self.ch.mesh(q);fr=self.c.fragments(m,cid);base,alpha,w,*_=self.c.aware(fr,cid,True);t=self.c.views[cid]['target'];fg=((1-alpha)**2*t).sum()/t.sum().clamp_min(1);known=w*(1-t);fp=(alpha**2*known).sum()/known.sum().clamp_min(1);cd,_=self.contour(self.ch.vertices(q),cid);loss=self.w[cid]*(base+ramp*(.05*fg+.05*fp+.01*cd))
   for k,z in [('silhouette',base),('missing',fg),('extra',fp),('contour',cd)]:parts[k]+=self.w[cid]*float(z.detach())
   if self.depth and cid in self.depth.obs:
    a,b,info,_=self.depth.terms(m,cid,'E3');loss+=(.01*a+.01*b)/len(self.depth.obs);parts['absolute']+=float(a.detach())/len(self.depth.obs);parts['relative']+=float(b.detach())/len(self.depth.obs);self.last.append(info)
   parts['total']+=float(loss.detach())
   if gradient:loss.backward()
   if self.hero and cid in self.hero.obs:
    m=self.ch.mesh(q);h,info,_=self.hero.term(m,cid);L=.01*self.hero.w[cid]*h;parts['hero']+=self.hero.w[cid]*float(h.detach());parts['total']+=float(L.detach());self.last.append(info)
    if gradient:L.backward()
  reg=relative_total(self.prior(self.ch.mesh(q)));parts['prior']=float(reg.detach());parts['total']+=parts['prior']
  if gradient:reg.backward()
  parts['ramp']=ramp;parts['weighted_HERO']=.01*parts['hero'];parts['weighted_old_absolute']=.01*parts['absolute'];parts['weighted_old_relative']=.01*parts['relative'];parts['weighted_prior']=parts['prior'];parts['weighted_silhouette']=parts['total']-parts['weighted_HERO']-parts['weighted_old_absolute']-parts['weighted_old_relative']-parts['prior'];return parts['total'],parts
 def diagnostic(self,q,label):
  gradients=[];records=[]
  for cid in self.c.fit:
   m=self.ch.mesh(q);fr=self.c.fragments(m,cid);b,alpha,w,*_=self.c.aware(fr,cid,True);t=self.c.views[cid]['target'];fg=((1-alpha)**2*t).sum()/t.sum().clamp_min(1);known=w*(1-t);fp=(alpha**2*known).sum()/known.sum().clamp_min(1);cd,_=self.contour(self.ch.vertices(q),cid);loss=self.w[cid]*(b+(.25+.75*min(1.,self.attempt/40.))*(.05*fg+.05*fp+.01*cd));g=torch.autograd.grad(loss,q)[0].detach().cpu().numpy();gradients.append(('silhouette_'+cid,g));records.append(dict(view=cid,term='silhouette',weighted_loss=float(loss.detach()),gradient_norm=float(np.linalg.norm(g))))
   if self.hero and cid in self.hero.obs:
    h,info,data=self.hero.term(self.ch.mesh(q),cid,True);L=.01*self.hero.w[cid]*h;g=torch.autograd.grad(L,q)[0].detach().cpu().numpy();gradients.append(('hero_'+cid,g));records.append(dict(info,term='HERO',weighted_loss=float(L.detach()),gradient_norm=float(np.linalg.norm(g))));folder=R/'local_results'/self.c.name;folder.mkdir(exist_ok=True);np.savez_compressed(folder/(label+'_'+cid+'_CORRESPONDENCE.npz'),**data)
  prior=relative_total(self.prior(self.ch.mesh(q)));g=torch.autograd.grad(prior,q)[0].detach().cpu().numpy();gradients.append(('prior',g));records.append(dict(term='prior',weighted_loss=float(prior.detach()),gradient_norm=float(np.linalg.norm(g))));records.append(dict(term='Ring',indicator=0,gradient_norm=None,meaning='hard feasibility constraint, not differentiable loss'))
  save('metrics/'+self.c.name+'_'+label+'_GRADIENTS.json',records);np.savez_compressed(R/'local_results'/self.c.name/(label+'_COMPONENT_GRADIENTS.npz'),**{k:v for k,v in gradients});return records
