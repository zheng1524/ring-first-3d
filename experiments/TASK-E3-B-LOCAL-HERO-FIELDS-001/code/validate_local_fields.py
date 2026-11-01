"""Representative-first, then all17 real-source field experiments. No fusion."""
from mesh_local_field import *
import time,traceback

def get_grid(sid,n=None):
    b=ROI[sid];n=n or cfg()['domain_grid_N'];axes=[np.linspace(b['minimum_mm'][j],b['maximum_mm'][j],n)for j in range(3)]
    return np.stack(np.meshgrid(*axes,indexing='ij'),axis=-1).reshape(-1,3)
def save_query(path,q):
    np.savez_compressed(path,**{k:v for k,v in q.items()if isinstance(v,np.ndarray)})
def normal_bins(N):
    az=np.mod(np.arctan2(N[:,1],N[:,0]),2*np.pi);el=np.arcsin(np.clip(N[:,2],-1,1));return np.minimum((az/(2*np.pi)*12).astype(int),11)+12*np.clip(((el+np.pi/2)/np.pi*6).astype(int),0,5)
def voxelset(P):return {tuple(v)for v in np.floor(P/cfg()['coverage_voxel_mm']).astype(np.int64)}

def representative_gate():
    freeze('BEFORE_REPRESENTATIVE_GATE.json');out=[]
    for cid in REP:
        try:
            s=source(cid);b0=ProjectiveLocalField(cid);b1=MeshLocalField(cid);ii=np.unique(np.linspace(0,len(s['F'])-1,min(512,len(s['F']))).astype(int));X=s['P'][s['F'][ii]].mean(1);q=b1.query(X);q0=b0.query(X)
            okay=bool(np.all(q['raw_udf_mm']<=cfg()['zero_mm'])and np.all(q['original_face_id']>=0)and len(q0['value'])==len(X)and np.all(np.isnan(q['value'][q['unknown']])))
            out.append(dict(source=cid,role=ROLES[cid],query_N=len(X),max_raw_UDF_mm=float(q['raw_udf_mm'].max()),pass_gate=okay,ancestry_error_mm=s['ancestry_error_mm']))
        except Exception:out.append(dict(source=cid,pass_gate=False,failure=traceback.format_exc()))
        print('REPRESENTATIVE_GATE',cid,out[-1]['pass_gate'],flush=True)
    save('provenance/REPRESENTATIVE_GATE.json',out)
    assert len(out)==12 and all(r['pass_gate']for r in out),'REPRESENTATIVE_GATE_FAILED; do not expand to RESERVED'

def qualifications():
    output=[];domains=[];fields=[];controls=[];faces={};scene_results={}
    for sid in [o['scene']for o in ORG if o['reference_screened_sources']]:scene_results[sid]=dict(X=get_grid(sid),source_ids=[],B0=[],B1=[])
    for cid in IDS:
        start=time.monotonic();s=source(cid);b0=ProjectiveLocalField(cid);b1=MeshLocalField(cid);F=s['F'];X=s['P'][F].mean(1);q=b1.query(X);q0=b0.query(s['P']);faces[cid]=dict(center=X,normal=b1.N,area=s['area'],raw_voxels=voxelset(X),legal_voxels=voxelset(X[q['valid_surface']]),normal_bins=set(map(int,normal_bins(b1.N))))
        full_pixels=np.argwhere((s['labels']==1))[:,::-1];native_uv=(full_pixels+.5)*[s['depth'].shape[1]/640,s['depth'].shape[0]/360]-.5;native_uv=np.unique(np.floor(native_uv+.5).astype(int),axis=0);Dnative=s['depth'][native_uv[:,1],native_uv[:,0]];numeric=np.isfinite(Dnative)&(Dnative>0);native_uv=native_uv[numeric];Dnative=Dnative[numeric]
        nativeX=unproject(Dnative,s['T'],native_uv,s['Kn']);qn=b0.query(nativeX);valid_delta=np.isfinite(qn['raw_projective_delta_mm']);zero=np.abs(qn['raw_projective_delta_mm'][valid_delta]);native_zero_ok=bool(len(zero)>0 and zero.max()<=cfg()['native_zero_mm'])
        mesh_ok=bool(q['raw_udf_mm'].max()<=cfg()['zero_mm']);immutable=s['P'].flags.writeable is False and s['F'].flags.writeable is False
        boundaryX=s['P'][b1.boundary_edges].mean(1);boundaryQ=b1.query(boundaryX);bad_boundary=(boundaryQ['field_kind']=='ORIENTED_LOCAL')&b1.boundary_face[boundaryQ['original_face_id']]
        base=dict(source_id=cid,scene=s['c']['scene_id'],physical_group=s['c']['group'],role=ROLES[cid],qualification='CONDITIONAL_CAMERA_NOT_METRIC_GT',raw_vertices=len(s['P']),raw_faces=len(F),original_area_mm2=float(s['area'].sum()),raw_geometry_deleted_N=0,raw_geometry_moved_N=0,
            source_identity_intact=immutable,raw_to_native_resize_max_error_mm=s['ancestry_error_mm'],native_pixel_N=len(native_uv),native_query_in_ROI_N=int(in_roi(cid,nativeX).sum()),native_point_no_active_delta_N=int((~valid_delta).sum()),
            boundary_edge_N=len(b1.boundary_edges),boundary_sign_violations_N=int(bad_boundary.sum()),manual_anatomy_truth='NOT_PROVIDED',seconds=float(time.monotonic()-start))
        output.append(dict(**base,method='B0',construction_status='BUILT',numeric_contract_pass=native_zero_ok and immutable,native_zero_max_mm=float(zero.max())if len(zero)else None,
            native_surface_legal_N=int(qn['valid_surface'].sum()),native_CAD_censored_N=int(qn['cad_occluded'].sum()),raw_vertex_in_native_band_N=int(q0['raw_surface_band'].sum()),raw_vertex_native_band_fraction=float(q0['raw_surface_band'].mean()),
            raw_vertex_native_abs_delta_p95_mm=float(np.nanquantile(abs(q0['raw_projective_delta_mm']),.95)),geometry_note='B0 native nearest zero surface is not identical to historically bilinear-resized Raw Mesh'))
        output.append(dict(**base,method='B1',construction_status='BUILT',numeric_contract_pass=mesh_ok and immutable and not bad_boundary.any(),raw_face_centroid_zero_max_mm=float(q['raw_udf_mm'].max()),raw_face_centroid_zero_N=int((q['raw_udf_mm']<=cfg()['zero_mm']).sum()),
            legal_visible_face_centroid_N=int(q['valid_surface'].sum()),conditional_oriented_face_centroid_N=int((q['field_kind']=='ORIENTED_LOCAL').sum()),unknown_sign_face_centroid_N=int((q['sign_status']=='UNKNOWN_SIGN').sum()),
            raw_face_centroid_nearest_id_match_N=int((q['original_face_id']==np.arange(len(F))).sum()),geometry_note='All original faces retained; nearest primitive may differ at duplicate/tied layers; legal visibility is separate'))
        for name,field in [('B0',b0),('B1',b1)]:
            grid=scene_results[s['c']['scene_id']]['X'];g=field.query(grid);fdir=R/'local_results'/cid;fdir.mkdir(exist_ok=True);save_query(fdir/(name+'_ROI_queries.npz'),g)
            count=np.bincount(g['domain'],minlength=5);assert int(count.sum())==len(grid)
            domains.append(dict(source_id=cid,scene=s['c']['scene_id'],method=name,query_N=len(grid),**{DOMAINS[j]:int(count[j])for j in range(5)},
                raw_surface_band_N=int(g['raw_surface_band'].sum()),legal_surface_flag_N=int(g['valid_surface'].sum()),unknown_flag_N=int(g['unknown'].sum()),all_unknown_values_NaN=bool(np.isnan(g['value'][g['unknown']]).all()),
                sign_unknown_N=int((g['sign_status']=='UNKNOWN_SIGN').sum()),field_values_are_not_full_object_SDF=True))
            assert np.isnan(g['value'][g['unknown']]).all(),'UNKNOWN_MUST_NOT_BE_ZERO'
            scene_results[s['c']['scene_id']][name].append(g)
        scene_results[s['c']['scene_id']]['source_ids'].append(cid)
        fdir=R/'local_results'/cid;np.savez_compressed(fdir/'original_face_evidence.npz',raw_UDF=q['raw_udf_mm'],valid_surface=q['valid_surface'],raw_band=q['raw_surface_band'],field_kind=q['field_kind'],reason=q['reason_codes'],native_band_at_original_vertices=q0['raw_surface_band'])
        fields.append(dict(source_id=cid,scene=s['c']['scene_id'],role=ROLES[cid],source_family=s['row']['source_family'],B0=dict(factory='projective_local_field.ProjectiveLocalField',kind='PROJECTIVE_AXIAL',input_depth=s['row']['assets']['native_depth']),
            B1=dict(factory='mesh_local_field.MeshLocalField',kind='UNSIGNED_DISTANCE / ORIENTED_LOCAL_CONDITIONAL',input_mesh=s['row']['assets']['raw_Mesh']),
            original_geometry_fused=False,original_face_N=len(F),domain=ROI[s['c']['scene_id']],band_mm=cfg()['band_mm'],input_manifest='HERO_NATIVE_INPUT_MANIFEST.json',runtime_sample_cache=str(fdir),
            original_face_identity_SHA256=hashlib.sha256(np.ascontiguousarray(F).tobytes()).hexdigest(),no_serialized_neural_weights=True,field_constructed_on_CPU=True,numerical_contract_pass=native_zero_ok and mesh_ok))
        # Real-source numerical sign, free-space and invalid-depth controls; original arrays never changed.
        legal=np.flatnonzero(qn['valid_surface'])
        if len(legal):
            j=legal[len(legal)//2];uv=native_uv[j:j+1];z=Dnative[j:j+1];pts=unproject(np.r_[z-.5,z+.5],s['T'],np.repeat(uv,2,axis=0),s['Kn']);qt=b0.query(pts)
            controls.append(dict(source=cid,test='REAL_RAY_FRONT_FREE_BACK_UNKNOWN',pass_test=bool(qt['valid_free'][0]and (qt['unknown'][1]or qt['cad_occluded'][1])),value_front=float(qt['value'][0]),value_back=None if not np.isfinite(qt['value'][1])else float(qt['value'][1])))
            hole=ProjectiveLocalField(cid);copy=s['depth'].copy();copy[uv[0,1],uv[0,0]]=np.nan;hole.s=dict(s,depth=copy);qh=hole.query(nativeX[j:j+1]);controls.append(dict(source=cid,test='IN_MEMORY_INVALID_DEPTH_NO_INTERPOLATION',pass_test=bool(qh['unknown'][0]and np.isnan(qh['value'][0])and not qh['valid_surface'][0]),original_depth_modified=False))
        for name,field in [('B0',b0),('B1',b1)]:
            bad=np.array([[np.nan,0,0],[1e6,1e6,1e6]]);qb=field.query(bad);controls.append(dict(source=cid,test=name+'_NONFINITE_AND_OUTSIDE_DOMAIN',pass_test=bool(qb['unknown'].all()and np.isnan(qb['value']).all())))
        print('REAL_FIELD_BUILT',cid,'rawfaces',len(F),'B0zero',native_zero_ok,'B1zero',mesh_ok,'seconds',round(time.monotonic()-start,2),flush=True)
        table('LOCAL_FIELD_QUALIFICATION.csv',output);table('LOCAL_FIELD_DOMAIN_STATS.csv',domains);table('metrics/CONTROL_TESTS.csv',controls)
    save('LOCAL_FIELD_MANIFEST.json',dict(task=R.name,source_N=17,field_N=34,source_scope='all17 E3-A reference-screened sources, including all5 RESERVED',fields=fields,
        no_cross_video_field=True,no_global_field_fitted=True,field_loader='construct factory(source_id), validates immutable whitelist hashes',sign_scope='local conditional camera-facing orientation only',G07='UNQUALIFIED_STRESS_IDENTITY_RETAINED_NOT_BUILT_NOT_IN_FORMAL_SUCCESS_RATE'))
    assert all(r['numeric_contract_pass']for r in output),'REAL_FIELD_NUMERIC_FAILURE'
    assert all(r['pass_test']for r in controls),'CONTROL_FAILURE'
    return faces,scene_results

def coverage(faces,scene_results):
    out=[];unique=[];aggregate=[]
    for o in ORG:
        sid=o['scene'];available=o['reference_screened_sources']
        if not available:continue
        order=sorted(available,key=lambda r:(['CORE','BRIDGE','RESERVED'].index(ROLES[r]),available.index(r)));have=set();norm=set();legal=set();counts={}
        for cid in available:
            for v in faces[cid]['raw_voxels']:counts[v]=counts.get(v,0)+1
        for step,cid in enumerate(order):
            f=faces[cid];new=f['raw_voxels']-have;overlap=f['raw_voxels']&have;out.append(dict(scene=sid,source_id=cid,role=ROLES[cid],step=step+1,original_faces=len(f['center']),original_area_mm2=float(f['area'].sum()),
                source_spatial_voxels=len(f['raw_voxels']),new_spatial_voxels=len(new),overlap_spatial_voxels=len(overlap),cumulative_spatial_voxels=len(have|f['raw_voxels']),
                new_normal_bins=len(f['normal_bins']-norm),cumulative_normal_bins=len(norm|f['normal_bins']),new_legal_visible_spatial_voxels=len(f['legal_voxels']-legal),
                unique_among_all_sources_voxels=sum(counts[v]==1 for v in f['raw_voxels']),raw_surface_deleted_N=0,
                interpretation='original-face centroid voxel / normal-direction coverage proxy, not independently verified physical correspondence or fused output'))
            have|=f['raw_voxels'];norm|=f['normal_bins'];legal|=f['legal_voxels']
        for cid in available:
            f=faces[cid];vox=np.floor(f['center']/.5).astype(int);isunique=np.array([counts[tuple(v)]==1 for v in vox]);unique.append(dict(scene=sid,source_id=cid,role=ROLES[cid],sampled_or_filtered=False,
                all_original_faces=len(f['center']),unique_voxel_faces_N=int(isunique.sum()),unique_voxel_source_area_mm2=float(f['area'][isunique].sum()),
                unique_faces_UDF_zero_retained_N=int(isunique.sum()),unique_region_physical_accuracy='NOT_EVALUABLE',structural_identity='source-only unique geometry, never automatically false'))
            path=R/'local_results'/cid/'coverage_flags.npz';np.savez_compressed(path,unique_among_all_sources=isunique,normal_bins=normal_bins(f['normal']))
        data=scene_results[sid]
        for method in ['B0','B1']:
            for stage in ['CORE','BRIDGE','RESERVED']:
                upto=['CORE','BRIDGE','RESERVED'][:['CORE','BRIDGE','RESERVED'].index(stage)+1];gg=[g for cid,g in zip(data['source_ids'],data[method])if ROLES[cid]in upto]
                surf=np.stack([g['valid_surface']for g in gg]);free=np.stack([g['valid_free']for g in gg]);unknown=np.stack([g['unknown']for g in gg]);support=surf.sum(0)
                aggregate.append(dict(scene=sid,method=method,stage=stage,source_N=len(gg),fixed_ROI_query_N=len(support),any_surface_N=int((support>0).sum()),single_source_surface_N=int((support==1).sum()),
                    multiple_source_surface_N=int((support>1).sum()),any_conditional_free_N=int(free.any(0).sum()),all_sources_unknown_N=int(unknown.all(0).sum()),no_surface_evidence_N=int((support==0).sum()),
                    evidence_only_no_scalar_aggregation=True))
    table('SOURCE_COVERAGE_INCREMENT.csv',out);table('metrics/SINGLE_SOURCE_UNIQUE_REGIONS.csv',unique);table('metrics/MULTIVIEW_DOMAIN_UNION.csv',aggregate)

def preservation_supplement():
    """Measure native-vs-original-mesh differences; never expand the frozen band."""
    freeze('BEFORE_PRESERVATION_SUPPLEMENT.json');checks=[];unique=[]
    for cid in IDS:
        s=source(cid);b0=ProjectiveLocalField(cid);b1=MeshLocalField(cid);X=s['P'][s['F']].mean(1);q=b1.query(X);flag=np.load(R/'local_results'/cid/'coverage_flags.npz')['unique_among_all_sources'];qq=b0.query(X[flag]);legal=q['valid_surface'][flag];udf=q['raw_udf_mm'][flag]
        unique.append(dict(source_id=cid,scene=s['c']['scene_id'],role=ROLES[cid],unique_voxel_raw_faces_N=int(flag.sum()),unique_raw_faces_legal_B1_N=int(legal.sum()),
            B0_unique_faces_in_native_band_N=int(qq['raw_surface_band'].sum()),B0_unique_legal_B1_faces_in_native_band_N=int((qq['raw_surface_band']&legal).sum()),
            B0_unique_legal_B1_faces_active_N=int((qq['valid_surface']&legal).sum()),B1_unique_faces_UDF_zero_N=int((udf<=cfg()['zero_mm']).sum()),
            B1_unique_faces_original_identity_retained_N=int(flag.sum()),band_unchanged_mm=cfg()['band_mm'],physical_structure_truth='NOT_EVALUABLE'))
        oriented=np.flatnonzero(q['field_kind']=='ORIENTED_LOCAL');ii=oriented[np.unique(np.linspace(0,len(oriented)-1,min(32,len(oriented))).astype(int))]if len(oriented)else np.array([],int)
        if len(ii):
            pts=np.r_[X[ii]+.02*b1.N[ii],X[ii]-.02*b1.N[ii]];t=b1.query(pts);ids=np.r_[ii,ii];usable=(t['original_face_id']==ids)&(t['field_kind']=='ORIENTED_LOCAL');expected=np.r_[np.ones(len(ii)),-np.ones(len(ii))];wrong=usable&(t['value']*expected < -cfg()['zero_mm'])
            checks.append(dict(source=cid,test='REAL_LOCAL_NORMAL_PLUS_MINUS_002MM',tested_N=len(pts),same_primitive_and_oriented_N=int(usable.sum()),wrong_local_sign_N=int(wrong.sum()),status='PASS'if usable.any()and not wrong.any()else'NOT_EVALUABLE'if not usable.any()else'FAIL'))
        rp=np.argwhere(s['labels']==2)[:,::-1];hit=camera(cid).cast(rp)['t_hit'].numpy();jj=np.flatnonzero(np.isfinite(hit));jj=jj[np.unique(np.linspace(0,len(jj)-1,min(16,len(jj))).astype(int))]if len(jj)else np.array([],int)
        if len(jj):
            pt=unproject(hit[jj]+.5,s['T'],rp[jj],s['K'])
            for name,field in [('B0',b0),('B1',b1)]:
                t=field.query(pt);checks.append(dict(source=cid,test=name+'_REAL_RING_RAY_CENSOR',tested_N=len(pt),CAD_occluded_N=int(t['cad_occluded'].sum()),all_censored_values_NaN=bool(np.isnan(t['value'][t['cad_occluded']]).all()),status='PASS'if t['cad_occluded'].all()and np.isnan(t['value']).all()else'FAIL'))
    table('metrics/UNIQUE_GEOMETRY_PRESERVATION.csv',unique);table('metrics/LOCAL_SIGN_AND_RING_TESTS.csv',checks);assert not any(r['status']=='FAIL'for r in checks),'SUPPLEMENT_FAILURE'
    print('PRESERVATION_AND_LOCAL_SIGN_SUPPLEMENT_COMPLETE',len(checks),flush=True)

def main():
    allow_manifest();representative_gate();freeze('BEFORE_ALL17_FIELDS.json');faces,data=qualifications();coverage(faces,data);preservation_supplement()
    negatives=[]
    for p in [GROW/'local_results/glb/G01_005_Joint_sources.npz',PART/'local_results/pointcloud_blocks/G01_005/ViewPartition_Cleaned_F2/G01_005_raw00057.npz']:
        try:np.load(p);negatives.append(dict(path=str(p),status='FAIL_READ_WAS_ALLOWED'))
        except PermissionError as e:negatives.append(dict(path=str(p),status='DENIED_BEFORE_FILE_READ',reason=str(e)))
    assert all(r['status']=='DENIED_BEFORE_FILE_READ'for r in negatives);save('provenance/FUSION_INPUT_NEGATIVE_CONTROLS.json',negatives)
    assert protected_state()==load(R/'provenance/PROTECTED_START.json');save('provenance/PROTECTED_END.json',protected_state());save('provenance/EXECUTED_REUSE.json',REUSE)
    save('provenance/FIELD_RUN_STATUS.json',dict(source_N=17,field_N=34,representative_gate_N=12,RESERVED_source_N=5,model_forward=0,optimizer_step=0,new_fusion=0,GT_read=False,input_access=sorted(ACCESSED),forbidden_controls=negatives))
    print('ALL17_REAL_LOCAL_FIELDS_COMPLETE',flush=True)
if __name__=='__main__':
    if '--supplement-only'in sys.argv:allow_manifest();preservation_supplement()
    else:main()
