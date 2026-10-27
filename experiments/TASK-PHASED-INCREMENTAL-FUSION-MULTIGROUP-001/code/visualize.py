"""Actual XYZ review figures, base geometry and local gallery. No fake surfaces."""
from metric_geometry import *
from matplotlib.patches import Polygon
import html,shutil
plt=vis.configure()
COLORS={0:'#d76b91',1:'#999999',2:'#e63946',3:'#999999',4:'#457b9d',5:'#14a67b'}
def pointplot(ax,P,rgb,bounds,basis,t,title,showring=True):
    return diag.points(ax,P,rgb,bounds,title,point_size=.08,alpha=1,basis=basis,ring_scene=scene_for(t)if showring else None,ring_alpha=.15)
def png(fig,p):
    p.parent.mkdir(parents=True,exist_ok=True);fig.tight_layout(rect=[0,.015,1,.93])
    if p.name=='Fig2_incremental_fusion.png':fig.subplots_adjust(hspace=.27)
    fig.savefig(p,dpi=150,facecolor='white');plt.close(fig)
def A_points(sc,label):
    P=[];C=[];states=[]
    for cid in sc['references']:
        s=source(cid)
        if label=='Raw':ids=np.arange(len(s['P']))
        else:ids=np.load(R/f'local_results/{cid}/{label}_exact.npz')['kept_original_indices']
        P.append(s['P'][ids]);C.append(s['rgb'][ids])
    return np.r_[tuple(P)],np.r_[tuple(C)]
def cleaning_figure(sc,dest):
    basis=vis.basis((0,0));raw,_=A_points(sc,'Raw');bounds=diag.square_bounds([raw,ring(source(sc['main_reference'])['c']).vertices],[basis])[0];fig,axes=plt.subplots(2,3,figsize=(18,11));a=load(R/'metrics/A_cleaning.json');decision=next(x for x in load(R/'metrics/A_decisions.json')if x['scene']==sc['id']);meta=[]
    for j,(label,title)in enumerate([('Raw','Raw / 原始全部参考'),('Historical_Density','既有T2密度候选（未认证）'),('Distance_Exempt_Candidate','一次距离豁免后候选')]):
        if j>0 and not decision['historical_threshold_present']:title='无已激活T2阈值 / 与Raw相同'if j==1 else'无删点、无距离豁免 / 与Raw相同'
        P,C=A_points(sc,label);meta.append(pointplot(axes[0,j],P,C,bounds,basis,target(sc['id']),title+f'\n实际原点N={len(P):,}'))
        ids=[];pts=[]
        if label!='Raw':
            for cid in sc['references']:
                s=source(cid);z=np.load(R/f'local_results/{cid}/{label}_exact.npz');pts.append(s['P'][z['deleted_original_indices']])
        mark=np.r_[tuple(pts)]if pts else np.empty((0,3));pointplot(axes[1,j],raw,np.full_like(raw,[.78,.76,.76]),bounds,basis,target(sc['id']),'原点删除标记；未删除仍保留\n'+f'删除N={len(mark):,}')
        if len(mark):vis.draw_rgb_points(axes[1,j],np.c_[mark@basis[1],mark@basis[2]],np.tile([.9,.12,.2],(len(mark),1)),mark@basis[0],size=.08)
    fig.suptitle(sc['id']+' '+source(sc['main_reference'])['c']['morphology']+'/'+source(sc['main_reference'])['c']['ring']+' '+source(sc['main_reference'])['c']['condition']+'｜同视角/同毫米范围\nApplied='+decision['applied']+'；未通过结构门槛的候选没有进入融合；少删不代表安全；GT=NONE');png(fig,dest/'Fig1_cleaning.png');return meta
def class_points(sc,mode):
    P=[];C=[]
    for rank,cid in enumerate(sc['reference_order']):
        if mode=='primary'and rank>0:continue
        if mode=='second'and rank>1:continue
        a=np.load(R/f'local_results/scenes/{sc["id"]}/{cid}_faces_exact.npz');N=int(a['original_vertex_N']);st=a['face_status'];classes=np.full(N,3,int)
        for k in [4,1,3,0,5,2]:
            mask=st==k
            if mode!='evidence'and rank>0:mask&=st==5
            ids=np.unique(a['faces'][mask]);ids=ids[ids<N];classes[ids]=k
        if rank==0 or mode=='evidence':ids=applied(cid)['kept_original_indices']
        else:
            keep=st!=4 if mode=='evidence'else st==5;ids=np.unique(a['faces'][keep]);ids=ids[ids<N]
        P.append(source(cid)['P'][ids]);C.append(np.array([__import__('matplotlib').colors.to_rgb(COLORS[int(k)])for k in classes[ids]]).reshape(-1,3))
    return np.r_[tuple(P)],np.r_[tuple(C)]
def fusion_figure(sc,dest):
    basis=vis.basis((-65,22));P,C,_rr,_ii=scene_points(sc,'evidence');bounds=diag.square_bounds([P,ring(source(sc['main_reference'])['c']).vertices],[basis])[0];fig,axes=plt.subplots(2,4,figsize=(23,13));labels=[('primary','固定主体'),('second','加入第二参考'if len(sc['references'])>1 else'第二参考缺失 / NO MULTIREF'),('core','主体优先最终补片'),('evidence','证据保留 / 含冲突与未知')];meta=[]
    for j,(mode,label)in enumerate(labels):
        pts,col,_rr,_ii=scene_points(sc,mode);meta.append(pointplot(axes[0,j],pts,col,bounds,basis,target(sc['id']),label+f'\n原XYZ N={len(pts):,}'));pts,col=class_points(sc,mode);pointplot(axes[1,j],pts,col,bounds,basis,target(sc['id']),'原面分类关联点（非逐点GT）\n粉=主支持，绿=补片，红=冲突，灰=未知\n蓝=重复观测，仅在末列诊断显示')
    fig.suptitle(sc['id']+' | '+source(sc['main_reference'])['c']['condition']+' | main='+sc['main_reference']+' | '+sc['status']+'\n补片模型面积='+f'{sc["new_patch_area_mm2"]:.6f}'+' mm²；不是解剖面积/真实准确率；细分中点不冒充P0采样点；源子面详见GLB。GT=NONE');png(fig,dest/'Fig2_incremental_fusion.png');return meta
def plane_quad(plane,Q,span):
    n=plane[:3];u,v=plane_basis(n);anchor=np.median(Q,0)if len(Q)else np.zeros(3);anchor-=n*(anchor@n+plane[3]);corners=np.array([[-1,-1],[1,-1],[1,1],[-1,1]])*span;quad=anchor+corners[:,0,None]*u+corners[:,1,None]*v;return anchor,quad
def geometry_figure(sc,row,dest):
    cid=row['reference'];upper=row['ROI_pixels'][1];a=np.load(R/f'local_results/metric_geometry/{cid}_{upper}.npz');P,C,_rr,_ii=scene_points(sc,'core');Q=a['background_XYZ_mm'];qc=a['background_RGB'];inside=a['inlier_by_frozen_plane'];s=source(cid);frame=np.asarray(Image.open(s['c']['RGB']).convert('RGB'));labels=s['p']['labels'];plane=None if row['plane']is None else np.array(row['plane']);fig=plt.figure(figsize=(21,16));gs=fig.add_gridspec(3,3);ax1=fig.add_subplot(gs[0,0]);ax1.imshow(frame);ax1.contour(labels==1,levels=[.5],colors=['cyan'],linewidths=.6);ax1.set_title('真实源帧 + Polyp Mask\n'+cid);ax1.axis('off');uv=a['background_source_uv'];ax2=fig.add_subplot(gs[0,1]);ax2.imshow(frame)
    if len(uv):ax2.scatter(uv[:,0],uv[:,1],s=.08,c='#00ad70',alpha=.8,linewidths=0)
    ax2.set_title('实际背景ROI / 非基底GT\n5–'+str(upper)+'px，N='+str(len(Q)));ax2.axis('off');ax3=fig.add_subplot(gs[0,2]);ax3.imshow(frame)
    if len(uv):ax3.scatter(uv[:,0],uv[:,1],s=.08,c=np.where(inside[:,None],np.array([.1,.7,.35]),np.array([.95,.2,.15])),linewidths=0)
    ax3.set_title('拟合平面残差内/外点\n报告内点比例='+f'{row["inlier_fraction"]:.3f}'+', 分母='+str(len(Q)));ax3.axis('off')
    bases=[vis.basis((0,0)),vis.basis((-65,22))];span=max(3,min(10,float(np.ptp(P,axis=0).max()/2)));anchor,quad=(None,None)if plane is None else plane_quad(plane,Q,span);H=row['diagnostic_H95_candidate_mm'];Hquad=None if quad is None or H is None else quad+plane[:3]*H;sets=[P,Q,ring(s['c']).vertices]+([]if quad is None else[quad,Hquad]);bounds=diag.square_bounds(sets,bases)
    for j,basis in enumerate(bases):
        ax=fig.add_subplot(gs[1,j]);allp=np.r_[P,Q];allc=np.r_[C,qc];pointplot(ax,allp,allc,bounds[j],basis,target(sc['id']),('侧视'if j==0 else'斜视')+'：实际XYZ / mm')
        if quad is not None:
            project=lambda X:np.c_[X@basis[1],X@basis[2]];ax.add_patch(Polygon(project(quad),closed=True,facecolor='#27b5d3',edgecolor='#158ca3',alpha=.18,linewidth=.7));ax.add_patch(Polygon(project(Hquad),closed=True,fill=False,edgecolor='#a83279',linestyle='--',linewidth=.8));aa=project(np.array([anchor,anchor+plane[:3]*min(5,max(2,abs(H or 0)/2))]));ax.annotate('n',xy=aa[1],xytext=aa[0],arrowprops=dict(arrowstyle='->',color='blue'));ax.text(.02,.03,'青=拟合基底代理；虚线=H95参考平面\n两平面均为分析几何，不是重建组织面',transform=ax.transAxes,fontsize=8)
    ax=fig.add_subplot(gs[1,2]);colors=np.where(inside[:,None],np.array([.1,.7,.35]),np.array([.95,.2,.15]));pointplot(ax,Q,colors,bounds[1],bases[1],target(sc['id']),'实际基底点：内点绿、外点红\n'+row['base_status'])
    ax=fig.add_subplot(gs[2,0]);h=a['Polyp_signed_h_mm'];h=h[np.isfinite(h)]
    if len(h):ax.hist(h,bins=60,color='#ce7998');ax.axvline(0,color='#159eb5');ax.axvline(H,color='#a83279',linestyle='--')
    ax.set(xlabel='到拟合基底有符号距离 / mm',ylabel='实际源点数量',title='H95='+('NaN'if row['H95_mm']is None else f'{row["H95_mm"]:.4f}mm')+' / 诊断候选='+('无'if H is None else f'{H:.4f}mm'))
    dr=next(x for x in load(R/'metrics/D_observed_surface_definition_audit.json')if x['scene']==sc['id']and x['base_reference']==cid and x['ROI_pixels']==row['ROI_pixels']and x['model']=='core');ax=fig.add_subplot(gs[2,1]);M,mapping,_ar=measurement_mesh(sc,'core')
    if plane is not None and M is not None:
        u,v=plane_basis(plane[:3]);xy=np.c_[M.vertices@u,M.vertices@v];ax.scatter(xy[:,0],xy[:,1],s=.08,c='#cb7393',linewidths=0);f=projected_feret(M.vertices,plane[:3])
        if f is not None:
            poly=xy[f['hull_indices']];ax.plot(*np.r_[poly,poly[:1]].T,'--',color='#999999',linewidth=.6,label='凸包包络，非填充表面');e=xy[f['vertex_ids']];ok=dr['observed_surface_Dproj_mm']is not None;ax.plot(e[:,0],e[:,1],'-o'if ok else'--x',color='#16855c'if ok else'#d62728',markersize=4,label='可评价端点'if ok else'未通过端点/基底检查的候选');ax.legend(fontsize=7)
    candidate=dr['diagnostic_candidate_Dproj_mm'];ax.set_aspect('equal');ax.set(xlabel='基底平面u / mm',ylabel='基底平面v / mm',title='3D MODEL PROJECTED DIAMETER — PROTOTYPE\n'+('NOT EVALUABLE'+(' / 候选='+f'{candidate:.4f}mm'if candidate is not None else'')if dr['observed_surface_Dproj_mm']is None else f'Observed Ω: {dr["observed_surface_Dproj_mm"]:.4f} mm'))
    ax=fig.add_subplot(gs[2,2]);ax.axis('off');ax.text(0,1,'基底: '+row['base_status']+'\n相机: '+row['camera_condition']+'\n原始严格足迹门槛: '+dr['strict_initial_status']+'\n定义审计: '+dr['observed_surface_status']+'\n观测面Feret后验定义审计；非预注册成功\n临床/完整最大直径 = NOT EVALUABLE\n未知、冲突面不参与投影测量\n平面 n = '+('无'if plane is None else np.array2string(plane[:3],precision=4))+'\nGT=NONE',va='top',fontsize=10,wrap=True);fig.suptitle(sc['id']+' | '+cid+' | ROI '+str(row['ROI_pixels'])+'\n真实源RGB/Mask、实际背景点、冻结基底拟合、高度与观测投影直径；不能作为绝对三维精度证明',fontsize=15);png(fig,dest)
def compose_reviews(index=None):
    index=index or load(R/'metrics/VISUALIZATION_INDEX.json');public=[]
    for group in cfg()['groups']:
        items=[x for x in index if x['group']==group];rows=[]
        for item in items:
            a,b,c=[Image.open(p).convert('RGB')for p in item['core_png']];a.thumbnail((2080,1600));b.thumbnail((2080,1600));c.thumbnail((4160,3200));top=max(a.height,b.height);panel=Image.new('RGB',(4200,top+c.height+60),'white');panel.paste(a,((2100-a.width)//2,0));panel.paste(b,(2100+(2100-b.width)//2,0));panel.paste(c,((4200-c.width)//2,top+40));rows.append(panel)
        sheet=Image.new('RGB',(4200,sum(p.height for p in rows)),'white');y=0
        for panel in rows:sheet.paste(panel,(0,y));y+=panel.height
        p=R/'figures'/(group+'_three_stage_review.png');sheet.save(p);public.append(dict(group=group,path=str(p),sha256=sha(p),source_scene_ids=[x['scene']for x in items],content='Full-height metric panel below cleaning/fusion; genuine original image composition only; no cropping'))
    thumbs=Image.new('RGB',(2100,1800),'white')
    for i,p in enumerate(public):
        im=Image.open(p['path']);im.thumbnail((1040,890));thumbs.paste(im,((i%2)*1050,(i//2)*900))
    thumbs.save(R/'visualizations/Overview_Contact_Sheet.png');save('metrics/PUBLIC_FIGURES.json',public);return public
def main():
    scenes_=load(R/'metrics/B_scenes.json');rows=load(R/'metrics/C_height_geometry.json');index=[];params=[]
    for sc in scenes_:
        dest=R/'visualizations'/sc['id'];dest.mkdir(parents=True,exist_ok=True);params+=cleaning_figure(sc,dest);params+=fusion_figure(sc,dest)
        for row in [x for x in rows if x['scene']==sc['id']]:
            p=dest/'height_conditions'/(row['reference']+'_'+str(row['ROI_pixels'][1])+'.png');geometry_figure(sc,row,p)
            if row['reference']==sc['main_reference']and row['ROI_pixels']==[5,30]:shutil.copyfile(p,dest/'Fig3_height_Dxy_geometry.png')
        print('VIS_SCENE_COMPLETE',sc['id'],flush=True);index.append(dict(scene=sc['id'],group=sc['group'],folder=str(dest),core_png=[str(dest/f'Fig{i}_{n}.png')for i,n in [(1,'cleaning'),(2,'incremental_fusion'),(3,'height_Dxy_geometry')]],height_condition_pngs=len([x for x in rows if x['scene']==sc['id']]),status=sc['status']))
    compose_reviews(index);save('metrics/VISUALIZATION_INDEX.json',index);save('provenance/VISUALIZATION_PARAMETERS.json',dict(point_size=.08,alpha=1,CAD_alpha=.15,renderer=str(REPO/'visualization/real_p0_renderer.py'),core_views=dict(cleaning=[0,0],fusion=[-65,22]),source_point_subsampling=False,subdivision_midpoints_rendered_as_P0_points=False,panels=params));print('FOUR_GROUP_REVIEW_SHEETS_COMPLETE',flush=True)
if __name__=='__main__':main()
