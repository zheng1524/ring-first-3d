"""Replace only the verified Panel-2 rectangle in a copy of each original PNG."""
from scene_renderer import *
import matplotlib.transforms as transforms
def panel_canvas(image,depth=None):
    # Exact original figure_pair GridSpec/axes bounds: no reflow of any panel.
    fig=plt.figure(figsize=(16,13.8),dpi=180);gs=fig.add_gridspec(3,2,height_ratios=[1,1,.67],hspace=.18,wspace=.035);ax=fig.add_subplot(gs[0,1]);ax.imshow(image,interpolation='nearest');ax.axis('off');title='2｜A同相机几何：统一灰XYZ + 黑色实体CAD'if depth is None else'2｜A同相机几何：粉红Polyp / 蓝绿Background · 轴向深度Z';ax.set_title(title,fontsize=11,pad=5);fig.subplots_adjust(left=.025,right=.99,top=.965,bottom=.105);fig.canvas.draw();bb=ax.get_window_extent();tb=ax.title.get_window_extent();H=int(fig.bbox.height);W=int(fig.bbox.width)
    # Original image rectangle and title + unchanged whitespace belonging to Panel2.
    rect=[int(np.floor(bb.x0))-1,int(np.floor(H-tb.y1))-1,int(np.ceil(bb.x1))+1,int(np.ceil(H-bb.y0))+1]
    if depth is not None:
        cfg=load(R/'color_config.json');lo=depth['min_Z_mm'];hi=depth['max_Z_mm'];xs=np.linspace(0,1,256);light=cfg['near_lightness']+(cfg['far_lightness']-cfg['near_lightness'])*xs;x0=bb.x0+115;x1=bb.x1-20
        fig.text(bb.x0/W,(bb.y0-4)/H,'A 轴向 Z / mm｜共享范围：近亮 → 远暗；上条 Polyp，下条 BG',fontsize=7.5,va='top')
        for i,(name,hue)in enumerate([('Polyp',cfg['Polyp_hue']),('BG',cfg['Background_hue'])]):
            y=bb.y0-34-i*8;bar=fig.add_axes([x0/W,y/H,(x1-x0)/W,7/H]);C=np.array([colorsys.hls_to_rgb(hue,float(v),cfg['saturation'])for v in light]);bar.imshow(C[None],aspect='auto',interpolation='nearest');bar.axis('off')
        for frac,value,align in [(0,lo,'left'),(.5,(lo+hi)/2,'center'),(1,hi,'right')]:fig.text((x0+frac*(x1-x0))/W,(bb.y0-48)/H,f'{value:.2f}',fontsize=7,ha=align,va='top')
        rect[3]=int(np.ceil(H-bb.y0+72))
    fig.canvas.draw();canvas=np.asarray(fig.canvas.buffer_rgba()).copy();plt.close(fig);return canvas,rect,bb.bounds
def render_one(r):
    pid=r['pair_id'];out=R/'figures/cases'/pid;out.mkdir(parents=True,exist_ok=True);old_path=PREV/r['figures']['Five_Panels.png'];old=np.asarray(Image.open(old_path).convert('RGBA'));old_gray=np.asarray(Image.open(PREV/r['figures']['A_neutral_geometry.png']).convert('RGB'))
    control,control_rect,_=panel_canvas(old_gray);x0,y0,x1,y1=control_rect;assert np.array_equal(control[y0:y1,x0:x1],old[y0:y1,x0:x1]),'Panel2 layout differs from frozen original'
    image,meta,cad,drawn=panel2_image(r['A']);canvas,rect,bounds=panel_canvas(image,meta);x0,y0,x1,y1=rect;assert canvas.shape==old.shape;assert np.all(old[control_rect[3]:y1,x0:x1]==255),'Legend must use existing blank space only';new=old.copy();new[y0:y1,x0:x1]=canvas[y0:y1,x0:x1];outside=np.ones(old.shape[:2],bool);outside[y0:y1,x0:x1]=False;changed=np.any(old!=new,2);assert not changed[outside].any()
    Image.fromarray(image).save(out/'A_geometry_depth_color.png');dest=out/'Five_Panels_depth_color.png';Image.fromarray(new).save(dest)
    # Exposed CAD pixels in the original geometry image must be pixel-identical.
    exposed=(cad[:,:,3]==1)&(old_gray.max(2)<=25);assert np.array_equal(image[exposed],old_gray[exposed]),'Ring appearance changed'
    oldmeta=r['geometry_render'];assert meta['Polyp_drawn']==oldmeta['Polyp_drawn']and meta['Background_drawn']==oldmeta['Background_drawn'];assert meta['point_size']==oldmeta['shared_point_size'];assert np.array_equal(meta['K_display'],oldmeta['K_display'])and np.array_equal(meta['c2w'],oldmeta['c2w_display'])
    return dict(pair_id=pid,A=r['A'],group=r['group'],angle_deg=r['angle_deg'],pose_status=r['pose_status'],old_figure=str(old_path),new_figure=str(dest.relative_to(R)),new_geometry=str((out/'A_geometry_depth_color.png').relative_to(R)),allowed_panel2_rectangle_xyxy=rect,unchanged_pixels_outside_Panel2=int(outside.sum()),changed_pixels_outside_Panel2=0,changed_pixels_inside_Panel2=int(changed.sum()),old_panel2_control_pixel_differences=0,unchanged_exposed_CAD_pixels=int(exposed.sum()),all_other_panels_copied_from_original=True,depth=meta,new_figure_SHA256=sha(dest))
