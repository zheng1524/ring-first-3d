"""Immediate human review of all55 original pixels, never input deletion."""
from crop import *
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.patches import Rectangle
from matplotlib.colors import ListedColormap
plt=vis.configure();plt.rcParams.update({'font.size':10,'axes.titlesize':11})

def archive_uv(s,uv):return affine_uv(uv,s['K']@np.linalg.inv(s['Kn']))
def add_mask(ax,s,alpha=1):
    ax.contour(s['labels']==1,[.5],colors=['#20de65'],linewidths=.8,alpha=alpha);ax.contour(s['labels']==2,[.5],colors=['#19b9ff'],linewidths=.8,alpha=alpha)
def image_axes(ax,s,title,uv=None,window=None,mask=False):
    ax.imshow(s['RGB']);ax.set_title(title)
    if mask:add_mask(ax,s)
    if uv is not None:ax.scatter(uv[:,0],uv[:,1],s=15,facecolors='none',edgecolors='#f23436',linewidths=.8)
    if window is not None:ax.set_xlim(window[0],window[2]);ax.set_ylim(window[3],window[1])
    else:ax.set_xlim(0,640);ax.set_ylim(360,0)
    ax.set_aspect('equal');ax.set_xlabel('归档原图 u / px');ax.set_ylabel('归档原图 v / px')
def wire_box(ax,dom,color,label):
    lo=np.asarray(dom['world_cube_min_mm']);hi=np.asarray(dom['world_cube_max_mm']);V=np.array([[hi[d]if i&(1<<d)else lo[d]for d in range(3)]for i in range(8)])
    for i in range(8):
        for d in range(3):
            j=i^(1<<d)
            if i<j:ax.plot(*V[[i,j]].T,c=color,lw=1,alpha=.7)
    ax.plot([],[],[],c=color,label=label)
def main():
    metric=load(R/'METRIC_TRANSFORM.json');dom=metric['domains']['RAW_AGREEMENT_DIAGNOSTIC_ONLY'];s=native('G01_004_new_r00');O=np.array(dom['O_mm']);L=dom['L_mm'];g=(s['X']-O)/L;outside=((g<0)|(g>=1)).any(1);idx=np.flatnonzero(outside);assert len(idx)==55
    uv=s['native_uv'][idx];p=archive_uv(s,uv);z=s['depth'][uv[:,1],uv[:,0]];M=np.zeros(s['depth'].shape,np.uint8);M[uv[:,1],uv[:,0]]=1;n,labels,stats_cc,ctrs=cv2.connectedComponentsWithStats(M,8)
    rows=[]
    for k,j in enumerate(idx):
        u,v=s['native_uv'][j];X=s['X'][j];rows.append(dict(review_id='P'+str(k+1).zfill(2),source=s['id'],native_pixel_id=int(s['native_id'][j]),native_u=int(u),native_v=int(v),archive_u=float(p[k,0]),archive_v=float(p[k,1]),HERO_axial_Z_mm=float(z[k]),X_mm=float(X[0]),Y_mm=float(X[1]),Z_world_mm=float(X[2]),native_label=int(s['native_labels'][v,u]),outside_diagnostic_domain=True,inside_all_input_domain=True,deleted=False,physical_validity='UNRESOLVED_HUMAN_REVIEW'))
    table('HUMAN_REVIEW_POINTS.csv',rows);focus=[int(idx[np.argmax(z)]),int(idx[np.argmin(z)])];window=[max(0,p[:,0].min()-20),max(0,p[:,1].min()-20),min(639,p[:,0].max()+20),min(359,p[:,1].max()+20)]
    fig=plt.figure(figsize=(19,13));axes=[fig.add_subplot(3,3,i+1)for i in range(9)];fig.suptitle('现场判读 1 | 扩大三维盒子的55个点：全部来自 new_r00；尚未删除或判错',fontsize=17)
    image_axes(axes[0],s,'① 未标注的真实 RGB（frame index 00）');image_axes(axes[1],s,'② 原始 Mask + 全部55点（红圈）',p,mask=True);axes[1].add_patch(Rectangle((window[0],window[1]),window[2]-window[0],window[3]-window[1],fill=False,edgecolor='yellow',lw=1))
    dep=np.ma.masked_where(~s['valid'],s['depth']);im=axes[2].imshow(dep,cmap='viridis',vmin=20,vmax=90);axes[2].scatter(uv[:,0],uv[:,1],s=12,c='red',marker='+');axes[2].set_title('③ 原生 HERO 合法 Polyp 深度（mm）');axes[2].set(xlabel='native u',ylabel='native v');fig.colorbar(im,ax=axes[2],label='相机轴向 Z / mm',fraction=.04)
    image_axes(axes[3],s,'④ 真实 RGB 放大；保留原始亮度',p,window);image_axes(axes[4],s,'⑤ 同位置 + 原始 Mask 边界',p,window,True)
    A=s['K']@np.linalg.inv(s['Kn']);inv=np.linalg.inv(A);nw=affine_uv(np.array([[window[0],window[1]],[window[2],window[3]]]),inv);axes[5].imshow(s['native_labels'],cmap=ListedColormap(['#f4f4f4','#50c878','#24a6ef']),vmin=0,vmax=2,interpolation='nearest');axes[5].scatter(uv[:,0],uv[:,1],s=18,facecolors='none',edgecolors='red');axes[5].set(xlim=(nw[0,0],nw[1,0]),ylim=(nw[1,1],nw[0,1]),title='⑥ 原生 Mask 像素：绿=Polyp，蓝=Ring，白=背景',xlabel='native u',ylabel='native v')
    row=int(uv[np.argmax(z),1]);xx=np.arange(max(0,int(uv[:,0].min())-15),min(640,int(uv[:,0].max())+16));dd=s['depth'][row,xx];axes[6].plot(xx,dd,'.-',c='#2e6fb5',ms=3);sel=uv[:,1]==row;axes[6].scatter(uv[sel,0],s['depth'][row,uv[sel,0]],c='red',s=25,label='55点中位于此行的点');axes[6].set(title=f'⑦ 最高深度点所在原生行 v={row}',xlabel='native u / px',ylabel='原始 HERO 轴向深度 / mm');axes[6].grid(alpha=.2);axes[6].legend(fontsize=8)
    fig.delaxes(axes[7]);ax3=fig.add_subplot(3,3,8,projection='3d')
    for cid in IDS:
        ss=native(cid);ii=np.unique(np.linspace(0,len(ss['X'])-1,min(6000,len(ss['X'])),dtype=int));ax3.scatter(*ss['X'][ii].T,s=.25,c='#829aaf',alpha=.5)
    ax3.scatter(*s['X'][idx].T,s=9,c='red',label='55个保留的原始点');ring=ringmesh();ax3.add_collection3d(Poly3DCollection(np.asarray(ring.vertices)[np.asarray(ring.faces)],facecolors='black',edgecolors='none'));wire_box(ax3,metric['domains']['ALL_INPUTS'],'#929292','全包域 61.837mm');wire_box(ax3,dom,'#248c46','诊断小域 25.735mm');ax3.set(xlabel='X / mm',ylabel='Y / mm',zlabel='Z / mm',title='⑧ 实际三维位置 + 黑色冻结 Ring CAD');ax3.view_init(20,-65);ax3.set_box_aspect((1,1,1));ax3.legend(fontsize=7,loc='upper left')
    axes[8].axis('off');axes[8].text(0,1,'供现场判断\n\n红圈是否落在真正息肉上？\n绿色 Polyp 边界是否包含了 Ring 或背景？\n\n55 / 22,815 个合法 new_r00 像素\n原生深度范围：'+f'{z.min():.2f}–{z.max():.2f} mm\n'+f'像素连通小簇：{n-1}\n\n'+'原始相机资格：INSUFFICIENT_EVIDENCE\n图像位置可以判读，深度仍需几何证据。\n输入未删除，正式模型域未选择。',va='top',fontsize=12)
    fig.text(.5,.015,'真实项目数据；红圈是待判断输入，不是物理错误标签。原生352×640与归档360×640按冻结K映射。没有网络融合输出。',ha='center');fig.tight_layout(rect=(0,.04,1,.96));p1=R/'figures/REVIEW01_new_r00_55_points.png';fig.savefig(p1,dpi=170,facecolor='white');plt.close(fig)
    # Four representative connected clusters, if present; every point remains in CSV.
    components=sorted(range(1,n),key=lambda k:(-stats_cc[k,4],k));chosen=components[:4];fig,ax=plt.subplots(2,4,figsize=(18,9));fig.suptitle('现场判读 2 | 原始像素局部：远端点区域与 r14 裁剪薄结构代理',fontsize=16)
    for j in range(4):
        if j>=len(chosen):ax[0,j].axis('off');continue
        k=chosen[j];member=labels[uv[:,1],uv[:,0]]==k;q=p[member];box=[max(0,q[:,0].min()-10),max(0,q[:,1].min()-10),min(639,q[:,0].max()+10),min(359,q[:,1].max()+10)];image_axes(ax[0,j],s,f'远端点簇 {k}：{member.sum()} 点\n原图 / Mask；深度 {z[member].min():.1f}–{z[member].max():.1f}mm',q,box,True)
    r14=native('G01_004_growth_r14');c=np.load(R/'local_results/crops'/(r14['id']+'.npz'));dt,ridge=ridge_proxy(c['valid']);bad=ridge&(2*dt<3);yy,xx=np.nonzero(bad);u,v=int(xx[0]),int(yy[0]);native_pix=c['nearest_source_uv'][v,u];arch=archive_uv(r14,native_pix[None])[0]
    image_axes(ax[1,0],r14,'r14 真实RGB：黄色位置为薄结构代理',window=[max(0,arch[0]-25),max(0,arch[1]-25),min(639,arch[0]+25),min(359,arch[1]+25)],mask=True);ax[1,0].plot(*arch,'+',c='yellow',ms=12)
    un,vn=native_pix;ax[1,1].imshow(r14['native_labels'],cmap=ListedColormap(['white','#50c878','#24a6ef']),vmin=0,vmax=2,interpolation='nearest');ax[1,1].plot(un,vn,'r+');ax[1,1].set(xlim=(un-10,un+10),ylim=(vn+10,vn-10),title='r14 原生 Mask 局部',xlabel='native u',ylabel='native v')
    ax[1,2].imshow(c['labels'],cmap=ListedColormap(['white','#50c878','#24a6ef']),vmin=0,vmax=2,interpolation='nearest');ax[1,2].plot(u,v,'r+');ax[1,2].set(xlim=(u-11,u+11),ylim=(v+11,v-11),title='r14 320×240 Mask 同位置\n红十字宽度代理=2输出像素',xlabel='crop u',ylabel='crop v')
    ax[1,3].axis('off');ax[1,3].text(0,1,'r14 此例尚不是已认证的细柄。\n它也可能只是重采样后的 Mask 边缘锯齿。\n\n上排展示按点数排序的前4个远端点簇，\n全部55点仍保留在第一张图和CSV中。\n\n请优先判断：\n① new_r00红圈的组织/Mask归属；\n② r14红十字是否是实际独有结构。',va='top',fontsize=11)
    fig.text(.5,.015,'所有局部窗只用于人工放大显示，没有改变送入适配器的ROI、Mask或深度。未作单源手工修正。',ha='center');fig.tight_layout(rect=(0,.04,1,.95));p2=R/'figures/REVIEW02_pixel_details_and_r14.png';fig.savefig(p2,dpi=180,facecolor='white');plt.close(fig)
    save('HUMAN_REVIEW_CONTEXT.json',dict(status='AWAITING_RESEARCHER_IMAGE_JUDGMENT',out_of_domain_original_pixel_N=55,all_from='G01_004_new_r00',native_depth_range_mm=[float(z.min()),float(z.max())],connected_cluster_N=n-1,figures=[asset(p1),asset(p2)],original_assets=next(r for r in MANIFEST['sources']if r['source_id']==s['id'])['assets'],input_mutations=0,physical_ROI_frozen=False,r14_candidate=dict(crop_uv=[u,v],native_uv=native_pix,archive_uv=arch,width_output_px=2.,anatomy_certified=False)))
    print('REVIEW_READY',p1,p2,'55 points; all original inputs intact',flush=True)
if __name__=='__main__':main()
