"""Inventory exact existing HERO assets and ancestry; no inference or remeshing."""
from common import *

def preregister():
    assert git(REPO,'rev-parse','HEAD')=='fcdcefb13c00a3c940926dd2266137847eb768b6'
    save('config/AUDIT_PROTOCOL_FROZEN.json',dict(task=R.name,main_physical_groups=['G01','G06','G08','G07'],main_scenes=scenes(),
        additional_catalog_groups=['G02','G03','G04','G05'],source_scope='all36 E1 sources + all4 additional catalog HERO; no new inference',
        camera_gate='source_camera_qualified true AND not UNQUALIFIED; group-level NORMAL/LIMITED is NOT per-source certification',
        parent_gate='record every HERO input pose state separately; even screened reference may have candidate-only parents',
        camera_bins=dict(azimuth_width_deg=10,elevation_width_deg=10),normal_bins=dict(azimuth_N=12,elevation_N=6,minimum_area_fraction=.01),
        geometric_voxel_mm=.5,pair_sample_vertices_max=2048,pair_depth_diagnostic_mm=.5,pair_depth_pixel_footprints=3,
        pair_cycle_max_px=2,normal_compatibility_cos_min=.8,physical_correspondence_requires_independent_evidence=True,
        stretch_proxy_max_edge_over_footprint=8,fragment_proxy_component_area_fraction=.01,CAD_margin_mm=.05,
        selection='preserve existing G01 triples / other screened legacy primary; add <=1 G01 bridge, <=2 other bridges by deterministic raw spatial+normal coverage; never SDF outcomes',
        source_budget_G01=4,source_budget_other=3,graph_edge_min_mutual_source_fraction=.1,
        ROI_rule='AABB of every reference-screened raw original vertex and full CAD, margin=max(2mm,0.25*CAD outer diameter); unqualified/candidate envelopes separately disclosed',
        ROI_uses_quantile_crop=False,diagnostic_slice_N=121,slice_surface_distance_mm=.25,
        true_same_surface_conflict='not inferable from depth residual alone; preserve unresolved unless independent correspondence certification',
        representative_regions=['HEAD','RING_NEAR','ABOVE_RING','BELOW_RING','SIDE','THIN_BASE_PROXY','STRETCH_PROXY','MINOR_COMPONENT_PROXY'],
        new_LocalField_implemented=False,global_fit_N=0,geometry_deformation_N=0,model_forward_N=0,GPU_training_N=0,GT_opened=False))
    if (R/'provenance/PROTECTED_START.json').exists():assert load(R/'provenance/PROTECTED_START.json')==protected_state()
    else:save('provenance/PROTECTED_START.json',protected_state())
    freeze('BEFORE_AUDIT_NUMBERS.json')
    ra=[]
    for name in ['RA_PHASE_E3_LOCAL_TO_GLOBAL_SDF_FUSION_REVIEW_v1.1.md','RA_PHASE_E3_ALGORITHM_AND_EXPERIMENT_BLUEPRINT_v1.2.md']:
        p=Path('/home/liu/下载')/name;receipts=load(R/'provenance/RA_READING_RECEIPTS.json')if(R/'provenance/RA_READING_RECEIPTS.json').exists()else{}
        completed=p.exists()and receipts.get(name,{}).get('sha256')==sha(p)
        a=dict(name=name,**asset(p),read_complete=completed,
            search_scope='Downloads, attachments, research-worktree documentation; missing chapters not inferred');a['access_status']='READ_COMPLETE'if completed else'AVAILABLE_NOT_READ'if p.exists()else'NOT_FOUND_BOUNDED_SEARCH';ra.append(a)
    save('provenance/RA_DOCUMENT_ACCESS.json',ra)

def supplemental():
    rows=[];q=readrows(EXTRA/'metrics/RESULTS.csv')
    for group in ['G02','G03','G04','G05']:
        b=EXTRA/'groups'/group;ledger=load(b/'inputs/ledger005.json');z=np.load(b/'predictions/HERO_native.npz');ref=int(z['reference']);inputs=[ref]+list(map(int,z['sources']));cam=np.load(b/'predictions/local005_camera_0.npz');v=next(x for x in q if x['id']==group+'_004')
        meshpath=b/'meshes/004/Polyp_raw_open.ply';m=trimesh.load(meshpath,process=False);rgb=ledger[ref]['RGB_path'];mask=ledger[ref]['Mask_path']
        validation=load(b/'metrics/local_validation.json')['versions'][0];refscreen=validation['per_frame'][ref]['status']=='LOCAL_GEOMETRY_SCREENED'
        rows.append(dict(record_kind='HERO_SOURCE',physical_group=group,video_id='004',source_id=group+'_004_archive_ref04',reference_frame=ledger[ref]['id'],
            morphology='Is'if group in ['G04','G05']else'Ip',Ring_type='R10',source_RGB_path=rgb,source_RGB_SHA256=sha(rgb),
            HERO_input_RGB_IDs=[group+'_'+ledger[i]['id']for i in inputs],HERO_input_RGB_SHA256s=[sha(ledger[i]['RGB_path'])for i in inputs],HERO_input_RGB_paths=[ledger[i]['RGB_path']for i in inputs],
            camera_K=cam['K'],camera_c2w=cam['c2w'][ref],camera_status='REFERENCE_SCREENED_INPUT_CHAIN_INCOMPLETE'if refscreen else'UNQUALIFIED_ARCHIVED_CAMERA',camera_coordinate_frame=group+'_004_LOCAL_RING_MM',camera_provenance=str(b/'metrics/local_validation.json'),
            camera_reference_screened=refscreen,camera_parent_status=v['HERO_input_cameras_screened'],camera_screened_frames=v['camera_screened'],
            Ring_CAD_path=str(OLD/'surface_fusion_v2/inputs/R10_ring.obj'),Ring_CAD_SHA256=sha(OLD/'surface_fusion_v2/inputs/R10_ring.obj'),Polyp_Mask_path=mask,Ring_Mask_path=mask,Mask_encoding='labels1 Polyp,2 Ring',
            native_HERO_depth_path=str(b/'predictions/HERO_native.npz'),native_HERO_depth_shape=z['depth_mm'].shape,native_depth_unit='mm / axial Z',depth_valid_fraction=float((np.isfinite(z['depth_mm'])&(z['depth_mm']>0)).mean()),
            Raw_XYZ_path=str(b/'meshes/004/Polyp_depth_points.ply'),Raw_Mesh_path=str(meshpath),original_vertices=len(m.vertices),original_faces=len(m.faces),original_surface_area_mm2=float(m.area),
            Cleaned_asset_path=None,Type2_status='NOT_AUDITED_NOT_ADMITTED',source_ancestry='native HERO; no new evidence from raw point/mesh exports',view_direction=None,view_angle_group='NOT_FORMAL_UNQUALIFIED',camera_overlap_status='NOT_EVALUABLE_CAMERA_GATE',
            independent_geometry_status='NEW_NATIVE_REFERENCE_BUT_CORRELATED_RGB_INPUTS',qualification='UNQUALIFIED',role='UNQUALIFIED',source_family='family:'+group+'_004',
            reason='supplemental screen only: incomplete input-camera screening and original UV/face ancestry not E1-certified; no promotion from numeric mesh availability',native_depth_SHA256=sha(b/'predictions/HERO_native.npz'),Raw_Mesh_SHA256=sha(meshpath)))
    return rows

def main():
    preregister();rows=[];camera_rows=[];inputs={};nodes={};edges=[]
    def node(i,**kw):nodes[i]=dict(id=i,**kw)
    def track(path,role,expected=None):
        p=Path(path);a=asset(p,role,expected);inputs[str(p)]=a;return a
    # Connected ancestry components among all36 native reference estimates.
    fam={c['id']:c['id']for c in D['references']}
    def root(a):
        while fam[a]!=a:a=fam[a]
        return a
    for c in D['references']:
        for d in D['references']:
            if c['id']<d['id']and set(c['source_alias_hashes'])&set(d['source_alias_hashes']):fam[root(d['id'])]=root(c['id'])
    for c in D['references']:
        cid=c['id'];s=source(cid);P,F,uv=s['P'],s['F'],s['uv'];native=c['E1_actual_native'];z=np.load(native['path']);depth=z['depth_mm'];family='family:'+root(cid)
        for key in ['RGB','Mask','pack','mesh','source_points','camera_file']:track(c[key],key,c['files'][key]['sha256'])
        track(native['path'],'actual native HERO',native['sha256']);track(c['cleaned_flags']['path'],'Cleaned flags',c['cleaned_flags']['sha256']);track(c['Ring_CAD']['path'],'fixed CAD',c['Ring_CAD']['sha256'])
        parents=c['HERO_input_views'];pv=[VV[v['id']]for v in parents];candidate_N=sum(bool(v.get('camera_candidate_only'))for v in pv)
        for v in parents:
            track(v['RGB'],'HERO actual input RGB',v['sha256']);node('rgb:'+v['sha256'],kind='REAL_RGB',path=v['RGB'],sha256=v['sha256']);edges.append(dict(parent='rgb:'+v['sha256'],child='hero:'+cid,relation='ACTUAL_HERO_INPUT'))
        node('hero:'+cid,kind='NATIVE_HERO_ESTIMATE',source_family=family,path=native['path'],sha256=native['sha256'],independent_physical_group=c['group'])
        for typ,path,parent in [('RawXYZ',c['source_points'],'hero:'+cid),('RawMesh',c['mesh'],'hero:'+cid),('Cleaned',c['cleaned_flags']['path'],'RawMesh:'+cid)]:
            node(typ+':'+cid,kind=typ,path=path,independent_geometry_increment=0,source_family=family);edges.append(dict(parent=parent,child=typ+':'+cid,relation='DERIVED_SAME_NATIVE_REFERENCE'))
        k=s['K'];T=s['T'];image=Image.open(c['RGB']);mesh=trimesh.load(c['mesh'],process=False);q=np.load(c['source_points']);original=q['original_faces']if'original_faces'in q else s['clean']['original_faces']
        intact=bool(np.array_equal(F,original)and len(P)==len(mesh.vertices)and np.allclose(P,mesh.vertices,atol=1e-5,rtol=0))
        back=unproject(s['depth'][uv[:,1],uv[:,0]],T,uv,k);project,Z=vis.project_camera(P,k,T)
        status='CONDITIONAL_SCREENED_REFERENCE'if eligible(c)else'UNQUALIFIED_REFERENCE_CAMERA'
        if eligible(c)and'LIMITED'in c['condition']:status='LIMITED_CONDITIONAL_SCREENED_REFERENCE'
        qualification='CONDITIONAL'if eligible(c)and intact else'UNQUALIFIED'
        row=dict(record_kind='HERO_SOURCE',physical_group=c['group'],video_id=c['video'],source_id=cid,reference_frame=c['reference'],reference_raw_frame=c.get('raw_frame'),
            source_RGB_path=c['RGB'],source_RGB_SHA256=c['files']['RGB']['sha256'],HERO_input_RGB_IDs=[v['id']for v in parents],HERO_input_RGB_SHA256s=[v['sha256']for v in parents],HERO_input_RGB_paths=[v['RGB']for v in parents],
            morphology=c['morphology'],camera_K=k,camera_c2w=T,camera_status=status,camera_reference_screened=eligible(c),camera_parent_candidate_N=candidate_N,camera_parent_N=len(parents),
            camera_parent_status=[v.get('pose_status')for v in pv],camera_coordinate_frame=c['coord_frame'],camera_provenance=c['camera_file'],camera_source_pose_status=c['pose_status'],
            Ring_type=c['ring'],Ring_CAD_path=c['Ring_CAD']['path'],Ring_CAD_SHA256=c['Ring_CAD']['sha256'],Polyp_Mask_path=c['Mask'],Ring_Mask_path=c['Mask'],Mask_encoding='labels1 Polyp,2 Ring',
            native_HERO_depth_path=native['path'],native_depth_SHA256=native['sha256'],native_HERO_depth_shape=depth.shape,native_depth_unit='mm / camera axial Z',depth_valid_fraction=float((np.isfinite(depth)&(depth>0)).mean()),
            adapted_depth_path=c['pack'],adapted_depth_shape=s['depth'].shape,adaptation='existing archived native-to-pack chain; no new resizing or depth correction',
            Raw_XYZ_path=c['source_points'],Raw_Mesh_path=c['mesh'],Raw_Mesh_SHA256=c['files']['mesh']['sha256'],original_vertices=len(P),original_faces=len(F),original_surface_area_mm2=float(s['area'].sum()),
            original_face_identity_intact=intact,original_point_identity='source array original index with exact original UV',Cleaned_asset_path=c['cleaned_flags']['path'],Type2_status='FROZEN_DELETION_FLAGS_AND_PROTECTED_RESTORATION_NOT_NEW_EVIDENCE',
            source_ancestry='hero:'+cid,source_family=family,view_direction=None,view_angle_group='TO_BE_DETERMINISTICALLY_ORGANIZED',camera_overlap_status='SAME_VIDEO_CONDITIONAL_ONLY',
            independent_geometry_status='NATIVE_REFERENCE_ESTIMATE_WITH_CORRELATED_PARENTS',qualification=qualification,role='RESERVED'if qualification=='CONDITIONAL'else'UNQUALIFIED',
            group_level_condition=c['condition'],static_UV_roundtrip_max_px=float(abs(project-uv).max()),static_unproject_max_mm=float(abs(back-P).max()),full_pipeline_independence='NOT_AVAILABLE')
        rows.append(row);camera_rows.append({k:row[k]for k in ['source_id','physical_group','video_id','camera_status','camera_reference_screened','camera_parent_candidate_N','camera_parent_N','camera_parent_status','camera_coordinate_frame','camera_provenance','static_UV_roundtrip_max_px','static_unproject_max_mm','qualification']})
    extra=supplemental();rows+=extra
    for r in extra:
        for k in ['source_RGB_path','Polyp_Mask_path','native_HERO_depth_path','Raw_XYZ_path','Raw_Mesh_path','camera_provenance','Ring_CAD_path']:track(r[k],k)
        node('hero:'+r['source_id'],kind='NATIVE_HERO_UNQUALIFIED_CAMERA',path=r['native_HERO_depth_path'],source_family=r['source_family'])
        for i,path,h in zip(r['HERO_input_RGB_IDs'],r['HERO_input_RGB_paths'],r['HERO_input_RGB_SHA256s']):track(path,'extra HERO input RGB',h);node('rgb:'+h,kind='REAL_RGB',path=path,sha256=h);edges.append(dict(parent='rgb:'+h,child='hero:'+r['source_id'],relation='ACTUAL_HERO_INPUT'))
        camera_rows.append({k:r.get(k)for k in ['source_id','physical_group','video_id','camera_status','camera_reference_screened','camera_parent_status','camera_provenance','qualification']})
    photos=load(E1/'provenance/PHOTO_QUALIFICATION.json')
    for p in photos:
        rows.append(dict(record_kind='PHOTO_ONLY',physical_group='G01',video_id='PHOTO',source_id=p['id'],source_RGB_path=p['RGB']['path'],source_RGB_SHA256=p['RGB']['sha256'],Polyp_Mask_path=p['Mask']['path'],Ring_Mask_path=p['Mask']['path'],
            camera_K=p['K_candidate'],camera_c2w=None,camera_status='METRIC_GEOMETRY_NOT_QUALIFIED',qualification='UNQUALIFIED',role='UNQUALIFIED',independent_geometry_status='APPEARANCE_ONLY_NO_METRIC_FIELD',
            camera_provenance='historical matches only; no certified K/c2w',reason=p['reason']))
        for k in ['RGB','Mask']:track(p[k]['path'],'photo appearance '+k,p[k]['sha256'])
        node('photo:'+p['id'],kind='APPEARANCE_ONLY_NOT_METRIC',path=p['RGB']['path'],camera_status='METRIC_GEOMETRY_NOT_QUALIFIED')
    derivatives=[]
    for c in D['references']:
        derivatives.append(dict(record_kind='DERIVED_ASSET',physical_group=c['group'],video_id=c['video'],source_id='Cleaned:'+c['id'],source_ancestry=['hero:'+c['id']],source_family='family:'+root(c['id']),
            Raw_Mesh_path=c['mesh'],Cleaned_asset_path=c['cleaned_flags']['path'],qualification='DERIVED_NOT_INDEPENDENT',role='DUPLICATE_DERIVED',independent_geometry_status='ZERO_NEW_NATIVE_REFERENCE'))
    for sid in scenes():
        refs=[c['id']for c in D['references']if c['scene_id']==sid]
        blocks=load(GROW/f'local_results/scenes/{sid}_Final.json')['blocks'];f3refs=sorted(set(b['reference']for b in blocks))
        for kind,parents in [('F1',refs),('F2',refs),('F3',f3refs)]:
            path=GROW/f'local_results/scenes/{sid}_Final.json'if kind=='F3'else(PART/f'local_results/pointcloud_blocks/{sid}')
            node(kind+':'+sid,kind='DERIVED_FUSION',path=str(path),independent_geometry_increment=0,original_source_ids=parents,
                geometry_moved=(kind=='F3'),not_an_independent_HERO=True)
            for cid in parents:edges.append(dict(parent='Cleaned:'+cid,child=kind+':'+sid,relation='HISTORICAL_SELECTION_OR_TRANSFORM_NOT_NEW_OBSERVATION'))
            derivatives.append(dict(record_kind='DERIVED_ASSET',physical_group=sid[:3],video_id=sid[-3:],source_id=kind+':'+sid,source_ancestry=parents,Raw_Mesh_path=str(path),
                qualification='DERIVED_NOT_INDEPENDENT',role='DUPLICATE_DERIVED',independent_geometry_status='ZERO_NEW_NATIVE_REFERENCE',geometry_moved=(kind=='F3')))
    rows+=derivatives;table('metrics/E3_SOURCE_AND_VIEW_MANIFEST.csv',rows);table('metrics/E3_CAMERA_QUALIFICATION.csv',camera_rows)
    save('provenance/E3_SOURCE_DAG.json',dict(nodes=list(nodes.values()),edges=edges,main_native_N=36,supplemental_native_N=4,Raw_Cleaned_F1_F2_F3_independent_increment=0,
        warning='Source DAG edges are ancestry, not independent votes; shared RGB parents define correlated families; G01 two videos one physical group but no certified transform'))
    save('provenance/INPUT_HASHES.json',dict(files=list(inputs.values()),scope='only directly relevant observations/code metadata; no GT/evaluation values',all_hashes_match=all(x.get('hash_match',True)for x in inputs.values())))
    save('provenance/INVENTORY_SUMMARY.json',dict(main_native_N=36,supplemental_native_N=4,main_reference_screened_N=sum(eligible(c)for c in D['references']),
        parent_all_noncandidate_N=sum(eligible(c)and all(not VV[v['id']].get('camera_candidate_only')for v in c['HERO_input_views'])for c in D['references']),
        original_faces_intact_N=sum(r.get('original_face_identity_intact',False)for r in rows),extra_qualified_Is_R5_N=0,
        selected_main_groups=4,screened_supplemental_groups=4,main_total_original_faces=sum(len(source(c['id'])['F'])for c in D['references']),
        group_labels_not_reference_qualification=True,metric_photos_N=0))
    print('E3_INVENTORY_COMPLETE',len(rows),'manifest rows;40 native HERO,36 indexed main meshes;',sum(eligible(c)for c in D['references']),'screened references')
if __name__=='__main__':main()
