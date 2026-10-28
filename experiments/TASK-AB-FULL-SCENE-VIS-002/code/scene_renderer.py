"""Minimal existing-renderer scene adapter. A-only real XYZ; no upstream models."""
from common import *
from functools import lru_cache
plt=vis.configure()
@lru_cache(None)
def scene_data(cid):
    c,P,C,m,p,uv=source(cid);z=np.load(INC/f'local_results/background/{cid}.npz');ids=np.flatnonzero(z['display']);B=z['XYZ_mm'][ids];BC=z['RGB'][ids];BU=z['source_uv'][ids];frame=np.asarray(Image.open(c['RGB']).convert('RGB'));assert np.array_equal(BC,frame[BU[:,1],BU[:,0]]/255.);assert np.all(p['labels'][BU[:,1],BU[:,0]]==0)
    out=R/'local_results/source_layers';out.mkdir(parents=True,exist_ok=True);np.savez_compressed(out/(cid+'.npz'),Polyp_XYZ_mm=P,Polyp_source_uv=uv,Polyp_RGB=C,Polyp_original_ids=np.arange(len(P)),Background_XYZ_mm=B,Background_RGB=BC,Background_source_uv=BU,Background_original_cache_ids=ids,K=p['K'],c2w=p['pose'],coordinate_frame=c['group']+'_video'+c['video']+'_LOCAL_RING_MM')
    return dict(c=c,P=P,C=C,m=m,p=p,uv=uv,B=B,BC=BC,BU=BU,B_ids=ids,ring=ring(c))
def camera_scene(d,K,pose,size=(640,360)):
    return SameCameraScene(d['ring'],K,pose,size,str(VENDOR))
def scene_image(d,K,pose,neutral=False):
    """One unchanged SameCameraScene.draw for both Polyp and Background."""
    cfg=load(R/'config.json');display=load(R/'display_config.json');size=tuple(cfg['render_size']);Khi=vis.scaled_intrinsics(K,(640,360),size);sc=camera_scene(d,Khi,pose,size);dpi=cfg['render_DPI'];fig=plt.figure(figsize=(size[0]/dpi,size[1]/dpi),dpi=dpi,facecolor='#eeeeee');ax=fig.add_axes([0,0,1,1]);gray=np.array(cfg['neutral_RGB']);pc=np.broadcast_to(gray,d['C'].shape)if neutral else d['C'];bc=np.broadcast_to(gray,d['BC'].shape)if neutral else d['BC'];sizepoint=display['neutral_geometry_point_size']if neutral else display['RGB_point_size'];ri,drawn,info=sc.draw(ax,d['P'],pc,d['B'],bc,point_size=sizepoint);scale=sc.scale_bar(ax);fig.canvas.draw();canvas=np.asarray(fig.canvas.buffer_rgba()).copy();plt.close(fig)
    info.update(neutral=neutral,source_RGB_used_for_point_colors=not neutral,source_CAD_original_A_coordinates=True,scale=scale,K_display=Khi,c2w_display=pose,display_size=size)
    return canvas[:,:,:3],info
def point_projection(d,K,pose):
    """Exact centers of A XYZ; native pixels. No target image/Mask/depth inputs."""
    sc=camera_scene(d,K,pose);P=np.r_[d['P'],d['B']];C=np.r_[d['C'],d['BC']];kind=np.r_[np.ones(len(d['P']),int),np.zeros(len(d['B']),int)];orig=np.r_[np.arange(len(d['P'])),d['B_ids']];uvs=np.r_[d['uv'],d['BU']];uv,z=vis.project_camera(P,K,pose);valid=np.isfinite(uv).all(1)&(z>0)&(uv[:,0]>=-.5)&(uv[:,0]<639.5)&(uv[:,1]>=-.5)&(uv[:,1]<359.5);ids=np.flatnonzero(valid)
    cad_at_point=sc.cast(uv[ids])['t_hit'].numpy();ids=ids[(~np.isfinite(cad_at_point))|(z[ids]<=cad_at_point+.002)];xy=np.floor(uv[ids]+.5).astype(int);pix=xy[:,1]*640+xy[:,0];order=np.lexsort((ids,z[ids],pix));ids=ids[order];pix=pix[order];_p,first=np.unique(pix,return_index=True);ids=ids[first];pix=pix[first]
    grid=np.c_[np.tile(np.arange(640),360),np.repeat(np.arange(360),640)];cad=sc.cast(grid)['t_hit'].numpy();ri=sc.ring_image();rgba=np.rint(np.clip(ri,0,1)*255).astype(np.uint8).reshape(-1,4);layers=np.where(np.isfinite(cad),2,-1).astype(np.int8);depth=cad.copy();source_index=np.full(360*640,-1,int);source_uv=np.full((360*640,2),-1,int)
    ok=(~np.isfinite(cad[pix]))|(z[ids]<=cad[pix]+.002);ids=ids[ok];pix=pix[ok];rgba[pix,:3]=np.rint(C[ids]*255).astype(np.uint8);rgba[pix,3]=255;layers[pix]=kind[ids];depth[pix]=z[ids];source_index[pix]=orig[ids];source_uv[pix]=uvs[ids]
    return dict(RGBA=rgba.reshape(360,640,4),layer=layers.reshape(360,640),axial_depth_mm=depth.reshape(360,640),source_original_id=source_index.reshape(360,640),source_uv=source_uv.reshape(360,640,2),CAD_depth_mm=cad.reshape(360,640),CAD_RGBA=ri)
def background_eval_roi(mask):
    v,u=np.nonzero(mask==1);rv,ru=np.nonzero(mask==2);base=v>=np.quantile(v,.8);center=np.median(np.c_[u[base],v[base]],0);radius=2*max(np.ptp(u)/2,np.ptp(ru)/2);yy,xx=np.indices(mask.shape);ellipse=((xx-center[0])/radius)**2+((yy-center[1])/(.75*radius))**2<=1
    return ellipse&(mask==0),dict(center_uv=center,radius_x_px=radius,radius_y_px=.75*radius,identity='B_MASK_EVALUATION_ONLY_PREDECLARED_ELLIPSE; no B RGB/depth')
def scene_metrics(pred,B,mask):
    roi,params=background_eval_roi(mask);lay=pred['layer'];pp=lay==1;bg=lay==0;targetP=mask==1;cp=pp&targetP;cb=bg&roi;diff=abs(pred['RGBA'][:,:,:3].astype(float)-B.astype(float)).mean(2)
    def metric(a):return float(diff[a].mean())if a.any()else None
    row=dict(identity='NEW_FULL_SCENE_POINT_DIAGNOSTIC; NOT_LEGACY_TRIANGLE_METRIC',Polyp_target_N=int(targetP.sum()),Polyp_prediction_N=int(pp.sum()),Polyp_common_N=int(cp.sum()),Polyp_target_coverage=float(cp.sum()/targetP.sum()),Polyp_RGB_MAE=metric(cp),Polyp_prediction_outside_Mask_N=int((pp&~targetP).sum()),Background_target_ROI_N=int(roi.sum()),Background_prediction_N=int(bg.sum()),Background_common_N=int(cb.sum()),Background_target_coverage=float(cb.sum()/roi.sum()),Background_RGB_MAE=metric(cb),Background_prediction_outside_target_ROI_N=int((bg&~roi).sum()),Background_on_target_Polyp_N=int((bg&targetP).sum()),Polyp_on_target_Background_ROI_N=int((pp&roi).sum()),CAD_visible_N=int((lay==2).sum()),CAD_hit_N=int(np.isfinite(pred['CAD_depth_mm']).sum()),total_supported_N=int((lay>=0).sum()),unknown_N=int((lay<0).sum()),background_ROI=params,B_RGB_used_for_prediction=False,B_Mask_used_for_prediction=False,background_depth_status='BACKGROUND_FROM_FROZEN_DEPTH — DISPLAY_ONLY')
    return row,diff,roi
def side_plot(ax,d,title,angle_=(0,0),neutral=False):
    """Existing XYZ point method + true orthographic CAD first-hit occlusion."""
    basis=vis.basis(angle_);P=np.r_[d['P'],d['B']];C=np.full_like(P,.58)if neutral else np.r_[d['C'],d['BC']];bounds=diag.square_bounds([P,d['ring'].vertices],[basis])[0];eye,right,up=basis;sc=camera_scene(d,d['p']['K'],d['p']['pose']);xy=np.c_[P@right,P@up];rays=np.c_[1000*eye+xy[:,0,None]*right+xy[:,1,None]*up,np.broadcast_to(-eye,P.shape)];hit=sc.scene.cast_rays(sc.o3d.core.Tensor(rays.astype(np.float32)))['t_hit'].numpy();visible=(~np.isfinite(hit))|(1000-P@eye<=hit+.002);im=diag.mesh_rgba(sc,bounds,eye,right,up,n=600,alpha=1.);ax.imshow(im,extent=(*bounds[0],*bounds[1]),origin='upper',interpolation='nearest',zorder=2);info=diag.points(ax,P[visible],C[visible],bounds,title,basis=basis,point_size=.08,alpha=1);ax.collections[-1].set_zorder(3);return info
