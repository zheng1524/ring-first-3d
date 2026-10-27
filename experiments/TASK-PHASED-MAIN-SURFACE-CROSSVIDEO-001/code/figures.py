"""Four review figures, complete source XYZ layers, and same-camera L5 displays."""
from evaluation import *
plt=vis.configure()
from matplotlib import colormaps
def scenes():
    values=[]
    for video in ['004','005']:
        P,rgb,kind=point_data(video,'D0_FULL');values.append(dict(name='video'+video,video=video,P=P[kind==1],rgb=rgb[kind==1],B=P[kind==2],brgb=rgb[kind==2],frame='LOCAL FRAME',H=np.eye(4)))
    H=np.array(load(R/'metrics/D1_display_candidate.json')['H_005_to_004']);a,b=values;values.append(dict(name='004 + 005 candidate',video='004',P=np.r_[a['P'],transform(b['P'],H)],rgb=np.r_[a['rgb'],b['rgb']],B=np.r_[a['B'],transform(b['B'],H)],brgb=np.r_[a['brgb'],b['brgb']],frame='REGISTRATION CANDIDATE — NOT FUSED',H=H));return values
def allpoints(s):return np.r_[s['P'],s['B']],np.r_[s['rgb'],s['brgb']]
def plot(ax,s,basis,limits,title,depth=False,ring_alpha=.15):
    P,rgb=allpoints(s);r=diag.points(ax,P,rgb,limits,title,basis=basis,point_size=.08,alpha=1,ring_scene=scene_for(target('004','selection')[0]),ring_alpha=ring_alpha,depth_color=depth);return r
def finish(fig,name,top=.94):
    fig.tight_layout(rect=[0,.02,1,top])
    if name.startswith('Fig4'):fig.subplots_adjust(hspace=.32,wspace=.22)
    fig.savefig(R/'figures'/name,dpi=160,facecolor='white');plt.close(fig)
def three_columns():
    ss=scenes();angles=[(-65,22),(0,0),(-45,70)];bases=[vis.basis(x)for x in angles];limits=diag.square_bounds([*[allpoints(s)[0]for s in ss],ring(cases()[0]).vertices],bases);fig,ax=plt.subplots(3,3,figsize=(25,20));heads=['SINGLE-VIDEO RECONSTRUCTION — video004\nAll available references | Visible surface | Ring-anchored\nLOCAL FRAME; CONFLICT/UNKNOWN retained','SINGLE-VIDEO RECONSTRUCTION — video005\nAll available references | Visible surface | Ring-anchored\nLOCAL FRAME; CONFLICT/UNKNOWN retained','CROSS-VIDEO REGISTRATION CANDIDATE — NOT FUSED\nCached LightGlue + source-depth PnP | No GT\nNo certified common physical pose']
    for j,s in enumerate(ss):
        for i,basis in enumerate(bases):plot(ax[i,j],s,basis,limits[i],['主体斜视 / actual XYZ','侧视：错层/延伸不隐藏','俯视/斜后方：虚拟诊断'][i]+f'\nP={len(s["P"]):,}, B={len(s["B"]):,}')
        fig.text((j+.5)/3,.975,heads[j],ha='center',va='top',fontsize=12)
    fig.text(.5,.012,'Same millimeter scale, actual source RGB points; no smooth surfaces/texture planes. Ring is known CAD. Unresolved layers remain separate.',ha='center',fontsize=12);finish(fig,'Fig1_three_complete_scenes.png',.92)
def six_views():
    ss=scenes();s4=source(load(R/'metrics/D0_004.json')['main_reference']);s5=source(load(R/'metrics/D0_005.json')['main_reference']);H=np.array(load(R/'metrics/D1_display_candidate.json')['H_005_to_004']);R4=s4['p']['pose'][:3,:3];R5=H[:3,:3]@s5['p']['pose'][:3,:3];bases=[(-R4[:,2],R4[:,0],-R4[:,1]),(-R5[:,2],R5[:,0],-R5[:,1]),vis.basis((25,30)),*[x[:3]for x in diag.AXES.values()]];limits=diag.square_bounds([*[allpoints(s)[0]for s in ss],ring(cases()[0]).vertices],bases);fig,ax=plt.subplots(3,6,figsize=(32,16));labels=['接近004方向（正交诊断）','接近005方向（正交诊断）','第三虚拟观察方向','World +X','World +Y','World +Z']
    for i,s in enumerate(ss):
        for j,basis in enumerate(bases):plot(ax[i,j],s,basis,limits[j],s['name']+'\n'+labels[j]+(' / LOCAL FRAME'if i<2 else' / NOT FUSED'))
    fig.suptitle('统一毫米尺度六视角｜3个成果均为真实来源XYZ；每方向使用相同相机朝向、范围及点大小\nLOCAL FRAME行仅作数值方向对照，不声称物理方位已对齐；候选行005采用派生刚体副本',fontsize=15);finish(fig,'Fig2_six_views_actual_XYZ.png',.94)
def reprojection():
    display=load(R/'metrics/D1_display_candidate.json')['candidate'];old='HISTORICAL_FULL_LightGlue';spec=[('005','004',target('004','holdout')[0]),('004','005',target('005','holdout')[0])];ss=scenes();fig,ax=plt.subplots(2,7,figsize=(30,11));metrics=[]
    H=np.array(load(R/'metrics/D1_display_candidate.json')['H_005_to_004'])
    for i,(video,other,t)in enumerate(spec):
        dest=R/f'local_results/D1_evaluation/{display}/{video}_to_{other}/{t["id"]}';odest=R/f'local_results/D1_evaluation/{old}/{video}_to_{other}/{t["id"]}';B=np.asarray(Image.open(dest/'B_real.png'));tri=dict(np.load(dest/'triangle_prediction_exact.npz'));tri0=dict(np.load(odest/'triangle_prediction_exact.npz'));p=dict(np.load(dest/'point_prediction_exact.npz'));p0=dict(np.load(odest/'point_prediction_exact.npz'));lab=cv2.imread(t['Mask'],0);common=(tri['kind']==1)&(tri0['kind']==1)&(lab==1);commonP=(p['kind']==1)&(p0['kind']==1)&(lab==1);diff=np.zeros((360,640,4));err=np.abs(tri['RGBA'][:,:,:3].astype(float)-B).mean(2);diff[:,:,:3]=colormaps['magma'](np.clip(err/128,0,1))[:,:,:3];diff[:,:,3]=common;overlay=np.asarray(Image.open(dest/'Overlay.png'));ims=[B,tri0['RGBA'],tri['RGBA'],p['RGBA'],overlay,diff];titles=['真实B '+t['id'],'历史LightGlue / 原面','新PnP候选 / 原面','新候选 / 实际源点','新候选叠加 / 未知透明','共同B Polyp支持误差\nN='+str(int(common.sum()))+'，0–128/255']
        titles[0]=f'video{video}三参考场景 → video{other}\n真实B raw{t["raw_frame"]:05d}'
        for j,(im,title)in enumerate(zip(ims,titles)):ax[i,j].imshow(im,interpolation='nearest');ax[i,j].set_title(title,fontsize=10);ax[i,j].axis('off')
        s=ss[0]if video=='004'else ss[1];T=H if video=='005'else np.linalg.inv(H);copy=dict(s,P=transform(s['P'],T),B=transform(s['B'],T));basis=vis.basis((0,0));bounds=diag.square_bounds([allpoints(copy)[0],ring(cases()[0]).vertices],[basis])[0];plot(ax[i,6],copy,basis,bounds,'A派生XYZ侧视 / B坐标\n不是视频帧')
        row=dict(source_video=video,target=t['id'],common_triangle_support_N=int(common.sum()),historical_common_RGB=errors(tri0,B,common),new_common_RGB=errors(tri,B,common),common_point_support_N=int(commonP.sum()),historical_common_point_RGB=errors(p0,B,commonP),new_common_point_RGB=errors(p,B,commonP));metrics.append(row);Image.fromarray(np.rint(diff*255).astype(np.uint8)).save(dest/'Difference_common_support.png');f,side=plt.subplots(figsize=(8,8));plot(side,copy,basis,bounds,'实际XYZ在B坐标；虚拟侧视');f.tight_layout();f.savefig(dest/'XYZ_side.png',dpi=160);plt.close(f)
    fig.suptitle('真实A→B留出验证｜预测颜色只来自A场景的真实源RGB，不用B重着色\n点与原始三角面是两种可见性显示；原面内源RGB插值明确标记，无补面/补洞；配准未通过融合门控',fontsize=15);fig.tight_layout(rect=[0,0,1,.91]);fig.subplots_adjust(hspace=.35,wspace=.18);fig.savefig(R/'figures/Fig3_real_crossframe_reprojection.png',dpi=160,facecolor='white');plt.close(fig);save('metrics/D1_common_support_RGB.json',metrics);csvsave('metrics/D1_common_support_RGB.csv',metrics)
def baseline_figure():
    extras=load(R/'metrics/D0_common_denominator_geometry.json');bench=load(R/'metrics/D0_BC_comparison.json');fig=plt.figure(figsize=(26,19));gs=fig.add_gridspec(3,4,height_ratios=[1,1,.65]);modes=['SINGLE','B','C','D0_FULL'];basis=vis.basis((0,0))
    for i,video in enumerate(['004','005']):
        arrays=[point_data(video,mode,False)for mode in modes];limits=diag.square_bounds([*[x[0]for x in arrays],ring(cases()[0]).vertices],[basis])[0]
        for j,(mode,(P,rgb,kind))in enumerate(zip(modes,arrays)):
            ax=fig.add_subplot(gs[i,j]);top=next(x['topology']for x in bench if x['video']==video and x['method']==mode);temp=dict(P=P,rgb=rgb,B=np.empty((0,3)),brgb=np.empty((0,3)));plot(ax,temp,basis,limits,f'{video} {mode} | F={top["faces"]:,}\ncomponents={top["components"]}, nonmanifold={top["nonmanifold_edges"]}')
    a=fig.add_subplot(gs[2,:2]);b=fig.add_subplot(gs[2,2:]);allm=['SINGLE','B','C','D0_CORE','D0_FULL'];xx=np.arange(len(allm))
    for video,offset,color in [('004',-.18,'#377eb8'),('005',.18,'#e41a1c')]:
        values=[next(x for x in extras if x['video']==video and x['method']==m)for m in allm];a.bar(xx+offset,[100*x['fixed_source_retained_surface_fraction']for x in values],.36,label=video,color=color);b.bar(xx+offset,[100*x['front_conflict_exposure_fraction']for x in values],.36,label=video,color=color)
    for ax in [a,b]:ax.set_xticks(xx,allm);ax.legend();ax.grid(axis='y',alpha=.15)
    a.set_title('固定原始源点分母的近面保留率≤0.25mm\n004 N=51,382；005 N=47,461；非真实准确率');b.set_title('三源深度前冲突面曝光面积比例（非唯一解剖面积）\n主面原面保留100%；不把去重/未知层隐去算作改善')
    fig.suptitle('历史B/C与新D0真实XYZ同视角对照｜无重跑历史融合器\nD0_CORE为主面+有限补片；D0_FULL保留其他来源CONFLICT/UNKNOWN；主要错层仍未消除',fontsize=16);finish(fig,'Fig4_BC_new_coverage_conflict_loss.png',.93)
def local_layers():
    ss=scenes();index=[]
    for s in ss:
        video=s['video'];c=next(c for c in cases()if c['id']==load(R/f'metrics/D0_{video}.json')['main_reference']);src=source(c['id']);p=src['p'];frame=np.asarray(Image.open(c['RGB']).convert('RGB'));name=s['name'].replace(' ','_').replace('+','plus');dest=R/'local_results/visualizations'/name;dest.mkdir(parents=True,exist_ok=True);basis=vis.basis((-65,22));bounds=diag.square_bounds([allpoints(s)[0],ring(cases()[0]).vertices],[basis])[0];fig,ax=plt.subplots(5,2,figsize=(14,26));metadata=[]
        for row,(label,P,rgb,showring)in enumerate([('L1 source-derived Polyp (Raw archives unchanged)',s['P'],s['rgb'],False),('L2 actual background XYZ',s['B'],s['brgb'],False),('L3 exact point union',*allpoints(s),False),('L4 exact XYZ + original CAD',*allpoints(s),True)]):
            for j in [0,1]:metadata.append(dict(stage=row+1,**diag.points(ax[row,j],P,rgb,bounds,label+f' N={len(P):,}',basis=basis,point_size=.08,alpha=1,depth_color=bool(j),ring_scene=scene_for(target('004','selection')[0])if showring else None)))
        sc=SameCameraScene(ring(c),p['K'],p['pose'],(640,360),str(OLD/'surface_fusion_v3/vendor'));f=plt.figure(figsize=(4,2.25),dpi=160);view=f.add_axes([0,0,1,1]);sc.draw(view,s['P'],s['rgb'],s['B'],s['brgb'],point_size=.8);sc.scale_bar(view);f.canvas.draw();L5=np.asarray(f.canvas.buffer_rgba()).copy()[:,:,:3];plt.close(f);ax[4,0].imshow(frame);ax[4,1].imshow(L5);ax[4,0].set_title('L5 actual source frame / frozen camera');ax[4,1].set_title('L5 DISPLAY_ONLY / same camera');ax[4,0].axis('off');ax[4,1].axis('off');fig.suptitle(s['name']+' / '+s['frame']+'\nDerived source points; no smoothing/interpolation. L5 only is dense point rendering.');fig.tight_layout(rect=[0,0,1,.96]);fig.savefig(dest/'Layers_L1-L5.png',dpi=160);plt.close(fig);Image.fromarray(L5).save(dest/'Local_3D_Scene.png');pair=Image.new('RGB',(1280,360),'white');pair.paste(Image.fromarray(frame),(0,0));pair.paste(Image.fromarray(L5),(640,0));pair.save(dest/'Real_vs_3D.png');np.savez_compressed(dest/'actual_XYZ_RGB.npz',Polyp_XYZ_mm=s['P'],Polyp_RGB=s['rgb'],Background_XYZ_mm=s['B'],Background_RGB=s['brgb'],display_H_005_to_004=s['H'],source_K=p['K'],source_c2w=p['pose']);index.append(dict(scene=s['name'],status=s['frame'],Polyp_N=len(s['P']),Background_N=len(s['B']),stages=metadata,local_output=str(dest),source_main_frame=c['reference'],display_camera_pose_unchanged=True,point_size=.08,L5_point_size=.8))
    save('metrics/VISUAL_LAYER_INDEX.json',index)
if __name__=='__main__':
    three_columns();six_views();reprojection();baseline_figure();local_layers();print('FOUR_CORE_PNG_AND_LOCAL_LAYERS_COMPLETE',flush=True)
