# Original actual-mesh ray renderer, with the same MAX-COVERAGE face-colour adapter.
import numpy as np
import trimesh
import open3d as o3d
import matplotlib

def actual_mesh_image(V,F,RV,RF,V0,elev,azim,color,face_colors=None):
    # Fixed viewer from P0+Ring bounds, NOT optimized or GT geometry.
    allv=np.r_[V0,RV];center=(allv.min(0)+allv.max(0))/2;rad=np.linalg.norm(allv-center,axis=1).max();el,az=np.radians([elev,azim]);pos=center+rad*3.4*np.array([np.cos(el)*np.cos(az),np.cos(el)*np.sin(az),np.sin(el)])
    forward=(center-pos)/np.linalg.norm(center-pos);right=np.cross(forward,[0.,0.,1.]);right/=np.linalg.norm(right);down=np.cross(forward,right);T=np.eye(4);T[:3,:3]=np.array([right,down,forward]).T;T[:3,3]=pos
    h=w=400;K=np.array([[490.,0,199.5],[0,490.,199.5],[0,0,1.]])
    rt=o3d.t.geometry.RaycastingScene(nthreads=2)
    for v,f in[(V,F),(RV,RF)]:rt.add_triangles(o3d.core.Tensor(np.asarray(v,np.float32)),o3d.core.Tensor(np.asarray(f,np.uint32)))
    yy,xx=np.mgrid[:h,:w];d=np.c_[xx.ravel(),yy.ravel(),np.ones(h*w)]@np.linalg.inv(K).T;rays=np.c_[np.broadcast_to(pos,d.shape),d@T[:3,:3].T].astype(np.float32);hit=rt.cast_rays(o3d.core.Tensor(rays));gid=hit['geometry_ids'].numpy();fid=hit['primitive_ids'].numpy();rgb=np.full((h*w,3),.96)
    for idx,(v,f,col)in enumerate([(V,F,matplotlib.colors.to_rgb(color)),(RV,RF,(.035,.035,.035))]):
        sel=gid==idx;normal=trimesh.Trimesh(v,f,process=False).face_normals;light=(pos-center)/np.linalg.norm(pos-center);shade=.50+.50*np.maximum(0,normal[fid[sel]]@light);rgb[sel]=np.array(col)*shade[:,None]
        if idx==0 and face_colors is not None:rgb[sel]=np.asarray(face_colors)[fid[sel]]*shade[:,None]
    # Pixel scale at fixed viewer-center depth, visibly labeled approximate for perspective.
    return np.clip(rgb.reshape(h,w,3),0,1),490./np.linalg.norm(pos-center)
