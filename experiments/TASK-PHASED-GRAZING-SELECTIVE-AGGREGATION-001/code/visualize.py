"""Real XYZ only, accepted point renderer / CAD; no image-generation models."""
from scene_renderer import *
def savefig(f,path,dpi=170):
    p=R/path;p.parent.mkdir(parents=True,exist_ok=True);f.savefig(p,dpi=dpi,facecolor='white');plt.close(f)
def empty_background(d):return dict(d,B=np.empty((0,3)),BC=np.empty((0,3)))
def cleaning_figures(render_details=True):
    table=load(R/'metrics/cleaning_comparison.json');chosen=['G01_004_ref13','G01_005_raw00057','G01_005_raw00745'];versions=['Raw','Density-T2','Angle-10','Angle-15','Angle-20'];fig,ax=plt.subplots(3,6,figsize=(20,14.7));clean_angle=(0,12)
    for row,cid in enumerate(chosen):
        s=source(cid);d=empty_background(source_data(cid));bounds=diag.square_bounds([s['P'],s['ring'].vertices],[vis.basis(clean_angle)])[0];n=normals(cid)
        for j,version in enumerate(versions):
            z=np.load(R/f'local_results/cleaning/{cid}/{version}.npz');ids=z['kept_original_ids'];x=dict(d,P=s['P'][ids],C=s['C'][ids]);r=next(r for r in table if r['reference']==cid and r['version']==version);title=cid+'\n'+version+('（最终回退）'if version=='Raw'else'')+f" 删{r['deleted_points']}/{r['raw_points']}\n主片保留{r['largest_raw_main_piece_retention']:.1%}；内孔候选{r['interior_deletion_patches']}";side(ax[row,j],x,title,clean_angle,bounds)
        col=plt.get_cmap('viridis')(np.clip(n['beta_deg']/90,0,1))[:,:3];side(ax[row,5],dict(d,C=col),'Raw 法向/源相机射线\nβ: 紫0° → 黄90°，非错误标签',clean_angle,bounds);basis=vis.basis(clean_angle);ids=np.flatnonzero(n['reliable']);ids=ids[np.linspace(0,len(ids)-1,min(10,len(ids)),dtype=int)]
        for i in ids:
            P=s['P'][i];N=n['normal'][i];C=s['p']['pose'][:3,3];v=(P-C)/np.linalg.norm(P-C);Q=np.array([P,P+N*.6,P+v*.8])@np.c_[basis[1],basis[2]];ax[row,5].plot(Q[:2,0],Q[:2,1],color='#bd234f',lw=.5);ax[row,5].plot(Q[[0,2],0],Q[[0,2],1],color='#075a87',lw=.5)
        if row==0:ax[row,5].text(.01,.01,'红：法向；蓝：真实源射线',transform=ax[row,5].transAxes,fontsize=7,bbox=dict(facecolor='white',alpha=.8,edgecolor='none'))
    fig.suptitle('角度清理一次性审计｜Raw / 历史T2 / Angle10°15°20°｜最终 ANGLE_REJECTED_USE_RAW_BASELINE\n同毫米窗口、真实源RGB、离散点；黑色实体CAD，12°侧向诊断；少删不等于安全，移除代理不等于误差清除',fontsize=15);fig.tight_layout(rect=[0,0,1,.92]);fig.subplots_adjust(hspace=.52);savefig(fig,'figures/Fig1_cleaning_comparison.png',160)
    if not render_details:return
    for c in cases():
        cid=c['id'];s=source(cid);d=empty_background(source_data(cid));bounds=diag.square_bounds([s['P'],s['ring'].vertices],[vis.basis((0,0))])[0];f,aa=plt.subplots(3,3,figsize=(12,12))
        for row,version in enumerate(versions[2:]):
            mask=np.load(R/f'local_results/cleaning/{cid}/{version}.npz')['deleted'];marked=s['C'].copy();marked[mask]=[1,.05,.08]
            for j,x in enumerate([d,dict(d,C=marked),dict(d,P=s['P'][~mask],C=s['C'][~mask])]):side(aa[row,j],x,version+' '+['Raw','候选红标（全原点）','Cleaned 派生'][j],bounds=bounds)
        f.suptitle(cid+'｜'+c['condition']+'；本轮实际聚合采用Raw，全部角度候选未认证');f.tight_layout(rect=[0,0,1,.95]);savefig(f,'figures/diagnostics/'+cid+'_Raw_Marked_Cleaned.png',140)
def single_video_figures(ss,render_details=True):
    core=[next(x for x in ss if x['scene']==sid)for sid in ['G01_004','G01_005']];fig,ax=plt.subplots(2,3,figsize=(16,11));contrib=load(R/'metrics/source_contribution.json')
    for i,sc in enumerate(core):
        ds=[data(sc,'primary'),data(sc,'core',False),data(sc,'evidence',False)];bounds=diag.square_bounds([ds[-1]['P'],ds[-1]['B'],ds[-1]['ring'].vertices],[vis.basis((-65,22))])[0]
        for j,d in enumerate(ds):
            title=['冻结主体 '+sc['primary'],'主体优先 + 有条件观测新增','证据保留：冲突/未知，不作可信新增'][j];side(ax[i,j],d,title,(-65,22),bounds)
        terms=[x for x in contrib if x['scene']==sc['scene']and not x['is_primary']];txt='；'.join(x['reference'].split('_',2)[2]+': '+str(x['accepted_new_points'])+'点'for x in terms);ax[i,1].text(.01,.015,txt+'\n面积代理 '+f"{sc['added_area_proxy_mm2']:.3f}mm²；方向分箱 {sc['primary_direction_bins']}→{sc['aggregate_direction_bins']}",transform=ax[i,1].transAxes,fontsize=8,bbox=dict(facecolor='white',edgecolor='none',alpha=.9))
    fig.suptitle('单视频选择性聚合｜主面XYZ固定，新增块不焊接、不平均\n粉：主面；蓝/橙：次参考原点；背景为原主面冻结深度DISPLAY_ONLY；有来源 ≠ 几何认证',fontsize=14);fig.tight_layout(rect=[0,0,1,.93]);fig.subplots_adjust(hspace=.23);savefig(fig,'figures/Fig2_single_video_aggregation.png')
    if not render_details:return
    for sc in ss:
        path='figures/cases/'+sc['scene']+'/';savefig(layer_figure(sc),path+'Layers_L1-L5.png',130)
        for name,f in six_views(sc).items():savefig(f,path+name,140)
        d=data(sc);im,meta=scene_image(d,d['p']['K'],d['p']['pose']);Image.fromarray(im).save(R/path/'Local_3D_Scene.png');frame=source(sc['primary'])['frame'];f,aa=plt.subplots(1,2,figsize=(14,4.8))
        for a,x,title in zip(aa,[frame,im],['主面真实源帧','同一冻结相机：实际XYZ + 实体CAD']):a.imshow(x);a.axis('off');a.set_title(title,fontsize=10)
        f.suptitle(sc['scene']+'｜'+sc['status']+'；多来源色彩来自各自RGB，不用目标帧重上色');f.tight_layout(rect=[0,0,1,.91]);savefig(f,path+'Real_vs_3D.png',160)
def cross_figures(ss):
    a=next(x for x in ss if x['scene']=='G01_004');b=next(x for x in ss if x['scene']=='G01_005');d4=data(a,source_colors=False);d5=data(b,source_colors=False);H=np.array(load(R/'metrics/crossvideo_candidate.json')['H_005_to_004']);joint=dict(d4,P=np.r_[d4['P'],transform(d5['P'],H)],C=np.r_[np.tile([.92,.27,.51],(len(d4['P']),1)),np.tile([.12,.57,.91],(len(d5['P']),1))],B=np.r_[d4['B'],transform(d5['B'],H)],BC=np.r_[d4['BC'],d5['BC']]);bounds=diag.square_bounds([joint['P'],joint['B'],d5['P'],d5['B'],d4['ring'].vertices],[vis.basis(x)for x in [(-65,22),(0,0),(25,75)]])
    f,aa=plt.subplots(3,3,figsize=(17,17));headers=['SINGLE-VIDEO RECONSTRUCTION — video004','SINGLE-VIDEO RECONSTRUCTION — video005','REGISTRATION CANDIDATE — NOT FUSED']
    for i,v in enumerate([(-65,22),(0,0),(25,75)]):
        for j,d in enumerate([d4,d5,joint]):side(aa[i,j],d,headers[j]+'\n'+['主体斜视','侧视','俯视/斜后'][i],v,bounds[i])
    f.suptitle('跨视频候选三列审查｜不同来源仍独立；未认证变换下不去重/不融合\n红004 / 蓝005；黑色CAD为004物理锚；原点坐标只应用显式派生刚体H，主面源数据不变',fontsize=15);f.tight_layout(rect=[0,0,1,.945]);savefig(f,'figures/Fig3_crossvideo_comparison.png',160)
    # Six views: actual near004 / actual near005 in004 / third virtual / Ring XYZ.
    p4=d4['p']['pose'];p5=H@d5['p']['pose'];q=p4.copy();q[:3,3]+=p4[:3,0]*3;poses=[p4,p5,q];allP=np.r_[joint['P'],joint['B']];allC=np.r_[joint['C'],joint['BC']];rs=camera_scene(joint,d4['p']['K'],p4);f,aa=plt.subplots(2,3,figsize=(18,10))
    for j,p in enumerate(poses):diag.points(aa[0,j],allP,allC,[(0,640),(0,360)],['接近004真实源相机','接近005相机（候选H）','第三虚拟方向/平移诊断'][j],K=d4['p']['K'],c2w=p,point_size=.08,alpha=1,ring_scene=rs,ring_alpha=1)
    bases=list(diag.AXES.items());bb=diag.square_bounds([allP,d4['ring'].vertices],[v[:3]for _,v in bases])
    for j,(label,v)in enumerate(bases):diag.points(aa[1,j],allP,allC,bb[j],label+'正交 / mm',basis=v[:3],labels=v[3:],point_size=.08,alpha=1,ring_scene=rs,ring_alpha=1)
    f.suptitle('G01跨视频六视角｜REGISTRATION CANDIDATE — NOT FUSED\n实际XYZ；重复层/间隙不修饰；上排像素相机、下排同尺度毫米正交');f.tight_layout(rect=[0,0,1,.93]);savefig(f,'figures/diagnostics/G01_crossvideo_6Views.png',170)
def reprojection_figures(ss):
    rows=[]
    # Frozen, predeclared targets: selection reused for diagnosis, prior actual
    # hold-outs for validation; never pick the visually best outcome.
    plan=[('G01_004_ref13',targets('G01_004')[-1],'FROZEN_SAME_VIDEO_CAMERA'),('G01_005_raw00057',targets('G01_005')[-1],'FROZEN_SAME_VIDEO_CAMERA'),('G06_004_ref04',targets('G06_004')[0],'NORMAL_CONDITIONAL'),('G08_005_ref04',targets('G08_005')[0],'LIMITED_STRESS'),('G07_004_ref04',targets('G07_004')[0],'UNQUALIFIED_CAMERA_STRESS')]
    for cid,t,state in plan:
        t=dict(t,ring_case=cid);dest=R/'figures/cases/A_to_B'/(cid+'__'+t['id']+'.png');rows.append(five_panel(cid,t,dest,state))
    H=np.array(load(R/'metrics/crossvideo_candidate.json')['H_005_to_004']);a=next(x for x in ss if x['scene']=='G01_004');b=next(x for x in ss if x['scene']=='G01_005');t=dict(targets('G01_005')[-1]);t.update(c2w=H@np.array(t['c2w']),ring_case=a['primary']);dest=R/'figures/Fig4_real_reprojection.png';rows.append(five_panel(a['primary'],t,dest,'REGISTRATION_CANDIDATE — NOT FUSED','困难跨视频真实验证'))
    both('figure_cross_view_cases',rows)
def main():
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--stage',default='all',choices=['all','cleaning','scenes','cross','AB','summaries']);args=p.parse_args();verify();ss=load(R/'metrics/aggregation_summary.json')
    if args.stage in ['all','cleaning']:cleaning_figures();print('FIG1 saved',flush=True)
    if args.stage in ['all','scenes']:single_video_figures(ss);print('FIG2 and all layer views saved',flush=True)
    if args.stage in ['all','cross']:cross_figures(ss);print('FIG3 and6views saved',flush=True)
    if args.stage in ['all','AB']:reprojection_figures(ss);print('FIG4+ fivepanel group cases saved',flush=True)
    if args.stage=='summaries':cleaning_figures(False);single_video_figures(ss,False);print('FIG1/2 layout refreshed; data unchanged',flush=True)
    save('provenance/RENDERER_MANIFEST.json',stamp([REPO/'visualization/real_p0_renderer.py',REPO/'visualization/same_camera_scene.py',REPO/'visualization/pointcloud_audit_renderer.py',DEPTH/'code/scene_renderer.py',R/'code/scene_renderer.py',R/'code/visualize.py'],point_size_diagnostic=.08,point_size_RGB=.8,CAD='black opaque original mesh',coordinate='millimeters, exact source P0 / frozen background',GT_used=False))
if __name__=='__main__':main()
