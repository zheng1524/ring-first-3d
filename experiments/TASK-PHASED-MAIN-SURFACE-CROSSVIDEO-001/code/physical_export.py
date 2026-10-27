"""Low-cost tissue-base prototypes and source-aware local GLB assets."""
from evaluation import *
def D3():
    save('provenance/D3_BEFORE_COMPUTE.json',dict(**stamp([Path(__file__),R/'config.json']),ROI=cfg()['D3_base_pixel_ROIs'],plane_translation_sensitivity_mm=[-.25,.25],plane_normal_sensitivity_degrees=[-1,1],source_points_changed=False,Ring_plane_used_as_tissue_base=False));o=o3d_module();rows=[]
    for c in cases():
        s=source(c['id']);b=background(c['id']);p=s['p'];dist=cv2.distanceTransform((p['labels']!=1).astype(np.uint8),cv2.DIST_L2,5)[b['uv'][:,1],b['uv'][:,0]];head=cohorts(s['a'],p)['head_source_proxy'];P=s['P'];center=np.median(P[head],0)
        for lower,upper in cfg()['D3_base_pixel_ROIs']:
            sel=(dist>=lower)&(dist<=upper)&b['quality'];Q=b['P'][sel];row=dict(video=c['video'],reference=c['id'],ROI_pixels=[lower,upper],background_input_N=len(Q),Polyp_input_N=len(P),Ring_plane_used=False,GT_error=None)
            if len(Q)<cfg()['D3_plane_minimum_points']:rows.append(dict(**row,status='NOT_EVALUABLE_INSUFFICIENT_BASE_SUPPORT',physical_height_mm=None));continue
            o.utility.random.seed(cfg()['random_seed']);pc=o.geometry.PointCloud(o.utility.Vector3dVector(Q));plane,inliers=pc.segment_plane(distance_threshold=cfg()['D3_plane_inlier_distance_mm'],ransac_n=3,num_iterations=cfg()['D3_plane_iterations']);plane=np.array(plane,float);plane/=np.linalg.norm(plane[:3]);plane*=1 if center@plane[:3]+plane[3]>=0 else-1;d=P@plane[:3]+plane[3];fraction=len(inliers)/len(Q);height=float(np.quantile(d,.95));res=abs(Q@plane[:3]+plane[3]);sensitivity=[];anchor=np.median(Q[np.array(inliers,int)],0)
            for shift in [-.25,.25]:sensitivity.append(dict(kind='base_plane_offset_mm',value=shift,height_p95_mm=height-shift))
            for axis in ['x','y']:
                for angle in [-1,1]:n=Rotation.from_euler(axis,angle,degrees=True).apply(plane[:3]);sensitivity.append(dict(kind='base_normal_'+axis+'_degrees',value=angle,height_p95_mm=float(np.quantile((P-anchor)@n,.95))))
            reliable=fraction>=cfg()['D3_plane_minimum_inlier_fraction'];rows.append(dict(**row,status='PREDICTED_GEOMETRY_HEIGHT_PROTOTYPE'if reliable else'NOT_EVALUABLE_UNSTABLE_BASE_MODEL',plane=plane,inlier_N=len(inliers),inlier_fraction=fraction,base_residual_mm=stats(res),height_candidate_p95_mm=height,height_candidate_max_mm=float(d.max()),height_candidate_min_mm=float(d.min()),physical_height_mm=height if reliable else None,sensitivity=sensitivity,anatomical_base_independently_verified=False))
        print('D3',c['id'],flush=True)
    summary=[]
    for video in ['004','005']:
        rr=[r for r in rows if r['video']==video];vals=np.array([r['physical_height_mm']for r in rr if r['physical_height_mm']is not None]);cand=np.array([r['height_candidate_p95_mm']for r in rr if'height_candidate_p95_mm'in r]);scene=load(R/f'metrics/D0_{video}.json');main=source(scene['main_reference']);mainarea=float(main['areas'].sum());areas=[dict(reference=c['id'],original_visible_triangle_area_mm2=float(source(c['id'])['areas'].sum()),independent_true_area=None)for c in cases()if c['video']==video];summary.append(dict(video=video,planned_ROI_reference_conditions=len(rr),base_fit_usable_conditions=len(vals),height_prototype_distribution_mm=stats(vals),all_base_fit_candidate_distribution_mm=stats(cand),height_range_mm=float(np.ptp(vals))if len(vals)else None,reference_and_ROI_spread_not_GT_error=True,selected_primary_visible_triangle_area_mm2=mainarea,selected_primary_supported_area_mm2=scene['supported_primary_observed_area_mm2'],added_nonduplicate_observed_triangle_area_mm2=scene['new_nonduplicate_observed_triangle_area_mm2'],conditional_main_plus_separated_patches_area_mm2=mainarea+scene['new_nonduplicate_observed_triangle_area_mm2'],per_reference_areas=areas,true_unique_observed_area_mm2=None,clinical_true_height_mm=None,complete_surface_area_mm2=None,volume_mm3=None,interpretation='Source-triangle and plane-derived prototypes; visible support and uncertainty retained, no closed back or physical accuracy certification'))
    save('metrics/D3_height_ROI_trials.json',rows);csvsave('metrics/D3_height_ROI_trials.csv',rows);save('metrics/D3_summary.json',summary);csvsave('metrics/D3_summary.csv',summary)
def material_ring():
    m=ring(cases()[0]);m=m.copy();m.vertices=np.asarray(m.vertices)/1000;m.visual=trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(baseColorFactor=[0,0,0,255],metallicFactor=0.,roughnessFactor=.8,doubleSided=True));m.metadata.update(identity='KNOWN_CAD_NOT_RECONSTRUCTED',centerline_radius_mm=5.6,tube_radius_mm=.6);return m
def export_with_point_sources(scene,path):
    # Trimesh serializes Mesh extras, but its POINTS exporter drops metadata.
    # Postprocessing adds provenance only; POSITION/COLOR buffers stay exact.
    def sources(tree):
        for item in tree['meshes']:
            g=scene.geometry[item['name']]
            item.setdefault('extras',{}).update(clean(g.metadata))
    scene.export(path,tree_postprocessor=sources)
def add_video(scene,video,H,drop=None):
    T=np.asarray(H).copy();T[:3,3]/=1000;D0=load(R/f'metrics/D0_{video}.json');records=[]
    for c in [c for c in cases()if c['video']==video]:
        a=np.load(R/f'local_results/D0/{video}/{c["id"]}_source_exact.npz');F=a['faces'];P=a['XYZ_mm'];rgb=np.rint(a['RGB']*255).astype(np.uint8);status=a['face_status'];usedall=np.zeros(len(P),bool)
        for k in [0,1,2,3,5]:
            fid=np.flatnonzero(status==k)
            if drop is not None and c['id']in drop:fid=fid[~np.isin(fid,drop[c['id']])]
            if not len(fid):continue
            f=F[fid];used=np.unique(f);back=np.full(len(P),-1,int);back[used]=np.arange(len(used));g=trimesh.Trimesh(P[used]/1000,back[f],vertex_colors=rgb[used],process=False);g.metadata.update(video=video,reference=c['id'],source_class=D0['class_legend'][str(k)],source_original_vertex_ids=used.tolist(),source_original_face_ids=fid.tolist(),source_uv=a['source_uv'][used].tolist(),coordinate_serialized='meters; original source XYZ in millimeters',H_005_to_004_direction='005_to_004'if video=='005'else'identity for 004',source_exact_file=str(R/f'local_results/D0/{video}/{c["id"]}_source_exact.npz'));scene.add_geometry(g,node_name=f'Polyp_{video}_{c["id"]}_{D0["class_legend"][str(k)]}',geom_name=f'Polyp_{c["id"]}_{k}',transform=T);usedall[used]=True;records.append(dict(video=video,reference=c['id'],class_id=k,faces=len(fid),area_exposure_mm2=float(source(c['id'])['areas'][fid].sum())))
        unref=np.ones(len(P),bool);unref[np.unique(F)]=False
        if unref.any():g=trimesh.points.PointCloud(P[unref]/1000,colors=rgb[unref]);g.metadata.update(reference=c['id'],video=video,status='ORIGINAL_UNREFERENCED_P0_POINTS_UNKNOWN',source_original_ids=np.flatnonzero(unref).tolist(),source_uv=a['source_uv'][unref].tolist());scene.add_geometry(g,node_name=f'Polyp_{c["id"]}_unreferenced_points',transform=T)
        b=background(c['id']);sel=b['display'];g=trimesh.points.PointCloud(b['P'][sel]/1000,colors=np.rint(b['rgb'][sel]*255).astype(np.uint8));g.metadata.update(video=video,reference=c['id'],status='OBSERVED_BACKGROUND_MODEL_PREDICTED_UNCERTIFIED',source_uv=b['uv'][sel].tolist(),original_background_ids=np.flatnonzero(sel).tolist(),full_original_background=str(R/f'local_results/background/{c["id"]}.npz'));scene.add_geometry(g,node_name=f'Background_{video}_{c["id"]}',transform=T)
    return records
def export():
    gate=load(R/'metrics/D2_gate.json');decision=load(R/'metrics/D1_decision.json');display=load(R/'metrics/D1_display_candidate.json');folder=R/'local_results/GLB';folder.mkdir(parents=True,exist_ok=True);records=[]
    for video in ['004','005']:
        sc=trimesh.Scene();sc.add_geometry(material_ring(),node_name='Ring_KNOWN_CAD');contents=add_video(sc,video,np.eye(4));sc.metadata.update(task=R.name,status='SINGLE_VIDEO_COMPLETE_OPEN_MULTISOURCE_NOT_GEOMETRY_CERTIFIED',coordinate_frame=video+'_LOCAL_RING_FRAME',serialized_unit='meters',original_unit='millimeters',GT_used=False,source_contents=contents,original_source_points_preserved=True,unknown_conflict_layers_visible=True);p=folder/f'video{video}_single_video_complete_visible.glb';export_with_point_sources(sc,p);records.append(dict(file=str(p),bytes=p.stat().st_size,sha256=sha(p),video=video,status=sc.metadata['status'],geometries=len(sc.geometry),source_contents=contents))
    sc=trimesh.Scene();sc.add_geometry(material_ring(),node_name='Ring_KNOWN_CAD_video004');H=np.array(display['H_005_to_004']);contents=add_video(sc,'004',np.eye(4));contents+=add_video(sc,'005',H);status='CROSS_VIDEO_REGISTRATION_CANDIDATE_NOT_FUSED';name='video004_video005_registration_candidate.glb';newarea=None
    if gate['status']=='ELIGIBLE_ONE_CONSERVATIVE_FUSION':
        # This branch is gated; only original trusted overlapping source faces are omitted.
        H=np.array(decision['H_005_to_004']);drop={};base=geometry('004','D0_CORE')
        for c in [c for c in cases()if c['video']=='005']:
            a=np.load(R/f'local_results/D0/005/{c["id"]}_source_exact.npz');P=transform(a['XYZ_mm'],H);F=a['faces'];points=np.concatenate([P[F[:,0]],P[F[:,1]],P[F[:,2]],P[F].mean(1),(P[F[:,0]]+P[F[:,1]])/2,(P[F[:,1]]+P[F[:,2]])/2,(P[F[:,2]]+P[F[:,0]])/2]);d,n=nearest(points,base);duplicate=(d.reshape(7,len(F)).max(0)<=cfg()['duplicate_distance_mm'])&np.isin(a['face_status'],[0,5]);drop[c['id']]=np.flatnonzero(duplicate);np.savez_compressed(R/f'local_results/D0/005/{c["id"]}_D2_duplicate_face_indices.npz',original_face_ids=drop[c['id']],H_005_to_004=H)
        sc=trimesh.Scene();sc.add_geometry(material_ring(),node_name='Ring_KNOWN_CAD');contents=add_video(sc,'004',np.eye(4));contents+=add_video(sc,'005',H,drop);status='SELECTIVE_SOURCE_AWARE_FUSION_POSE_CONDITIONAL_NOT_MEASUREMENT_CERTIFIED';name='video004_video005_cross_video_fusion.glb'
    sc.metadata.update(task=R.name,status=status,H_005_to_004_mm=H.tolist(),coordinate_frame='video004 Ring local; video005 transformed candidate',serialized_unit='meters',original_unit='millimeters',source_contents=contents,D2_gate=gate,GT_used=False,no_new_triangles=True,no_hidden_back_completion=True,diagnostic_display_candidate=display['candidate']);p=folder/name;export_with_point_sources(sc,p);records.append(dict(file=str(p),bytes=p.stat().st_size,sha256=sha(p),status=status,geometries=len(sc.geometry),H_005_to_004_mm=H,source_contents=contents,new_true_unique_area_mm2=newarea));save('metrics/GLB_INDEX.json',records);csvsave('metrics/GLB_INDEX.csv',records)
    print('EXPORTED',[(Path(x['file']).name,x['bytes'],x['geometries'])for x in records],flush=True)
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['D3','export']);a=p.parse_args();D3()if a.mode=='D3'else export()
