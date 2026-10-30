"""Accepted real-P0 point/CAD renderer; original-face edges are diagnostics."""
from render import *
from frontier import *
from matplotlib.collections import LineCollection
from matplotlib import cm,colors as mcolors
from evaluate import unique_points,old_f2_points,no_joint
PINK=np.array([.94,.29,.55]);BLUE=np.array([.15,.65,.93]);COLORS=np.array([PINK,BLUE,[.95,.66,.18],[.31,.74,.39],[.73,.38,.86],[.95,.42,.19]])
def data_blocks(blocks,by_generation=False):
    a=display_arrays(blocks);cid=blocks[0]['reference'];s=source(cid);b=background(cid);col=COLORS[a['generation']%len(COLORS)]if by_generation else a['C'];return dict(P=a['P'],C=col,B=b['P'],BC=b['C'],p=s['p'],ring=s['ring'],primary=cid)
def blank(cid,P,C):
    s=source(cid);return dict(P=P,C=C,B=np.empty((0,3)),BC=np.empty((0,3)),p=s['p'],ring=s['ring'],primary=cid)
def lines(ax,XYZ,color,angle_=(-65,22),lw=.8,zorder=4):
    eye,right,up=vis.basis(angle_);xy=np.stack([XYZ@right,XYZ@up],-1);ax.add_collection(LineCollection(xy,colors=color,linewidths=lw,zorder=zorder))
def p0():
    ids=load(R/'provenance/MAIN_SURFACES_SELECTED.json')['selections'];fig,axes=plt.subplots(3,4,figsize=(21,15));parameters=[]
    for i,g in enumerate(['G06','G07','G08']):
        sid=g+('_005'if g=='G08'else'_004');main=source(ids[sid]);new=next(c for c in cases()if c['group']==g and c.get('new_reference'));s=source(new['id']);z=old_F2(new['id']);raw=point_data(new['id']);mainids=np.unique(main['F'][clean_faces(ids[sid])]);fids=np.flatnonzero(z['accepted'][s['F']].all(1));newids=np.unique(s['F'][fids]);bounds=diag.square_bounds([main['P'],raw['P'],main['ring'].vertices],[vis.basis((-65,22))])[0];empty=lambda c,n:np.tile(c,(n,1))
        d=blank(ids[sid],main['P'][mainids],empty(PINK,len(mainids)));side(axes[i,0],d,g+' 主参考Cleaned / 粉\n'+('UNQUALIFIED_CAMERA_STRESS'if g=='G07'else main['c']['condition']),(-65,22),bounds)
        n=~cleaned(new['id'])['clean_removed'];d=blank(ids[sid],s['P'][n],empty(BLUE,n.sum()));side(axes[i,1],d,'Cleaned F1蓝色完整来源（非整片获认可）\nF2实际接纳点 '+str(z['accepted'].sum())+'/'+str(n.sum()),(-65,22),bounds)
        d=blank(ids[sid],np.r_[main['P'][mainids],s['P'][newids]],np.r_[empty(PINK,len(mainids)),empty(BLUE,len(newids))]);side(axes[i,2],d,'实际F2完整原面：'+str(len(fids))+'面\n'+f'{s["areas"][fids].sum():.3f} mm²（工程认可，非GT）',(-65,22),bounds)
        edges,_=edge_counts(s['F'][fids]);lines(axes[i,2],s['P'][edges],BLUE,lw=.3,zorder=1)
        b=load_scene(sid,0);front=frontier(b);side(axes[i,3],d,'真实开放边界；非自动可生长\n绿外观测终止 / 橙选面切口 / 红Ring遮挡',(-65,22),bounds);colors=np.array([{'OBSERVATION_TERMINATION':'#159c40','GROWTH_SELECTION_FRONTIER':'#dd891e','RING_OCCLUSION':'#bc3333'}.get(x,'#777')for x in front['categories']]);lines(axes[i,3],front['XYZ_edges'],colors,lw=.7);parameters.append(dict(scene=sid,source=new['id'],bounds_mm=bounds,angle=[-65,22],original_faces_used=fids,old_F2_points=int(z['accepted'].sum()),camera_condition=new['condition']))
    fig.suptitle('P0｜人工认可区域的来源核对：完整F1来源 ≠ F2接纳点 ≠ 完整原始三角面\n主体/新增均实际XYZ，黑色实体CAD。旧几何保存独立版本；用户最新授权允许派生的局部联合调整。',fontsize=13);fig.tight_layout(rect=[0,.01,1,.94]);fig.subplots_adjust(hspace=.26);put(fig,'Fig1_engineering_seed_recovery.png');save('provenance/Fig1_PARAMETERS.json',parameters)
    fig,axes=plt.subplots(2,3,figsize=(19,11))
    for i,sid in enumerate(['G01_004','G01_005']):
        d=data_blocks(load_scene(sid,0));fr=frontier(load_scene(sid,0));bounds=diag.square_bounds([d['P'],d['B'],d['ring'].vertices],[vis.basis((-65,22)),vis.basis((0,0))])
        for j,a in enumerate([(-65,22),(0,0)]):side(axes[i,j],d,sid+' 初始主参考 / 实际RGB / mm',a,bounds[j]);lines(axes[i,j],fr['XYZ_edges'][fr['eligible']],'#d0472d',a,lw=.8)
        axes[i,2].axis('off');text=sid+' 生长边界分类\n'
        for kind in sorted(set(fr['categories'])):text+=kind+f'：{fr["lengths"][fr["categories"]==kind].sum():.2f} mm\n'
        axes[i,2].text(.02,.95,text+'\n清理内孔/深度断裂/未知不自动当外边界。\nRing边界须新源真实可见才可尝试外延。\n旧F2仅对照，不再用其点级接纳作唯一算法。',va='top',fontsize=10)
    fig.suptitle('P1｜G01实际原面边界：斜视 / 侧视 / 分类，黑色实体CAD；背景仅DISPLAY_ONLY',fontsize=13);fig.tight_layout(rect=[0,.01,1,.94]);put(fig,'Fig2_G01_initial_frontiers.png')
    fig,axes=plt.subplots(5,3,figsize=(18,23))
    for i,sid in enumerate(ids):
        cc=[c for c in historical_cases()if sceneid(c)==sid];Ps=[];Cs=[];Fp=[];Fc=[]
        for j,c in enumerate(cc):
            s=source(c['id']);k=~cleaned(c['id'])['clean_removed'];Ps.append(s['P'][k]);Cs.append(np.tile(COLORS[j%6],(k.sum(),1)));k=old_F2(c['id'])['accepted'];Fp.append(s['P'][k]);Fc.append(np.tile(COLORS[j%6],(k.sum(),1)))
        main=source(ids[sid]);bounds=diag.square_bounds(Ps+[main['ring'].vertices],[vis.basis((-65,22))])[0]
        for j,(P,C,title)in enumerate([(np.concatenate(Ps),np.concatenate(Cs),'历史Cleaned F1全来源'),(np.concatenate(Fp),np.concatenate(Fc),'历史F2点级选择（只读对照）')]):side(axes[i,j],blank(ids[sid],P,C),sid+' / '+title,(-65,22),bounds)
        d=data_blocks(load_scene(sid,0),True);d['B']=np.empty((0,3));d['BC']=d['B'];side(axes[i,2],d,'按质量/连续支持面积选定S0\n'+('UNQUALIFIED_CAMERA_STRESS'if sid.startswith('G07')else main['c']['condition']),(-65,22),bounds)
    fig.suptitle('P0基线｜Cleaned F1 / 历史F2 / 本轮初始主体与工程种子\n每行固定同视角、毫米范围与点大小；所有完整原面/源点均保留，最终几何是否改善尚待实验',fontsize=13);fig.tight_layout(rect=[0,.01,1,.96]);fig.subplots_adjust(hspace=.30);put(fig,'Fig3_F1_F2_selected_initial.png')
def grown_data(blocks,total_rounds=None,rgb=False,background_on=False):
    a=unique_points(blocks);cid=load(R/'provenance/MAIN_SURFACES_SELECTED.json')['selections'][sceneid(case(blocks[0]['reference']))];s=source(cid);gen=a['generation'];total=total_rounds or max(1,int(gen.max()));C=a['C'].copy()if rgb else cm.turbo(gen/(total+1))[:,:3]
    if not rgb:C[gen==0]=PINK;C[(gen==0)&(a['references']!=cid)]=BLUE
    b=background(cid);return dict(P=a['P'],C=C,B=b['P']if background_on else np.empty((0,3)),BC=b['C']if background_on else np.empty((0,3)),p=s['p'],ring=s['ring'],primary=cid)
def fixed_bounds(sid,angles=[(-65,22)]):
    cc=[c for c in cases()if sceneid(c)==sid];s=source(cc[0]['id']);return diag.square_bounds([source(c['id'])['P']for c in cc]+[s['ring'].vertices],[vis.basis(a)for a in angles])
def growth_progress(sid,num,local_frames=True,core=True):
    final=load(R/f'local_results/scenes/{sid}_Final.json');N=final['accepted_steps'];steps=load(R/f'metrics/growth_steps_{sid}.json');milestones=list(dict.fromkeys([0,1,min(2,N),max(1,N//2),N]));fig,axes=plt.subplots(2,5,figsize=(22,10),gridspec_kw=dict(height_ratios=[1,.8]));bb=fixed_bounds(sid)[0]
    for j,k in enumerate(milestones):
        d=grown_data(load_scene(sid,k),N);side(axes[0,j],d,sid+' / S'+str(k)+(' Final'if k==N else''),(-65,22),bb);f=frontier(load_scene(sid,k));lines(axes[0,j],f['XYZ_edges'][f['eligible']],'#d38527',lw=.45)
    for j in range(len(milestones),5):axes[0,j].axis('off')
    x=np.arange(1,N+1);delta=np.array([r['delta_area_mm2']for r in steps]);axes[1,0].bar(x,delta,color='#269dcc');axes[1,0].set(title='每轮完整原面 ΔA（暴露代理）',xlabel='轮次',ylabel='mm²');axes[1,1].plot(np.r_[0,x],np.r_[0,np.cumsum(delta)],'o-',ms=2);axes[1,1].set(title='累计新增完整原面（非解剖真面积）',xlabel='轮次',ylabel='mm²');axes[1,2].plot(x,[r['seam_distance_mm']['median']for r in steps],'.-',label='中位');axes[1,2].plot(x,[r['seam_distance_mm']['p95']for r in steps],'.-',label='p95');axes[1,2].legend(fontsize=8);axes[1,2].set(title='边界附近几何距离（未焊接）',xlabel='轮次',ylabel='mm')
    axes[1,3].axis('off');axes[1,3].text(.01,.98,f'接受 {N} 轮\n实际新增HERO参考 {final["new_HERO_attempts"]}\nΔA={delta.sum():.4f} mm²\n'+f'联合调整接纳 {sum(r["joint_alignment"].get("accepted",False)for r in steps)} 轮\n'+final['stop_reason']+'\n\n后期微小增益完整记录；不以轮数当成功率。\n不是GT几何精度。',va='top',fontsize=10);latest=source(steps[-1]['reference'])if steps else source(final['blocks'][0]['reference']);axes[1,4].imshow(latest['frame']);axes[1,4].axis('off');axes[1,4].set_title('最后接纳来源的真实帧\n'+latest['c']['reference'],fontsize=9)
    cond='UNQUALIFIED_CAMERA_STRESS'if sid.startswith('G07')else case(final['blocks'][0]['reference'])['condition'];fig.suptitle(sid+'｜'+cond+'｜S0→逐轮生长→Final\n粉：初始主面；蓝：工程种子；各生长轮次用turbo连续色标。实际XYZ/完整原面，不平滑补面；同窗口与点大小；橙线为条件边界。',fontsize=13);fig.tight_layout(rect=[0,.01,1,.92]);fig.subplots_adjust(hspace=.25);bar=axes[1,3].inset_axes([.01,.09,.94,.035]);fig.colorbar(cm.ScalarMappable(norm=mcolors.Normalize(0,N+1),cmap='turbo'),cax=bar,orientation='horizontal',ticks=list(dict.fromkeys([1,max(1,N//2),N])));bar.set_xlabel('新增面轮次（粉/蓝另作S0图例）',fontsize=8);bar.tick_params(labelsize=7);put(fig,f'Fig{num}_{sid}_incremental_growth.png'if core else f'local/{sid}/Incremental_growth.png')
    for k in range(N+1)if local_frames else[]:
        d=grown_data(load_scene(sid,k),N);f,ax=plt.subplots(figsize=(9,7));side(ax,d,sid+f' / S{k} / {cond}',(-65,22),bb);f.suptitle('实际来源XYZ，轮次着色；同一毫米窗口；未补面/平滑',fontsize=10);f.tight_layout();put(f,f'local/{sid}/rounds/S{k:03d}.png')
def joint_comparison():
    fig,axes=plt.subplots(3,3,figsize=(18,16))
    for i,sid in enumerate(['G06_004','G07_004','G08_005']):
        b=load_scene(sid);bb=fixed_bounds(sid)[0];N=load(R/f'local_results/scenes/{sid}_Final.json')['accepted_steps']
        for j,(blocks,label)in enumerate([(load_scene(sid,0),'初始主面+工程种子'),(no_joint(b),'同样选中原面 / 优化前'),(b,'同样选中原面 / 局部联合优化后')]):
            d=grown_data(blocks,N);side(axes[i,j],d,sid+' / '+label+'\n'+('UNQUALIFIED_CAMERA_STRESS'if sid.startswith('G07')else case(blocks[0]['reference'])['condition']),(-65,22),bb)
    fig.suptitle('局部联合配准对照｜优化前后保留完全相同的原始面ID，派生SE(3)独立保存\n仅完整原面/实际点；主面和新增面均可移动，形状分量保持刚性。未焊接接缝，黑色CAD和科研相机均未动。',fontsize=13);fig.tight_layout(rect=[0,.01,1,.94]);fig.subplots_adjust(hspace=.25);put(fig,'Fig7_local_joint_before_after.png')
def g01_comparison():
    fig,axes=plt.subplots(4,3,figsize=(20,21))
    for i,sid in enumerate(['G01_004','G01_005']):
        blocks=load_scene(sid);cid=blocks[0]['reference'];cc=[c for c in historical_cases()if sceneid(c)==sid];P=np.concatenate([source(c['id'])['P'][~cleaned(c['id'])['clean_removed']]for c in cc]);C=np.concatenate([np.tile(COLORS[j%6],((~cleaned(c['id'])['clean_removed']).sum(),1))for j,c in enumerate(cc)]);f2=old_f2_points(sid);ds=[blank(cid,P,C),blank(cid,f2['P'],f2['C']),grown_data(blocks,rgb=True)];bounds=fixed_bounds(sid)[0];ring=source(cid)['ring'];q=ring.vertices@vis.basis((-65,22))[1];v=ring.vertices@vis.basis((-65,22))[2];cx=np.median(q);cy=np.median(v);zoom=[(cx-12,cx+12),(cy-16,cy+8)]
        for j,(d,title)in enumerate(zip(ds,['Historical Cleaned F1','Historical F2','Boundary Growth F3 / Joint'])):
            side(axes[2*i,j],d,sid+' / '+title+' / 全尺度',(-65,22),bounds);side(axes[2*i+1,j],d,title+' / 相同局部放大窗口',(-65,22),zoom)
    fig.suptitle('G01｜从整片叠加到边界外延：F1 / F2 / F3\n上行全源范围保留异常，下行只作同窗口放大；未靠裁切计算指标；原始曲面和冲突完整保存，RGB均来自各自真实来源。',fontsize=13);fig.tight_layout(rect=[0,.01,1,.95]);fig.subplots_adjust(hspace=.28);put(fig,'Fig8_G01_F1_F2_F3_full_and_zoom.png')
def local_AB_and_scenes():
    from evaluate import target_rows
    ns=dict(globals());node=next(n for n in ast.parse((GRAZ/'code/scene_renderer.py').read_text()).body if isinstance(n,ast.FunctionDef)and n.name=='five_panel');exec(compile(ast.Module(body=[node],type_ignores=[]),str(GRAZ/'code/scene_renderer.py'),'exec'),ns);rows=[]
    for sid in load(R/'provenance/MAIN_SURFACES_SELECTED.json')['selections']:
        path=R/f'local_results/scenes/{sid}_Final.json'
        if not path.exists():continue
        blocks=load_scene(sid);cid=blocks[0]['reference'];N=load(path)['accepted_steps'];t=list(target_rows(sid))[0];d0=grown_data([b for b in load_scene(sid,0)if b['role'].startswith('PRIMARY')],rgb=True,background_on=True);old=old_f2_points(sid);d2=dict(d0,P=old['P'],C=old['C']);d3=grown_data(blocks,rgb=True,background_on=True)
        for name,d in [('Selected_Main',d0),('Historical_F2',d2),('F3_Joint',d3)]:
            ns['source_data']=lambda _,d=d:d;out=R/f'figures/local/A_to_B/{sid}_{name}_to_{t["id"]}.png';row=ns['five_panel'](cid,t,out,('UNQUALIFIED_CAMERA_STRESS'if sid.startswith('G07')else case(cid)['condition']),main_title=name+' 多参考场景A（颜色均来自各自源图，非B）→冻结真实B');row.update(method=name,scene=sid);rows.append(row)
        # A strict single-source A→B figure is retained in addition to the
        # multi-reference scene comparisons; no ambiguity about color origin.
        new=next((c for c in reversed(cases())if sceneid(c)==sid and c['id']in set(b['reference']for b in blocks)and'_growth_'in c['id']),None)
        if new:
            ns['source_data']=lambda _,cid=new['id']:point_data(cid,'Cleaned');out=R/f'figures/local/A_to_B/{sid}_single_new_source_to_{t["id"]}.png';row=ns['five_panel'](new['id'],t,out,'SOURCE_ONLY_FROZEN_CAMERA_CANDIDATE',main_title='严格单源A XYZ与A RGB → B；不混入其他源颜色');row.update(method='Single_New_A_Only',scene=sid);rows.append(row)
        im,info=scene_image(d3,d3['p']['K'],d3['p']['pose']);f,aa=plt.subplots(1,2,figsize=(16,5));aa[0].imshow(source(cid)['frame']);aa[1].imshow(im)
        for ax in aa:ax.axis('off')
        aa[0].set_title('真实选中主帧 '+cid);aa[1].set_title('同相机F3真实来源RGB + 黑CAD + 实际背景');f.suptitle(sid+'｜展示，不是三维精度证据；背景DISPLAY_ONLY');f.tight_layout();put(f,f'local/{sid}/Real_vs_F3.png');save(f'provenance/SCENE_DISPLAY_{sid}.json',info)
    both('A_to_B_display_index',rows)
    # One representative standard five-panel is public; all methods/groups
    # remain in the local gallery, target fixed before errors were computed.
    representative=next((r for r in rows if r['scene']=='G06_004'and r['method']=='F3_Joint'),None)
    if representative:
        from shutil import copyfile
        copyfile(R/representative['figure'],R/'figures/Fig10_standard_A_to_B_F3_G06.png')
def g01_six_views():
    a=grown_data(load_scene('G01_004'),rgb=True,background_on=True);b=grown_data(load_scene('G01_005'),rgb=True,background_on=True);edge=next(e for e in load(BASE/'metrics/registration_edges.json')if e['kind']=='CROSS_VIDEO');H=np.linalg.inv(np.array(edge['Ring']['H_source_to_target_world']));d=dict(a,P=np.r_[a['P'],transform(b['P'],H)],C=np.r_[a['C'],b['C']],B=np.r_[a['B'],transform(b['B'],H)],BC=np.r_[a['BC'],b['BC']]);poses=[a['p']['pose'],H@b['p']['pose']];virtual=poses[0].copy();virtual[:3,3]+=2*virtual[:3,0];poses.append(virtual);Ks=[a['p']['K'],b['p']['K'],a['p']['K']];angles=[(0,0),(90,0),(-90,90)];bounds=diag.square_bounds([d['P'],d['B'],d['ring'].vertices],[vis.basis(x)for x in angles]);P=np.r_[d['P'],d['B']];C=np.r_[d['C'],d['BC']];params=[]
    for depth in [False,True]:
        fig,axes=plt.subplots(2,3,figsize=(19,11))
        for j,(K,pose)in enumerate(zip(Ks,poses)):
            sc=camera_scene(d,K,pose);colors=C
            if depth:
                z=vis.project_camera(P,K,pose)[1];colors=diag.colors_for_depth(z)[0]
            sc.draw(axes[0,j],d['P'],colors[:len(d['P'])],d['B'],colors[len(d['P']):],point_size=.08);sc.scale_bar(axes[0,j]);axes[0,j].set_title(['接近004冻结源相机','接近005（候选H映入004）','第三视点：004横移+2mm，虚拟诊断'][j]+(' / Z色'if depth else' / 源RGB'),fontsize=10)
        for j,ang in enumerate(angles):
            col=diag.colors_for_depth(P@vis.basis(ang)[0])[0]if depth else C;side(axes[1,j],d,['Ring X正交','Ring Y正交','Ring Z正交'][j]+(' / 视向坐标色 mm'if depth else' / 源RGB'),ang,bounds[j],colors=col);axes[1,j].set_xlabel([ 'Ring Y / mm','−Ring X / mm','Ring X / mm'][j]);axes[1,j].set_ylabel(['Ring Z / mm','Ring Z / mm','Ring Y / mm'][j])
        fig.suptitle('G01｜完整F3点云六方向｜CROSS-VIDEO REGISTRATION CANDIDATE — NOT FUSED\n004/005独立模型仅按既有候选H共同诊断；CAD以004为固定锚点。全部实际接纳点和背景，不补面；上行为相机诊断，下行为统一毫米正交。',fontsize=13);fig.tight_layout(rect=[0,.01,1,.93]);put(fig,'local/G01_six_views_depth.png'if depth else'Fig11_G01_six_views_candidate_not_fused.png')
    save('provenance/G01_SIX_VIEW_PARAMETERS.json',dict(H_005_to_004=H,poses=poses,K=Ks,XYZ_bounds_mm=bounds,point_size=.08,CAD_fixed_to='video004',status='CANDIDATE_NOT_FUSED',GT_used=False))
if __name__=='__main__':
    arg=sys.argv[1]if len(sys.argv)>1 else'P0'
    if arg=='P0':p0()
    elif arg=='positive':
        for sid,n in [('G06_004',4),('G07_004',5),('G08_005',6)]:growth_progress(sid,n)
        joint_comparison()
    elif arg=='final':
        for sid in ['G01_004','G01_005']:growth_progress(sid,9,True,False)
        g01_comparison();local_AB_and_scenes();g01_six_views()
