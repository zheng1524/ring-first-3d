from hero_tsdf_adapter import *
def main():
    assert git(REPO,'rev-parse','HEAD')=='6423b2709d1b528124ba6cc855883ba8a437e28c'
    assert not(R/'TSDF_CONFIG.json').exists(),'FROZEN_CONFIGURATION_ALREADY_EXISTS'
    save('config/PROTECTED_START.json',protected_state())
    views=load(PART/'metrics/view_distribution.json');views=views if isinstance(views,list)else views['views']
    vb={v['index']:v for v in views if v['source_id']=='G01_video004'}
    rows=[]
    for cid,c in CC.items():
        block=vb[c['reference_index']]['block'];selected=cid in G1
        reason='G0 inherited CORE reference'if cid in CORE else ('explicit r04; Ring and two real-RGB relationships supported'if cid.endswith('r04')else ('only available original HERO in uncovered '+block if cid in G1 else 'direction already covered; retained original source not selected under minimal-direction budget'))
        rows.append(dict(source_id=cid,reference_index=c['reference_index'],view_block=block,view_partition_role=vb[c['reference_index']]['role'],G0=cid in CORE,G1=selected,admission='CONDITIONAL_NOT_HIGH_CONFIDENCE'if selected else 'NOT_SELECTED_REDUNDANT_DIRECTION',reason=reason,severe_geometry_contradiction_established=False,camera_evidence='Camera Gate pilot'if cid in CORE+['G01_004_growth_r04','G01_004_new_r00']else 'inherited frozen candidate; not individually piloted',selection_uses_TSDF=False))
    table('VIEW_COVERAGE_SELECTION.csv',rows)
    assert {vb[CC[c]['reference_index']]['block']for c in G1}=={v['block']for v in vb.values()}
    sources=[];footprint=[];zmax=0
    for cid in G1:
        s=source(cid);c=s['c'];assets={}
        for key,path in dict(native_depth=c['E1_actual_native']['path'],archived_direct_depth=c['pack'],raw_XYZ=c['source_points'],raw_mesh=c['mesh'],RGB=c['RGB'],Mask=c['Mask'],camera_file=c['camera_file'],Ring_CAD=c['Ring_CAD']['path']).items():
            exp=c['E1_actual_native']['sha256']if key=='native_depth'else (c['Ring_CAD']['sha256']if key=='Ring_CAD'else next((v['sha256']for v in c['files'].values()if v['path']==path),None))
            assets[key]=checked_asset(path,exp)
        labels=cv2.resize(s['labels'],(s['depth'].shape[1],s['depth'].shape[0]),interpolation=cv2.INTER_NEAREST);v=(labels==1)&np.isfinite(s['depth'])&(s['depth']>0);d=s['depth'][v];zmax=max(zmax,float(d.max()));pix=d/min(s['Kn'][0,0],s['Kn'][1,1]);footprint.extend(pix.tolist())
        sources.append(dict(source_id=cid,assets=assets,K_native=s['Kn'],K_archived=s['K'],c2w_mm=s['T'],native_shape=s['depth'].shape,archived_shape=s['labels'].shape,native_Polyp_N=int(v.sum()),depth_mm_stats=stats(d),pixel_footprint_mm=stats(pix),native_to_raw_resize_max_mm=s['ancestry_mm'],raw_XYZ_roundtrip_max_mm=s['XYZ_roundtrip_mm'],HERO_upstream_RGB=c['HERO_input_views'],world_frame='G01_004_LOCAL_RING_MM',geometry_fused_or_adjusted=False))
    c=dict(task=R.name,parent_commit=git(REPO,'rev-parse','HEAD'),frozen_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),open3d_version=o3d.__version__,engine='official ScalableTSDFVolume RGB8 + extract_triangle_mesh',voxel_length_mm=.1,sdf_trunc_mm=.4,depth_trunc_mm=float(np.ceil((zmax+10)/10)*10),volume_unit_resolution=16,depth_sampling_stride=1,depth_scale=1.,internal_unit='m',export_unit='mm',G0=CORE,G1=G1,Single=['G01_004_ref08'],uniform_official_weights=True,
        selection_rule='G0 + task-required r04 + unique original HERO in uncovered B1 and B4; no mesh inspection',mask='native nearest categorical mask: only finite positive label1; zero otherwise; no far-depth unknown; no CAD/E3C filtering',RGB='archived RGB INTER_AREA to native',K='frozen half-pixel-preserving archived-to-native scale',CAD='black geometry for diagnostics/rendering; never integrated, never used for post-hoc deletion',ROI='inherited frame; no clipping of source or TSDF geometry',
        parameter_basis=dict(native_pixel_footprint_mm=stats(footprint),noise_proxy_mm=.25,noise_proxy_origin='E3B finite band, not calibrated sensor noise; no GT',voxel_choice='0.1 mm comparable to native pixel spacing',trunc_choice='4 voxels; larger than inherited 0.25 mm uncertainty proxy; unvalidated science parameter'),
        optional_resolution_control=dict(allowed_max=1,voxel_mm=.05,sdf_trunc_mm=.4,trigger='single-source p95 native-ray error >0.2 mm OR native valid-depth hit fraction <0.90, after adapter algebra checks pass; this would diagnose discretization, not replace primary G0/G1',run=False),
        engineering_gate=dict(raw_XYZ_mm=1e-6,native_resize_mm=2e-5,roundtrip_pixel=1e-8,metric_scale_mesh_Hausdorff_mm=.002,single_native_hit_fraction_min=.90,single_native_depth_p95_mm_max=.2,point_retention_at_0p2_mm_min=.90,scope='interface fidelity only; no anatomical accuracy claim'),
        evaluation=dict(max_faces_per_source=12000,original_face_sampling='linspace fixed original Face ID; all original face centroids for preservation metric',distance_threshold_mm=.25,depth_agreement_mm=.25,mask_pixel_stride=2,case_count=3,case_selection='source with largest CORE loss (G0), largest G1-G0 area-retention decrease, largest G1-G0 increase; deterministic ties source order',Unknown='output with no original source agreeing in finite image Mask and axial depth within 0.25 mm; no physical truth implied'),
        prohibited=dict(GT=False,GPU=0,new_inference=0,camera_updates=0,custom_weights=0,geometry_deletion=0,search=0))
    save('TSDF_CONFIG.json',c);save('HERO_TSDF_INPUT_MANIFEST.json',dict(task=R.name,sources=sources,source_count=len(sources),all_existing_source_count=len(CC),selection=asset(R/'VIEW_COVERAGE_SELECTION.csv'),upstream_audit=asset(E1/'provenance/INPUT_ELIGIBILITY.json'),view_partition=asset(PART/'metrics/view_distribution.json'),CAD=checked_asset(CAD),forbidden_inputs=['F1/F2/F3','historical adjusted/fused Mesh','E2.7','other video'],reused=REUSE))
    snapshot('BEFORE_ANY_INTEGRATION');print('FROZEN',len(sources),'sources',stats(footprint),'trunc',c['depth_trunc_mm'],flush=True)
if __name__=='__main__':main()
