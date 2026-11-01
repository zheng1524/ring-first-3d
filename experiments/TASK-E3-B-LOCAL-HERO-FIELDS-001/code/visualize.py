"""Four CPU figures made only from original whitelisted HERO geometry."""
from mesh_local_field import *
from matplotlib.collections import PolyCollection
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
plt=vis.configure();FIGS={}
PALETTE=['#17967b','#edcf65','#273346','#c4c4c4','#a900b6']
def finish(fig,name,description,source_ids):
    fig.savefig(R/'figures'/name,dpi=140,facecolor='white');plt.close(fig);FIGS[name]=dict(description=description,source_ids=source_ids,geometry='exact immutable original HERO vertices/faces only; no fusion/cleanup/field isosurface extraction',Ring='opaque fixed CAD',model_forward=0);print('FIGURE',name,flush=True)
def mesh(ax,cid,colors=None,bounds=((-13,13),(-13,13)),angle=(-65,22),inset=False):
    s=source(cid);P,F=s['P'],s['F'];cad=ring(s['c']['ring']);e,right,up=vis.basis(angle);C=s['RGB'][s['uv'][:,1],s['uv'][:,0]]/255
    if colors is None:colors=C[F].mean(1)
    if np.asarray(colors).ndim==1:colors=np.tile(colors,(len(F),1))
    V=np.r_[P,cad.vertices];FF=np.r_[F,np.asarray(cad.faces)+len(P)];tri=V[FF];col=np.r_[colors,np.tile([.015,.015,.015],(len(cad.faces),1))];order=np.argsort(tri.mean(1)@e);xy=np.stack([tri@right,tri@up],axis=2)
    ax.add_collection(PolyCollection(xy[order],facecolors=col[order],edgecolors='none',rasterized=True));ax.set(xlim=bounds[0],ylim=bounds[1]);ax.set_aspect('equal');ax.set_xticks([]);ax.set_yticks([])
    lo,yl=bounds[0][0],bounds[1][0];ax.plot([lo+.8,lo+5.8],[yl+.8]*2,'k-',lw=1.4);ax.text(lo+.8,yl+1.1,'5 mm',fontsize=6)
    if inset:
        q=np.c_[V@right,V@up];mid=(q.min(0)+q.max(0))/2;span=max(np.ptp(q,axis=0))+2;b=[(x-span/2,x+span/2)for x in mid];a=ax.inset_axes([.70,.70,.29,.29]);mesh(a,cid,colors,b,angle,False);a.text(.05,.85,'全范围',transform=a.transAxes,fontsize=5)
def camera_panel(ax,sid):
    refs=next(o['reference_screened_sources']for o in ORG if o['scene']==sid);cad=ring(CC[refs[0]]['ring']);tri=np.asarray(cad.vertices)[cad.faces][:,:,:2];ax.add_collection(PolyCollection(tri,facecolors='black',edgecolors='none'))
    T=np.array([source(c)['T'][:3,3]for c in refs]);ax.scatter(T[:,0],T[:,1],s=12,c='#2464b8')
    for cid,p in zip(refs,T):
        ax.annotate(cid.replace(sid+'_',''),p[:2],fontsize=6);ax.plot([p[0],0],[p[1],0],lw=.4,c='gray')
    ax.autoscale();ax.set_aspect('equal');ax.set_xlabel('Ring world X (mm)',fontsize=7);ax.set_ylabel('Ring world Y (mm)',fontsize=7);ax.tick_params(labelsize=6);ax.set_title(sid+' | 冻结相机中心',fontsize=8)
def figure1():
    fig=plt.figure(figsize=(22,15));gs=fig.add_gridspec(5,5);layout=[('G01_004',IDS[:3],0),('G01_005',[s for s in IDS if CC[s]['scene_id']=='G01_005'][:4],1),('G01_005',[s for s in IDS if CC[s]['scene_id']=='G01_005'][4:],2),('G06_004',[s for s in IDS if CC[s]['scene_id']=='G06_004'],3),('G08_005',[s for s in IDS if CC[s]['scene_id']=='G08_005'],4)]
    for sid,refs,row in layout:
        for j,cid in enumerate(refs):
            inner=gs[row,j].subgridspec(1,2,wspace=.02);a=fig.add_subplot(inner[0]);a.imshow(source(cid)['RGB']);a.axis('off');a.set_title(cid.replace(sid+'_','')+'\n'+ROLES[cid],fontsize=8);b=fig.add_subplot(inner[1]);mesh(b,cid,inset=True);b.set_title('原始 '+str(len(source(cid)['F']))+' 面',fontsize=7)
        a=fig.add_subplot(gs[row,4]);camera_panel(a,sid)
    fig.suptitle('E3-B | 全部17份真实参考帧与原始 HERO 开放Mesh：3 / 8 / 4 / 2\n每段视频独立 Ring 毫米坐标；主窗统一±13mm，小窗全范围；相机资格均为条件性',fontsize=15);fig.tight_layout(rect=[0,0,1,.95]);finish(fig,'Fig1_multiview_HERO.png','All17 real RGB/Raw meshes and frozen camera centers, no historical fusion geometry',IDS)
def figure2():
    refs=['G01_004_ref03','G01_005_raw00745'];fig,axs=plt.subplots(2,5,figsize=(22,11));metadata=[]
    for k,cid in enumerate(refs):
        s=source(cid);roi=ROI[s['c']['scene_id']];n=161;y=float(np.median(s['P'][:,1]));xx,zz=np.meshgrid(np.linspace(roi['minimum_mm'][0],roi['maximum_mm'][0],n),np.linspace(roi['minimum_mm'][2],roi['maximum_mm'][2],n));X=np.c_[xx.ravel(),np.full(n*n,y),zz.ravel()];q0=ProjectiveLocalField(cid).query(X);q1=MeshLocalField(cid).query(X);extent=[xx.min(),xx.max(),zz.min(),zz.max()]
        mesh(axs[k,0],cid,inset=True);axs[k,0].set_title(cid+'\n原始Mesh（未训练）',fontsize=10)
        h=axs[k,1].imshow(q0['value'].reshape(n,n),origin='lower',extent=extent,vmin=-.25,vmax=.25,cmap='coolwarm');fig.colorbar(h,ax=axs[k,1],shrink=.65,label='axial delta mm（色限±0.25）');axs[k,1].set_title('B0 原生投影场\n自由空间值可超出色限',fontsize=10)
        value=np.where(q1['valid_surface'],q1['raw_udf_mm'],np.nan);h=axs[k,2].imshow(value.reshape(n,n),origin='lower',extent=extent,vmin=0,vmax=.25,cmap='viridis');fig.colorbar(h,ax=axs[k,2],shrink=.65,label='UDF mm');axs[k,2].set_title('B1 原面距离场\n仅合格窄带；非全物体SDF',fontsize=10)
        for j,q in [(3,q0),(4,q1)]:
            axs[k,j].imshow(q['domain'].reshape(n,n),origin='lower',extent=extent,vmin=0,vmax=4,cmap=ListedColormap(PALETTE),interpolation='nearest');axs[k,j].set_title(('B0'if j==3 else'B1')+f' 定义域 | y={y:.2f}mm',fontsize=10)
        for a in axs[k,1:]:a.set_xlabel('world X (mm)');a.set_ylabel('world Z (mm)')
        metadata.append(dict(source=cid,slice_y_mm=y,N=n*n,B0_surface_N=int(q0['valid_surface'].sum()),B1_surface_N=int(q1['valid_surface'].sum()),B1_oriented_N=int((q1['field_kind']=='ORIENTED_LOCAL').sum())))
    fig.legend(handles=[Patch(color=c,label=l)for c,l in zip(PALETTE,['Surface','条件 Free-space','CAD-occluded','Unknown','Ambiguous'])],loc='lower center',ncol=5);fig.suptitle('E3-B | 实际可调用局部场的真实空间切片；NaN保持未知，未插值缺深度，未生成全局零面',fontsize=15);fig.tight_layout(rect=[0,.07,1,.94]);fig.subplots_adjust(hspace=.35);table('metrics/FIG2_SLICE_QUERIES.csv',metadata);finish(fig,'Fig2_local_fields.png','Real B0/B1 queries on same frozen per-video ROI slice',refs)
def figure3():
    sceneids=[o['scene']for o in ORG if o['reference_screened_sources']];fig,axs=plt.subplots(4,4,figsize=(20,16));increments=rows(R/'SOURCE_COVERAGE_INCREMENT.csv');union=rows(R/'metrics/MULTIVIEW_DOMAIN_UNION.csv')
    for k,sid in enumerate(sceneids):
        refs=[r['source_id']for r in increments if r['scene']==sid];previous=set()
        for j,stage in enumerate(['CORE','BRIDGE','RESERVED']):
            active=[cid for cid in refs if ROLES[cid]in['CORE','BRIDGE','RESERVED'][:j+1]];new=[cid for cid in active if ROLES[cid]==stage];a=axs[k,j];P=[];F=[];colors=[];offset=0;cad=ring(CC[refs[0]]['ring']);e,right,up=vis.basis((-65,22))
            active_counts={}
            for cid in active:
                for v in voxelset_centroids(cid):active_counts[v]=active_counts.get(v,0)+1
            for cid in active:
                s=source(cid);center=s['P'][s['F']].mean(1);vox=np.floor(center/.5).astype(int);newface=np.array([tuple(v)not in previous for v in vox]);col=np.tile([.28,.46,.72],(len(s['F']),1))
                if cid in new:
                    exclusive=np.array([active_counts[tuple(v)]==1 for v in vox]);col[newface&exclusive]=[.98,.57,.12];col[~newface|~exclusive]=[.62,.24,.67]
                P.append(s['P']);F.append(s['F']+offset);colors.append(col);offset+=len(s['P'])
            vertices=np.r_[np.concatenate(P),cad.vertices];faces=np.r_[np.concatenate(F),np.asarray(cad.faces)+offset];tri=vertices[faces];col=np.r_[np.concatenate(colors),np.tile([.015,.015,.015],(len(cad.faces),1))];order=np.argsort(tri.mean(1)@e);xy=np.stack([tri@right,tri@up],axis=2);a.add_collection(PolyCollection(xy[order],facecolors=col[order],edgecolors='none',rasterized=True));a.set(xlim=(-13,13),ylim=(-13,13));a.set_aspect('equal');a.set_xticks([]);a.set_yticks([]);a.plot([-12,-7],[-12,-12],'k-');a.text(-12,-11.5,'5 mm',fontsize=7)
            a.set_title(sid+' | '+stage+f' | {len(active)}来源\n本阶段新增{len(new)}来源；原面完整叠画',fontsize=9)
            previous=set().union(*(voxelset_centroids(cid)for cid in active))
        a=axs[k,3];rr=[r for r in increments if r['scene']==sid];a.bar(range(len(rr)),[int(r['new_spatial_voxels'])for r in rr],color=['#3568b0'if r['role']=='CORE'else'#f1a544'if r['role']=='BRIDGE'else'#3f9d74'for r in rr]);a.set_xlabel('固定加入顺序（未重新选择）',fontsize=8);a.set_ylabel('新增0.5mm原面重心格',fontsize=8);a.set_xticks(range(len(rr)));a.set_xticklabels([r['source_id'].replace(sid+'_','')for r in rr],rotation=65,fontsize=7)
        text='\n'.join(stage+': 全Unknown '+next(r['all_sources_unknown_N']for r in union if r['scene']==sid and r['method']=='B1'and r['stage']==stage)+'/15625'for stage in ['CORE','BRIDGE','RESERVED']);a.text(.02,.98,text,transform=a.transAxes,va='top',fontsize=8,bbox=dict(facecolor='white',alpha=.8,edgecolor='none'))
    fig.legend(handles=[Patch(color=c,label=l)for c,l in [('#4775b8','先前来源'),('#fa911f','新源新增空间格'),('#9e3dab','新源与已有格重叠')]],loc='lower center',ncol=3);fig.suptitle('E3-B | CORE → BRIDGE → RESERVED 原始几何互补性；不平均局部场，不建立融合Mesh\n颜色为原面重心空间格代理，重叠不认证同一物理面；Unknown为固定ROI场查询，非隐藏形态真值',fontsize=14);fig.tight_layout(rect=[0,.06,1,.94]);finish(fig,'Fig3_multiview_coverage.png','All original faces progressively displayed; only evidence coverage unions, no fused scalar or geometry',IDS)
def voxelset_centroids(cid):return {tuple(v)for v in np.floor(source(cid)['P'][source(cid)['F']].mean(1)/.5).astype(int)}
def figure4():
    refs=['G01_004_ref03','G01_005_raw00745','G06_004_ref04','G08_005_ref04'];fig,axs=plt.subplots(4,4,figsize=(19,16));evidence=[]
    for k,cid in enumerate(refs):
        s=source(cid);b1=MeshLocalField(cid);F=s['F'];stalk=s['clean']['protected_possible_stalk'][F].any(1);minor=b1.area_by_component[b1.component]<.01*b1.area_by_component.max();colors=np.tile([.86,.62,.62],(len(F),1));colors[b1.stretch]=[.85,0,.85];colors[minor]=[0,.8,.8];colors[stalk]=[1,.7,0]
        a=axs[k,0];a.imshow(s['RGB']);uv=s['uv'];ids=np.unique(F[stalk]);a.scatter(uv[ids,0],uv[ids,1],s=2,c='#ffc600');a.axis('off');a.set_title(cid+'\n黄色：既有possible-stalk代理，非人工真值',fontsize=9)
        mesh(axs[k,1],cid,colors,inset=True);axs[k,1].set_title('连续主体 / 原始长边(紫) / 小片(青)\n只表达与标记，未删除',fontsize=9)
        a=axs[k,2];a.imshow(s['RGB']);edgeuv=uv[b1.boundary_edges];a.add_collection(__import__('matplotlib').collections.LineCollection(edgeuv,colors='#00dddd',linewidths=.5));a.axis('off');a.set_title(f'原始开放边界 {len(b1.boundary_edges)} 条\n边界/不可靠符号返回UDF或Unknown',fontsize=9)
        a=axs[k,3];a.imshow(s['RGB']);a.imshow(camera(cid).ring_image());a.axis('off');rp=np.argwhere(s['labels']==2)[:,::-1];hits=camera(cid).cast(rp)['t_hit'].numpy();good=np.flatnonzero(np.isfinite(hits));count=0
        if len(good):
            ii=good[np.unique(np.linspace(0,len(good)-1,min(32,len(good))).astype(int))];X=unproject(hits[ii]+.5,s['T'],rp[ii],s['K']);q=ProjectiveLocalField(cid).query(X);count=int(q['cad_occluded'].sum());assert np.isnan(q['value'][q['cad_occluded']]).all()
        a.set_title(f'黑色实体CAD；后方查询 {count}/32 被截断\n遮挡不产生“后方无息肉”负票',fontsize=9);evidence.append(dict(source=cid,stalk_proxy_faces=int(stalk.sum()),stretch_proxy_faces=int(b1.stretch.sum()),minor_proxy_faces=int(minor.sum()),boundary_edges=len(b1.boundary_edges),actual_Ring_ray_occluded_N=count,no_hidden_geometry_generated=True))
    fig.suptitle('E3-B | 真实原生 HERO 结构与合法遮挡：原面及来源完整保留\n所有三维主窗±13mm / 5mm标尺；RGB与冻结相机一一对应；细柄/错误延伸仍是待人工确认的结构候选',fontsize=14);fig.tight_layout(rect=[0,0,1,.94]);table('metrics/FIG4_STRUCTURE_CHECKS.csv',evidence);finish(fig,'Fig4_real_geometry.png','Actual raw components, potential stalk labels, open boundaries and CAD-censored real rays',refs)
def main():
    allow_manifest();freeze('BEFORE_FIGURES.json');figure1();figure2();figure3();figure4();save('provenance/FIGURE_PROVENANCE.json',FIGS)
if __name__=='__main__':main()
