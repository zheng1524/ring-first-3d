"""Small adapters of accepted SameCameraScene / original real-P0 point methods."""
from evaluate import scene_points
from aggregation import *
import colorsys
plt=vis.configure()
PALETTE=np.array([[.94,.29,.55],[.15,.65,.93],[.96,.63,.12],[.45,.7,.25]])
def data(sc,mode='core',source_colors=True):
    a=scene_points(sc,mode);s=source(sc['primary']);b=background(sc['primary']);C=a['C']if source_colors else PALETTE[a['reference_index']%len(PALETTE)]
    return dict(P=a['P'],C=C,B=b['P'],BC=b['C'],p=s['p'],ring=s['ring'],primary=sc['primary'],refs=a['reference_index'],ids=a['original_point_id'],uv=a['source_uv'])
def source_data(cid):
    s=source(cid);b=background(cid);return dict(P=s['P'],C=s['C'],B=b['P'],BC=b['C'],p=s['p'],ring=s['ring'],primary=cid)
def camera_scene(d,K,pose,size=(640,360)):return SameCameraScene(d['ring'],K,pose,size,str(VENDOR))
def depth_colors(d):
    # Exact approved Panel2 HLS mapping; one axial-Z range for both layers.
    P=np.r_[d['P'],d['B']];pose=d['p']['pose'];z=((P-pose[:3,3])@pose[:3,:3])[:,2];good=np.isfinite(P).all(1)&np.isfinite(z)&(z>0);lo=float(z[good].min());hi=float(z[good].max());t=np.zeros(len(z));t[good]=(z[good]-lo)/max(hi-lo,1e-12);light=.82-.55*t
    def col(h,L):return np.array([colorsys.hls_to_rgb(h,float(x),.7)for x in L]).reshape(-1,3)
    return col(340/360,light[:len(d['P'])]),col(170/360,light[len(d['P']):]),(lo,hi)
def scene_image(d,K,pose,geometry=False):
    size=(1280,720);dpi=160;Ks=vis.scaled_intrinsics(K,(640,360),size);sc=camera_scene(d,Ks,pose,size);fig=plt.figure(figsize=(size[0]/dpi,size[1]/dpi),dpi=dpi,facecolor='#eeeeee');ax=fig.add_axes([0,0,1,1]);pc,bc,zlim=depth_colors(d)if geometry else(d['C'],d['BC'],None);ri,drawn,info=sc.draw(ax,d['P'],pc,d['B'],bc,point_size=.08 if geometry else .8)
    if geometry:ax.collections[-1].set_antialiased(False)
    scale=sc.scale_bar(ax);fig.canvas.draw();im=np.asarray(fig.canvas.buffer_rgba()).copy()[:,:,:3];plt.close(fig)
    return im,dict(**info,depth_range_mm=zlim,scale=scale,geometry_depth_color=geometry,B_RGB_used=False)
def side(ax,d,title,angle_=(0,0),bounds=None,colors=None,size=.08):
    basis=vis.basis(angle_);P=np.r_[d['P'],d['B']];C=np.r_[d['C'],d['BC']]if colors is None else colors;bounds=bounds or diag.square_bounds([P,d['ring'].vertices],[basis])[0];eye,right,up=basis;sc=camera_scene(d,d['p']['K'],d['p']['pose']);xy=np.c_[P@right,P@up];rays=np.c_[1000*eye+xy[:,0,None]*right+xy[:,1,None]*up,np.broadcast_to(-eye,P.shape)];hit=sc.scene.cast_rays(sc.o3d.core.Tensor(rays.astype(np.float32)))['t_hit'].numpy();visible=(~np.isfinite(hit))|(1000-P@eye<=hit+.002);im=diag.mesh_rgba(sc,bounds,eye,right,up,n=420,alpha=1.);ax.imshow(im,extent=(*bounds[0],*bounds[1]),origin='upper',interpolation='nearest',zorder=2);diag.points(ax,P[visible],C[visible],bounds,title,basis=basis,point_size=size,alpha=1);ax.collections[-1].set_zorder(3);ax.tick_params(labelsize=7);ax.xaxis.label.set_size(8);ax.yaxis.label.set_size(8)
    return bounds
def layer_figure(sc):
    d=data(sc);s=source(sc['primary']);cid=sc['primary'];delete=selected_mask(cid);raw=source_data(cid);clean=dict(raw,P=s['P'][~delete],C=s['C'][~delete]);primary=dict(clean,B=np.empty((0,3)),BC=np.empty((0,3)));novel=data(sc,source_colors=False);angle_=(-65,22);bounds=diag.square_bounds([d['P'],d['B'],s['ring'].vertices],[vis.basis(angle_)])[0];f,ax=plt.subplots(5,2,figsize=(13,23));states=[('L1 Raw 原始点',raw),('L2 选中清理：Raw回退',clean),('L3 冻结主体',primary),('L4 主体 + 来源色新增块',novel),('L5 完整局部场景 / RGB',d)]
    for j,(name,x)in enumerate(states):
        side(ax[j,0],x,name+' / mm',angle_,bounds);im,info=scene_image(x,x['p']['K'],x['p']['pose'],geometry=j<4);ax[j,1].imshow(im);ax[j,1].axis('off');ax[j,1].set_title(name+'｜冻结来源相机',fontsize=11)
    f.suptitle(sc['scene']+'｜'+('UNQUALIFIED_CAMERA_STRESS'if'UNQUALIFIED'in case(sc['primary'])['condition']else case(sc['primary'])['condition'])+'｜真实XYZ五层；黑色实体CAD；背景仅冻结深度DISPLAY_ONLY\n没有补面、位移、重采样；L1–L4离散点，L5原RGB点云；观察图不是精度证据',fontsize=13);f.tight_layout(rect=[0,0,1,.965]);return f
def six_views(sc):
    d=data(sc);P=np.r_[d['P'],d['B']];C=np.r_[d['C'],d['BC']];pose=d['p']['pose'];poses=[]
    for delta in [0,-1,1]:q=pose.copy();q[:3,3]+=delta*pose[:3,0];poses.append(q)
    f,ax=plt.subplots(2,3,figsize=(16,9));bounds=[(0,640),(0,360)];rs=camera_scene(d,d['p']['K'],pose)
    for j,q in enumerate(poses):
        for i in range(2):diag.points(ax[i,j],P,C,bounds,['源相机','左移−1mm虚拟诊断','右移＋1mm虚拟诊断'][j]+(' RGB'if i==0 else' Z/mm'),K=d['p']['K'],c2w=q,depth_color=i==1,ring_scene=rs,ring_alpha=1,point_size=.08,alpha=1)
    f.suptitle(sc['scene']+'｜'+('UNQUALIFIED_CAMERA_STRESS'if'UNQUALIFIED'in case(sc['primary'])['condition']else case(sc['primary'])['condition'])+'｜同一实际XYZ，近相机RGB/轴向深度；虚拟诊断不冒充真实帧');f.tight_layout(rect=[0,0,1,.94]);out={'Camera_3Views.png':f}
    f,ax=plt.subplots(2,3,figsize=(16,10));bases=list(diag.AXES.items());bb=diag.square_bounds([P,d['ring'].vertices],[b[:3]for _,b in bases])
    for j,(label,b)in enumerate(bases):
        for i in range(2):diag.points(ax[i,j],P,C,bb[j],label+'正交 / '+('源RGB'if i==0 else'视向深度mm'),basis=b[:3],labels=b[3:],depth_color=i==1,ring_scene=rs,ring_alpha=1,point_size=.08,alpha=1)
    f.suptitle(sc['scene']+'｜'+('UNQUALIFIED_CAMERA_STRESS'if'UNQUALIFIED'in case(sc['primary'])['condition']else case(sc['primary'])['condition'])+'｜世界XYZ三方向，同毫米窗口；只显示实际点');f.tight_layout(rect=[0,0,1,.94]);out['XYZ_3Views.png']=f;return out
def five_panel(cid,t,out,status,main_title='真实跨视角验证'):
    d=source_data(cid);s=source(cid);P=np.r_[d['P'],d['B']];C=np.r_[d['C'],d['BC']];kind=np.r_[np.ones(len(d['P']),int),np.zeros(len(d['B']),int)];pred=projection(P,C,t,kind=kind);pol=projection(d['P'],d['C'],t);m=metric(pol,t);geo,ginfo=scene_image(d,d['p']['K'],d['p']['pose'],True);full,finfo=scene_image(d,np.asarray(t['K']),np.asarray(t['c2w']));A=s['frame'];B=np.asarray(Image.open(t['RGB']).convert('RGB'));mask=cv2.imread(t['Mask'],0);target=mask==1;valid=pred['layer']>=0;diff=abs(pred['RGBA'][:,:,:3].astype(float)-B).mean(2);angle_=angle(d['p']['pose'][:3,2],np.asarray(t['c2w'])[:3,2]);base=float(np.linalg.norm(d['p']['pose'][:3,3]-np.asarray(t['c2w'])[:3,3]));lo,hi=ginfo['depth_range_mm'];fig=plt.figure(figsize=(16,13.8));gs=fig.add_gridspec(3,2,height_ratios=[1,1,.67],hspace=.18,wspace=.035);axes=[fig.add_subplot(gs[i//2,i%2])for i in range(4)];titles=['1｜A真实完整视场 '+cid,'2｜A实际XYZ：粉Polyp / 蓝绿BG；近亮远暗','3｜B真实完整视场 '+t['id'],'4｜A→B：只用A XYZ/RGB + 黑色实体CAD']
    for ax,im,title in zip(axes,[A,geo,B,full],titles):ax.imshow(im,interpolation='nearest');ax.axis('off');ax.set_title(title,fontsize=11,pad=5)
    # Approved two-hue legend occupies the original white gap below Panel2,
    # not point data. Both classes use exactly the same near/far Z bounds.
    fig.subplots_adjust(left=.025,right=.99,top=.965,bottom=.105);fig.canvas.draw();bb=axes[1].get_position();xs=np.linspace(0,1,256);light=.82-.55*xs
    fig.text(bb.x0,bb.y0-.006,f'A轴向Z / mm：共享范围 {lo:.2f} → {hi:.2f}；近亮远暗；上Polyp / 下BG',fontsize=7,va='top')
    for j,hue in enumerate([340/360,170/360]):
        bar=fig.add_axes([bb.x0+.055,bb.y0-.019-j*.006,bb.width-.06,.004]);col=np.array([colorsys.hls_to_rgb(hue,float(L),.7)for L in light]);bar.imshow(col[None],aspect='auto',interpolation='nearest');bar.axis('off')
    aa=[fig.add_subplot(gs[2,:].subgridspec(1,4,wspace=.12)[i])for i in range(4)];small=cv2.resize(full,(640,360),interpolation=cv2.INTER_AREA);overlay=B.copy().astype(float)/255.;overlay[valid]=.5*overlay[valid]+.5*small[valid]/255.;aa[0].imshow(overlay);aa[0].set_title('5a｜B和A场景 50%叠加',fontsize=9)
    roi=np.full((360,640,3),.82);roi[target&(pred['layer']!=1)]=[1,.76,.1];roi[(pred['layer']==1)&~target]=[.9,.15,.2];roi[(pred['layer']==1)&target]=[.1,.75,.4];roi[pred['layer']==0]=[.15,.55,.95];roi[np.isfinite(pred['CAD_z'])&(pred['layer']<0)]=[0,0,0];aa[1].imshow(roi);aa[1].set_title('5b｜绿共同P，黄未覆盖，红外逸\n蓝背景预测（独立分母），黑CAD',fontsize=9);common=(pol['layer']==1)&target;pol_diff=abs(pol['RGBA'][:,:,:3].astype(float)-B).mean(2);aa[2].imshow(np.where(common,pol_diff,np.nan),cmap='magma',vmin=0,vmax=80);aa[2].set_facecolor('#ccc');aa[2].set_title('5c｜Polyp-only点中心支持RGB差异\n背景不混入P分母；色阶0–80',fontsize=9);side(aa[3],d,'5d｜实际XYZ侧视 / mm')
    for ax in aa[:3]:ax.axis('off')
    fig.suptitle(f'{main_title}｜{status}｜光轴 {angle_:.2f}°；基线 {base:.2f}mm（冻结/候选条件）',fontsize=12,y=.996,color='#992d24'if'CANDIDATE'in status or'STRESS'in status else'black');fig.text(.025,.014,f"P独立点中心投影：覆盖 {m['covered_N']}/{m['target_Polyp_N']}={m['coverage']:.1%}；MAE {m['RGB']['MAE']:.2f}/255。\n背景为冻结深度XYZ — DISPLAY_ONLY；黑色CAD为已知先验；真实点间隙/拉伸保留；不等同于三维精度。",fontsize=9);fig.subplots_adjust(left=.025,right=.99,top=.965,bottom=.105);out.parent.mkdir(parents=True,exist_ok=True);fig.savefig(out,dpi=180,facecolor='white');plt.close(fig)
    return dict(source=cid,target=t['id'],angle_deg=angle_,baseline_mm=base,pose_status=status,Polyp_metric=m,Panel2=ginfo,Panel4=finfo,figure=str(out.relative_to(R)))
