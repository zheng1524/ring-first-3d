"""018 official PyTorch3D path plus fixed qualified native point/face constraints."""
from hero_objective018 import *
from native_multi import CFG,Source,source_weights,correspond,weak_anchors,geometry_score,bias_proposal
from pytorch3d.loss.point_mesh_distance import point_face_distance
from gate018 import configure
from coherent016 import coherent_directions

class NativeDepth:
 def __init__(self,c,ch,ss):
  self.c=c;self.ss=ss;self.obs={}
  for s in ss:
   a=s.o;h,w=map(int,a['native_shape']);K=s.K.copy();K[:2,2]+=.5;rot=s.C[:3,:3].T;tv=(rot@c.center-rot@s.C[:3,3])/c.scale;cam=cameras_from_opencv_projection(tensor(rot[None]),tensor(tv[None]),tensor(K[None]),tensor([[h,w]]));rs=MeshRasterizer(cameras=cam,raster_settings=RasterizationSettings(image_size=(h,w),blur_radius=0.,faces_per_pixel=1,bin_size=0,perspective_correct=True));zi=(c.V-s.C[:3,3])@s.C[:3,2];worst=np.maximum(abs(zi.min()-s.z0),abs(zi.max()-s.z0))+ch.D+CFG['cumulative_depth_limit_mm'];miss=huber018(tensor(worst/.5,torch.float64))+1
   self.obs[s.id]=dict(raster=rs,index=tensor(s.uv[:,1]*w+s.uv[:,0],torch.int64),weight=tensor(a['weight'],torch.float64),cad=tensor(a['cad_z'],torch.float64),miss=miss)
 def term(self,m,s):
  a=self.obs[s.id];fr=a['raster'](m);fid=fr.pix_to_face.reshape(-1,1)[a['index']];bary=fr.bary_coords.reshape(-1,1,3)[a['index']];attr=m.verts_packed()[m.faces_packed()];pt=interpolate_face_attributes(fid[None,:,None,:],bary[None,:,None,:,:],attr)[0,:,0,0,:].double()*self.c.scale+tensor(self.c.center,torch.float64);z=(pt-tensor(s.C[:3,3],torch.float64))@tensor(s.C[:3,2],torch.float64);active=(fid[:,0]>=0)&torch.isfinite(z)&(z>0)&(z<a['cad']-.05);target=tensor(s.z0+s.A@s.theta,torch.float64);cost=torch.where(active,huber018((z-target)/.5),a['miss']);return(cost*a['weight']).sum()/a['weight'].sum()

class JointObjective:
 def __init__(self,c,ch,ss):
  self.c=c;self.ch=ch;self.ss=ss;self.prior=FrozenPrior(c);self.contour=ContourDistance(c);self.w=weights(c,c.fit);self.native=NativeDepth(c,ch,ss);self.bind={};self.attempt=40 # final 018 ramp fixed across all arms/rounds, no changing acceptance objective
 def bind_geometry(self,V,ring):
  body=scene(V,self.c.F);rows=[]
  for s in self.ss:
   cr=correspond(s,V,self.c.F,body,ring);wa=weak_anchors(s,cr,V,self.c.F,body,ring);ii=np.where(cr['matched'])[0];idx=cr['index'][ii];tri=V[self.c.F[cr['face'][ii]]];Q=cr['Q'][ii];v0=tri[:,1]-tri[:,0];v1=tri[:,2]-tri[:,0];v2=Q-tri[:,0];d00=(v0*v0).sum(1);d01=(v0*v1).sum(1);d11=(v1*v1).sum(1);d20=(v2*v0).sum(1);d21=(v2*v1).sum(1);den=np.maximum(d00*d11-d01*d01,1e-15);v=(d11*d20-d01*d21)/den;w=(d00*d21-d01*d20)/den;bar=np.c_[1-v-w,v,w]
   self.bind[s.id]=dict(native_index=idx,face=tensor(cr['face'][ii],torch.int64),bary=tensor(bar,torch.float64),X=tensor(cr['X'][ii],torch.float64),normal=tensor(cr['normal'][ii],torch.float64),weak=wa,weakX=tensor(cr['X'][wa[:,0]]if len(wa)else np.empty((0,3))),denominator=len(cr['index']))
   rows.append(dict(source=s.id,sampled_N=len(cr['index']),matched=len(ii),weak_nohit_anchors=len(wa),unexplained=int((cr['state']==1).sum()),conflict=int((cr['state']==2).sum()),unknown=int((cr['state']==3).sum())))
  return rows
 def geometry_term(self,V,s):
  a=self.bind[s.id];zero=V.sum()*0;strong=zero;weak=zero
  if len(a['face']):
   pt=(V[tensor(self.c.F,torch.int64)[a['face']]]*a['bary'][:,:,None]).sum(1);target=tensor(s.points()[a['native_index']],torch.float64);res=((pt-target)*a['normal']).sum(1);strong=huber018(res/.5).sum()/a['denominator']
  if len(a['weak']):
   tris=V[tensor(self.c.F[a['weak'][:,1]],torch.int64)].float();N=len(tris);first=torch.arange(N,device=device,dtype=torch.int64);target=tensor(s.points()[s.sub[a['weak'][:,0]]]);d2=point_face_distance(target,first,tris,first,1,1e-10);weak=(torch.sqrt(1+d2/.25)-1).sum()/a['denominator']
  return strong,weak
 def compute(self,q,gradient=False):
  if gradient:q.grad=None
  parts=dict(silhouette=0.,contour=0.,hero=0.,correspondence=0.,weak=0.,prior=0.,total=0.)
  for cid in self.c.fit:
   m=self.ch.mesh(q);base,alpha,w,*_=self.c.aware(self.c.fragments(m,cid),cid,True);t=self.c.views[cid]['target'];fg=((1-alpha)**2*t).sum()/t.sum().clamp_min(1);known=w*(1-t);fp=(alpha**2*known).sum()/known.sum().clamp_min(1);cd,_=self.contour(self.ch.vertices(q),cid);loss=self.w[cid]*(base+.05*fg+.05*fp+.01*cd);parts['silhouette']+=self.w[cid]*float((base+.05*fg+.05*fp).detach());parts['contour']+=self.w[cid]*float(cd.detach());parts['total']+=float(loss.detach())
   if gradient:loss.backward()
  for s in self.ss:
   h=self.native.term(self.ch.mesh(q),s);strong,weak=self.geometry_term(self.ch.vertices(q),s);loss=s.w*(CFG['hero_weight']*h+CFG['correspondence_weight']*strong+CFG['unexplained_weight']*weak)
   for name,x in [('hero',h),('correspondence',strong),('weak',weak)]:parts[name]+=s.w*float(x.detach())
   parts['total']+=float(loss.detach())
   if gradient:loss.backward()
  reg=relative_total(self.prior(self.ch.mesh(q)));parts['prior']=float(reg.detach());parts['total']+=parts['prior']
  if gradient:reg.backward()
  return parts['total'],parts
