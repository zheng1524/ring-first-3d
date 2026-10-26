"""Actual XYZ diagnostics and transparent A-RGB predictions; no invented geometry."""
from reprojection import *
plt=vis.configure()
from matplotlib import colors,cm
def bounds(c,P=None,B=None):
    if P is None:P=data(c)[0]['XYZ_mm']
    pts=[P,ring(c).vertices]+([]if B is None else[B]);return diag.square_bounds(pts,[vis.basis((-65,22))])[0]
def cloud(ax,c,P,rgb,title,lim=None,mode='RGB',marked=None):
    a,p,col,m=data(c);basis=vis.basis((-65,22));mesh=ring(c);scene=SameCameraScene(mesh,p['K'],p['pose'],(p['labels'].shape[1],p['labels'].shape[0]),str(OLD/'surface_fusion_v3/vendor'))
    if mode=='density':rgb=cm.viridis(colors.LogNorm(1,500,clip=True)(np.maximum(a['rho_surface_radius'],1)))[:,:3]
    if marked is not None:rgb=np.array(rgb).copy();rgb[marked]=[.95,.07,.04]
    diag.points(ax,P,rgb,lim or bounds(c),title,basis=basis,point_size=.08,alpha=1,ring_scene=scene,ring_alpha=.15)
    if mode=='density':bar=ax.figure.colorbar(cm.ScalarMappable(norm=colors.LogNorm(1,500),cmap='viridis'),ax=ax,fraction=.04,pad=.02);bar.set_label('rho [点/mm²]（0值按最低色显示）',fontsize=8)
def publish(fig,name):
    fig.tight_layout(rect=[0,0,1,.95]);fig.savefig(R/'figures'/name,dpi=160,facecolor='white');plt.close(fig)
def P1():
    cc=cases();rows=load(R/'metrics/P1_candidate_damage.json');dg=load(R/'metrics/spatial_diagnostics.json')
    for video in ['004','005']:
        refs=[c for c in cc if c['group']=='G01'and c['video']==video];fig,ax=plt.subplots(3,4,figsize=(22,15));video_limit=diag.square_bounds([*[data(c)[0]['XYZ_mm']for c in refs],ring(refs[0]).vertices],[vis.basis((-65,22))])[0]
        for i,c in enumerate(refs):
            a,p,rgb,m=data(c);P=a['XYZ_mm'];lim=video_limit;trial=np.load(R/f'local_results/{c["id"]}/T2_exact.npz');mask=a['rho_surface_radius']<float(trial['rho_threshold']);row=next(x for x in rows if x['id']==c['id']and x['tier']=='T2');d=next(x for x in dg if x['id']==c['id']);cloud(ax[i,0],c,P,rgb,c['id']+f' Raw N={len(P):,}',lim);cloud(ax[i,1],c,P,rgb,f'实际XYZ密度；q80/q10={d["drop_q80_over_q10"]:.2f}',lim,mode='density');cloud(ax[i,2],c,P,rgb,f'T2候选红：ρ<{float(trial["rho_threshold"]):.2f}，N={mask.sum():,}',lim,marked=mask);cloud(ax[i,3],c,P[~mask],rgb[~mask],f'未采纳的T2派生；非最终清理\n细柄代理损失{row["possible_stalk_proxy_deleted_fraction"]:.1%}',lim)
        fig.suptitle('P1 G01 video'+video+'｜真实P0空间密度→统一视频阈值→损伤审查\n所有列同Raw毫米范围/点大小；最终状态INSUFFICIENT_EVIDENCE，保留Raw；GT=NONE',fontsize=16);publish(fig,'FigP1_'+video+'_spatial_trials.png')
    refs=[cc[7],cc[10],cc[11]];fig,ax=plt.subplots(3,4,figsize=(22,15))
    for i,c in enumerate(refs):
        a,p,rgb,m=data(c);P=a['XYZ_mm'];lim=bounds(c);mask=a['rho_surface_radius']<50;decision=next(x for x in load(R/'metrics/P1_video_decisions.json')if x['group']==c['group']and x['video']==c['video']);cloud(ax[i,0],c,P,rgb,c['id']+' / '+c['condition'],lim);cloud(ax[i,1],c,P,rgb,'实际XYZ密度（统一色阶）',lim,mode='density');cloud(ax[i,2],c,P,rgb,f'固定50对照：红色将删除{mask.sum():,}/{len(P):,}',lim,marked=mask);cloud(ax[i,3],c,P,rgb,'最终保留全部Raw\n'+decision['status'],lim)
    fig.suptitle('P1 跨组反例｜整体稀疏不等于错误；G03/G07为压力条件\n视频门控/结构检查拒绝自动清理；固定50仅对照，不作为预测',fontsize=16);publish(fig,'FigP1_crossgroup_counterexamples.png')
    fig,ax=plt.subplots(2,2,figsize=(16,12));ref=cc[4];a,p,rgb,m=data(ref);mask=a['rho_surface_radius']<next(x['threshold_points_per_mm2']for x in rows if x['id']==ref['id']and x['tier']=='T3');cloud(ax[0,0],ref,a['XYZ_mm'],rgb,'005 raw459 T3反例：同视频阈值损伤密集区域',marked=mask)
    for panel,field,title in [(ax[0,1],'deleted_fraction','派生删点比例（越高不代表越好）'),(ax[1,0],'possible_stalk_proxy_deleted_fraction','可能细柄代理删除比例，非真实误删率'),(ax[1,1],'dense_proxy_area_retained','高密度代理原面面积保留')]:
        for c in cc[:6]:
            rr=[x for x in rows if x['id']==c['id']and x['tier']in ['T1','T2','T3']];panel.plot([1,2,3],[x[field]for x in rr],marker='o',label=c['id'])
        panel.set(xticks=[1,2,3],xticklabels=['T1','T2','T3'],title=title);panel.grid(alpha=.2);panel.legend(fontsize=7)
    fig.suptitle('P1 失败与损伤：不存在六参考共同通过的候选，停止调参',fontsize=16);publish(fig,'FigP1_damage_and_failure.png')
def all_scenes():
    cfg=load(REPO/'experiments/TASK-PHASEC-SCENE-POINTCLOUD-AUDIT-001/config.json');index=[]
    for c in cases():
        a,p,rgb,m=data(c);P=a['XYZ_mm'];B,brgb,buv=background(c);mesh=ring(c);size=(p['labels'].shape[1],p['labels'].shape[0]);scene=SameCameraScene(mesh,p['K'],p['pose'],size,str(OLD/'surface_fusion_v3/vendor'));dest=R/'local_results/visuals'/c['id'];dest.mkdir(parents=True,exist_ok=True);frame=np.asarray(Image.open(c['RGB']).convert('RGB'));fig=plt.figure(figsize=(size[0]/160,size[1]/160),dpi=160);ax=fig.add_axes([0,0,1,1]);scene.draw(ax,P,rgb,B,brgb,point_size=.8);scene.scale_bar(ax);fig.canvas.draw();l5=np.asarray(fig.canvas.buffer_rgba()).copy()[:,:,:3];plt.close(fig);Image.fromarray(l5).save(dest/'Local_3D_Scene.png');pair=Image.new('RGB',(2*size[0],size[1]),'white');pair.paste(Image.fromarray(frame),(0,0));pair.paste(Image.fromarray(l5),(size[0],0));pair.save(dest/'Real_vs_3D.png')
        poses=[]
        for name,offset in [('source_reference',0),('diagnostic_left',-1),('diagnostic_right',1)]:d=p['pose'].copy();d[:3,3]+=offset*d[:3,0];poses.append(dict(name=name,c2w=d))
        figs,meta=diag.figures(P,rgb,B,brgb,mesh,scene,p['K'],p['pose'],poses,size,cfg,c['id'],c['morphology'],c['ring'],c['condition'],l5_images=(frame,l5))
        for name,f in figs.items():f.savefig(dest/name,dpi=160,facecolor='white');plt.close(f)
        np.savez_compressed(dest/'actual_layers_exact.npz',P0_XYZ_mm=P,P0_RGB=rgb,source_u=a['source_u'],source_v=a['source_v'],background_XYZ_mm=B,background_RGB=brgb,background_source_uv=buv,source_K=p['K'],source_c2w=p['pose'],source_image_size=size,diagnostic_left_c2w=poses[1]['c2w'],diagnostic_right_c2w=poses[2]['c2w'],scene_id=c['id'],condition=c['condition'],morphology=c['morphology'],ring=c['ring'])
        final=np.load(R/f'local_results/{c["id"]}/Final_Cleaned_exact.npz');keep=np.ones(len(P),bool);keep[:]=True
        if'kept_original_indices'in final:keep[:]=False;keep[final['kept_original_indices']]=True
        trial=R/f'local_results/{c["id"]}/T2_exact.npz';marked=a['rho_surface_radius']<float(np.load(trial)['rho_threshold'])if trial.exists()else np.zeros(len(P),bool);f,ax=plt.subplots(1,3,figsize=(18,7));lim=bounds(c)
        cloud(ax[0],c,P,rgb,'Raw',lim);cloud(ax[1],c,P,rgb,'Candidate Marked / 未采纳T2（有候选时）',lim,marked=marked);cloud(ax[2],c,P[keep],rgb[keep],'Final Cleaned = Raw；证据不足不删除',lim);f.suptitle(c['id']+' / '+c['condition']+' / 原XYZ与RGB，统一范围');f.tight_layout();f.savefig(dest/'Raw_Marked_Final.png',dpi=160);plt.close(f)
        info=dict(id=c['id'],local_folder=str(dest),P0_N=len(P),background_N=len(B),L1_N=len(P),L2_N=len(B),L3_N=len(P)+len(B),L4_N=len(P)+len(B),L5_input_N=len(P)+len(B),XYZ='actual_layers_exact.npz; Ring-local mm; no points moved',source=c,parameters=cfg,diagnostic_cameras=poses,**meta);save('metrics/layers/'+c['id']+'.json',info);index.append(info);print('LAYER_SCENE',c['id'],flush=True)
    save('metrics/LAYER_SCENES.json',index)
def projection_figures(stage):
    rows=load(R/f'metrics/{stage}_results.json');pairs=load(R/'provenance'/('P2_PAIRS_FROZEN.json'if stage=='P2'else'P3_PAIRS_FROZEN.json'));groups=['004','005']
    for video in groups:
        rr=[x for x in rows if next(c for c in cases()if c['id']==x['A'])['video']==video];fig,ax=plt.subplots(len(rr),5,figsize=(24,5*len(rr)),squeeze=False)
        for i,row in enumerate(rr):
            c=next(c for c in cases()if c['id']==row['A']);dest=Path(row['local_output']);raw=dict(np.load(dest/'RAW/projection_exact.npz'));clean=dict(np.load(dest/'CLEANED/projection_exact.npz'));real=np.asarray(Image.open(dest/'RAW/B_real_frame.png'));valid=raw['kind']==1;delta=np.abs(raw['RGBA'][:,:,:3].astype(float)-real).mean(2);err=np.zeros((*valid.shape,4));err[:,:,:3]=cm.magma(np.clip(delta/128,0,1))[:,:,:3];err[:,:,3]=valid
            panels=[(real,'B真实帧 '+row['B']),(raw['RGBA'],'A→B：仅A RGB；Raw'),(clean['RGBA'],'未采纳T2诊断'if stage=='P2'and c['group']=='G01'else'最终Raw保留；未配准认证'),(err,'Raw全预测P0像素差异（含Mask外）\n0–128/255固定色阶；无覆盖透明')]
            for j,(im,title)in enumerate(panels):ax[i,j].set_facecolor('#dddddd');ax[i,j].imshow(im,interpolation='nearest');ax[i,j].set_title(title);ax[i,j].axis('off')
            a,p,rgb,m=data(c);cloud(ax[i,4],c,a['XYZ_mm'],rgb,c['id']+'实际XYZ侧视\n'+row['candidate']);ax[i,0].set_title('B '+row['B']+f' / Raw覆盖{row["raw_coverage"]:.1%}');ax[i,2].set_title(ax[i,2].get_title()+f'\n覆盖{row["cleaned_coverage"]:.1%} / 共同N={row["common_support_N"]}')
            Image.fromarray(np.rint(err*255).astype(np.uint8)).save(dest/'RAW/Difference_valid.png')
            f,side=plt.subplots(figsize=(7,7));cloud(side,c,a['XYZ_mm'],rgb,'A原始XYZ侧视 / '+c['id']);f.tight_layout();f.savefig(dest/'XYZ_side.png',dpi=160);plt.close(f)
        fig.suptitle(stage+' video'+video+'｜真实另一帧验证；B颜色绝不用于预测\n'+('未采纳T2不改变最终Raw；非全流程盲测，RGB误差不是深度精度'if stage=='P2'else'仅历史H及其逆变换；NO_VERIFIED_REGISTRATION，无新融合'),fontsize=15);publish(fig,'Fig'+stage+'_'+video+'_crossframe.png')
    fig,ax=plt.subplots(2,2,figsize=(17,12));labels=[x['A'].replace('G01_','')+'\n'+x['candidate']for x in rows];xx=np.arange(len(rows));ax[0,0].bar(xx-.18,[x['raw_coverage']for x in rows],.36,label='Raw');ax[0,0].bar(xx+.18,[x['cleaned_coverage']for x in rows],.36,label='Rejected T2 / final Raw');ax[0,0].set_title('B Polyp Mask覆盖，全分母');ax[0,0].legend()
    for key,label in [('raw_valid','Raw独立支持'),('cleaned_valid','候选独立支持'),('common_raw','Raw共同支持'),('common_cleaned','候选共同支持')]:ax[0,1].plot(xx,[x[key]['MAE']for x in rows],marker='o',label=label)
    ax[0,1].set_title('RGB MAE / 255，支持集分开');ax[0,1].legend(fontsize=8)
    worst=max(rows,key=lambda x:x['raw_valid']['MAE']or-1);dest=Path(worst['local_output']);ax[1,0].imshow(Image.open(dest/'RAW/Overlay.png'));ax[1,0].set_title('Raw叠加反例 / '+worst['A']+' → '+worst['B']);ax[1,0].axis('off');ax[1,1].axis('off');ax[1,1].text(.02,.95,'证据限制\n\n源相机和HERO均已冻结，无GT。\nB仅独立比较，不重着色或抹错点。\n单像素源点Z-buffer；未知背面不补全。\n光照/反光、相机、深度与遮挡均可贡献差异。\n相同原点共同支持颜色误差按构造不变。\n覆盖损失不能被更低独立支持均值掩盖。\n跨视频无新静态背景对应认证，不融合。',va='top',fontsize=15)
    for panel in ax[0]:panel.set_xticks(xx,labels,rotation=30,fontsize=7);panel.grid(alpha=.2)
    fig.suptitle(stage+'｜覆盖、共同支持与失败；不是三维准确率',fontsize=16);publish(fig,'Fig'+stage+'_support_and_failure.png')
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['P1','P2','P3','layers']);args=p.parse_args();all_scenes()if args.stage=='layers'else P1()if args.stage=='P1'else projection_figures(args.stage)
