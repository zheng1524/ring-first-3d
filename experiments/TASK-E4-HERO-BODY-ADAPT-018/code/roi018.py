"""Exact pixel-grid cropping for official rasterization. No view/observation thinning."""
from p3d import *
from pytorch3d.renderer.mesh.rasterizer import Fragments
import torch.nn.functional as Fpad
def cropped_camera(c,d,x0,y0,h,w,K):
 T=d['T'];k=K.copy();k[:2,2]-=[x0,y0];k[:2,2]+=.5;rot=T[:3,:3].T;tv=(rot@c.center-rot@T[:3,3])/c.scale
 return cameras_from_opencv_projection(tensor(rot[None]),tensor(tv[None]),tensor(k[None]),tensor([[h,w]]))
def soft_roi(c,m,cid):
 d=c.views[cid];h,w=c.size;V=m.verts_packed().detach().cpu().numpy()*c.scale+c.center;cam=(V-d['T'][:3,3])@d['T'][:3,:3]
 if cam[:,2].min()<=.01:return c.renderer.rasterizer(m,cameras=d['cam'])
 p=cam@d['Ksmall'].T;uv=p[:,:2]/p[:,2:];margin=int(np.ceil(np.sqrt(c.renderer.rasterizer.raster_settings.blur_radius)*min(h,w)/2))+2
 x0,y0=np.maximum(np.floor(uv.min(0)).astype(int)-margin,[0,0]);x1,y1=np.minimum(np.ceil(uv.max(0)).astype(int)+margin+1,[w,h]);x0,y0,x1,y1=map(int,[x0,y0,x1,y1])
 if x1<=x0 or y1<=y0:return c.renderer.rasterizer(m,cameras=d['cam'])
 hh,ww=y1-y0,x1-x0;ratio=min(h,w)/min(hh,ww);settings=RasterizationSettings(image_size=(hh,ww),blur_radius=c.renderer.rasterizer.raster_settings.blur_radius*ratio**2,faces_per_pixel=50,bin_size=0,perspective_correct=True)
 r=MeshRasterizer(cameras=cropped_camera(c,d,x0,y0,hh,ww,d['Ksmall']),raster_settings=settings)(m)
 pad=(0,0,x0,w-x1,y0,h-y1);padb=(0,0,0,0,x0,w-x1,y0,h-y1)
 return Fragments(pix_to_face=Fpad.pad(r.pix_to_face,pad,value=-1),zbuf=Fpad.pad(r.zbuf,pad,value=-1),bary_coords=Fpad.pad(r.bary_coords,padb,value=0),dists=Fpad.pad(r.dists/ratio**2,pad,value=1.))
def enable(c,hero=None):
 c.fragments=lambda m,cid:soft_roi(c,m,cid)
 if hero:
  for cid,a in hero.obs.items():
   uv=a['uv'];x0,y0=uv.min(0).astype(int);x1,y1=uv.max(0).astype(int)+1;h,w=int(y1-y0),int(x1-x0);d=dict(T=a['T']);cam=cropped_camera(c,d,int(x0),int(y0),h,w,a['K']);a['cam']=cam;a['raster']=MeshRasterizer(cameras=cam,raster_settings=RasterizationSettings(image_size=(h,w),blur_radius=0.,faces_per_pixel=1,bin_size=0,perspective_correct=True));a['index']=tensor((uv[:,1]-y0)*w+uv[:,0]-x0,torch.int64);a['raster_ROI_original_pixels']=[int(x0),int(y0),int(x1),int(y1)]
