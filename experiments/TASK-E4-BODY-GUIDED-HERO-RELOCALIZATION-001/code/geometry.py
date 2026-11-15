"""A1 analytic ellipsoid projection + existing exact source ray convention."""
from common import *
from scipy.ndimage import map_coordinates
import ast

def reuse(path,names):
 nodes=[n for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef)and n.name in names];assert len(nodes)==len(names);exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),globals())
reuse(REPO/'experiments/TASK-E4-A1-COARSE-BODY-001/code/models.py',['decode','sphere_mesh'])
reuse(REPO/'experiments/TASK-E4-A1-ELLIPSE-VS-FULLMASK-001/code/losses.py',['ellipse_projection','signed_distance'])

def project(X,C,K):
 p=(X-C[:3,3])@C[:3,:3];u=p@K.T;return u[...,:2]/np.where(abs(u[...,2:])>1e-12,u[...,2:],1e-12),p[...,2]
def rays(C,K,uv):
 d=np.c_[uv,np.ones(len(uv))]@np.linalg.inv(K).T;return np.c_[np.broadcast_to(C[:3,3],d.shape),d@C[:3,:3].T]
def rayquery(rt,C,K,uv):return {k:v.numpy()for k,v in rt.cast_rays(o3d.core.Tensor(rays(C,K,uv).astype(np.float32))).items()}
def transform(X,H):return X@H[:3,:3].T+H[:3,3]
def yaw(deg):
 H=np.eye(4);H[:3,:3]=Rotation.from_rotvec([0,0,np.radians(deg)]).as_matrix();return H
def pose_delta(x):
 H=np.eye(4);H[:3,:3]=Rotation.from_rotvec(x[3:]).as_matrix();H[:3,3]=x[:3];return H
def pose_difference(A,B):
 H=A@np.linalg.inv(B);return dict(translation_mm=float(np.linalg.norm(H[:3,3])),rotation_deg=float(np.degrees(Rotation.from_matrix(H[:3,:3]).magnitude())))
def proper_rigid(X,Y):
 c=X.mean(0);d=Y.mean(0);U,s,V=np.linalg.svd((X-c).T@(Y-d));rot=V.T@np.diag([1,1,np.linalg.det(V.T@U.T)])@U.T;H=np.eye(4);H[:3,:3]=rot;H[:3,3]=d-rot@c;return H

def ellipse_descriptor(mask):
 """Uniform OpenCV AMS core descriptor, NOT DXY and not a true anatomical boundary.
 Same DT-superlevel and offset rule for every morphology; full mask stays unchanged.
 """
 mask=mask.astype(np.uint8);dt=cv2.distanceTransform(mask,cv2.DIST_L2,cv2.DIST_MASK_PRECISE);mx=float(dt.max());level=.25*mx;core=dt>=level;count,lab,stats0,cent=cv2.connectedComponentsWithStats(core.astype(np.uint8));valid=1+int(np.argmax(stats0[1:,cv2.CC_STAT_AREA]))if count>1 else 0;core=(lab==valid)&core;cs,_=cv2.findContours(core.astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
 if not cs or len(max(cs,key=len))<5:raise ValueError('NO_VALID_2D_ELLIPSE')
 p=max(cs,key=len);(cx,cy),(w,h),angle=cv2.fitEllipseAMS(p);th=np.radians(angle);U=np.array([[np.cos(th),-np.sin(th)],[np.sin(th),np.cos(th)]]);axes=np.array([w,h])/2+level;order=np.argsort(axes)[::-1];axes=axes[order];U=U[:,order]
 if np.linalg.det(U)<0:U[:,1]*=-1
 if not np.isfinite(axes).all()or min(axes)<1:raise ValueError('INVALID_ELLIPSE_AXES')
 return dict(center=np.array([cx,cy]),axes=axes,U=U,dt_max_px=mx,core_level_px=level,core_pixels=int(core.sum()),method='cv2.fitEllipseAMS on largest DT>=.25*max component; add level to semiaxes; generic descriptor only')
def ellipse_coords(uv,e):return(uv-e['center'])@e['U']/e['axes']
def ellipse_curve(e,N=128):return np.c_[np.cos(np.arange(N)*2*np.pi/N),np.sin(np.arange(N)*2*np.pi/N)]@np.diag(e['axes'])@e['U'].T+e['center']
def ellipse_mesh(p):
 c,Q,a=decode(p,np.eye(3));V,F=sphere_mesh(64,32);return V*a@Q.T+c,F

def sample_spatial(ids,q,budget):
 # Round-robin equal polar cells, identity frozen before reading Body geometry.
 angle=np.floor((np.arctan2(q[:,1],q[:,0])+np.pi)/(2*np.pi)*12).astype(int)%12;rad=np.minimum(3,np.floor(np.linalg.norm(q,axis=1)*4).astype(int));bins=angle+12*rad;lists=[list(ids[bins==b])for b in sorted(set(bins))];out=[]
 for i in range(max([len(x)for x in lists],default=0)):
  for v in lists:
   if i<len(v):out.append(v[int(i)])
   if len(out)>=budget:return np.array(out)
 return np.array(out,int)
