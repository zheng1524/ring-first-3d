"""Panel 2 point colors only; unchanged SameCameraScene geometry/occlusion/style."""
from common import *
import colorsys
def depth_colors(a):
    cfg=load(R/'color_config.json');P=a['Polyp_XYZ_mm'];B=a['Background_XYZ_mm'];pose=a['c2w'];points=np.r_[P,B];Z=((points-pose[:3,3])@pose[:3,:3])[:,2];valid=np.isfinite(points).all(1)&np.isfinite(Z)&(Z>0);lo=float(Z[valid].min());hi=float(Z[valid].max());t=np.zeros(len(Z));t[valid]=0 if hi==lo else(Z[valid]-lo)/(hi-lo);L=cfg['near_lightness']+(cfg['far_lightness']-cfg['near_lightness'])*t
    def color(hue,values):return np.array([colorsys.hls_to_rgb(hue,float(v),cfg['saturation'])for v in values])
    return color(cfg['Polyp_hue'],L[:len(P)]),color(cfg['Background_hue'],L[len(P):]),dict(min_Z_mm=lo,max_Z_mm=hi,Polyp_N=len(P),Background_N=len(B),valid_N=int(valid.sum()),range_shared_between_layers=True,axial_Z_SHA256=hashlib.sha256(Z.tobytes()).hexdigest()),Z
def panel2_image(cid,gray_control=False):
    a,m,rp=layers(cid);pc,bc,depth,Z=depth_colors(a);cfg=load(PREV/'config.json');display=load(PREV/'display_config.json');size=tuple(cfg['render_size']);K=vis.scaled_intrinsics(a['K'],(640,360),size);sc=SameCameraScene(m,K,a['c2w'],size,str(VENDOR));dpi=cfg['render_DPI'];fig=plt.figure(figsize=(size[0]/dpi,size[1]/dpi),dpi=dpi,facecolor='#eeeeee');ax=fig.add_axes([0,0,1,1])
    if gray_control:pc=np.full_like(pc,.58);bc=np.full_like(bc,.58)
    ri,drawn,info=sc.draw(ax,a['Polyp_XYZ_mm'],pc,a['Background_XYZ_mm'],bc,point_size=display['neutral_geometry_point_size']);ax.collections[-1].set_antialiased(False);scale=sc.scale_bar(ax);fig.canvas.draw();im=np.asarray(fig.canvas.buffer_rgba()).copy()[:,:,:3];plt.close(fig)
    return im,dict(**depth,Polyp_drawn=info['Polyp_drawn'],Background_drawn=info['Background_drawn'],point_size=info['shared_point_size'],alpha=info['shared_point_alpha'],CAD_alpha_values=info['CAD_alpha_values'],CAD_opaque_pixels=info['CAD_opaque_pixels'],CAD_max_display_RGB=info['CAD_max_display_RGB'],ring_source=str(rp),ring_SHA256=sha(rp),K_display=K,c2w=a['c2w'],scale=scale),ri,drawn
