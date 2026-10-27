"""Controlled exact prior source/background helpers; task-specific camera interface."""
from common import *
from source_rgb_projection import raster,errors
from functools import lru_cache
ABS=Path('/home/liu/ring_first_3d_abs_density/experiments/TASK-PHASEC-ABS-DENSITY-REPROJ-001')
PHASE=Path('/home/liu/ring_first_3d_phase_d/experiments/TASK-PHASED-MAIN-SURFACE-CROSSVIDEO-001')
def scenes():
    return [dict(id=g+'_'+v,group=g,video=v,references=[c['id']for c in cases()if c['group']==g and c['video']==v])for g,v in dict.fromkeys((c['group'],c['video'])for c in cases())]
def mesh(P,F):return trimesh.Trimesh(P,F,process=False)
def o3d_module():
    sys.path.insert(0,str(OLD/'surface_fusion_v3/vendor'));import open3d;return open3d
def scene_for(t):return SameCameraScene(ring(source(t['ring_case'])['c']),np.array(t['K']),np.array(t['c2w']),(640,360),str(OLD/'surface_fusion_v3/vendor'))
def target(scene):return load(R/'provenance/TARGETS_FROZEN.json')[scene]
def nearest(P,m):
    o=o3d_module();sc=o.t.geometry.RaycastingScene(nthreads=2);sc.add_triangles(o.core.Tensor(np.asarray(m.vertices,np.float32)),o.core.Tensor(np.asarray(m.faces,np.uint32)));v=sc.compute_closest_points(o.core.Tensor(np.asarray(P,np.float32)));return np.linalg.norm(np.asarray(P)-v['points'].numpy(),axis=1),v['primitive_normals'].numpy()
def point_projection(P,rgb,t):return raster(P,rgb,np.ones(len(P),int),np.arange(len(P)),np.array(t['K']),np.array(t['c2w']),(360,640),scene_for(t))
def observation_support(P,rgb,t,pred=None):
    if pred is None:pred=point_projection(P,rgb,t)
    uv,z=vis.project_camera(P,np.array(t['K']),np.array(t['c2w']));xy=np.zeros_like(uv,int);finite=np.isfinite(uv).all(1)&(z>0);xy[finite]=np.floor(uv[finite]+.5).astype(int);inside=finite&(xy[:,0]>=0)&(xy[:,0]<640)&(xy[:,1]>=0)&(xy[:,1]<360);ids=np.flatnonzero(inside);u,v=xy[ids].T;B=np.asarray(Image.open(t['RGB']).convert('RGB'));lab=cv2.imread(t['Mask'],0);err=np.abs(rgb[ids]*255-B[v,u]).mean(1);supported=np.zeros(len(P),bool);supported[ids]=(lab[v,u]==1)&(err<=cfg()['source_rgb_support_MAE_maximum'])&(z[ids]<=pred['z'][v,u]+cfg()['consistency_mm']);return supported
def source_conflicts(P,reference,others):
    front=np.zeros(len(P),bool);support=np.ones(len(P),int)
    for cid in others:
        if cid==reference:continue
        p=source(cid)['p'];uv,z=vis.project_camera(P,p['K'],p['pose']);finite=np.isfinite(uv).all(1)&(z>0);xy=np.zeros_like(uv,int);xy[finite]=np.rint(uv[finite]).astype(int);inside=finite&(xy[:,0]>=0)&(xy[:,0]<640)&(xy[:,1]>=0)&(xy[:,1]<360);ii=np.flatnonzero(inside);u,v=xy[ii].T;valid=(p['labels'][v,u]==1)&np.isfinite(p['depth_mm'][v,u]);ii=ii[valid];u,v=xy[ii].T;r=z[ii]-p['depth_mm'][v,u];front[ii[r<-cfg()['consistency_mm']]]=True;support[ii[abs(r)<=cfg()['consistency_mm']]]+=1
    return front,support
def cfg():return load(R/'config.json')
@lru_cache(None)
def source(cid):
    c=next(c for c in cases()if c['id']==cid);a,p,rgb,m=data(c);P=a['XYZ_mm'];areas=np.linalg.norm(np.cross(P[m.faces[:,1]]-P[m.faces[:,0]],P[m.faces[:,2]]-P[m.faces[:,0]]),axis=1)/2
    return dict(c=c,a=a,p=p,rgb=rgb,m=m,P=P,areas=areas)
@lru_cache(None)
def background(cid):
    s=source(cid);p=s['p'];lab=p['labels'];rgb=np.asarray(Image.open(s['c']['RGB']).convert('RGB'));v,u=np.nonzero((lab==0)&np.isfinite(p['depth_mm'])&(p['depth_mm']>0));P=unproject(np.c_[u,v],p['depth_mm'][v,u],p['K'],p['pose']);a=s['a'];uv=np.c_[a['source_u'],a['source_v']];base=uv[:,1]>=np.quantile(uv[:,1],.8);center=np.median(uv[base],0);pv,pu=np.nonzero(lab==1);rv,ru=np.nonzero(lab==2);radius=max(np.ptp(pu)/2,np.ptp(ru)/2);q=cfg();ellipse=lambda k:((u-center[0])/(k*radius))**2+((v-center[1])/(q['background_ellipse_y_over_x']*k*radius))**2<=1
    mask=np.zeros(lab.shape,np.uint8);mask[uv[base,1],uv[base,0]]=1;contact=cv2.distanceTransform(1-mask,cv2.DIST_L2,5)[v,u]<=12;near_display=np.linalg.norm(P-np.median(s['P'][base],0),axis=1)<=q['background_display_far_outer_diameters']*2*(s['c']['R_mm']+.6);display=(ellipse(q['background_display_ellipse_scale'])&near_display)|contact;fit_roi=ellipse(q['background_fit_ellipse_scale']);z=p['depth_mm'];valid=np.isfinite(z)&(z>0);hi=cv2.dilate(np.where(valid,z,0).astype(np.float64),np.ones((3,3),np.uint8));lo=cv2.erode(np.where(valid,z,1e6).astype(np.float64),np.ones((3,3),np.uint8));gradient=(hi-lo)[v,u];col=rgb[v,u];quality=fit_roi&(col.max(1)<q['background_specular_value_max'])&(col.min(1)>q['background_dark_value_min'])&(gradient<=q['background_depth_gradient_max_mm'])
    folder=R/'local_results/background';folder.mkdir(parents=True,exist_ok=True);np.savez_compressed(folder/(cid+'.npz'),XYZ_mm=P,RGB=col/255.,source_uv=np.c_[u,v],display=display,fit_roi=fit_roi,quality=quality,gradient_mm=gradient,depth_axial_mm=z[v,u],base_proxy_uv=center)
    return dict(P=P,rgb=col/255.,uv=np.c_[u,v],display=display,fit_roi=fit_roi,quality=quality,gradient=gradient)
