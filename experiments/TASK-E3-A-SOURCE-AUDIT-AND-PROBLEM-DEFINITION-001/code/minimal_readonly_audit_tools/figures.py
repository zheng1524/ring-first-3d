"""Real original assets only. Figures are audit displays, not new reconstructions."""
from common import *
plt=vis.configure()
from matplotlib.collections import PolyCollection
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
combine=extract(E0/'code/evidence.py',['combine'],dict(globals()))['combine']
f3=extract(E0/'code/evidence.py',['f3'],dict(globals()))['f3']
FIGS={}

def finish(fig,name,description,inputs):
    fig.savefig(R/'figures'/name,dpi=135,facecolor='white');plt.close(fig)
    FIGS[name]=dict(description=description,inputs=inputs,all_geometry='existing real-project XYZ/original triangles; no fitting or new geometry',camera_pose_edited=False)
    print('FIGURE',name,flush=True)

def fig1():
    fig=plt.figure(figsize=(17,13));gs=fig.add_gridspec(6,4,height_ratios=[1,1,1,1,1,.75]);org=load(R/'provenance/SOURCE_ORGANIZATION.json')
    for k,sid in enumerate(scenes()):
        refs=[c for c in D['references']if c['scene_id']==sid];first=refs[0];s=source(first['id']);a=fig.add_subplot(gs[k,0]);a.imshow(Image.open(first['RGB']));a.axis('off');a.set_title(sid+' | '+first['morphology']+'/'+first['ring'],fontsize=10)
        a=fig.add_subplot(gs[k,1],projection='polar');a.set_ylim(0,180)
        for i,c in enumerate(refs):
            T=source(c['id'])['T'];roi=load(R/'config/GLOBAL_ROI_FROZEN.json')[sid];v=T[:3,3]-np.array(roi['center_mm']);v/=np.linalg.norm(v);theta=np.arctan2(v[1],v[0]);el=np.degrees(np.arcsin(v[2]))
            a.scatter(theta,90-el,c='#157f3c'if eligible(c)else'#cc7449',s=35);a.text(theta,90-el,str(i+1),fontsize=7)
        a.set_title('相机方向：半径=90°−仰角\n每段视频各自 Ring 坐标',fontsize=9);a.tick_params(labelsize=7)
        a=fig.add_subplot(gs[k,2]);a.axis('off');ro=org[k];text='\n'.join(f'{i+1:02d} {c["id"].replace(sid+"_","")} [{"筛查"if eligible(c)else"候选"}]'for i,c in enumerate(refs));a.text(0,1,text,va='top',fontsize=8)
        a=fig.add_subplot(gs[k,3]);a.axis('off');a.text(0,1,f'全部 HERO {len(refs)}\n参考筛查 {len(ro["reference_screened_sources"])}\n代表来源 {len(ro["representative_sources"])}\n方向格 {ro["selected_camera_bins"]}/{ro["all_camera_bins"]}\n法向格 {ro["selected_normal_bins"]}/{ro["all_normal_bins"]}\n空间格 {ro["selected_spatial_voxels"]}/{ro["all_spatial_voxels"]}\n相关父系 {ro["all_source_family_N"]}\n'+first['condition'],va='top',fontsize=9)
    photos=load(E1/'provenance/PHOTO_QUALIFICATION.json')
    for j,p in enumerate(photos):
        a=fig.add_subplot(gs[5,j]);a.imshow(Image.open(p['RGB']['path']));a.axis('off');a.set_title(p['id']+' | K/c2w 未认证',fontsize=9)
    a=fig.add_subplot(gs[5,3]);a.axis('off');a.text(0,.9,'G01 为同一物理组、两段独立坐标\n三张照片不能加入公制几何\n绿色=参考已筛查，非绝对位姿真值\n橙色=未合格参考\n上下游相机资格详见 manifest',va='top',fontsize=9)
    fig.suptitle('E3-A | 完整来源与观察方向（4 个主物理组 / 5 视频；无跨视频配准）',fontsize=15);fig.tight_layout(rect=[0,0,1,.97]);finish(fig,'Fig1_sources_and_views.png','Real RGB and actual frozen camera directions, separate video frames',list(CC))

def draw_mesh(ax,m,cad,bounds,angle=(-65,22)):
    e,right,up=vis.basis(angle);P=m['P'];F=m['F'];C=m['C'];V=np.r_[P,np.asarray(cad.vertices)];FF=np.r_[F,np.asarray(cad.faces)+len(P)]
    colors=np.r_[C[F].mean(1),np.tile([.015,.015,.015],(len(cad.faces),1))];tri=V[FF];key=tri.mean(1)@e;order=np.argsort(key);xy=np.stack([tri@right,tri@up],axis=2)
    ax.add_collection(PolyCollection(xy[order],facecolors=colors[order],edgecolors='none',rasterized=True));ax.set(xlim=bounds[0],ylim=bounds[1]);ax.set_aspect('equal');ax.set_xticks([]);ax.set_yticks([])
    ax.plot([bounds[0][0]+1,bounds[0][0]+6],[bounds[1][0]+1]*2,'k-',lw=2);ax.text(bounds[0][0]+1,bounds[1][0]+1.5,'5 mm',fontsize=7)

def fig2():
    sceneids=scenes();e,right,up=vis.basis((-65,22));allP=np.concatenate([source(cid)['P']for cid in CC]+[ring('R10').vertices,ring('R5').vertices]);xy=np.c_[allP@right,allP@up];low=xy.min(0)-1;high=xy.max(0)+1;span=max(high-low);mid=(high+low)/2;bounds=[(mid[i]-span/2,mid[i]+span/2)for i in range(2)]
    fig,axs=plt.subplots(5,6,figsize=(20,16));methods=['Raw 全来源','Cleaned 全来源','单参考完整原面','F1 历史来源','F2 历史来源','F3 / Growth 历史输出'];summary=[]
    for k,sid in enumerate(sceneids):
        refs=[c['id']for c in D['references']if c['scene_id']==sid];hist9=[c['id']for c in D['references'][:9]if c['scene_id']==sid];hist14=[c['id']for c in D['references'][:14]if c['scene_id']==sid]
        mm=[combine(sid,'Raw',refs),combine(sid,'Cleaned_F1',refs),combine(sid,'Raw',[refs[0]]),combine(sid,'Cleaned_F1',hist9),combine(sid,'F2',hist14),f3(sid)]
        for j,m in enumerate(mm):
            a=axs[k,j];cad=ring(CC[refs[0]]['ring']);draw_mesh(a,m,cad,[(-13,13),(-13,13)]);inset=a.inset_axes([.68,.68,.31,.31]);draw_mesh(inset,m,cad,bounds);inset.text(.05,.88,'完整范围',transform=inset.transAxes,fontsize=6);a.set_title(f'{sid} | {methods[j]}\n{len(m["F"]):,} 原面 / {len(m["input_refs"])} 来源',fontsize=8)
            summary.append(dict(scene=sid,panel=methods[j],face_N=len(m['F']),input_refs=m['input_refs'],same_input_replay=False))
    fig.suptitle('E3-A | 真实原始开放三角面与历史派生结果；主窗统一 ±13 mm，右上窗显示完整范围\n所有原面绘制；黑色实体=固定 CAD；历史来源集不同，不构成公平算法排名',fontsize=13);fig.tight_layout(rect=[0,0,1,.96]);table('metrics/FIG2_HISTORICAL_PANELS.csv',summary)
    finish(fig,'Fig2_existing_HERO_geometry.png','All original faces; no display subsampling, same metric scale; historical source sets differ',list(CC))

def fig3():
    fig,axs=plt.subplots(5,4,figsize=(18,17));facts=readrows(R/'metrics/E3_RAW_SURFACE_DIAGNOSTICS.csv');missing=readrows(R/'metrics/E3_OBSERVED_WITHOUT_TRIANGLE.csv')
    for k,sid in enumerate(scenes()):
        cid=next(c['id']for c in D['references']if c['scene_id']==sid);s=source(cid);ff=np.load(R/f'local_results/face_facts/{cid}.npz');own=np.load(R/f'local_results/own/{cid}.npz');img=np.asarray(Image.open(s['c']['RGB']));P,F=s['P'],s['F'];uv=s['uv'];mask=s['labels']==1
        a=axs[k,0];a.imshow(img);bad=np.unique(F[ff['stretch_proxy']]);a.scatter(uv[bad,0],uv[bad,1],s=2,c='#ca00d3',alpha=.6);a.set_title(sid+' | 长边/像素足迹代理',fontsize=10)
        a=axs[k,1];a.imshow(img);ids=np.unique(F[ff['minor_proxy']|ff['protected_proxy']]);a.scatter(uv[ids,0],uv[ids,1],s=2,c='#00ddbd',alpha=.6);a.set_title('小连通片/细柄与 Ring 保护代理\n不等同人工确认真实结构',fontsize=9)
        a=axs[k,2];a.imshow(img);miss=mask&~np.isfinite(own['raw_Z']);back=mask&np.isfinite(own['raw_Z'])&(own['raw_Z']>own['CAD_Z']+.002)
        overlay=np.zeros((360,640,4));overlay[miss]=[1,.15,.0,.9];overlay[back]=[0,.4,1,.9];a.imshow(overlay);a.set_title(f'红：无原面首交 {miss.sum()}\n蓝：正 Mask 与 CAD 前遮挡冲突 {back.sum()}',fontsize=9)
        # Two actual point layers in world XZ; correspondence remains unverified.
        peer=next(c['id']for c in D['references']if c['scene_id']==sid and c['id']!=cid);B=source(peer);a=axs[k,3];a.scatter(P[:,0],P[:,2],s=.2,c='#ee8e3b',rasterized=True);a.scatter(B['P'][:,0],B['P'][:,2],s=.2,c='#4575bc',rasterized=True);a.set_aspect('equal');a.set_xlabel('world X (mm)',fontsize=8);a.set_ylabel('world Z (mm)',fontsize=8);a.set_title(cid.replace(sid+'_','')+' + '+peer.replace(sid+'_','')+'\n两层投影≠已认证同表面错误',fontsize=9)
        for a in axs[k,:3]:a.axis('off')
    fig.suptitle('E3-A | 真实失败候选与可见性证据（未训练，不称为新三维重建）\n位置、原面/像素索引见 E3_CASEBOOK_POINTS.csv；异常与真实解剖的人工标签尚缺',fontsize=14);fig.tight_layout(rect=[0,0,1,.96]);finish(fig,'Fig3_geometry_failure_cases.png','Original source image locations, raw triangle misses, CAD contradictions, separate original point layers',[c['id']for c in D['references'][:9]])

def fig4():
    fig,axs=plt.subplots(2,3,figsize=(18,11));roi=load(R/'config/GLOBAL_ROI_FROZEN.json');out=[]
    for k,sid in enumerate(['G01_004','G01_005']):
        refs=next(x['reference_screened_sources']for x in load(R/'provenance/SOURCE_ORGANIZATION.json')if x['scene']==sid);cid=refs[0];s=source(cid);b=roi[sid];n=121;y=float(np.median(s['P'][:,1]));xx,zz=np.meshgrid(np.linspace(b['minimum_mm'][0],b['maximum_mm'][0],n),np.linspace(b['minimum_mm'][2],b['maximum_mm'][2],n));X=np.c_[xx.ravel(),np.full(n*n,y),zz.ravel()]
        states=np.zeros(len(X),np.uint8);possible=np.zeros(len(X),bool);censored=np.zeros(len(X),bool);free_candidate=np.zeros(len(X),bool)
        sys.path.insert(0,str(VENDOR));import open3d as o3d
        for ref in refs:
            q=source(ref);uv,z=vis.project_camera(X,q['K'],q['T']);xy=np.floor(uv+.5).astype(int);inside=(z>0)&(xy[:,0]>=0)&(xy[:,0]<640)&(xy[:,1]>=0)&(xy[:,1]<360);ids=np.flatnonzero(inside);u=xy[ids];polyp=q['labels'][u[:,1],u[:,0]]==1;cad=source_camera(ref).cast(uv[ids])['t_hit'].numpy();hit,_=cast_mesh(ref,uv[ids]);blocked=np.isfinite(cad)&(z[ids]>cad+.002);censored[ids[blocked]]=True
            close=mesh_scene(ref).compute_closest_points(o3d.core.Tensor(X.astype(np.float32)))['points'].numpy();dist=np.linalg.norm(X-close,axis=1)
            support=polyp&~blocked&np.isfinite(hit)&(abs(hit-z[ids])<=.25)&(dist[ids]<=.25);possible[ids[support]]=True
            # Display a conditional ray segment only. It is NOT a computed free-space field.
            fr=polyp&~blocked&np.isfinite(hit)&(z[ids]<hit-.25)&(hit<=cad+.002);free_candidate[ids[fr]]=True
        states[censored]=1;states[free_candidate]=2;states[possible]=3;extent=[xx.min(),xx.max(),zz.min(),zz.max()];a=axs[k,0];a.imshow(states.reshape(n,n),origin='lower',extent=extent,interpolation='nearest',cmap=ListedColormap(['#bfbfbf','#2c354a','#efe5ac','#209671']),vmin=0,vmax=3);a.set_title(sid+f' | 固定 y={y:.2f} mm 切片',fontsize=10);a.set_xlabel('world X (mm)');a.set_ylabel('world Z (mm)')
        a=axs[k,1];img=np.asarray(Image.open(s['c']['RGB']));a.imshow(img);own=np.load(R/f'local_results/own/{cid}.npz');missing=(s['labels']==1)&~np.isfinite(own['raw_Z']);u=np.argwhere(missing);a.scatter(u[:,1],u[:,0],s=3,c='red');a.axis('off');a.set_title('红：图像可见但无原面首交\n三维位置未定位，不投射成“真实空洞”',fontsize=10)
        peer=refs[1];B=source(peer);uv,z=vis.project_camera(s['P'],B['K'],B['T']);xy=np.floor(uv+.5).astype(int);inside=(z>0)&(xy[:,0]>=0)&(xy[:,0]<640)&(xy[:,1]>=0)&(xy[:,1]<360);ids=np.flatnonzero(inside);hit,_=cast_mesh(peer,uv[ids]);cad=source_camera(peer).cast(uv[ids])['t_hit'].numpy();tau=np.maximum(.5,3*hit/min(B['K'][0,0],B['K'][1,1]));good=(B['labels'][xy[ids,1],xy[ids,0]]==1)&np.isfinite(hit)&(hit<=cad+.002)&(z[ids]<=cad+.002);sep=good&(abs(z[ids]-hit)>tau);a=axs[k,2];a.scatter(s['P'][:,0],s['P'][:,2],c='#c5c5c5',s=.6,rasterized=True);p=s['P'][ids[sep]];a.scatter(p[:,0],p[:,2],s=1,c='#a500be',rasterized=True);a.set_aspect('equal');a.set_xlabel('world X (mm)');a.set_ylabel('world Z (mm)');a.set_title('紫：投影错层候选 / 对应未认证\n不能直接作为同一表面融合标签',fontsize=10)
        out.append(dict(scene=sid,reference_ids=refs,slice_y_mm=y,grid_N=n*n,possible_raw_narrowband_N=int(possible.sum()),CAD_censored_any_source_N=int(censored.sum()),conditional_first_surface_front_N=int(free_candidate.sum()),
            unassigned_no_legal_evidence_N=int((states==0).sum()),independent_truly_unobserved_anatomy_labels_N=0,field_created=False,projected_separation_display_N=int(sep.sum())))
    labels=['Unknown / 无足够合法证据','CAD 遮挡（非不存在）','有条件的可信首表面前方候选','原面窄带观测候选（非真值）'];fig.legend(handles=[Patch(color=c,label=l)for c,l in zip(['#bfbfbf','#2c354a','#efe5ac','#209671'],labels)],loc='lower center',ncol=2,fontsize=10)
    fig.suptitle('E3-A | 真实观测支持域审计示意：2D 切片与有限距离查询，未构建 LocalField / 全局 Φ\n灰色不等于正 SDF；三维 Unknown 与图像缺面分开；相机和 HERO 仍有条件',fontsize=14);fig.tight_layout(rect=[0,.08,1,.94]);fig.subplots_adjust(hspace=.35);table('metrics/E3_SUPPORT_SLICE_DIAGNOSTICS.csv',out);finish(fig,'Fig4_observation_support_domains.png','Finite actual-mesh distance/projection queries; evidence audit only, not local/global field output',['G01_004','G01_005'])

def main():
    freeze('BEFORE_FIGURES.json');fig1();fig2();fig3();fig4();save('provenance/FIGURE_PROVENANCE.json',FIGS)
if __name__=='__main__':main()
