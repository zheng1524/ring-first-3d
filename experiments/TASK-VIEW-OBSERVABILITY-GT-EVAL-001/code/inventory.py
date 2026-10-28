"""Read-only cameras/source support. No new relative-pose estimation or fusion."""
from io_utils import *
from itertools import combinations
sys.addaudithook(guard_no_gt)
def main():
    verify_predictions();views=[];src=[];pairs=[];files=[];oldviews=load(V13/'inputs/views.json');vphotos=[x for x in oldviews if x['id'].startswith('photo')];raw=Path('/home/liu/polyp_research/smart_endoscope_20260805/raw')
    groupnames={'G01':'GP_Ip_12.0mm_closed_R10_single_refY','G06':'GP_IIa_14.0mm_closed_R10_single_refY','G07':'GP_Is_14.0mm_closed_R5_single_refY','G08':'GP_IIa_22.0mm_closed_R10_single_refY'}
    cached={}
    for c in cases():
        sid=c['group']+'_video'+c['video'];cached.setdefault(sid,[]).append(c)
    allv={}
    for sid,cc in cached.items():
        c=cc[0];cam=dict(np.load(c['camera_file']));poses=cam['c2w'];ids=cam.get('ids',np.array(['004_'+str(i).zfill(2)for i in range(len(poses))]));files.append(Path(c['camera_file']));validation=Path(c['camera_file']).parent.parent/'metrics/local_validation.json';quality={}
        if validation.exists():
            vv=load(validation);version=next(x for x in vv['versions']if x['version']==vv['primary']);quality={x['id']:x for x in version['per_frame']};files.append(validation)
        for i,(vid,pose)in enumerate(zip(ids,poses)):
            vid=str(vid)
            if c['group']=='G01':
                b=OLD/'surface_fusion_v1'if c['video']=='004'else OLD/'surface_reconstruction_v4';rgb=b/'inputs'/('real_rgb_'+str(i).zfill(3)+'.png'if c['video']=='004'else vid+'.png');mask=b/('inputs'if c['video']=='004'else'observations')/('real_labels_'+str(i).zfill(3)+'.png'if c['video']=='004'else vid+'.png')
            else:
                b=Path(c['camera_file']).parent.parent;rgb=b/'inputs'/(vid+'.png');mask=b/'observations'/(vid+'_labels.png')
            q=quality.get(vid,{});row=dict(group=c['group'],source_id=sid,view_id=vid,index=i,RGB=str(rgb),Mask=str(mask),RGB_exists=rgb.exists(),Mask_exists=mask.exists(),K=np.asarray(cam['K']).tolist(),c2w=pose.tolist(),coordinate_frame=sid+'_LOCAL_RING_MM',camera_condition=c['condition'],pose_status=q.get('status','FROZEN_MODEL_CANDIDATE_NOT_GT'),held_reprojection=q.get('held_reprojection'),camera_center_distance_to_Ring_mm=float(np.linalg.norm(pose[:3,3])),observed_Ring_pixels=int((cv2.imread(str(mask),0)==2).sum())if mask.exists()else None,observed_Polyp_pixels=int((cv2.imread(str(mask),0)==1).sum())if mask.exists()else None,frame_binding='CACHE_KEY_AND_RGB_SHA; raw004 index NOT independently exact'if sid=='G01_video004'else'FROZEN_LEDGER_FRAME_ID')
            if rgb.exists():row['RGB_SHA256']=sha(rgb);files.append(rgb)
            if mask.exists():files.append(mask)
            views.append(row);allv[(sid,vid)]=row
        for i,j in combinations(range(len(poses)),2):
            a,b=poses[[i,j]];pairs.append(dict(group=c['group'],A_source=sid,B_source=sid,A_view=str(ids[i]),B_view=str(ids[j]),coordinate_comparable=True,common_frame_status='SAME_FROZEN_LOCAL_CANDIDATE_NOT_INDEPENDENT_POSE_GT',optical_axis_angle_deg=angle(a[:3,2],b[:3,2]),baseline_mm=float(np.linalg.norm(a[:3,3]-b[:3,3])),candidate_optical_angle_deg=None,candidate_baseline_mm=None,registration_status='REGISTERED_LOCAL_CONDITIONAL',effective_matches=None,reprojection_error_px=None,common_support=None,failure_reason='UNQUALIFIED_CAMERA_STRESS'if c['condition']=='UNQUALIFIED_STRESS'else'Nominal frozen local coordinates; independent accuracy unknown'))
    # Audit all exact group-prefix sources, including photos/extra videos with no reconstructed P0.
    for g,prefix in groupnames.items():
        for path in sorted(raw.glob(prefix+'_*')):
            num=path.stem.rsplit('_',1)[-1];typ='video'if path.suffix.lower()=='.mp4'else'photo';sid=g+'_'+typ+num;cc=cached.get(sid,[]);photo=next((v for v in vphotos if v['source_id']==num),None)if g=='G01'and typ=='photo'else None;cap=cv2.VideoCapture(str(path))if typ=='video'else None;count=int(cap.get(cv2.CAP_PROP_FRAME_COUNT))if cap is not None else None;fps=cap.get(cv2.CAP_PROP_FPS)if cap is not None else None
            if cap is not None:cap.release()
            # No raw video hashing/copying: source path+size metadata; all actual cached inputs SHA stamped.
            if photo:files +=[Path(photo[k])for k in ['RGB_path','Mask_path','raw_path']]
            src.append(dict(group_id=g,source_id=sid,file_path=str(path),file_bytes=path.stat().st_size,source_type=typ,frame_or_image_id=num,raw_frame_count=count,fps=fps,usable_cached_frames=sum(x['RGB_exists']and x['Mask_exists']for x in views if x['source_id']==sid),camera_intrinsics='FROZEN_K490_CANDIDATE_NOT_CALIBRATION_GT'if cc else photo['K_status']if photo else'MISSING_UNAUDITED',camera_pose_exists=bool(cc),pose_source=cc[0]['camera_file']if cc else'V13 candidates FAILED; no formal pose'if photo else'NO_TRACEABLE_POSE_FOUND',Ring_visible=any(x['observed_Ring_pixels']for x in views if x['source_id']==sid)if cc else bool(photo and photo['Ring_descriptor']['Ring_pixels']>0)if photo else None,Ring_CAD_available=True,Polyp_visible=True if cc or photo else None,background_visible=True if cc or photo else None,existing_depth=[x['pack']for x in cc],existing_pointcloud=[x['source_points']for x in cc],existing_mesh=[x['mesh']for x in cc],Mask=photo['Mask_path']if photo else list(dict.fromkeys(x['Mask']for x in cc)),coordinate_frame=sid+'_LOCAL_RING_MM'if cc else'UNREGISTERED',reliable_link_to_other_source=False,registration_status='LOCAL_ONLY'if cc else'UNREGISTERED',failure_reason=''if cc else'NO_VERIFIED_K_OR_POSE_OR_DEPTH; matches exist but fail independent geometry'if photo else'RAW_SOURCE_ONLY; no traced frozen camera/depth/P0; not reconstructed this task'))
    # Full source-to-source graph: no unsupported physical baseline.
    candidate=load(PHASE/'metrics/D1_display_candidate.json');H=np.array(candidate['H_005_to_004']);mains={s['id']:s['main_reference']for s in load(R/'prediction_snapshot/B_scenes.json')};source_edges=[]
    oldedges=list(csv.DictReader((V13/'pairwise_edges.csv').open()));files +=[V13/'pairwise_edges.csv',V13/'inputs/views.json',V13/'metrics/photo_contribution.csv',V13/'metrics/bounded_rigid_registration.json',V13/'metrics/sparse_registration.json',V13/'metrics/sparse_photo_bridges.json',PHASE/'metrics/D1_display_candidate.json']
    for g in groupnames:
        rr=[x for x in src if x['group_id']==g]
        for a,b in combinations(rr,2):
            cross=g=='G01'and a['source_type']==b['source_type']=='video';ca=cb=None;ea=eb=None
            if cross:
                ca=np.load(case(mains['G01_004'])['pack'])['pose'];cb=H@np.load(case(mains['G01_005'])['pack'])['pose'];ea=angle(ca[:3,2],cb[:3,2]);eb=float(np.linalg.norm(ca[:3,3]-cb[:3,3]))
            def vsource(row):return row['frame_or_image_id']if row['source_type']=='video'else'photo_'+row['frame_or_image_id']
            va,vb=vsource(a),vsource(b);vidsrc={x['id']:x['source']for x in oldviews};ee=[e for e in oldedges if {vidsrc.get(e['a']),vidsrc.get(e['b'])}=={va,vb}and e['region']=='ALL']if g=='G01'else[]
            edge=dict(group=g,A_source=a['source_id'],B_source=b['source_id'],A_view=None,B_view=None,coordinate_comparable=False,common_frame_status='UNVERIFIED_SEPARATE_LOCAL_FRAMES',optical_axis_angle_deg=None,baseline_mm=None,candidate_optical_angle_deg=ea,candidate_baseline_mm=eb,registration_status='CANDIDATE'if cross else'FAILED'if ee else'UNREGISTERED',effective_matches=sum(int(e['F_inliers']or 0)for e in ee)if ee else None,matches_denominator='SUM_OF_CACHED_FRAME_PAIR_METHOD_F_INLIER_EXPOSURES; NOT UNIQUE TRACKS'if ee else None,reprojection_error_px=None,common_support=None,Ring_constraint_available=g=='G01',background_constraint_available=bool(ee),stability='CANDIDATE_ONLY_NOT_CERTIFIED'if cross else'NO_VERIFIED_RELATIVE_POSE',failure_reason='Historical independently checked transforms failed certification; Ring yaw not fixed by round contour'if g=='G01'else'No traceable common coordinate transform / geometry for additional raw sources')
            pairs.append(edge);source_edges.append(edge)
    both('source_view_inventory',src);both('camera_frame_inventory',views);both('view_pairwise_metrics',pairs);both('source_graph_edges',source_edges)
    # Freeze every executable A->B before any new image prediction/error.
    plan=[];oldpairs=load(Path('/home/liu/ring_first_3d_abs_density/experiments/TASK-PHASEC-ABS-DENSITY-REPROJ-001/provenance/P2_PAIRS_FROZEN.json'));targets=load(PREV/'provenance/TARGETS_FROZEN.json')
    for c in cases():
        if c['group']=='G01':
            q=next(x for x in oldpairs if x['A']==c['id']);ts=[dict(id=q['B'],RGB=q['B_RGB'],Mask=q['B_Mask'],K=q['B_K'],c2w=q['B_c2w'],ring_case=c['id'],role='REUSED_PRESELECTED_P2_TARGET',not_in_any_source_HERO_inputs=q['B_not_A_HERO_input']),targets[c['group']+'_'+c['video']]]
        else:ts=[targets[c['group']+'_'+c['video']]]
        for t in ts:
            if any(x['A']==c['id']and x['B']==t['id']for x in plan):continue
            plan.append(dict(pair_id=c['id']+'__to__'+t['id'],group=c['group'],A=c['id'],B=t['id'],B_target=t,H_A_to_B_world=np.eye(4),pose_status=c['condition'],selection='EXISTING_FROZEN_SELECTION_OR_P2_PAIR; no new target-error selection',executable=True,failure_reason='',whole_pipeline_independent=False))
    for av,bv in [('004','005'),('005','004')]:
        a=mains['G01_'+av];t=targets['G01_'+bv];plan.append(dict(pair_id=a+'__to__video'+bv+'_'+t['id'],group='G01',A=a,B=t['id'],B_target=t,H_A_to_B_world=np.linalg.inv(H)if av=='004'else H,pose_status='CANDIDATE_NOT_REGISTERED_NOT_FUSED',selection='Prior D1 display candidate, frozen main+selection target; no new fitting',executable=True,failure_reason='CROSS_VIDEO_TRANSFORM_UNVERIFIED',whole_pipeline_independent=False))
    for edge in source_edges:
        for a,b in [(edge['A_source'],edge['B_source']),(edge['B_source'],edge['A_source'])]:
            if edge['group']=='G01'and 'video'in a and'video'in b:continue
            plan.append(dict(pair_id=a+'__to__'+b,group=edge['group'],A=a,B=b,B_target=None,H_A_to_B_world=None,pose_status=edge['registration_status'],selection='Complete source-pair inventory',executable=False,failure_reason='NO_VERIFIED_SOURCE_POSE/DEPTH or target pose; no false projection',whole_pipeline_independent=False))
    for x in plan:
        if x['executable']:
            for k in ['RGB','Mask']:files.append(Path(x['B_target'][k]))
    save('provenance/A_TO_B_PAIRS_BEFORE_RENDER.json',stamp(files,pairs=plan,new_RGB_errors_computed=False,GT_used=False));both('a_to_b_pair_inventory',plan)
    supports=[]
    for sc in load(R/'prediction_snapshot/B_scenes.json'):
        for r in sc['source_summaries']:
            cls=r['classes'];get=lambda k:cls.get(str(k),{}).get('model_area_mm2',0)
            supports.append(dict(group_id=sc['group'],source_id=sc['group']+'_video'+sc['video'],reference_id=r['reference'],coordinate_frame=sc['group']+'_video'+sc['video']+'_LOCAL_RING_MM',independent_visible_surface=r['original_source_area_mm2'],common_support_model_area_mm2=get(4),source_only_candidate_model_area_mm2=get(5),conflict_model_area_mm2=get(2),unknown_model_area_mm2=get(1)+get(3),primary_conditional_support_area_mm2=get(0),effective_visible_area_mm2=get(0)+get(5),new_candidate_surface_area_mm2=get(5),certified_new_anatomical_area_mm2=None,evaluation_status=sc['status'],comparison_scope='WITHIN_VIDEO_ONLY; original/subdivided face exposures; duplicates are model overlap, not independently certified repeated tissue'))
    for s in src:
        if s['source_id']not in cached:supports.append(dict(group_id=s['group_id'],source_id=s['source_id'],reference_id=None,coordinate_frame='UNREGISTERED',evaluation_status='NOT_EVALUABLE',failure_reason=s['failure_reason'],certified_new_anatomical_area_mm2=None))
    both('source_surface_support',supports)
    save('provenance/OBSERVABILITY_INPUTS.json',stamp(files,GT_used=False))
    print('INVENTORY_COMPLETE sources',len(src),'frames',len(views),'pairwise',len(pairs),'AtoB executable',sum(x['executable']for x in plan),'blocked',sum(not x['executable']for x in plan))
if __name__=='__main__':main()
