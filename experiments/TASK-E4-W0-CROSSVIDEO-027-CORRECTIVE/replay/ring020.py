"""Actual CAD occluding edges, separate Inner/Outer, differentiable projections.

Discrete visibility/edge identities are recomputed from fixed CAD; the projected
3D segment distance is differentiable. No three-planar-circle approximation.
"""
from p3d import *
from pytorch3d.transforms import se3_exp_map
from scipy.ndimage import distance_transform_edt
import open3d as o3d

def exp_se3(x):return se3_exp_map(x[None].float())[0].T.double()
def canonical(T):
 a=-torch.atan2(T[1,3],T[0,3]);z=a*0;o=z+1;c=a.cos();s=a.sin();G=torch.stack([torch.stack([c,-s,z,z]),torch.stack([s,c,z,z]),torch.stack([z,z,o,z]),torch.stack([z,z,z,o])]);return G@T
def ellipse_points(e,t):
 c,s=np.cos(np.radians(e['angle_deg'])),np.sin(np.radians(e['angle_deg']));A=np.array([[c,-s],[s,c]]);return np.c_[np.cos(t)*e['major_radius'],np.sin(t)*e['minor_radius']]@A.T+[e['cx'],e['cy']]
def ellipse_phase(e,p):
 c,s=np.cos(np.radians(e['angle_deg'])),np.sin(np.radians(e['angle_deg']));q=(p-[e['cx'],e['cy']])@np.array([[c,-s],[s,c]]);return np.arctan2(q[:,1]/e['minor_radius'],q[:,0]/e['major_radius'])%(2*np.pi)
def evidence(v):
 path=R/'ring_evidence_v2'/(v['id']+'.npz')
 if path.exists():return dict(np.load(path))
 p=np.load(R/'ring'/(v['id']+'.npz'));j=load(R/'ring'/(v['id']+'.json'));a=np.load(v['cache']);lab=a['labels'];raw=contour(lab==2);tree=cKDTree(raw);out={};bins={}
 for key,side in [('inner',-1),('outer',1)]:
  q=p[key].astype(float);dist,idx=tree.query(q);keep=dist<=2.5;real=np.unique(raw[idx[keep]],axis=0);out[key]=real;out[key+'_raw']=q;out[key+'_unsupported_preprocessed_points']=q[~keep];out[key+'_original_mask_nearest_distance_px']=dist[keep];phase=ellipse_phase(j[key],real);bins[key]=np.unique(np.floor(phase/(2*np.pi)*72).astype(int))
 t=np.arange(720)/720*2*np.pi;mid=ellipse_points(j['centerline'],t);tb=np.floor(t/(2*np.pi)*72).astype(int);coverage={key:np.isin(tb,bins[key])for key in bins};qual=coverage['inner'].astype(int)+coverage['outer'].astype(int);w=np.where(qual==2,1.,np.where(qual==1,.25,0.));out.update(mid=mid,mid_weight=w,mid_support_class=qual,mid_ellipse_derived=True)
 path.parent.mkdir(exist_ok=True);np.savez_compressed(path,**out);return out
def contours(m):
 cc,hh=cv2.findContours(m.astype(np.uint8),cv2.RETR_CCOMP,cv2.CHAIN_APPROX_NONE);z={'inner':[],'outer':[]}
 if hh is not None:
  for c,h in zip(cc,hh[0]):z['inner'if h[3]>=0 else'outer'].append(c[:,0])
 return {k:np.concatenate(v).astype(float)if v else np.empty((0,2))for k,v in z.items()}

class CADCurves:
 def __init__(self):
  r=np.load(R/'inputs/G01/RING.npz');self.V=r['V'];self.F=r['F'];m=trimesh.Trimesh(self.V,self.F,process=False);self.N=m.face_normals;self.FC=m.triangles_center;self.edge=m.face_adjacency_edges;self.adj=m.face_adjacency;self.cad=scene(self.V,self.F);self.mid=np.c_[5.6*np.cos(np.arange(720)*2*np.pi/720),5.6*np.sin(np.arange(720)*2*np.pi/720),np.zeros(720)]
 def segments(self,C,K,return_aux=False):
  # Detached visibility only. Actual differentiable endpoints remain original CAD V.
  C=np.asarray(C);K=np.asarray(K);front=np.sum(self.N*(C[:3,3]-self.FC),axis=1)>0;ids=np.flatnonzero(front[self.adj[:,0]]!=front[self.adj[:,1]]);edges=self.edge[ids];X=self.V[edges];cent=X.mean(1);P=(cent-C[:3,3])@C[:3,:3];uv=P@K.T;uv=uv[:,:2]/uv[:,2:];ray=P/P[:,2:];z=self.cad.cast_rays(o3d.core.Tensor(np.c_[np.broadcast_to(C[:3,3],ray.shape),ray@C[:3,:3].T].astype(np.float32)))['t_hit'].numpy();visible=(P[:,2]>0)&(z>=P[:,2]-.002)
  depth=cast(self.cad,K,C,360,640);cc=contours(np.isfinite(depth));dist={k:cKDTree(q).query(uv)[0]if len(q)else np.full(len(uv),np.inf)for k,q in cc.items()};inner=dist['inner']<dist['outer'];result={k:edges[visible&(inner if k=='inner'else~inner)]for k in ['inner','outer']}
  if return_aux:return result,dict(contours=cc,visible_edges_N=int(visible.sum()),raw_occluding_edges_N=len(edges),depth=depth)
  return result
 def project(self,X,C,K):
  P=(X-C[:3,3])@C[:3,:3];q=P@K.T;return q[...,:2]/q[...,2:]
 def point_to_segments(self,obs,w,segments,C,K,key):
  if not len(obs):return C.sum()*0,dict(N=0,status='UNOBSERVED_NO_LOSS')
  if not len(segments):return C.sum()*0+100.,dict(N=len(obs),status='NO_CORRESPONDING_CAD_CURVE')
  X=tensor(self.V[segments],torch.float64);p=self.project(X,C,K);a,b=p[:,0],p[:,1];u=tensor(obs,torch.float64);v=b-a;D=u[:,None]-a[None];t=(D*v[None]).sum(-1)/v.square().sum(-1).clamp_min(1e-12);closest=a[None]+t.clamp(0,1)[...,None]*v[None];d2=(u[:,None]-closest).square().sum(-1);dist=(d2.min(-1).values+1e-12).sqrt();weights=tensor(w,torch.float64);x=dist/3.;loss=torch.where(x<1,.5*x*x,x-.5);return (loss*weights).sum()/weights.sum().clamp_min(1),dict(N=len(obs),weight_sum=float(weights.sum()),distance_px=stats(dist.detach().cpu().numpy()),key=key)

class RingRenderer:
 def __init__(self,ids):
  self.curves=CADCurves();norm=load(R/'inputs/G01/NORMALIZATION.json');self.center=np.asarray(norm['center']);self.scale=norm['scale_mm'];self.ring=mesh((self.curves.V-self.center)/self.scale,self.curves.F);self.raster=MeshRasterizer(raster_settings=RasterizationSettings(image_size=(180,320),blur_radius=float(np.log(9999)*1e-4),faces_per_pixel=50,bin_size=32,max_faces_per_bin=len(self.curves.F)+1,perspective_correct=True));self.shader=SoftSilhouetteShader(blend_params=BlendParams(sigma=1e-4));self.data={};views={v['id']:v for v in load(R/'config/VIEWS.json')}
  for cid in ids:
   v=views[cid];a=np.load(v['cache']);lab=cv2.resize(a['labels'],(320,180),interpolation=cv2.INTER_NEAREST);K=a['K'].copy();K[:2]*=.5;K[:2,2]+=.25;self.data[cid]=dict(meta=v,T=tensor(a['T'],torch.float64),K=tensor(a['K'],torch.float64),Ksmall=tensor(K),target=tensor(lab==2),known=tensor(lab!=1),evidence=evidence(v))
 def camera(self,C,K):
  rot=C[:3,:3].T;t=(rot@tensor(self.center,torch.float64)-rot@C[:3,3])/self.scale;return cameras_from_opencv_projection(rot[None].float(),t[None].float(),K[None],tensor([[180,320]]))
 def losses(self,H,cid,selection=None,details=False):
  d=self.data[cid];C=canonical(H@d['T']);cam=self.camera(C,d['Ksmall']);fr=self.raster(self.ring,cameras=cam);alpha=self.shader(fr,self.ring,cameras=cam)[0,...,3];p=d['target'];known=d['known'];M=.5*(((1-alpha)**2*p).sum()/p.sum().clamp_min(1)+(alpha.square()*known*(1-p)).sum()/(known*(1-p)).sum().clamp_min(1));e=d['evidence'];segs=selection if selection is not None else self.curves.segments(C.detach().cpu().numpy(),d['K'].cpu().numpy());loss={'M':M};aux={}
  for key,letter in [('inner','I'),('outer','O')]:loss[letter],aux[letter]=self.curves.point_to_segments(e[key],np.ones(len(e[key])),segs[key],C,d['K'],key)
  midX=tensor(self.curves.mid,torch.float64);uv=self.curves.project(midX,C,d['K']);u=e['mid'];w=e['mid_weight'];# Polyline is the true 3D centerline, not a physical tube boundary.
  a,b=uv,uv.roll(-1,0);Q=tensor(u,torch.float64);v=b-a;D=Q[:,None]-a[None];tt=(D*v[None]).sum(-1)/v.square().sum(-1).clamp_min(1e-12);dd=((Q[:,None]-(a[None]+tt.clamp(0,1)[...,None]*v[None]))**2).sum(-1).min(-1).values.add(1e-12).sqrt();ww=tensor(w,torch.float64);x=dd/3;loss['C']=(torch.where(x<1,.5*x*x,x-.5)*ww).sum()/ww.sum().clamp_min(1);aux['C']=dict(N=int((w>0).sum()),weight_sum=float(w.sum()),distance_px=stats(dd.detach().cpu().numpy()[w>0]),dual=int((e['mid_support_class']==2).sum()),single=int((e['mid_support_class']==1).sum()),unknown=int((e['mid_support_class']==0).sum()));return loss,aux,segs
