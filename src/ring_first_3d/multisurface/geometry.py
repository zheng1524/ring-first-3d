"""Depth-grid topology, exact mesh sections and owned-surface geometry helpers."""
import numpy as np
from scipy.spatial import cKDTree
from ..sim.geometry import transform,se3,parameters,scene,closest,summary,choose,cast,camera_rays
from ..contracts.coordinates import unproject


def depth_grid_mesh(z,labels,K,stride=2,edge_limit=1.):
    y,x=np.mgrid[0:z.shape[0]:stride,0:z.shape[1]:stride];uv=np.c_[x.ravel(),y.ravel()]
    good=(labels[y,x]==1)&np.isfinite(z[y,x])&(z[y,x]>0)
    ids=np.full(good.shape,-1,int);ids[good]=np.arange(good.sum());coords=uv[good.ravel()]
    V=unproject(coords,z[y[good],x[good]],K,np.eye(4));a=ids[:-1,:-1].ravel();b=ids[1:,:-1].ravel();c=ids[:-1,1:].ravel();d=ids[1:,1:].ravel()
    faces=np.r_[np.c_[a,b,c],np.c_[c,b,d]];faces=faces[(faces>=0).all(1)]
    if len(faces):
        tri=V[faces];edges=np.stack([tri[:,1]-tri[:,0],tri[:,2]-tri[:,0],tri[:,2]-tri[:,1]],1)
        keep=(np.linalg.norm(edges,axis=2).max(1)<=edge_limit)&(np.linalg.norm(np.cross(edges[:,0],edges[:,1]),axis=1)>1e-10)
        dropped=int((~keep).sum());faces=faces[keep]
    else:dropped=0
    return dict(V=V,F=faces,uv=coords),dict(valid_depth_grid_vertices=len(V),triangles=len(faces),depth_discontinuity_triangles_rejected=dropped,stride_native_px=stride,source='RGB/Mask/axial depth grid only; no GT vertex/face IDs')


def vertex_normals(V,F):
    n=np.cross(V[F[:,1]]-V[F[:,0]],V[F[:,2]]-V[F[:,0]]);out=np.zeros_like(V)
    for j in range(3):np.add.at(out,F[:,j],n)
    out/=np.maximum(1e-12,np.linalg.norm(out,axis=1)[:,None]);return out


def mesh_sections(V,F,axis,offset):
    return mesh_section_faces(V,F,axis,offset)[0]


def mesh_section_faces(V,F,axis,offset):
    import trimesh
    origin=np.zeros(3);origin[axis]=offset;normal=np.eye(3)[axis]
    segments,faces=trimesh.intersections.mesh_plane(trimesh.Trimesh(V,F,process=False),normal,origin,return_faces=True)
    return np.asarray(segments).reshape(-1,2,3),np.asarray(faces,int)


def plane_coordinates(segments,axis):return np.asarray(segments)[...,[j for j in range(3)if j!=axis]]


def point_segment_distance(points,segments):
    if not len(segments):return np.full(len(points),np.nan)
    A=segments[:,0];D=segments[:,1]-A;den=np.maximum((D*D).sum(1),1e-18);out=[]
    for batch in np.array_split(points,max(1,int(np.ceil(len(points)/200)))):
        t=np.clip(np.einsum('pni,ni->pn',batch[:,None,:]-A,D)/den,0,1)
        Q=A[None]+t[:,:,None]*D[None];out.extend(np.linalg.norm(batch[:,None,:]-Q,axis=2).min(1))
    return np.asarray(out)


def sample_mesh(V,F,n,seed):
    rng=np.random.default_rng(seed);tri=V[F];area=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)/2
    if not len(F)or area.sum()==0:return np.full((n,3),np.nan),np.full(n,-1,int),np.full((n,3),np.nan)
    ids=rng.choice(len(F),n,p=area/area.sum());a=np.sqrt(rng.random(n));b=rng.random(n);bary=np.c_[1-a,a*(1-b),a*b]
    return np.einsum('ni,nij->nj',bary,tri[ids]),ids,bary


def rotation_about_camera(local,C):return C@se3(local)@np.linalg.inv(C)


def distribution(z):
    return dict(empirical_mean=z.mean(0).tolist(),empirical_std_ddof1=z.std(0,ddof=1).tolist(),empirical_covariance_ddof1=np.cov(z,rowvar=False,ddof=1).tolist())
