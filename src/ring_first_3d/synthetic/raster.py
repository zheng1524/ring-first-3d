"""T24 projection convention adapted to arbitrary fixed metric triangle meshes."""
import numpy as np
from ..contracts.coordinates import validate_c2w
from ..rendering.pytorch3d_renderer import legacy_namespace
from .._legacy import definitions


def rasterize(V,F,K,T,size=(180,320)):
    """Native integer ray index -> P3D half-integer center; mm camera Z."""
    validate_c2w(T)
    import torch
    from pytorch3d.renderer import MeshRasterizer,RasterizationSettings
    from pytorch3d.utils import cameras_from_opencv_projection
    ns=legacy_namespace(".")
    tensor=ns["tensor"];Ke=np.asarray(K,float).copy();Ke[:2,2]+=.5
    rot=T[:3,:3].T;t=-rot@T[:3,3]
    cam=cameras_from_opencv_projection(tensor(rot[None]),tensor(t[None]),tensor(Ke[None]),tensor(np.array(size)[None]))
    mesh=ns["mesh"](V,F)
    renderer=MeshRasterizer(raster_settings=RasterizationSettings(image_size=size,blur_radius=0.,faces_per_pixel=1,
        max_faces_per_bin=len(F)+1,perspective_correct=True,cull_backfaces=False))
    with torch.no_grad():fr=renderer(mesh,cameras=cam)
    face=fr.pix_to_face[0,...,0].cpu().numpy().astype(int);bary=fr.bary_coords[0,...,0,:].cpu().numpy().astype(float)
    valid=face>=0;points=np.full((*face.shape,3),np.nan)
    points[valid]=np.einsum("ni,nij->nj",bary[valid],np.asarray(V)[np.asarray(F)[face[valid]]])
    z=np.full(face.shape,np.inf);z[valid]=((points[valid]-T[:3,3])@T[:3,:3])[:,2]
    return dict(face=face,bary=bary,points=points,z=z,valid=valid)


def scene(V,F):
    ns=definitions("common",["scene"],dict(np=np))
    return ns["scene"](V,F)


def closest(V,F,P):
    import open3d as o3d
    result=scene(V,F).compute_closest_points(o3d.core.Tensor(np.asarray(P,np.float32)),nthreads=2)
    face=result["primitive_ids"].numpy().astype(int);uv=result["primitive_uvs"].numpy().astype(float)
    bary=np.c_[1-uv.sum(1),uv]
    points=np.einsum("ni,nij->nj",bary,np.asarray(V)[np.asarray(F)[face]])
    return dict(points=points,face=face,bary=bary,valid=np.ones(len(P),bool))


def independent_rays(V,F,uv,K,T):
    import open3d as o3d
    rays=np.c_[np.broadcast_to(T[:3,3],(len(uv),3)),(np.c_[uv,np.ones(len(uv))]@np.linalg.inv(K).T)@T[:3,:3].T].astype(np.float32)
    r=scene(V,F).cast_rays(o3d.core.Tensor(rays),nthreads=2)
    return r["t_hit"].numpy().astype(float)


def ray_map(V,F,K,T,size=(180,320)):
    """Independent generator's full ray/triangle material identities, no raster ROI."""
    import open3d as o3d
    y,x=np.mgrid[:size[0],:size[1]];uv=np.c_[x.ravel(),y.ravel()]
    rays=np.c_[np.broadcast_to(T[:3,3],(len(uv),3)),(np.c_[uv,np.ones(len(uv))]@np.linalg.inv(K).T)@T[:3,:3].T].astype(np.float32)
    result=scene(V,F).cast_rays(o3d.core.Tensor(rays),nthreads=2)
    z=result["t_hit"].numpy().reshape(size).astype(float);valid=np.isfinite(z)
    face=result["primitive_ids"].numpy().reshape(size).astype(np.int64);face[~valid]=-1
    primitive=result["primitive_uvs"].numpy().reshape(*size,2).astype(float)
    bary=np.concatenate([1-primitive.sum(2,keepdims=True),primitive],axis=2);bary[~valid]=np.nan
    points=np.full((*size,3),np.nan);points[valid]=np.einsum("ni,nij->nj",bary[valid],np.asarray(V)[np.asarray(F)[face[valid]]])
    z[valid]=((points[valid]-T[:3,3])@T[:3,:3])[:,2]
    return dict(valid=valid,face=face,bary=bary,points=points,z=z)
