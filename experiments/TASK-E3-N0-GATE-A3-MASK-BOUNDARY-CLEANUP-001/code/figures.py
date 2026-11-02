"""Four real-data figures; original meshes unchanged and no fusion output."""
from analyze import *
from matplotlib.colors import ListedColormap
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
plt=vis.configure();plt.rcParams.update({'font.size':9,'axes.titlesize':10})
extract(A2/'code/figures.py',['image','axes3','cad3'],globals())
DISPLAY_VERSIONS=['V1','V2','V3','V4']

def finish(fig,name):
    fig.text(.5,.008,'真实RGB/HERO输入诊断；黑色为冻结Ring CAD实体；毫米坐标不变；无GT、补面、神经融合。V4=V3再屏蔽人工指定260点；不是5px方案。',ha='center',fontsize=8)
    fig.tight_layout(rect=(0,.027,1,.96));fig.savefig(R/'figures'/name,dpi=145,facecolor='white');plt.close(fig);print('FIG',name,flush=True)

def figure1():
    aa=read_csv(R/'CANDIDATE_DISTANCE_AUDIT.csv');extra=read_csv(R/'V4_260_CANDIDATES.csv');old=read_csv(A2/'PROJECTIVE_CLEANUP_DECISIONS.csv');fig,axes=plt.subplots(6,3,figsize=(18,22));fig.suptitle('Figure 1 | 原RGB/Mask：红=V2边缘B，橙=V2保留B，青=背景B；蓝菱=V4人工指定池外260点',fontsize=13)
    counts=[]
    for i,cid in enumerate(IDS):
        s=v1(cid);rows=[a for a in aa if a['source']==cid];p=np.array([[float(a['archive_continuous_u']),float(a['archive_continuous_v'])] for a in rows]);colors=['#11a9d1' if a['user_approved_BG']=='True' else '#e33535' if a['V2_new_suppress']=='True' else '#e3a10b' for a in rows]
        image(axes[i,0],s,cid+' / 原RGB+Mask+黑色CAD');axes[i,0].scatter(*p.T,s=7,c=colors,linewidths=0,zorder=5)
        aold=[a for a in old if a['source']==cid and a['action']=='DERIVED_EXCLUDE'];op=archive_uv(s,np.array([[int(a['native_u']),int(a['native_v'])] for a in aold]));axes[i,0].scatter(*op.T,s=5,c='#444444',marker='x',linewidths=.4,zorder=4)
        er=[a for a in extra if a['source']==cid];ep=archive_uv(s,np.array([[int(a['native_u']),int(a['native_v'])] for a in er])) if er else np.empty((0,2));pp=np.r_[p,ep]
        axes[i,0].scatter(*ep.T,s=9,facecolors='none',edgecolors='#255bd0',marker='D',linewidths=.55,zorder=6)
        if len(pp):lo=pp.min(0)-15;hi=pp.max(0)+15;window=[max(0,lo[0]),max(0,lo[1]),min(639,hi[0]),min(359,hi[1])]
        else:window=None
        image(axes[i,1],s,'同一真实RGB放大；灰×为A2已屏蔽红A',window=window);axes[i,1].scatter(*p.T,s=11,c=colors,linewidths=0,zorder=5);axes[i,1].scatter(*ep.T,s=13,facecolors='none',edgecolors='#255bd0',marker='D',linewidths=.6,zorder=6)
        dist=[float(a['distance_native_px']) for a in rows if a['original_mask_label']=='1'];axes[i,2].hist(dist,bins=np.arange(0,max(6,max(dist,default=5))+1,.5),color='#dca026',edgecolor='white');axes[i,2].axvline(2,color='red',lw=1.3)
        edge=sum(a['insidePolyp_edge_le2']=='True' for a in rows);bg=sum(a['user_approved_BG']=='True' for a in rows);interior=sum(a['original_mask_label']=='1' and float(a['distance_native_px'])>2 for a in rows)
        axes[i,2].set(title=f"B={len(rows)}；Polyp边缘≤2px={edge}\n内部保留={interior}；背景={bg}；V4额外={len(er)}",xlabel='原始Mask距离 / 原生像素单位',ylabel='B候选数');axes[i,2].grid(axis='y',alpha=.2);counts.append(dict(source=cid,B=len(rows),edge=edge,BG=bg,interior=interior,V4_extra=len(er)))
    save('config/FIGURE1_COUNTS.json',counts);finish(fig,'Fig1_RGB_Mask_Decisions.png')

def figure2():
    fig=plt.figure(figsize=(21,12));fig.suptitle('Figure 2 | V1/V2/V3/V4：相同相机、毫米范围、点ID预算、CAD及27.959mm共同模型域',fontsize=14)
    ref=native(CORE[0]);scene=SameCameraScene(ringmesh(),ref['K'],ref['T'],(640,360),VENDOR);dom=primary_protocol()['common_model_domain'];lo=np.asarray(dom['world_cube_min_mm']);hi=np.asarray(dom['world_cube_max_mm'])
    # Fixed identity display pool from V1, with every B candidate also included.
    pool={};aa=read_csv(R/'CANDIDATE_DISTANCE_AUDIT.csv')+read_csv(R/'V4_260_CANDIDATES.csv')
    for cid in IDS:
        b=v1(cid);idx=np.unique(np.linspace(0,len(b['native_id'])-1,min(1800,len(b['native_id'])),dtype=int));pool[cid]=np.union1d(b['native_id'][idx],np.array([int(a['native_id']) for a in aa if a['source']==cid],int))
    allP=np.concatenate([v1(cid)['X'] for cid in IDS]);uv,z=vis.project_camera(allP,ref['K'],ref['T']);good=(z>0)&np.isfinite(uv).all(1);zoom=[max(0,uv[good,0].min()-12),max(0,uv[good,1].min()-12),min(640,uv[good,0].max()+12),min(360,uv[good,1].max()+12)]
    totals=load(R/'FOUR_VERSION_COMPARISON.json')['versions'];render=[]
    for k,version in enumerate(DISPLAY_VERSIONS):
        pts=[];rgb=[]
        for cid in IDS:
            s=cohort(cid,version);ids=pool[cid];ids=ids[s['valid'].ravel()[ids]];uv=np.c_[ids%640,ids//640];pts.append(unproject(s['depth'].ravel()[ids].astype(float),s['T'],uv,s['Kn']));rgb.append(s['native_RGB'][uv[:,1],uv[:,0]]/255.)
        P=np.concatenate(pts);C=np.concatenate(rgb);ax=fig.add_subplot(2,4,k+1);_,_,details=scene.draw(ax,P,C,np.empty((0,3)),np.empty((0,3)),point_size=.9);ax.set(xlim=(zoom[0],zoom[2]),ylim=(zoom[3],zoom[1]),title=f"{version} / 固定ref08真实相机\n输入N={totals[k]['retained_N']:,}；显示ID={len(P):,}");ax.text(.01,.02,'黑色CAD外径12.4mm（公制参考）',transform=ax.transAxes,fontsize=8,clip_on=True)
        ax=fig.add_subplot(2,4,k+5,projection='3d');ax.scatter(*P.T,s=.6,c=C,depthshade=False);cad3(ax);axes3(ax,lo,hi);wire_box(ax,dom,'#808080','共享比较域');ax.set_title(f"{version} / 相同世界毫米范围\nRaw距离>1mm代理N={totals[k]['retained_raw_far_gt1mm_N']}")
        render.append(dict(version=version,display_N=len(P),actual_total_N=totals[k]['retained_N'],fixed_V1_identity_pool=True,renderer=details))
    save('config/FIGURE2_RENDER.json',render);finish(fig,'Fig2_Three_Version_3D.png')

def depth_patch(ax,s,u,v,title):
    im=ax.imshow(np.ma.masked_where(~s['valid'],s['depth']),cmap='viridis',vmin=25,vmax=55,interpolation='nearest');ax.contour(s['native_labels']==1,[.5],colors=['#28a65f'],linewidths=.6);ax.plot(u,v,'r+',ms=10);ax.set(xlim=(u-7,u+7),ylim=(v+7,v-7),xlabel='native u',ylabel='native v',title=title);return im

def figure3():
    cases=[a for a in read_csv(R/'FIXED_DEPTH_CASES.csv') if a['version']=='V1'];fig,axes=plt.subplots(3,6,figsize=(23,13));fig.suptitle('Figure 3 | 固定三个原生深度断层：屏蔽产生Unknown，不把缺失当作深度纠正',fontsize=14)
    trace=[]
    for i,a in enumerate(cases):
        cid=a['source'];b=v1(cid);u,v=int(a['original_u']),int(a['original_v']);pu,pv=int(a['selected_u']),int(a['selected_v']);q=archive_uv(b,np.array([[u,v],[pu,pv]]));window=[q[:,0].min()-20,q[:,1].min()-20,q[:,0].max()+20,q[:,1].max()+20]
        image(axes[i,0],b,cid.split('004_')[1]+f" / 原生ID {a['original_native_id']}\n红=原点，黄=被NN选中的原点",q[0],window);axes[i,0].plot(*q[1],'y+',ms=11,zorder=6)
        for j,version in enumerate(DISPLAY_VERSIONS):
            s=cohort(cid,version);valid=bool(s['valid'][pv,pu]);im=depth_patch(axes[i,j+1],s,pu,pv,f"{version} / 被选远层仍有效={valid}\n原点仍有效={bool(s['valid'][v,u])}");axes[i,j+1].plot(u,v,'r+',ms=9);axes[i,j+1].plot(pu,pv,'y+',ms=9)
        xx=np.arange(min(u,pu)-6,max(u,pu)+7);axes[i,5].plot(xx,np.where(b['valid'][v,xx],b['depth'][v,xx],np.nan),'.-',c='#657789',label='V1合法原生深度')
        for version,col in [('V2','#dc7620'),('V3','#cc3333'),('V4','#2166c5')]:
            s=cohort(cid,version);zz=np.where(s['valid'][v,xx],s['depth'][v,xx],np.nan);axes[i,5].plot(xx,zz,'.-',color=col,label=version,alpha=.8)
        axes[i,5].set(title=f"原生跳变{abs(float(a['V1_original_depth_mm'])-float(a['V1_selected_depth_mm'])):.2f}mm\nV2/V3/V4对应输出Unknown",xlabel='native u',ylabel='轴向Z / mm');axes[i,5].legend(fontsize=8);axes[i,5].grid(alpha=.2)
    finish(fig,'Fig3_Depth_Discontinuities.png')

def center_of_gap(cid,region,incremental_V4=False):
    b=cohort(cid,'V3') if incremental_V4 else v1(cid);s=cohort(cid,'V4') if incremental_V4 else cohort(cid,'V3');mask=b['valid']&~s['valid']&regions(cid)[region];n,labels,st,cent=cv2.connectedComponentsWithStats(mask.astype(np.uint8),connectivity=8)
    if n>1:
        k=1+int(st[1:,4].argmax());v,u=np.nonzero(labels==k);pts=np.c_[u,v];j=int(np.argmin(np.linalg.norm(pts-cent[k],axis=1)));return pts[j],int(st[k,4])
    vv,uu=np.nonzero(regions(cid)[region]&b['valid']);return np.array([int(np.median(uu)),int(np.median(vv))]),0

def figure4():
    fig,axes=plt.subplots(5,5,figsize=(22,21));fig.suptitle('Figure 4 | 头部、连接处、侧面、主体内部及V4新增260点；保留缺口与风险证据',fontsize=14)
    specs=[(IDS[-1],'head','r14头部 / V3挖孔在V4仍存在'),(IDS[-1],'thin','Ring邻近连接处 / 不认证为细柄'),(IDS[4],'side','r00侧面 / V4额外屏蔽区'),(IDS[2],'body','ref03内部 / V2保留、V3消融'),(IDS[-1],'side','r14池外代理 / 本轮首次逐点审查')];manifest=[]
    for i,(cid,region,title) in enumerate(specs):
        b=v1(cid)
        if region=='thin':uv=np.array([282,215]);gapN=0;radius=10
        else:uv,gapN=center_of_gap(cid,region,incremental_V4=i in [2,4]);radius=22 if region=='head' else 13
        u,v=map(int,uv);p=archive_uv(b,uv[None])[0];window=[p[0]-radius*1.2,p[1]-radius*1.1,p[0]+radius*1.2,p[1]+radius*1.1];image(axes[i,0],b,title,p,window)
        vals=[]
        for j,version in enumerate(DISPLAY_VERSIONS):
            s=cohort(cid,version);labels=np.zeros(s['valid'].shape,np.uint8);labels[s['valid']]=1;labels[b['valid']&~s['valid']]=2
            ax=axes[i,j+1];ax.imshow(labels,cmap=ListedColormap(['#ececec','#54ae80','#e84b44']),vmin=0,vmax=2,interpolation='nearest');ax.contour(b['native_labels']==1,[.5],colors=['#294d38'],linewidths=.7);ax.plot(u,v,'k+',ms=9);ax.set(xlim=(u-radius,u+radius),ylim=(v+radius,v-radius),xlabel='native u',ylabel='native v',title=version+'：绿=保留 / 红=新增屏蔽\n'+f"中心({u},{v})仍有效={bool(s['valid'][v,u])}")
            vals.append(dict(version=version,center_native_id=v*640+u,center_valid=bool(s['valid'][v,u])))
        manifest.append(dict(source=cid,region_proxy=region,center_native_uv=[u,v],selected_V3_gap_component_N=gapN,versions=vals,anatomy_certified=False))
    save('config/FIGURE4_CASES.json',manifest);finish(fig,'Fig4_Surface_Retention_Gaps.png')

if __name__=='__main__':figure1();figure2();figure3();figure4()
