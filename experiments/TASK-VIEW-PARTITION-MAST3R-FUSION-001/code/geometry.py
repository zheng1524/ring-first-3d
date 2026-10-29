"""Existing original-face raycasting, exact source-center z-buffer and topology."""
from common import *
@lru_cache(None)
def o3d():
    sys.path.insert(0,str(VENDOR));import open3d;return open3d
@lru_cache(None)
def cad(cid,Kbytes,posebytes):
    K=np.frombuffer(Kbytes,dtype=np.float64).reshape(3,3);pose=np.frombuffer(posebytes,dtype=np.float64).reshape(4,4)
    return SameCameraScene(source(cid)['ring'],K,pose,(640,360),str(VENDOR))
def camera(t):return cad(t['ring_case'],np.asarray(t['K'],np.float64).tobytes(),np.asarray(t['c2w'],np.float64).tobytes())
def mesh_scene(P,F):
    o=o3d();sc=o.t.geometry.RaycastingScene(nthreads=2)
    if len(F):sc.add_triangles(o.core.Tensor(np.asarray(P,np.float32)),o.core.Tensor(np.asarray(F,np.uint32)))
    return sc
def raymesh(P,F,t):
    o=o3d();grid=np.c_[np.tile(np.arange(640),360),np.repeat(np.arange(360),640)];rays=vis.camera_rays(grid,np.asarray(t['K']),np.asarray(t['c2w']));sc=mesh_scene(P,F);hit=sc.cast_rays(o.core.Tensor(rays.astype(np.float32)));z=hit['t_hit'].numpy();rz=camera(t).cast(grid)['t_hit'].numpy();valid=np.isfinite(z)&(z>0)&(z<=rz+cfg()['CAD_tolerance_mm'])
    return dict(z=np.where(valid,z,np.inf).reshape(360,640),raw_z=z.reshape(360,640),face=hit['primitive_ids'].numpy().reshape(360,640),bary=hit['primitive_uvs'].numpy().reshape(360,640,2),CAD_z=rz.reshape(360,640),valid=valid.reshape(360,640))
def projection(P,C,t,ids=None,kind=None):
    """A geometry/colors only. B image/Mask not read by renderer."""
    if ids is None:ids=np.arange(len(P))
    if kind is None:kind=np.ones(len(P),int)
    K=np.asarray(t['K']);pose=np.asarray(t['c2w']);sc=camera(t);uv,z=vis.project_camera(P,K,pose);inside=np.isfinite(uv).all(1)&(z>0)&(uv[:,0]>=-.5)&(uv[:,0]<639.5)&(uv[:,1]>=-.5)&(uv[:,1]<359.5);ii=np.flatnonzero(inside)
    hit=sc.cast(uv[ii])['t_hit'].numpy();ii=ii[(~np.isfinite(hit))|(z[ii]<=hit+cfg()['CAD_tolerance_mm'])];xy=np.floor(uv[ii]+.5).astype(int);pix=xy[:,1]*640+xy[:,0];order=np.lexsort((ii,z[ii],pix));ii=ii[order];pix=pix[order];_,first=np.unique(pix,return_index=True);ii=ii[first];pix=pix[first]
    grid=np.c_[np.tile(np.arange(640),360),np.repeat(np.arange(360),640)];cz=sc.cast(grid)['t_hit'].numpy();ok=z[ii]<=cz[pix]+cfg()['CAD_tolerance_mm'];ii=ii[ok];pix=pix[ok];rgba=np.zeros((360*640,4),np.uint8);rgba[pix,:3]=np.rint(C[ii]*255).astype(np.uint8);rgba[pix,3]=255;layer=np.full(360*640,-1,int);layer[pix]=kind[ii];who=np.full(360*640,-1,int);who[pix]=ids[ii];zz=np.full(360*640,np.inf);zz[pix]=z[ii]
    return dict(RGBA=rgba.reshape(360,640,4),layer=layer.reshape(360,640),z=zz.reshape(360,640),source_id=who.reshape(360,640),CAD_z=cz.reshape(360,640),CAD_RGBA=sc.ring_image())
def metric(pred,t):
    B=np.asarray(Image.open(t['RGB']).convert('RGB'));mask=cv2.imread(t['Mask'],0)==1;valid=(pred['layer']==1)&mask;diff=abs(pred['RGBA'][:,:,:3].astype(float)-B).mean(2)
    return dict(target_id=t['id'],target_Polyp_N=int(mask.sum()),covered_N=int(valid.sum()),coverage=float(valid.sum()/mask.sum()),RGB=stats(diff[valid]),outside_Polyp_N=int(((pred['layer']==1)&~mask).sum()),not_depth_accuracy=True)
def common_metric(pred0,pred1,t):
    B=np.asarray(Image.open(t['RGB']).convert('RGB'));mask=cv2.imread(t['Mask'],0)==1;common=(pred0['layer']==1)&(pred1['layer']==1)&mask;err=lambda p:stats(abs(p['RGBA'][:,:,:3].astype(float)-B).mean(2)[common])
    return dict(common_N=int(common.sum()),baseline=err(pred0),candidate=err(pred1),target_Polyp_N=int(mask.sum()))
def depth_tau(z,K):return np.maximum(cfg()['reverse_depth_tolerance_mm_minimum'],cfg()['reverse_depth_tolerance_pixel_footprints']*np.asarray(z)/min(K[0,0],K[1,1]))
def additional_mask_support(P,t):
    uv,z=vis.project_camera(P,np.asarray(t['K']),np.asarray(t['c2w']));xy=np.zeros_like(uv,int);valid=np.isfinite(uv).all(1)&(z>0);xy[valid]=np.floor(uv[valid]+.5).astype(int);valid&=(xy[:,0]>=0)&(xy[:,0]<640)&(xy[:,1]>=0)&(xy[:,1]<360);ids=np.flatnonzero(valid);x,y=xy[ids].T;mask=cv2.imread(t['Mask'],0);out=np.zeros(len(P),bool);hit=camera(t).cast(uv[ids])['t_hit'].numpy();out[ids]=(mask[y,x]==1)&(z[ids]<=hit+cfg()['CAD_tolerance_mm']);return out
def area(P,F):return np.linalg.norm(np.cross(P[F[:,1]]-P[F[:,0]],P[F[:,2]]-P[F[:,0]]),axis=1)/2
def vertex_area(P,F):
    w=np.zeros(len(P));a=area(P,F)
    for j in range(3):np.add.at(w,F[:,j],a/3)
    return w
def topology(s,deleted):
    F=s['F'];ar=s['areas'];keep=~deleted[F].any(1);lab=face_components(F);sums=np.bincount(lab,weights=ar);head=lab==sums.argmax();cl=face_components(F[keep]);parts=np.bincount(cl[head[keep]],weights=ar[keep&head])if (head&keep).any()else np.array([0.]);e,n=edge_counts(F);e2,n2=edge_counts(F[keep]);old=set(map(tuple,e[n==1]));new=set(map(tuple,e2[n2==1]));return dict(raw_faces=len(F),kept_faces=int(keep.sum()),raw_area_proxy_mm2=float(ar.sum()),retained_area_proxy_mm2=float(ar[keep].sum()),raw_main_area_retention=float(ar[head&keep].sum()/ar[head].sum()),largest_raw_main_piece_retention=float(parts.max()/ar[head].sum()),raw_face_components=len(sums),kept_face_components=len(np.unique(cl)),new_boundary_edges=len(new-old),interior_deletion_patches=interior_deletion_patches(F,deleted),nonmanifold_edges=int((n2>2).sum()))
def direction(P,N,reliable,weights,pose):
    """Orient to real source camera; unreliable normals excluded."""
    N=N.copy();towards=pose[:3,3]-P;flip=(N*towards).sum(1)<0;N[flip]*=-1;az=np.mod(np.arctan2(N[:,1],N[:,0]),2*np.pi);el=np.arcsin(np.clip(N[:,2],-1,1));q=cfg();bins=np.minimum((az/(2*np.pi)*q['normal_bins_azimuth']).astype(int),q['normal_bins_azimuth']-1)+q['normal_bins_azimuth']*np.clip(((el+np.pi/2)/np.pi*q['normal_bins_elevation']).astype(int),0,q['normal_bins_elevation']-1);hist=np.bincount(bins[reliable],weights=weights[reliable],minlength=q['normal_bins_azimuth']*q['normal_bins_elevation']);active=hist>=max(1e-12,hist.sum()*q['direction_bin_minimum_area_fraction']);return dict(hist_area_proxy_mm2=hist,covered_bins=int(active.sum()),active_bins=np.flatnonzero(active),total_bins=len(hist),reliable_area_proxy_mm2=float(hist.sum()))
