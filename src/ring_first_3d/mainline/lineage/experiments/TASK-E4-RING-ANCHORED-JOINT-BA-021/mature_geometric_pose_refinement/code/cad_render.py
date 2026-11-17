"""M3T-inspired render-boundary + CAD association; no tangent MISS=>visible rule."""
from gcommon import *
from ring020 import CADCurves,contours
import open3d as o3d
from scipy.ndimage import binary_dilation
CAD_CACHE={}
class RenderedCAD(CADCurves):
 def __new__(cls,path):
  key=str(path)
  if key not in CAD_CACHE:CAD_CACHE[key]=super().__new__(cls)
  return CAD_CACHE[key]
 def __init__(self,path):
  if getattr(self,'ready',False):return
  super().__init__(path);self.ready=True;self.last_audit={}
  self.vertex_faces=[set()for _ in self.V]
  for i,f in enumerate(self.F):
   for j in f:self.vertex_faces[j].add(i)
 def segments(self,C,K,return_aux=False):
  # Ring yaw is already canonicalized by the caller; CAD stays unchanged.
  scale=2;Ks=K.copy();Ks[:2]*=scale;Ks[:2,2]+=(scale-1)/2;h,w=360*scale,640*scale;v,u=np.mgrid[:h,:w];p=np.c_[u.ravel(),v.ravel(),np.ones(h*w)]@np.linalg.inv(Ks).T;rays=np.c_[np.broadcast_to(C[:3,3],p.shape),p@C[:3,:3].T].astype(np.float32);casted=self.cad.cast_rays(o3d.core.Tensor(rays));depth=casted['t_hit'].numpy().reshape(h,w);prim=casted['primitive_ids'].numpy().reshape(h,w);cc=contours(np.isfinite(depth));curves={k:(a+.5)/scale-.5 for k,a in cc.items()};trees={k:cKDTree(a)if len(a)else None for k,a in curves.items()}
  front=np.sum(self.N*(C[:3,3]-self.FC),axis=1)>0;ids=np.flatnonzero(front[self.adj[:,0]]!=front[self.adj[:,1]]);edges=self.edge[ids];X=self.V[edges];P0=(X.mean(1)-C[:3,3])@C[:3,:3];q=P0@K.T;uv=q[:,:2]/q[:,2:];dist={k:trees[k].query(uv)[0]if trees[k]else np.full(len(uv),np.inf)for k in ['inner','outer']};inner=dist['inner']<dist['outer'];ds=np.minimum(dist['inner'],dist['outer']);pixel=np.rint((uv+.5)*scale-.5).astype(int);state=np.full(len(edges),2,np.uint8);support=np.zeros(len(edges),bool)
  # Adjacent rendered front surface gives independent evidence, even if an exact tangent ray misses.
  for i,(e,(xx,yy))in enumerate(zip(edges,pixel)):
   if ds[i]>1.0 or xx<0 or xx>=w or yy<0 or yy>=h or P0[i,2]<=0:continue
   visible_faces=set(prim[max(0,yy-2):min(h,yy+3),max(0,xx-2):min(w,xx+3)].ravel().tolist());neighborhood=self.vertex_faces[e[0]]|self.vertex_faces[e[1]];support[i]=bool(visible_faces&neighborhood)
  state[(ds<=1.)&support]=0
  # Finite depth may show actual occlusion. A ray/raster MISS without render support stays UNKNOWN.
  valid=(pixel[:,0]>=0)&(pixel[:,0]<w)&(pixel[:,1]>=0)&(pixel[:,1]<h);z=np.full(len(edges),np.inf);z[valid]=depth[pixel[valid,1],pixel[valid,0]];state[(state!=0)&np.isfinite(z)&(P0[:,2]>z+.002)]=1
  result={k:edges[(state==0)&(inner if k=='inner'else~inner)]for k in ['inner','outer']};self.last_audit=dict(edge_ids=edges,states=state,UV=uv,distance_to_rendered_boundary_px=ds,primitive_support=support,render_depth_finite=np.isfinite(z),state_names=['VISIBLE','OCCLUDED','UNKNOWN'],render_scale=2,association_px=1.,depth_margin_mm=.002)
  if return_aux:return result,self.last_audit
  return result

def material_points(V,segments,C,K,obs):
 if not len(obs):return np.empty((0,3))
 if not len(segments):raise ValueError('NO_RENDER_SUPPORTED_CAD_CURVE')
 X=V[segments];cam=(X-C[:3,3])@C[:3,:3];p=cam@K.T;p=p[...,:2]/p[...,2:];a,b=p[:,0],p[:,1];v=b-a;D=obs[:,None]-a[None];t=np.clip((D*v[None]).sum(-1)/np.maximum((v*v).sum(-1),1e-18),0,1);d=((D-t[...,None]*v[None])**2).sum(-1);ii=d.argmin(1);tt=t[np.arange(len(obs)),ii];s=(tt/cam[ii,1,2])/((1-tt)/cam[ii,0,2]+tt/cam[ii,1,2]);return (1-s[:,None])*X[ii,0]+s[:,None]*X[ii,1]
