"""Batch D figures through accepted source-XYZ/CAD drawing functions only.

No model, matching, camera optimization or geometry selection is run here.
"""
from render import *
from evaluate_d import pointset,scene_ids,eval_targets
from matching import views
from matplotlib.patches import Patch
PALETTE=np.array([[.94,.29,.55],[.15,.65,.93],[.96,.63,.12],[.45,.7,.25]])

def scene_data(sid,mode='ViewPartition_Cleaned_F2',source_colors=False):
    a=pointset(sid,mode);cid=a['references'][0];s=source(cid);b=background(cid)
    return dict(P=a['P'],C=PALETTE[a['reference_index']%4]if source_colors else a['C'],B=b['P'],BC=b['C'],p=s['p'],ring=s['ring'],primary=cid)

def cross_data():
    a=scene_data('G01_004');b=scene_data('G01_005');H=np.array(load(R/'metrics/CROSSVIDEO_GATE.json')['H_005_to_004'])
    return dict(a,P=np.r_[a['P'],transform(b['P'],H)],C=np.r_[a['C'],b['C']],B=np.r_[a['B'],transform(b['B'],H)],BC=np.r_[a['BC'],b['BC']])

def p8():
    contributions=load(R/'metrics/novel_surface_contribution.json')
    for label,sids in [('G01',['G01_004','G01_005']),('G06',['G06_004']),('G07_G08',['G07_004','G08_005'])]:
        fig,axes=plt.subplots(len(sids),4,figsize=(20,5.4*len(sids)),squeeze=False)
        for i,sid in enumerate(sids):
            raw=scene_data(sid,'Raw_F1');basis=vis.basis((-65,22));bounds=diag.square_bounds([raw['P'],raw['B'],raw['ring'].vertices],[basis])[0]
            for j,mode in enumerate(['Raw_F1','Cleaned_F1','ViewPartition_Cleaned_F2']):
                d=scene_data(sid,mode,True);condition='UNQUALIFIED_CAMERA_STRESS'if sid.startswith('G07')else case(d['primary'])['condition'];side(axes[i,j],d,sid+' / '+mode+f'\n{condition} / 实际点 N={len(d["P"]):,}',(-65,22),bounds)
            d=scene_data(sid,'ViewPartition_Cleaned_F2');order=pointset(sid,'ViewPartition_Cleaned_F2')['references'];side(axes[i,3],d,sid+' / F2 源RGB\n开放点块；间隙/孤点保留',(-65,22),bounds)
            handles=[Patch(color=PALETTE[j%4],label=c.replace(sid+'_',''))for j,c in enumerate(order)];axes[i,2].legend(handles=handles,loc='lower left',fontsize=6,framealpha=.75)
        fig.suptitle(label+'｜P8 方向负责制：Raw F1 / Cleaned F1 / Cleaned F2\n每行同视角、全Raw共同毫米窗口与相同点大小；颜色为真实来源身份，非真值；黑色实体CAD；背景DISPLAY_ONLY',fontsize=13)
        fig.tight_layout(rect=[0,.01,1,.93]);fig.subplots_adjust(hspace=.30);put(fig,'P8_selective_pointcloud/'+label+'.png')

def p9():
    angles=[(-65,22),(0,0),(125,42)]
    for label,sids in [('G01',['G01_004','G01_005']),('G06',['G06_004']),('G07_G08',['G07_004','G08_005'])]:
        ds=[scene_data(s)for s in sids];titles=['SINGLE-VIDEO RECONSTRUCTION — '+s for s in sids]
        if label=='G01':ds.append(cross_data());titles=['SINGLE-VIDEO RECONSTRUCTION — video004','SINGLE-VIDEO RECONSTRUCTION — video005','CROSS-VIDEO REGISTRATION CANDIDATE — NOT FUSED']
        raw=[scene_data(s,'Raw_F1')for s in sids];sets=[p for d in raw for p in [d['P'],d['B'],d['ring'].vertices]]
        if label=='G01':
            H=np.array(load(R/'metrics/CROSSVIDEO_GATE.json')['H_005_to_004']);sets+=[transform(raw[1]['P'],H),transform(raw[1]['B'],H)]
        bb=diag.square_bounds(sets,[vis.basis(a)for a in angles]);fig,axes=plt.subplots(3,len(ds),figsize=(7.4*len(ds),15),squeeze=False)
        for j,(d,title)in enumerate(zip(ds,titles)):
            for i,ang in enumerate(angles):side(axes[i,j],d,('主体斜视','侧视','斜后/俯视')[i]+'｜实际XYZ / mm',ang,bb[i])
            axes[0,j].set_title(title+'\n'+('双视频条件坐标；禁止当作已融合'if j==2 else case(d['primary'])['condition']),fontsize=10)
        fig.suptitle(label+'｜P9 完整局部场景：Polyp + 黑色CAD + 实际局部Background\n统一毫米尺度；全部实际来源RGB点；未补面/平滑；虚拟观察不冒充真实帧。G07为UNQUALIFIED_CAMERA_STRESS；G08为LIMITED',fontsize=13)
        fig.tight_layout(rect=[0,.01,1,.95]);put(fig,'P9_final_comparison/'+label+'.png')

def layers():
    rows=[]
    for sid in scene_ids():
        primary=pointset(sid,'Single_Cleaned')['references'][0];d=point_data(primary,'Raw');s=source(primary);allP=np.r_[d['P'],d['B']];allC=np.r_[d['C'],d['BC']];pose=d['p']['pose'];poses=[]
        for name,delta in [('REFERENCE',0),('LEFT_VIRTUAL',-1),('RIGHT_VIRTUAL',1)]:
            q=pose.copy();q[:3,3]+=delta*pose[:3,0];poses.append(dict(name=name,c2w=q))
        cfgd=dict(layer_oblique_angle_degrees=(-65,22),diagnostic_point_size=.08,diagnostic_point_alpha=1.,diagnostic_CAD_alpha=.25,diagnostic_ring_pixels=420)
        im,info=scene_image(d,d['p']['K'],pose);sc=camera_scene(d,d['p']['K'],pose)
        condition='UNQUALIFIED_CAMERA_STRESS'if sid.startswith('G07')else s['c']['condition'];figs,metadata=diag.figures(d['P'],d['C'],d['B'],d['BC'],d['ring'],sc,d['p']['K'],pose,poses,(640,360),cfgd,sid,s['c']['morphology']if'morphology'in s['c']else s['c']['group'],s['c']['ring'],condition,l5_images=(s['frame'],im))
        for name,fig in figs.items():put(fig,'local/'+sid+'/'+name)
        rows.append(dict(scene=sid,Polyp_N=len(d['P']),Background_N=len(d['B']),Polyp_XYZ=str(DENS/f'local_fields/{primary}_fields.npz'),Background_XYZ=str(INC/f'local_results/background/{primary}.npz'),coordinate_frame=sid+'_LOCAL_RING_MM',geometry_point_size=.08,RGB_display_point_size=.8,L1='Actual primary Raw P0 XYZ; F1/F2 comparison separately in P8/P9',L2='Actual primary frozen depth background XYZ, DISPLAY_ONLY',L3='L1+L2; gaps unchanged',L4='L3+known CAD',L5='source RGB display only, same primary camera',metadata=metadata,display_info=info))
    save('provenance/LAYER_DISPLAY_PARAMETERS.json',rows)

def six_cross():
    d=cross_data();a=scene_data('G01_004');b=scene_data('G01_005');H=np.array(load(R/'metrics/CROSSVIDEO_GATE.json')['H_005_to_004']);poses=[a['p']['pose'],H@b['p']['pose']];q=poses[0].copy();q[:3,3]+=2*q[:3,0];poses.append(q);P=np.r_[d['P'],d['B']];C=np.r_[d['C'],d['BC']];fig,axes=plt.subplots(2,3,figsize=(19,11));bb=diag.square_bounds([P,d['ring'].vertices],[t[:3]for t in diag.AXES.values()]);params=[]
    for j,pose in enumerate(poses):
        sc=camera_scene(d,d['p']['K'],pose);z=vis.project_camera(P,d['p']['K'],pose)[1];col=diag.colors_for_depth(z)[0]if j==2 else C
        meta=diag.points(axes[0,j],P,col,[(0,640),(0,360)],['接近004 / 条件RGB','接近005 / 候选H + RGB','第三虚拟视点 +2mm / Z'][j],K=d['p']['K'],c2w=pose,ring_scene=sc,ring_alpha=.3,point_size=.08,alpha=1);params.append(meta)
    for j,(name,base)in enumerate(diag.AXES.items()):
        sc=camera_scene(d,d['p']['K'],poses[0]);params.append(diag.points(axes[1,j],P,C,bb[j],name+'正交 / 真实源RGB / mm',basis=base[:3],labels=base[3:],ring_scene=sc,ring_alpha=.3,point_size=.08,alpha=1))
    fig.suptitle('G01｜统一尺度六方向：CROSS-VIDEO REGISTRATION CANDIDATE — NOT FUSED\n上：实际/候选近相机诊断（第三视点为虚拟，非视频帧）；下：Ring XYZ毫米正交。保留双层/冲突/散点；CAD透明辅助，不移动几何',fontsize=13);fig.tight_layout(rect=[0,.01,1,.93]);put(fig,'P9_final_comparison/G01_six_views_not_fused.png');save('provenance/CROSS_SIX_VIEW_PARAMETERS.json',dict(poses=poses,point_N=len(P),XYZ_bounds_mm=bb,panels=params,status='NOT_FUSED',only_actual_XYZ=True))

def five_panels():
    # Exact latest accepted five-panel function, only resolves Cleaned this task.
    ns=dict(globals(),source_data=lambda cid:point_data(cid,'Cleaned'))
    node=next(n for n in ast.parse((GRAZ/'code/scene_renderer.py').read_text()).body if isinstance(n,ast.FunctionDef)and n.name=='five_panel');exec(compile(ast.Module(body=[node],type_ignores=[]),str(GRAZ/'code/scene_renderer.py'),'exec'),ns)
    pairs=[]
    for c in cases():
        if not c.get('new_reference'):continue
        ts=eval_targets(sceneid(c));s=source(c['id']);t=max(ts,key=lambda t:angle(s['p']['pose'][:3,2],np.array(t['c2w'])[:3,2]));pairs.append(dict(source=c['id'],target=t,status=c['condition']+' / '+c['camera_identity'],selection='largest optical-axis gap among pre-frozen targets; RGB errors not selection input'))
    for src,dst in [('G01_004_ref08','G01_005'),('G01_005_raw00459','G01_004')]:
        edge=next(e for e in load(R/'metrics/registration_edges.json')if e['kind']=='CROSS_VIDEO');H=np.array(edge['Ring']['H_source_to_target_world']);H=H if case(src)['video']=='004' else np.linalg.inv(H);t=dict(eval_targets(dst)[0]);t.update(c2w=np.linalg.inv(H)@np.array(t['c2w']),ring_case=src);pairs.append(dict(source=src,target=t,status='CROSS_VIDEO_CANDIDATE_ONLY — NOT FUSED',selection='first A-frozen target, not image-error selected'))
    edge=next(e for e in load(R/'metrics/registration_edges.json')if e['kind']=='PHOTO'and e['B'].endswith('003'));v=views()[edge['B']];t=dict(v,id=v['id'],K=np.array(v['K']),c2w=np.array(edge['c2w_target_in_source']),ring_case=edge['source_case']);pairs.append(dict(source=edge['source_case'],target=t,status='PHOTO_CANDIDATE_ONLY — ASSUMED_K / NO METRIC CERTIFICATION',selection='preselected photo003 route from Batch B; not image-error selected'))
    freeze=R/'provenance/D_DISPLAY_PAIRS_FROZEN.json'
    if not freeze.exists():save('provenance/D_DISPLAY_PAIRS_FROZEN.json',dict(pairs=pairs,selection_scope='visual representatives only; all quantitative target results retained',GT_used=False))
    else:
        old=load(freeze);changed=[]
        for row in pairs:
            if not row['status'].startswith('CROSS_VIDEO'):continue
            prior=next(p for p in old['pairs']if p['source']==row['source']and p['target']['id']==row['target']['id'])
            if not np.array_equal(np.array(prior['target']['c2w']),np.array(row['target']['c2w'])):changed.append((prior,row))
        if changed:
            history=R/'provenance/D_DISPLAY_PAIRS_INITIAL_TRANSFORM_BINDING.json'
            if not history.exists():save(str(history.relative_to(R)),old)
            for prior,row in changed:prior['target']['c2w']=row['target']['c2w']
            old['camera_binding_correction']='Use explicit source video metadata, not substring 004 (raw00459 contains004). A/B choice and frozen SE3 unchanged; only reverse diagnostic camera wrapper corrected before publication; original preserved.'
            save(str(freeze.relative_to(R)),old)
    pairs=load(freeze)['pairs'];rows=[]
    for p in pairs:
        if p['source'].startswith('G07'):p['status']=p['status'].replace('UNQUALIFIED_STRESS','UNQUALIFIED_CAMERA_STRESS')
        t=p['target'];path=R/'figures/local/A_to_B'/(p['source']+'_to_'+t['id']+'.png');row=ns['five_panel'](p['source'],t,path,p['status'],main_title='P9 新参考/候选真实A→B完整局部场景');rows.append(row)
    both('display_A_to_B',rows)

if __name__=='__main__':
    part=sys.argv[1]if len(sys.argv)>1 else'all'
    if part in ['all','core']:p8();p9();six_cross()
    if part in ['all','layers']:layers()
    if part in ['all','ab']:five_panels()
    print('D FIGURES',part,'complete',flush=True)
