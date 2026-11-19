"""Small rigid/pixel adapters; never change surface vertices except rigid motion."""
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.spatial import cKDTree
import cv2
from ..contracts.coordinates import validate_c2w,project,unproject
from ..synthetic.raster import scene


def transform(V,T):return np.asarray(V)@T[:3,:3].T+T[:3,3]


def se3(p):
    T=np.eye(4);T[:3,:3]=Rotation.from_rotvec(np.asarray(p)[:3]).as_matrix();T[:3,3]=np.asarray(p)[3:];return T


def parameters(T):return np.r_[Rotation.from_matrix(T[:3,:3]).as_rotvec(),T[:3,3]]


def error_transform(angle_deg,translation_mm):return se3([0,np.deg2rad(angle_deg),0,translation_mm,0,0])


def pose_error(T):return dict(rotation_deg=float(np.rad2deg(Rotation.from_matrix(T[:3,:3]).magnitude())),translation_mm=float(np.linalg.norm(T[:3,3])))


def rigid_fit(P,Q,weights=None):
    if weights is None:weights=np.ones(len(P))
    weights=np.asarray(weights)/np.sum(weights);a=np.sum(P*weights[:,None],0);b=np.sum(Q*weights[:,None],0)
    U,_,Vh=np.linalg.svd(((P-a)*weights[:,None]).T@(Q-b));R=Vh.T@np.diag([1,1,np.linalg.det(Vh.T@U.T)])@U.T
    T=np.eye(4);T[:3,:3]=R;T[:3,3]=b-R@a;return T


def contour(mask):
    curves,_=cv2.findContours(mask.astype(np.uint8),cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE)
    return np.concatenate([x[:,0,:]for x in curves]).astype(float)if curves else np.empty((0,2))


def visible_contour(labels):
    uv=contour(labels==1);adj=cv2.dilate((labels==2).astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool)
    contact=adj[uv[:,1].astype(int),uv[:,0].astype(int)]if len(uv)else np.empty(0,bool)
    return uv,contact


def choose(a,n):return np.asarray(a)[np.linspace(0,len(a)-1,min(len(a),n),dtype=int)]


def camera_rays(uv,K,T):
    return np.c_[np.broadcast_to(T[:3,3],(len(uv),3)),np.c_[uv,np.ones(len(uv))]@np.linalg.inv(K).T@T[:3,:3].T]


def cast(mesh_scene,uv,K,T):
    import open3d as o3d
    r=mesh_scene.cast_rays(o3d.core.Tensor(camera_rays(uv,K,T).astype(np.float32)),nthreads=2)
    z=r['t_hit'].numpy().astype(float);face=r['primitive_ids'].numpy().astype(np.int64);valid=np.isfinite(z);face[~valid]=-1
    uvb=r['primitive_uvs'].numpy().astype(float);bary=np.c_[1-uvb.sum(1),uvb];bary[~valid]=np.nan
    return z,face,bary


def closest(mesh_scene,P):
    import open3d as o3d
    r=mesh_scene.compute_closest_points(o3d.core.Tensor(np.asarray(P,np.float32)),nthreads=2)
    return r['points'].numpy().astype(float),r['primitive_normals'].numpy().astype(float),r['primitive_ids'].numpy()


def summary(values):
    a=np.asarray(values);a=a[np.isfinite(a)]
    return dict(N=len(a),MAE=float(abs(a).mean())if len(a)else None,median=float(np.median(abs(a)))if len(a)else None,p95=float(np.quantile(abs(a),.95))if len(a)else None,maximum=float(abs(a).max())if len(a)else None)


def boundary_error(a,b):
    if not len(a)or not len(b):return dict(N=0,MAE=None,median=None,p95=None,maximum=None)
    return summary(np.r_[cKDTree(a).query(b)[0],cKDTree(b).query(a)[0]])


def ellipse_proxy(mask):
    pts=contour(mask)
    if len(pts)<5:return None
    (x,y),(a,b),angle=cv2.fitEllipse(pts.astype(np.float32))
    if min(a,b)<=0:return None
    t=np.deg2rad(angle);U=np.array([[np.cos(t),-np.sin(t)],[np.sin(t),np.cos(t)]])
    return dict(center_px=np.array([x,y]),basis_px=U@np.diag([a/2,b/2]),status='SYNTHETIC_MASK_ELLIPSE_PROXY_NOT_FORMAL_DXY')


def spd_basis(basis):
    vals,U=np.linalg.eigh(basis@basis.T);return U@np.diag(np.sqrt(np.maximum(vals,1e-12)))@U.T
