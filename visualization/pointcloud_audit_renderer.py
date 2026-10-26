"""Sparse-glyph XYZ diagnostics through the frozen real-P0 point renderer."""
import numpy as np
from matplotlib import colors,cm
from . import real_p0_renderer as base

AXES = {
    'X': (np.array([1.,0,0]),np.array([0.,1,0]),np.array([0.,0,1]),'Ring Y / mm','Ring Z / mm'),
    'Y': (np.array([0.,1,0]),np.array([-1.,0,0]),np.array([0.,0,1]),'−Ring X / mm','Ring Z / mm'),
    'Z': (np.array([0.,0,1]),np.array([1.,0,0]),np.array([0.,1,0]),'Ring X / mm','Ring Y / mm')}

def square_bounds(point_sets, bases):
    bounds=[]
    for eye,right,up in bases:
        P=np.concatenate(point_sets);q=np.c_[P@right,P@up];low=q.min(0);high=q.max(0);bounds.append(((low+high)/2,max(high-low)/2))
    radius=max(x[1]for x in bounds)*1.06
    return [[(float(c[0]-radius),float(c[0]+radius)),(float(c[1]-radius),float(c[1]+radius))]for c,_r in bounds]

def colors_for_depth(depth,vmin=None,vmax=None):
    lo=float(np.min(depth))if vmin is None else vmin;hi=float(np.max(depth))if vmax is None else vmax
    norm=colors.Normalize(lo,hi if hi>lo else lo+1e-9)
    return cm.viridis(norm(depth))[:,:3],norm

def mesh_rgba(scene,bounds,eye=None,right=None,up=None,K=None,c2w=None,n=420,alpha=.15):
    x,y=np.meshgrid(np.linspace(*bounds[0],n),np.linspace(bounds[1][1],bounds[1][0],n));xy=np.c_[x.ravel(),y.ravel()]
    if K is not None:rays=base.camera_rays(xy,K,c2w)
    else:
        origin=1000*eye+xy[:,0,None]*right+xy[:,1,None]*up;rays=np.c_[origin,np.broadcast_to(-eye,origin.shape)]
    result=scene.scene.cast_rays(scene.o3d.core.Tensor(rays.astype(np.float32)));hit=np.isfinite(result['t_hit'].numpy());rgba=np.zeros((n*n,4));rgba[hit,:3]=.035;rgba[hit,3]=alpha
    return rgba.reshape(n,n,4)

def points(ax,P,rgb,bounds,title,point_size=.08,alpha=.8,basis=None,K=None,c2w=None,depth_color=False,depth_limits=None,ring_scene=None,ring_alpha=.15,ring_pixels=420,labels=None):
    if basis is not None:
        eye,right,up=basis;q=np.c_[P@right,P@up];depth=P@eye;order_key=depth;label='视向坐标 / mm';valid=np.ones(len(P),bool)
    else:
        q,depth=base.project_camera(P,K,c2w);valid=np.isfinite(q).all(1)&(depth>0);order_key=-depth;label='相机轴向Z / mm'
    col=rgb;norm=None
    if depth_color:
        dl=depth_limits or(float(depth[valid].min()),float(depth[valid].max()));col,norm=colors_for_depth(depth,*dl)
    artist=base.draw_rgb_points(ax,q[valid],np.asarray(col)[valid],order_key[valid],size=point_size);artist.set_alpha(alpha);artist.set_antialiased(False)
    if ring_scene is not None:
        image=mesh_rgba(ring_scene,bounds,*(basis or(None,None,None)),K=K,c2w=c2w,n=ring_pixels,alpha=ring_alpha)
        ax.imshow(image,extent=(*bounds[0],*bounds[1]),origin='upper',interpolation='nearest',zorder=3)
    ax.set(xlim=bounds[0],ylim=bounds[1],title=title);ax.set_aspect('equal');ax.grid(alpha=.12)
    if basis is None:ax.set_ylim(bounds[1][1],bounds[1][0]);ax.set(xlabel='投影u / px（诊断）',ylabel='投影v / px（诊断）')
    else:ax.set(xlabel=(labels or('Ring视平面横向 / mm','Ring视平面纵向 / mm'))[0],ylabel=(labels or('','Ring视平面纵向 / mm'))[1])
    if norm is not None:
        bar=ax.figure.colorbar(cm.ScalarMappable(norm=norm,cmap='viridis'),ax=ax,fraction=.035,pad=.02);bar.set_label(label,fontsize=8)
    return dict(input_points=len(P),positive_depth_drawn=int(valid.sum()),glyph_size=point_size,alpha=alpha,antialias=False,depth_color=depth_color,depth_color_range_mm=[float(norm.vmin),float(norm.vmax)]if norm else None,background_image_used=False,point_subsampling=False,CAD_hides_points=False)


def figures(P,rgb,B,bRGB,mesh,scene,K,pose,poses,image_size,cfg,scene_id,morphology,ring_name,condition,l5_images=None):
    """Draw diagnostics using XYZ/RGB alone. Only optional L5 receives images."""
    plt=base.configure();allP=np.r_[P,B];allRGB=np.r_[rgb,bRGB];panels=[]
    oblique=base.basis(cfg['layer_oblique_angle_degrees']);bounds=square_bounds([allP,mesh.vertices],[oblique])[0];depth=allP@oblique[0];dlim=(float(depth.min()),float(depth.max()))
    nrows=5 if l5_images is not None else 4;fig,ax=plt.subplots(nrows,2,figsize=(14,5.2*nrows))
    stages=[('L1 原P0',P,rgb,False),('L2 原背景XYZ',B,bRGB,False),('L3 P0＋背景',allP,allRGB,False),('L4 全点＋透明CAD',allP,allRGB,True)]
    common=dict(point_size=cfg['diagnostic_point_size'],alpha=cfg['diagnostic_point_alpha'],ring_alpha=cfg['diagnostic_CAD_alpha'],ring_pixels=cfg['diagnostic_ring_pixels'])
    for i,(name,pts,col,showring)in enumerate(stages):
        for j,color_depth in enumerate([False,True]):
            info=points(ax[i,j],pts,col,bounds,name+f' / N={len(pts):,} / '+('RGB实际点'if not color_depth else'视向深度实际点'),basis=oblique,depth_color=color_depth,depth_limits=dlim,ring_scene=scene if showring else None,**common);panels.append(dict(figure='Layers',stage=i+1,**info))
    if l5_images is not None:
        frame,l5=l5_images
        for j,image in enumerate([frame,l5]):ax[4,j].imshow(image,interpolation='nearest');ax[4,j].axis('off')
        ax[4,0].set_title('L5 对应真实帧；完整源视场');ax[4,1].set_title('L5 真实感展示；同源相机，非几何证据')
    fig.suptitle(scene_id+' '+morphology+'/'+ring_name+'｜L1–L4离散点标记直接XYZ'+('；L5才用真实感渲染'if l5_images is not None else'；独立XYZ/RGB重放')+'\n'+condition+'；前四层共同毫米窗口，无补面/插值/点坐标修改',fontsize=14);fig.tight_layout(rect=[0,.015,1,.96]);fig.subplots_adjust(hspace=.28)
    output={'Layers_L1-L5.png'if l5_images is not None else'Layers_L1-L4.png':fig}
    uv=np.concatenate([base.project_camera(np.r_[allP,mesh.vertices],K,np.array(v['c2w']))[0]for v in poses]);lo=np.minimum(uv.min(0),[0,0]);hi=np.maximum(uv.max(0),np.array(image_size)-1);pad=(hi-lo)*.025;cb=[(float(lo[k]-pad[k]),float(hi[k]+pad[k]))for k in range(2)];z=base.project_camera(allP,K,pose)[1]
    fig,ax=plt.subplots(2,3,figsize=(19,9.5));labels=['原始参考相机（点云诊断）','左侧平移−1mm（诊断，非视频帧）','右侧平移＋1mm（诊断，非视频帧）']
    for j,v in enumerate(poses):
        for i,color_depth in enumerate([False,True]):
            info=points(ax[i,j],allP,allRGB,cb,labels[j]+'\n'+('RGB'if not color_depth else'相机Z着色')+f' / N={len(allP):,}',K=K,c2w=np.array(v['c2w']),depth_color=color_depth,depth_limits=(float(z.min()),float(z.max())),ring_scene=scene,**common);panels.append(dict(figure='Camera_3Views',view=v['name'],**info))
    fig.suptitle(scene_id+' '+condition+'｜同一L4 XYZ，RGB/深度双行；CAD透明仅辅助定位\n左右为独立显示相机副本；科研相机未改，诊断窗口显示原画幅外投影点',fontsize=14);fig.tight_layout(rect=[0,.02,1,.93]);fig.subplots_adjust(hspace=.32);output['Camera_3Views.png']=fig
    axes=list(AXES.items());xb=square_bounds([allP,mesh.vertices],[a[:3]for _,a in axes]);fig,ax=plt.subplots(2,3,figsize=(19,12))
    for j,(name,data)in enumerate(axes):
        for i,color_depth in enumerate([False,True]):
            info=points(ax[i,j],allP,allRGB,xb[j],'沿＋'+name+'正交 / '+('RGB'if not color_depth else'视向坐标着色')+f'\nN={len(allP):,}，全点保留',basis=data[:3],depth_color=color_depth,ring_scene=scene,labels=data[3:],**common);panels.append(dict(figure='XYZ_3Views',view=name,**info))
    fig.suptitle(scene_id+' '+condition+'｜Ring固定XYZ正交，等比例毫米、三方向共同尺度\n仅实际预测点；间隙/重叠/拉伸不隐藏；CAD透明，无点云Mesh替代',fontsize=14);fig.tight_layout(rect=[0,.02,1,.93]);fig.subplots_adjust(hspace=.3);output['XYZ_3Views.png']=fig
    return output,dict(panels=panels,oblique_basis=oblique,layer_mm_bounds=bounds,camera_diagnostic_bounds_px=cb,XYZ_mm_bounds=xb)
