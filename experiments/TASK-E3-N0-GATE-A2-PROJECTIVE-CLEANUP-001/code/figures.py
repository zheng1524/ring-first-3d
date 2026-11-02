"""Real RGB/HERO samples and opaque unchanged CAD; no fusion output."""
from validate_inputs import *
from matplotlib.colors import ListedColormap
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
plt=vis.configure();plt.rcParams.update({'font.size':9,'axes.titlesize':10})
COL={'A':'#e23434','B':'#dc9417','C':'#9855bd','D':'#12a168'}

def finish(fig,name):
    fig.text(.5,.008,'真实项目数据 / 未训练输入诊断；相机为历史条件性资格。红=派生排除，橙=层竞争，紫=Unknown，绿=支持。GT未用。',ha='center',fontsize=8)
    fig.tight_layout(rect=(0,.025,1,.965));fig.savefig(R/'figures'/name,dpi=145,facecolor='white');plt.close(fig);print('FIG',name,flush=True)

def cad3(ax):
    m=ringmesh();ax.add_collection3d(Poly3DCollection(np.asarray(m.vertices)[np.asarray(m.faces)],facecolors='black',edgecolors='none'))

def axes3(ax,lo,hi):
    ax.set(xlim=(lo[0],hi[0]),ylim=(lo[1],hi[1]),zlim=(lo[2],hi[2]),xlabel='X / mm',ylabel='Y / mm',zlabel='Z / mm');ax.set_box_aspect(hi-lo);ax.view_init(20,-65)

def image(ax,s,title,point=None,window=None):
    ax.imshow(s['RGB']);ax.contour(s['labels']==1,[.5],colors=['#27dd72'],linewidths=.65);ax.contour(s['labels']==2,[.5],colors=['#22baff'],linewidths=.6)
    # Use the unchanged actual CAD raster, never a transparent geometry substitute.
    scene=SameCameraScene(ringmesh(),s['K'],s['T'],(640,360),VENDOR);ax.imshow(scene.ring_image(),extent=(-.5,639.5,359.5,-.5),zorder=2)
    if point is not None:ax.plot(point[0],point[1],'r+',ms=12,mew=1.5,zorder=5)
    ax.set(xlim=(0,640),ylim=(360,0),title=title)
    if window is not None:ax.set(xlim=(window[0],window[2]),ylim=(window[3],window[1]))
    ax.axis('off')

def fig1():
    cand=read_csv(R/'CLEANUP_CANDIDATES.csv');dec=read_csv(R/'PROJECTIVE_CLEANUP_DECISIONS.csv');summary=load(R/'CLEANUP_SUMMARY.json');cmap={r['candidate_id']:r for r in dec}
    dom=load(R/'MODEL_DOMAIN_COMPARISON.json')['cohorts'][1];lo=np.asarray(dom['world_cube_min_mm']);hi=np.asarray(dom['world_cube_max_mm'])
    fig=plt.figure(figsize=(17,23));fig.suptitle('Figure 1 | 六来源固定候选；共2,810点审查 / 106,098基线，候选条件不等于删除条件',fontsize=14)
    for i,cid in enumerate(IDS):
        s=baseline(cid);rows=[r for r in cand if r['source']==cid];uv=np.array([[float(r['archive_u']),float(r['archive_v'])] for r in rows]);colors=[COL[cmap[r['candidate_id']]['category'][0]] for r in rows]
        ax=fig.add_subplot(6,3,i*3+1);image(ax,s,cid+' / 真实RGB+原Mask+黑色CAD');ax.scatter(*uv.T,s=6,c=colors,linewidths=0,zorder=4)
        ax=fig.add_subplot(6,3,i*3+2);im=ax.imshow(np.ma.masked_where(~s['valid'],s['depth']),cmap='viridis',vmin=25,vmax=60);nu=np.array([[int(r['native_u']),int(r['native_v'])] for r in rows]);ax.scatter(*nu.T,s=6,c=colors,linewidths=0);n=next(r for r in summary['per_source'] if r['source']==cid);ax.set_title(f"原生深度 / 候选{len(rows)} / 新排除{n['incremental_excluded_N']}");ax.axis('off');fig.colorbar(im,ax=ax,fraction=.025,pad=.01,label='轴向Z / mm')
        ax=fig.add_subplot(6,3,i*3+3,projection='3d');j=np.unique(np.linspace(0,len(s['X'])-1,min(1800,len(s['X'])),dtype=int));ax.scatter(*s['X'][j].T,s=.3,c='#8798a3',alpha=.5);X=np.array([[float(r[k]) for k in ['X_mm','Y_mm','Z_mm']] for r in rows]);ax.scatter(*X.T,s=3,c=colors,depthshade=False);cad3(ax);axes3(ax,lo,hi);ax.set_title('同一世界毫米范围 / 黑色Ring CAD')
    finish(fig,'Fig1_Six_Source_Candidates.png')

def fig2():
    dd=read_csv(R/'PROJECTIVE_CLEANUP_DECISIONS.csv');ee=read_csv(R/'PROJECTIVE_CLEANUP_EVIDENCE.csv');rows=[]
    rows.append(max((r for r in dd if r['category'].startswith('A_')),key=lambda r:(float(r['axial_depth_mm']),-int(r['native_id']))))
    rows.append(next(r for r in dd if r['category'].startswith('D_')))
    rows.append(next(r for r in dd if r['previous_review_id']))
    rows.append(next(r for r in dd if r['category'].startswith('C_') and any(e['candidate_id']==r['candidate_id'] and e['evidence']=='C_CAD_OCCLUDED' for e in ee)))
    fig,axes=plt.subplots(4,4,figsize=(18,14));fig.suptitle('Figure 2 | 逐原Pixel ID的真实多视角证据：排除、支持、层竞争和遮挡未知',fontsize=14);case_manifest=[]
    for k,d in enumerate(rows):
        s=baseline(d['source']);pt=np.array([float(d['archive_u']),float(d['archive_v'])]);win=[max(0,pt[0]-65),max(0,pt[1]-60),min(639,pt[0]+65),min(359,pt[1]+60)]
        image(axes[k,0],s,f"源 {d['source'].split('004_')[1]}\n{d['candidate_id']} / PixelID={d['native_id']}",pt,win)
        ev=[e for e in ee if e['candidate_id']==d['candidate_id']]; key={'A':'A_','D':'D_','B':'B_','C':'C_CAD'}[d['category'][0]];first=[e for e in ev if e['evidence'].startswith(key)];other=[e for e in ev if e not in first];order=first+other
        if d['category'].startswith('A_'):
            distinct=[]
            for e in first:
                if e['observer_block'] not in [v['observer_block'] for v in distinct]:distinct.append(e)
            order=distinct+other
        chosen=order[:2]
        for j,e in enumerate(chosen):
            t=baseline(e['observer']);p=np.array([float(e['target_archive_u']),float(e['target_archive_v'])]);w=[max(0,p[0]-70),max(0,p[1]-60),min(639,p[0]+70),min(359,p[1]+60)]
            image(axes[k,j+1],t,f"{e['observer'].split('004_')[1]} / {e['observer_block']}\n{e['evidence']}",p,w)
            axes[k,j+1].text(.01,.02,f"Z={float(e['target_axial_Z_mm']):.2f}mm / CAD={e['CAD_first_hit_mm']}\nMask外距={float(e['outside_Polyp_distance_px']):.1f}px",transform=axes[k,j+1].transAxes,fontsize=8,bbox=dict(facecolor='white',alpha=.85,edgecolor='none'),zorder=6)
        short=lambda key:', '.join(v.split('004_')[-1].replace('G01_video004_','') for v in json.loads(d[key])) or '无'
        reasons={'A':'至少两个不同分区有明显轮廓反证；\n没有近深度支持或内部层竞争。','B':'目标Polyp内部存在深度层竞争；\n缺少足够证据，保留。','C':'有效反证不足，或存在遮挡；\n保留Unknown。','D':'其他来源有近深度支持；保留。'}
        axes[k,3].axis('off');axes[k,3].text(0,1,f"{d['category']}\n动作：{d['action']}\n反对块：{short('opposing_blocks')}\n支持源：{short('near_sources')}\n层竞争：{short('layer_sources')}\n\n{reasons[d['category'][0]]}\n\nRing/CAD遮挡不作为反证。\n相机条件性，轮廓反证是工程代理。",va='top',fontsize=9,wrap=True)
        case_manifest.append(dict(candidate_id=d['candidate_id'],source=d['source'],native_id=d['native_id'],observers=[e['observer'] for e in chosen],category=d['category']))
    save('config/FIGURE2_CASES.json',case_manifest);finish(fig,'Fig2_Projective_Evidence.png')

def fig3():
    dd=load(R/'MODEL_DOMAIN_COMPARISON.json')['cohorts'];loaders=[native,baseline,final_native];fig=plt.figure(figsize=(18,12));fig.suptitle('Figure 3 | 相同域规则、相同世界毫米范围；模型框缩小不是输入质量通过标准',fontsize=14)
    lo=np.asarray(dd[0]['world_cube_min_mm']);hi=np.asarray(dd[0]['world_cube_max_mm']);titles=['原始全部输入','上轮46点派生清理','本轮新增223点派生清理']
    for k,(dom,loader) in enumerate(zip(dd,loaders)):
        ax=fig.add_subplot(2,3,k+1,projection='3d');P=np.concatenate([loader(cid)['X'] for cid in IDS]);j=np.unique(np.linspace(0,len(P)-1,min(8000,len(P)),dtype=int));ax.scatter(*P[j].T,s=.4,c=['#8194a7','#49a5c3','#3c9b67'][k],alpha=.6);cad3(ax);wire_box(ax,dom,'#454545',f"L={dom['L_mm']:.3f}mm");axes3(ax,lo,hi);ax.set_title(f"{titles[k]}\nN={dom['total_retained_N']:,}; L={dom['L_mm']:.3f}mm\n128³：{dom['voxel_mm']:.5f}mm/格；Ring={dom['ring_outer_diameter_voxels']:.2f}格")
    ax=fig.add_subplot(2,3,4);sm=load(R/'CLEANUP_SUMMARY.json');xx=np.arange(6);values=[r['incremental_excluded_N'] for r in sm['per_source']];ax.bar(xx,values,color='#e24a4a');ax.set(xticks=xx,xticklabels=[c.split('004_')[1] for c in IDS],ylabel='本轮派生排除原像素N',title='各来源增量排除；不重复计算上轮46点');ax.tick_params(axis='x',rotation=20)
    for x,v in enumerate(values):ax.text(x,v+1,str(v),ha='center')
    ax=fig.add_subplot(2,3,5,projection='3d');s=final_native(IDS[4]);cand=read_csv(R/'PROJECTIVE_CLEANUP_DECISIONS.csv');prev=[r for r in cand if r['previous_review_id']];j=np.unique(np.linspace(0,len(s['X'])-1,3000,dtype=int));ax.scatter(*s['X'][j].T,s=.4,c='#98aab4');P=np.array([[float(r[key]) for key in ['X_mm','Y_mm','Z_mm']] for r in prev]);ax.scatter(*P.T,s=20,c='#dd9315',depthshade=False);cad3(ax);axes3(ax,np.asarray(dd[-1]['world_cube_min_mm']),np.asarray(dd[-1]['world_cube_max_mm']));ax.set_title('P47–P55：9个原未决点全部保留\nPolyp内部层竞争；不是强行缩框目标')
    ax=fig.add_subplot(2,3,6);ax.axis('off');ax.text(0,1,f"三个不同分母\n原生：106,144\n上轮派生：106,098\n本轮派生：105,875\n\n本轮审查：2,810 / 106,098\n未审查候选：1,641，全保留\n全部保留点均在当前模型域内\n\n所有新排除点都有逐观察源证据。\nRing/CAD、相机、RGB/Mask不改。\n未认证真实面积或独有组织的物理准确性。\n模型域为候选，未开启NeuralFusion。",va='top',fontsize=12)
    finish(fig,'Fig3_Domain_Resolution.png')

def patch(ax,data,u,v,title,depth=False):
    if depth:im=ax.imshow(np.ma.masked_where(data<=0,data),cmap='viridis',vmin=25,vmax=55,interpolation='nearest')
    else:im=ax.imshow(data,cmap=ListedColormap(['#eeeeee','#51b87d']),vmin=0,vmax=1,interpolation='nearest')
    ax.plot(u,v,'r+',ms=12,mew=1.5);ax.set(xlim=(u-6,u+6),ylim=(v+6,v-6),title=title,xlabel='u / px',ylabel='v / px');ax.grid(alpha=.2);return im

def fig4():
    diag=load(R/'R14_THIN_STRUCTURE_DIAGNOSIS.json');fig,axes=plt.subplots(5,4,figsize=(19,20));fig.suptitle('Figure 4 | 保留失败：r14薄结构未决 + 三个真实原生深度跳变 + 清理有效域碎片副作用',fontsize=14)
    s=final_native(IDS[-1]);c=make_crop(s);u,v=diag['mapped_native_uv'];a=diag['archive_uv'];win=[a[0]-30,a[1]-25,a[0]+30,a[1]+25]
    image(axes[0,0],s,'r14真实RGB / Polyp与Ring轮廓\n对应native(282,215)，不认证为细柄',a,win)
    patch(axes[0,1],s['valid'].astype(int),u,v,f"原生有效深度Mask / N9×9={diag['native_9x9_valid_N']}\n该点Z={diag['native_depth_mm']:.3f}mm，非原生局部ridge")
    cu,cv=diag['old_crop_uv'];patch(axes[0,2],c['valid'].astype(int),cu,cv,f"裁后有效深度Mask / N9×9={diag['crop_9x9_valid_N']}\n真实旧失败点(99,144)：宽代理2px<3px")
    axes[0,3].axis('off');axes[0,3].text(0,1,'同一原生Pixel ID仍保留。\n不是通过删除此点解决失败。\n\n旧文字(99,143)差1行；\n这里使用旧JSON/NPZ真实身份(99,144)。\n\n原生点处于边缘而非局部medial ridge；\n裁后出现局部ridge，可能是角点锯齿。\n原生9×9深度范围约38.13–47.78mm。\n\n无法只凭此证据证明真实细柄存在或不存在。\nTHIN_STRUCTURE_UNRESOLVED_BY_CROP\n旧3px门槛不变。',va='top',fontsize=10)
    cases=[r for r in read_csv(R/'RESAMPLING_FAILURE_DIAGNOSIS.csv') if r['stage']=='A2_INCREMENTAL']
    for i,d in enumerate(cases,1):
        s=final_native(d['source']);c=make_crop(s);u,v=int(d['original_u']),int(d['original_v']);pu,pv=int(d['selected_u']),int(d['selected_v']);a=archive_uv(s,np.array([[u,v],[pu,pv]]));w=[a[:,0].min()-24,a[:,1].min()-22,a[:,0].max()+24,a[:,1].max()+22]
        image(axes[i,0],s,d['source'].split('004_')[1]+f" / 原ID={d['original_native_id']}\n红=原点，黄=实际选中另一原像素",a[0],w);axes[i,0].plot(*a[1],'y+',ms=12,zorder=6)
        patch(axes[i,1],np.where(s['valid'],s['depth'],0),u,v,f"原生真实深度：ΔZ={float(d['native_depth_difference_mm']):.2f}mm\n1px邻接跨层；未做双线性平滑",True);axes[i,1].plot(pu,pv,'y+',ms=12)
        ou,ov=int(d['output_u']),int(d['output_v']);patch(axes[i,2],c['depth_mm'],ou,ov,f"320×240实际取值={float(d['selected_depth_mm']):.2f}mm\n正向配对误差={float(d['forward_pair_XYZ_error_mm']):.2f}mm",True)
        xx=np.arange(max(0,min(u,pu)-6),min(640,max(u,pu)+7));z=s['depth'][v,xx];ok=s['valid'][v,xx];axes[i,3].plot(xx,np.where(ok,z,np.nan),'.-',c='#2476b3');axes[i,3].plot(u,float(d['original_depth_mm']),'ro');axes[i,3].plot(pu,float(d['selected_depth_mm']),'yo',markeredgecolor='black');axes[i,3].set(title=f"native v={v} / 输出射线对所选原点偏移\n{float(d['chosen_original_XYZ_vs_actual_output_ray_mm']):.4f}mm；无混合深度",xlabel='native u / px',ylabel='轴向Z / mm');axes[i,3].grid(alpha=.25)
    topology_cases=[]
    for k,cid in enumerate(IDS[3:5]):
        b=make_crop(baseline(cid));f=make_crop(final_native(cid));bd,br=ridge_proxy(b['valid']);fd,fr=ridge_proxy(f['valid']);vv,uu=np.nonzero(fr&(2*fd<3)&~(br&(2*bd<3)));u,v=int(uu[0]),int(vv[0]);newN=int((fr&(2*fd<3)).sum())
        patch(axes[4,k*2],b['valid'].astype(int),u,v,f"{cid.split('004_')[1]} / 同区域清理前\n该处未触发sub3px ridge")
        patch(axes[4,k*2+1],f['valid'].astype(int),u,v,f"同区域清理后 / 仍保留的原像素\n全图新增{newN}个sub3px有效域ridge")
        topology_cases.append(dict(source=cid,crop_uv=[u,v],new_ridge_N=newN,source_native_id=int(f['source_ids'][v,u]),depth_input_preserved=float(f['depth_mm'][v,u])))
    save('config/FIGURE4_TOPOLOGY_CASES.json',topology_cases)
    finish(fig,'Fig4_Residual_Engineering.png')

if __name__=='__main__':
    fig1();fig2();fig3();fig4()
