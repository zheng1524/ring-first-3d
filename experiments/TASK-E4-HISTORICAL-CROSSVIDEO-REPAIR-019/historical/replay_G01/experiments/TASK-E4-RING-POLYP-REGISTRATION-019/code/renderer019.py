"""Frozen Mesh, official P3D cameras/raster/shader, one differentiable video transform."""
from p3d import *
from pytorch3d.transforms import se3_exp_map
import torch.nn.functional as tf

def exp_se3(x):return se3_exp_map(x[None].float())[0].T.double()
def yaw_matrix(deg,parity=1):
 ang=np.radians(deg);Q=np.diag([1.,float(parity),float(parity)]);A=np.array([[np.cos(ang),-np.sin(ang),0],[np.sin(ang),np.cos(ang),0],[0,0,1.]])@Q;H=np.eye(4);H[:3,:3]=A;return H

def canonical_ring_camera(T):
 ang=-torch.atan2(T[1,3],T[0,3]);z=ang*0;o=z+1;c=torch.cos(ang);s=torch.sin(ang);G=torch.stack([torch.stack([c,-s,z,z]),torch.stack([s,c,z,z]),torch.stack([z,z,o,z]),torch.stack([z,z,z,o])]);return G@T
class FrozenRenderer:
 def __init__(self,ids):
  self.size=(180,320);a=np.load(R/'inputs/G01/BODY018.npz');self.V=a['V'];self.F=a['F'];self.Fs=a['F_solid'];self.inferred=a['inferred_base_faces'];n=load(R/'inputs/G01/NORMALIZATION.json');self.center=np.asarray(n['center']);self.scale=n['scale_mm'];self.body=mesh((self.V-self.center)/self.scale,self.F);rv=np.load(R/'inputs/G01/RING.npz');self.ringV=rv['V'];self.ringF=rv['F'];self.ring=mesh((rv['V']-self.center)/self.scale,rv['F']);self.raster=MeshRasterizer(raster_settings=RasterizationSettings(image_size=self.size,blur_radius=float(np.log(1/1e-4-1)*1e-4),faces_per_pixel=50,bin_size=0,perspective_correct=True));self.ring_raster=MeshRasterizer(raster_settings=RasterizationSettings(image_size=self.size,blur_radius=float(np.log(1/1e-4-1)*1e-4),faces_per_pixel=50,bin_size=32,max_faces_per_bin=len(rv['F'])+1,perspective_correct=True));self.hard=MeshRasterizer(raster_settings=RasterizationSettings(image_size=self.size,blur_radius=0,faces_per_pixel=1,bin_size=0,perspective_correct=True));self.ring_hard=MeshRasterizer(raster_settings=RasterizationSettings(image_size=self.size,blur_radius=0.,faces_per_pixel=1,bin_size=32,max_faces_per_bin=len(rv['F'])+1,perspective_correct=True));self.shader=SoftSilhouetteShader(blend_params=BlendParams(sigma=1e-4));self.views={};P14=REPO/'experiments/TASK-E4-PYTORCH3D-014';P18=REPO/'experiments/TASK-E4-HERO-BODY-ADAPT-018'
  allv={v['id']:v for v in load(R/'config/VIEWS.json')}
  for cid in ids:
   v=allv[cid];a=np.load(v['cache']);K=a['K'].copy();K[:2,:]*=.5;K[:2,2]-=.25;K[:2,2]+=.5;target=cv2.resize((a['labels']==1).astype(np.uint8),(320,180),interpolation=cv2.INTER_NEAREST);lr=cv2.resize(a['labels'],(320,180),interpolation=cv2.INTER_NEAREST);side=P14/'inputs/G01'/(cid+'_SIDES.npz')
   if not side.exists():side=P18/'inputs/G01'/(cid+'_SIDES.npz')
   if not side.exists():side=P18/'holdout/G01'/(cid+'_SIDES.npz')
   assert side.exists(),('Missing frozen Ring sides',cid);classes=cv2.resize(np.load(side)['classes'],(320,180),interpolation=cv2.INTER_NEAREST);p=np.load(R/'ring'/(cid+'.npz'));arcs=np.r_[p['inner'],p['outer']];nativegrid=(arcs+.5)/np.array([640,360])*2-1;self.views[cid]=dict(meta=v,K=a['K'],Ksmall=tensor(K),T=tensor(a['T'],torch.float64),target=tensor(target),ringtarget=tensor(lr==2),ringknown=tensor(lr!=1),classes=tensor(classes,torch.int64),arcgrid=tensor(nativegrid)[None,None],labels=a['labels']);d=self.views[cid]
   with torch.no_grad():
    cam=self.camera(d,d['T']);fr=self.hard(self.ring,cameras=cam);z=fr.zbuf[0,...,0];d['cached_ring_z']=torch.where(z>0,z,torch.full_like(z,float('inf')))
 def camera(self,d,T):
  rot=T[:3,:3].T;tv=(rot@tensor(self.center,torch.float64)-rot@T[:3,3])/self.scale;return cameras_from_opencv_projection(rot[None].float(),tv[None].float(),d['Ksmall'][None],tensor([[180,320]]))
 def polyp(self,H,cid,pure_ring_motion=False):
  d=self.views[cid];T=H@d['T'];cam=self.camera(d,T);fr=self.raster(self.body,cameras=cam);valid=fr.pix_to_face[0]>=0;p=torch.sigmoid(-fr.dists[0]/1e-4)*valid
  if pure_ring_motion:rz=d['cached_ring_z']
  else:
   with torch.no_grad():z=self.ring_hard(self.ring,cameras=cam).zbuf[0,...,0];rz=torch.where(z>0,z,torch.full_like(z,float('inf')))
  finite=torch.isfinite(rz);vis=torch.where(finite[...,None],(fr.zbuf[0].detach()<=rz[...,None]).to(p.dtype),torch.ones_like(p));alpha=1-torch.prod(1-p*vis,-1);protected=torch.isin(d['classes'],tensor([1,2,4],torch.int64))&(d['target']==0);front=(valid&vis.bool()).any(-1).float();w=torch.where(protected,torch.where(finite,front,torch.zeros_like(front)),torch.ones_like(front));return ((alpha-d['target'])**2*w).mean()
 def ring_loss(self,H,cid):
  d=self.views[cid];Tc=canonical_ring_camera(H@d['T']);cam=self.camera(d,Tc);fr=self.ring_raster(self.ring,cameras=cam);alpha=self.shader(fr,self.ring,cameras=cam)[0,...,3];p=d['ringtarget'];known=d['ringknown'];pos=((1-alpha)**2*p).sum()/p.sum().clamp_min(1);bg=known*(1-p);neg=(alpha**2*bg).sum()/bg.sum().clamp_min(1)
  if d['arcgrid'].shape[2]:edge=tf.grid_sample(alpha[None,None],d['arcgrid'],align_corners=False,padding_mode='border')[0,0,0];arc=((edge-.5)**2).mean()
  else:arc=alpha.sum()*0
  return .5*(pos+neg)+.25*arc

def weights_for(ids,views):
 blocks={cid:views[cid]['meta'].get('direction_block019',0)for cid in ids};n=len(set(blocks.values()));return{cid:1/n/sum(blocks[k]==blocks[cid]for k in ids)for cid in ids}
