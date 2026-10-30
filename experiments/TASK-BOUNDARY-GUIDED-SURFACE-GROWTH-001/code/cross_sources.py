"""Finite local cross-video patch trials and real photo-boundary diagnostics.

No global conflict percentage veto, no unverified photo metric reconstruction.
"""
from growth import *
from evaluate import export,unique_points,target_rows
from render import *
def cross_video():
    E=next(e for e in load(BASE/'metrics/registration_edges.json')if e['kind']=='CROSS_VIDEO');H45=np.array(E['Ring']['H_source_to_target_world']);results=[];models=[];image_rows=[]
    save('provenance/CROSSVIDEO_TRIAL_INPUTS_FROZEN.json',stamp([R/'local_results/scenes/G01_004_Final.json',R/'local_results/scenes/G01_005_Final.json',BASE/'metrics/registration_edges.json',Path(__file__)],GT_used=False,scope='one source-connected local trial per direction; global candidate retained, no automatic unified fusion'))
    for srcsid,dstsid,H in [('G01_005','G01_004',np.linalg.inv(H45)),('G01_004','G01_005',H45)]:
        blocks=load_scene(dstsid);foreign=load(R/'provenance/MAIN_SURFACES_SELECTED.json')['selections'][srcsid];target_primary=blocks[0]['reference'];ns=dict(globals());original_target=target_source;original_train=train_neighbor;original_motion=motion_ok
        def mapped_target(cid):
            t=original_target(cid)
            if sceneid(case(cid))==srcsid:t.update(c2w=H@np.array(t['c2w']),ring_case=target_primary)
            return t
        def mapped_training(cid):
            t=original_train(cid)
            if sceneid(case(cid))==srcsid:t.update(c2w=H@np.array(t['c2w']),ring_case=target_primary)
            return t
        ns.update(target_source=mapped_target,train_neighbor=mapped_training,motion_ok=lambda T,role:original_motion(np.array(T)@np.linalg.inv(H)if role=='NEW'else np.array(T),role))
        for node in ast.parse((R/'code/growth.py').read_text()).body:
            if isinstance(node,ast.FunctionDef)and node.name in ['joint_alignment','attempt_component','attempt_reference']:exec(compile(ast.Module(body=[node],type_ignores=[]),str(R/'code/growth.py'),'exec'),ns)
        updated,records=ns['attempt_reference'](blocks,foreign,1,True,H)
        for row in records:results.append(dict(source_scene=srcsid,target_scene=dstsid,trial_status='CROSSVIDEO_LOCAL_PATCH_CANDIDATE_NOT_FUSED',**row))
        if updated is not None:
            tag=dstsid+'_with_'+srcsid+'_local_candidate_not_fused';save('local_results/scenes/'+tag+'.json',dict(scene=dstsid,blocks=updated,foreign_frame_H=H,status='REGISTRATION_CANDIDATE_NOT_FUSED',note='local overlap criterion passed, does not certify global registration'));models+=export(dstsid,updated,tag)
            save('provenance/'+tag+'_BEFORE_IMAGE_COMPARISON.json',stamp([R/'local_results/scenes'/ (tag+'.json')],GT_used=False))
            for t in target_rows(dstsid):
                a=unique_points(blocks);b=unique_points(updated);p=projection(a['P'],a['C'],t);q=projection(b['P'],b['C'],t);image_rows.append(dict(source=srcsid,target_scene=dstsid,target=t['id'],role=t['role'],status='CANDIDATE_ONLY_NOT_FUSED',before=metric(p,t),candidate=metric(q,t),common=common_metric(p,q,t)))
        else:
            save('local_results/scenes/'+dstsid+'_from_'+srcsid+'_UNCONNECTED_CANDIDATE.json',dict(source=foreign,target_scene=dstsid,H_source_video_to_target=H,status='NO_LOCAL_PATCH_ACCEPTED; RAW_SOURCE_AND_CONTINUOUS_COMPONENTS_PRESERVED',stop_reason='NO_SUPPORTED_FRONTIER_CONNECTION_OR_GEOMETRIC_CONFLICT',candidate_component_trials=records))
        print('CROSS LOCAL',srcsid,'to',dstsid,'connected candidate',updated is not None,flush=True)
    combined=copy.deepcopy(load_scene('G01_004'));H=np.linalg.inv(H45)
    for b in copy.deepcopy(load_scene('G01_005')):b['H']=H@np.array(b['H']);b['id']='video005__'+b['id'];b['role']='UNVERIFIED_CROSS_VIDEO_BLOCK_NOT_FUSED';combined.append(b)
    save('local_results/scenes/G01_combined_registration_candidate_not_fused.json',dict(scene='G01_004',blocks=combined,H_005_to_004=H,status='REGISTRATION_CANDIDATE_NOT_FUSED',no_cross_welding=True));models+=export('G01_004',combined,'G01_004_005_boundary_growth_registration_candidate_not_fused')
    both('crossvideo_local_patch_trials',results);both('crossvideo_local_image_validation',image_rows);both('crossvideo_candidate_GLB_INDEX',models)
def photos():
    from visualize import lines,put
    rows=[];failed=[x for x in load(R/'metrics/new_HERO_sources.json')if not x['success']];nrows=4 if failed else 3;fig,axes=plt.subplots(nrows,2,figsize=(16,5*nrows))
    for i,e in enumerate(e for e in load(BASE/'metrics/registration_edges.json')if e['kind']=='PHOTO'):
        cid=e['source_case'];sid=sceneid(case(cid));blocks=load_scene(sid);fr=frontier(blocks);v=views()[e['B']];pose=np.array(e['c2w_target_in_source']);K=np.array(v['K']);a=mesh_arrays(blocks);t=dict(id=v['id'],K=K,c2w=pose,ring_case=cid);ray=raymesh(a['P'],a['F'],t);uv,z=vis.project_camera(fr['midpoints'],K,pose);positive=np.isfinite(uv).all(1)&(z>0)&(uv[:,0]>=0)&(uv[:,0]<640)&(uv[:,1]>=0)&(uv[:,1]<360);A=np.asarray(Image.open(case(cid)['RGB']).convert('RGB'));B=np.asarray(Image.open(v['RGB']).convert('RGB'));axes[i,0].imshow(A);axes[i,0].axis('off');axes[i,0].set_title(cid+' / 已有真实源帧',fontsize=11);axes[i,1].imshow(B);axes[i,1].scatter(uv[positive,0],uv[positive,1],s=2,c='#e8a233',alpha=.7);axes[i,1].axis('off');axes[i,1].set_title(v['view_id']+'｜未认证K490 + 候选位姿\n橙：当前边界的候选投影，不是真实已知三维相机',fontsize=10)
        sourceuv,sourcez=vis.project_camera(fr['midpoints'],source(cid)['p']['K'],source(cid)['p']['pose']);visible=np.isfinite(sourceuv).all(1)&(sourcez>0)&(sourceuv[:,0]>=0)&(sourceuv[:,0]<640)&(sourceuv[:,1]>=0)&(sourceuv[:,1]<360);match=np.load(BASE/f'local_results/matches/{e["id"]}_MASt3R_ROI.npz');d=cKDTree(sourceuv[visible]).query(match['p'])[0]if visible.any()else np.full(len(match['p']),np.inf);sel=match['geometric_candidate']&(match['region']=='Polyp')&(d<=16);q=match['q'][sel];xy=np.clip(np.floor(q+.5).astype(int),[0,0],[639,359]);outside=~ray['valid'][xy[:,1],xy[:,0]]if len(q)else np.zeros(0,bool);axes[i,1].scatter(q[outside,0],q[outside,1],s=8,edgecolors='lime',facecolors='none',linewidths=.7);rows.append(dict(photo=v['id'],source_scene=sid,source_reference=cid,matched_near_current_frontier_N=int(sel.sum()),matched_near_frontier_outside_candidate_surface_projection_N=int(outside.sum()),pose_status='CANDIDATE_ONLY',K_status='ASSUMED_490_NOT_CALIBRATED',metric_new_area='NOT_EVALUABLE',HERO_attempted=False,status='PHOTO_DERIVED_GROWTH_CANDIDATE_IMAGE_ONLY',stop_reason='UNCERTIFIED_INTRINSICS_AND_METRIC_POSE',green_points_mean='real MASt3R image correspondences near source frontier and outside current candidate projected mesh; not true unique surface evidence',GT_used=False))
    runtime_rows=[]
    if failed:
        for j in range(2):
            if j>=len(failed):axes[3,j].axis('off');continue
            r=failed[j];v=views()[r['reference_view']];axes[3,j].imshow(Image.open(v['RGB']));axes[3,j].axis('off');axes[3,j].set_title(v['id']+'｜只有真实输入；未生成HERO XYZ\nCUDA_RUNTIME_FAILURE，不是补片无收益或输入被判错误',fontsize=10,color='#aa3028');runtime_rows.append(dict(reference=r['reference'],source_view=v['id'],RGB=v['RGB'],RGB_sha256=sha(v['RGB']),native_depth_generated=False,XYZ_generated=False,failure_kind='CUDA_RUNTIME_UNAVAILABLE',no_raw_data_deletion=True))
    fig.suptitle('三照片实际边界互补审计｜原图 + 候选边界投影 + 真实MASt3R匹配\n精确位姿/新公制面积NOT_EVALUABLE；不伪造照片XYZ。末行是两次CUDA运行失败的真实输入，不是几何失败结果。',fontsize=13);fig.tight_layout(rect=[0,.01,1,.94]);put(fig,'Fig12_photo_boundary_candidates.png');both('photo_growth_audit',rows);both('runtime_failure_view_inventory',runtime_rows)
def strict_cross_AB():
    from visualize import grown_data
    ns=dict(globals());node=next(n for n in ast.parse((GRAZ/'code/scene_renderer.py').read_text()).body if isinstance(n,ast.FunctionDef)and n.name=='five_panel');exec(compile(ast.Module(body=[node],type_ignores=[]),str(GRAZ/'code/scene_renderer.py'),'exec'),ns);e=next(e for e in load(BASE/'metrics/registration_edges.json')if e['kind']=='CROSS_VIDEO');H45=np.array(e['Ring']['H_source_to_target_world']);rows=[]
    for srcsid,dstsid,H in [('G01_005','G01_004',np.linalg.inv(H45)),('G01_004','G01_005',H45)]:
        blocks=load_scene(srcsid);cid=blocks[0]['reference'];d=grown_data(blocks,rgb=True,background_on=True);ns['source_data']=lambda _,d=d:d;t=dict(next(target_rows(dstsid)));t.update(c2w=np.linalg.inv(H)@np.array(t['c2w']),ring_case=cid);out=R/f'figures/local/A_to_B/CROSS_{srcsid}_to_{t["id"]}_F3_CANDIDATE.png';row=ns['five_panel'](cid,t,out,'CROSS_VIDEO_CANDIDATE_ONLY — NOT FUSED',main_title=srcsid+'原生F3→另一视频真实B；全部颜色来自源视频，目标几何不参与预测');rows.append(dict(source_scene=srcsid,target_scene=dstsid,**row))
    both('crossvideo_A_to_B_display',rows)
if __name__=='__main__':cross_video();photos();strict_cross_AB()
