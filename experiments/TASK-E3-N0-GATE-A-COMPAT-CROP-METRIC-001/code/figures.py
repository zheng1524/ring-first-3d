"""Four actual-data GateA figures; no neural/TSDF output is generated or displayed."""
from crop import *
from human_review_figures import wire_box
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.patches import Rectangle
from matplotlib.colors import ListedColormap
plt=vis.configure();plt.rcParams.update({'font.size':9,'axes.titlesize':10})
V=R/'derived_projective_v1';CL=['#2374b7','#33a868','#df8434']
def cdata(cid):return np.load(V/'local_results/crops'/(cid+'.npz'))
def finish(fig,name,footer):
    fig.text(.5,.009,footer,ha='center',fontsize=9);fig.tight_layout(rect=(0,.035,1,.965));fig.savefig(R/'figures'/name,dpi=155,facecolor='white');plt.close(fig);print('CORE_FIGURE',name,flush=True)
def fig1():
    fig,ax=plt.subplots(6,4,figsize=(17,19));fig.suptitle('Fig 1 | 六来源真实输入与独立等比例裁剪；派生副本仅排除经复核的46点',fontsize=15)
    rows=list(csv.DictReader((V/'CROP_GEOMETRY_TESTS.csv').open()))
    for i,cid in enumerate(IDS):
        s=native(cid);c=cdata(cid);row=rows[i];box=affine_uv(np.array([c['crop_bbox'][:2],c['crop_bbox'][2:]]),s['K']@np.linalg.inv(s['Kn']));ax[i,0].imshow(s['RGB']);ax[i,0].contour(s['labels']==1,[.5],colors=['#2dda6a'],linewidths=.6);ax[i,0].contour(s['labels']==2,[.5],colors=['#17bcff'],linewidths=.6);ax[i,0].add_patch(Rectangle(box[0],*(box[1]-box[0]),fill=False,edgecolor='yellow',lw=1));ax[i,0].set_title(cid+'\n归档640×360；黄色为native裁剪框映射');ax[i,0].axis('off')
        im=ax[i,1].imshow(np.ma.masked_where(~s['valid'],s['depth']),cmap='viridis',vmin=20,vmax=90);ax[i,1].set_title('原生640×352 / 原始合法Polyp深度');ax[i,1].axis('off');fig.colorbar(im,ax=ax[i,1],fraction=.035,pad=.01,label='mm')
        im=ax[i,2].imshow(np.ma.masked_where(~c['valid'],c['depth_mm']),cmap='viridis',vmin=20,vmax=90);pad=np.where(c['semantics']==4,1.,np.nan);ax[i,2].imshow(pad,cmap=ListedColormap(['#eeee77']),vmin=0,vmax=1,alpha=.8);ax[i,2].contour(c['labels']==2,[.5],colors=['#17bcff'],linewidths=.5);ax[i,2].set_title(f"320×240；a={row['scale'][:7]}\nPad={row['padding_output_N']}像素 / Ring深度=0");ax[i,2].axis('off')
        K=s['Kn'];Kp=c['K_crop'];ax[i,3].axis('off');ax[i,3].text(0,1,f"K native → K crop\nfx {K[0,0]:.3f} → {Kp[0,0]:.3f}\nfy {K[1,1]:.3f} → {Kp[1,1]:.3f}\ncx {K[0,2]:.3f} → {Kp[0,2]:.3f}\ncy {K[1,2]:.3f} → {Kp[1,2]:.3f}\n\n派生输入有效N={row['original_legal_N']}\n原ID直接采到={float(row['original_ID_retention'])*100:.2f}%\n解析最大={float(row['analytic_XYZ_max_mm']):.2e} mm\n{row['thin_status']}",va='top',fontsize=9)
    finish(fig,'Fig1_RGB_Mask_Crop.png','6源顺序固定；源原图/Mask/相机不变。灰黄仅为Padding，非法深度均0；原始与派生全部分母分别保留。')
def draw_cloud(ax,P,C,title,zoom=None):
    s=native(CORE[0]);scene=SameCameraScene(ringmesh(),s['K'],s['T'],(640,360),VENDOR);scene.draw(ax,P,C,np.empty((0,3)),np.empty((0,3)),point_size=.6);scene.scale_bar(ax);ax.set_title(title)
    if zoom is not None:ax.set_xlim(zoom[0],zoom[2]);ax.set_ylim(zoom[3],zoom[1])
def fig2():
    original=[];cropped=[];rgb=[];rgbc=[];source_col=[];source_colc=[];lostP=[]
    for j,cid in enumerate(CORE):
        s=native(cid);c=cdata(cid);original.append(s['X']);cropped.append(c['output_X_mm']);uv=s['native_uv'];rgb.append(s['native_RGB'][uv[:,1],uv[:,0]]/255.);q=c['output_uv'];rgbc.append(c['RGB'][q[:,1],q[:,0]]/255.);from matplotlib.colors import to_rgb
        source_col.append(np.tile(to_rgb(CL[j]),(len(s['X']),1)));source_colc.append(np.tile(to_rgb(CL[j]),(len(c['output_X_mm']),1)));represented=np.unique(c['source_ids'][c['valid']]);lostP.append(s['X'][~np.isin(s['native_id'],represented)])
    P=np.concatenate(original);Pc=np.concatenate(cropped);s=native(CORE[0]);uv,z=vis.project_camera(np.r_[P,Pc,ringmesh().vertices],s['K'],s['T']);inside=(z>0)&np.isfinite(uv).all(1);q=uv[inside];zoom=[max(0,q[:,0].min()-10),max(0,q[:,1].min()-10),min(640,q[:,0].max()+10),min(360,q[:,1].max()+10)]
    fig,ax=plt.subplots(2,2,figsize=(15,11));fig.suptitle('Fig 2 | 三CORE原始XYZ ↔ 实际裁后XYZ；同一冻结ref08观察相机、同毫米尺度',fontsize=15)
    draw_cloud(ax[0,0],P,np.concatenate(rgb),'原始native有效深度点 / source RGB');draw_cloud(ax[0,1],Pc,np.concatenate(rgbc),'实际320×240最近邻采样点 / crop RGB');draw_cloud(ax[1,0],P,np.concatenate(source_col),'源身份：ref08蓝 / ref13绿 / ref03橙；红=原ID未直接采到',zoom);draw_cloud(ax[1,1],Pc,np.concatenate(source_colc),'裁后保留同源身份；不同a不改变世界坐标',zoom)
    lost=np.concatenate(lostP);uv,z=vis.project_camera(lost,s['K'],s['T']);cad,_=cast(ringscene(),uv,s['K'],s['T']);visp=(z>0)&((~np.isfinite(cad))|(z<=cad+.002));ax[1,0].scatter(uv[visp,0],uv[visp,1],s=.4,c='red',linewidths=0,zorder=4)
    finish(fig,'Fig2_Raw_vs_Cropped_CORE3_XYZ.png','黑色CAD为真实冻结实体；没有Mesh补面或网络输出。红点表示重采样身份损失，不是被删的真实组织；解析误差与采样误差分开统计。')
def fig3():
    summary=list(csv.DictReader((R/'CROSS_VIEW_PROJECTION_VALIDATION.csv').open()))[:6];fig,ax=plt.subplots(6,3,figsize=(17,20));fig.suptitle('Fig 3 | 六组CORE有向投影：原始目标投影与裁后投影严格闭环',fontsize=15)
    for i,r in enumerate(summary):
        t=native(r['target']);c=cdata(r['target']);d=np.load(R/'local_results/cross_view'/(r['origin']+'__'+r['target']+'.npz'));n=len(d['X_world_mm']);j=np.unique(np.linspace(0,n-1,min(n,650),dtype=int));uvarch,_=vis.project_camera(d['X_world_mm'][j],t['K'],t['T']);backarch=affine_uv(d['inverse_crop_target_uv'][j],t['K']@np.linalg.inv(t['Kn']));q=d['crop_target_uv'][j];expect=d['affine_transformed_original_uv'][j];hidden=d['CAD_occluded'][j]
        ax[i,0].imshow(t['RGB']);ax[i,0].contour(t['labels']==1,[.5],colors=['#2cda6a'],linewidths=.6);ax[i,0].contour(t['labels']==2,[.5],colors=['#19baff'],linewidths=.6);ax[i,0].scatter(*uvarch.T,s=9,facecolors='none',edgecolors='red',lw=.5);ax[i,0].scatter(*backarch.T,s=5,c='#1e81d3',marker='+',lw=.4);ax[i,0].set(xlim=(0,640),ylim=(360,0),title=r['origin'].split('004_')[1]+' → '+r['target'].split('004_')[1]+' / 目标真实RGB');ax[i,0].axis('off')
        ax[i,1].imshow(c['RGB']);ax[i,1].contour(c['labels']==1,[.5],colors=['#2cda6a'],linewidths=.6);ax[i,1].scatter(*expect.T,s=10,facecolors='none',edgecolors='red',lw=.5);ax[i,1].scatter(*q.T,s=5,c='#1e81d3',marker='+',lw=.4);ax[i,1].scatter(q[hidden,0],q[hidden,1],s=8,c='gray',marker='x',lw=.5);ax[i,1].set(xlim=(0,320),ylim=(240,0),title='A·原投影 红圈 / Kcrop直接投影 蓝十字\n灰×=CAD遮挡，完全重叠是预期');ax[i,1].axis('off')
        ax[i,2].axis('off');ax[i,2].text(0,1,f"固定原点分母 N={r['source_point_denominator']}\n解析残差 / px\nmedian {float(r['analytic_projection_median_px']):.3e}\np95       {float(r['analytic_projection_p95_px']):.3e}\nmax       {float(r['analytic_projection_max_px']):.3e}\n\n原目标图内 {r['inside_native_target_N']}\n裁后图外 {r['OUT_OF_CROP_FIELD_N']}\nCAD遮挡 {r['CAD_OCCLUDED_N']}\n采样后目标支持未保留 {r['CROP_LOST_SUPPORT_N']}\nPASS：只证明变换不变性\n相机原资格仍为INSUFFICIENT_EVIDENCE",va='top',fontsize=10)
    finish(fig,'Fig3_CrossView_Invariance.png','每图按原ID均匀显示≤650点，仅显示采样；数值对全部原始合法点计算，无失败射线过滤。另18个条件性有向关系完整记录于CSV。')
def scene_domain(ax,domain,derived=False):
    for cid in IDS:
        s=native(cid);X=s['X'];m=np.load(R/'local_results/projective_cleanup_v1'/(cid+'.npz'))['projective_excluded'];keep=~m[s['native_uv'][:,1],s['native_uv'][:,0]]if derived else np.ones(len(X),bool);X=X[keep];j=np.unique(np.linspace(0,len(X)-1,min(5000,len(X)),dtype=int));ax.scatter(*X[j].T,s=.2,c='#88a1b2',alpha=.6)
    cad=ringmesh();ax.add_collection3d(Poly3DCollection(np.asarray(cad.vertices)[np.asarray(cad.faces)],facecolors='black',edgecolors='none'));wire_box(ax,domain,'#258552','共同128³候选边界');ax.set(xlabel='X / mm',ylabel='Y / mm',zlabel='Z / mm');ax.view_init(20,-65)
def fig4():
    before=load(R/'METRIC_TRANSFORM.json')['domains']['ALL_INPUTS'];after=load(V/'METRIC_TRANSFORM.json')['domains']['ALL_INPUTS'];cleanup=load(R/'PROJECTIVE_CLEANUP_SUMMARY.json');fig=plt.figure(figsize=(18,12));ax0=fig.add_subplot(2,3,1,projection='3d');ax1=fig.add_subplot(2,3,2,projection='3d');scene_domain(ax0,before);scene_domain(ax1,after,True);lim=np.array([before['world_cube_min_mm'],before['world_cube_max_mm']]);
    for a in [ax0,ax1]:a.set_xlim(*lim[:,0]);a.set_ylim(*lim[:,1]);a.set_zlim(*lim[:,2]);a.set_box_aspect((1,1,1))
    ax0.set_title('原始全部输入 / 61.837mm共同域');ax1.set_title('用户授权一轮派生清理后 / 29.641mm共同域')
    ax=fig.add_subplot(2,3,3);ax.axis('off');ax.text(0,1,f"不是神经重建，只是模型域候选\n\n清理候选55：排除46，保留未决9\n原始输入像素修改=0\n裁剪规则/相机/来源重选=0\n\n128³物理体素\n{before['voxel_mm']:.4f} → {after['voxel_mm']:.4f} mm\nRing外径占格数\n{before['ring_outer_diameter_voxels']:.1f} → {after['ring_outer_diameter_voxels']:.1f}\n\n清理后的全包域容纳全部保留输入。\n小诊断域仍有9点出界，不强删。\nr14细结构代理仍未解决。",va='top',fontsize=12)
    s=native('G01_004_new_r00');d=list(csv.DictReader((R/'PROJECTIVE_CLEANUP_DECISIONS.csv').open()));p=np.array([[float(r['archive_u']),float(r['archive_v'])]for r in d]);removed=np.array([r['derived_action']=='PROJECTIVE_EXCLUDE'for r in d]);ax=fig.add_subplot(2,3,4);ax.imshow(s['RGB']);ax.contour(s['labels']==1,[.5],colors=['#28ce69'],linewidths=.5);ax.scatter(*p[removed].T,s=12,facecolors='none',edgecolors='#2665d1',label='派生排除46');ax.scatter(*p[~removed].T,s=14,facecolors='none',edgecolors='#e97923',label='未决保留9');ax.set(xlim=(330,535),ylim=(160,35),title='真实RGB上的清理身份；未修改原图');ax.legend(fontsize=8)
    ax=fig.add_subplot(2,3,5);row=59;u=np.arange(340,530);depth=s['depth'][row,u];clean=np.load(R/'local_results/projective_cleanup_v1'/(s['id']+'.npz'));a=np.where((s['native_labels'][row,u]==1),depth,np.nan);b=np.where(clean['valid'][row,u],clean['depth_mm'][row,u],np.nan);ax.plot(u,a,'.-',c='gray',ms=2,label='原始合法Polyp');ax.plot(u,b,'.-',c='#2665d1',ms=2,label='派生保留Polyp');ax.set(xlabel='native u / px',ylabel='轴向深度 / mm',title='同一行原始/派生；断线为无效，不补深度');ax.legend();ax.grid(alpha=.2)
    r14=cdata('G01_004_growth_r14');dt,ridge=ridge_proxy(r14['valid']);v,u=np.argwhere(ridge&(2*dt<3))[0];ax=fig.add_subplot(2,3,6);ax.imshow(r14['labels'],cmap=ListedColormap(['white','#50c878','#24a6ef']),vmin=0,vmax=2,interpolation='nearest');ax.plot(u,v,'r+');ax.set(xlim=(u-10,u+10),ylim=(v+10,v-10),title='r14：2输出像素边缘代理（未认证细柄）',xlabel='crop u',ylabel='crop v')
    fig.suptitle('Fig 4 | 共同模型尺度、真实远端候选与保留失败；黑色实体为冻结 Ring CAD',fontsize=15);finish(fig,'Fig4_Metric_And_Failure.png','一轮清理依据跨视角条件性证据；9个未决点仍保留。原始失败门槛和所有原像素分母保留，正式GateA及GateB授权未升级。')
if __name__=='__main__':fig1();fig2();fig3();fig4()
