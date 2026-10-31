"""C1.3: existing XYZ/triangles -> legal official CPU input utilities, no model."""
from common import *
import copy, traceback

def main():
    sys.path[:0]=[str(E0/'runtime/python'),str(MAP),str(VENDOR)]
    import torch
    torch.set_num_threads(2)
    # These are official data utilities only, no model class is imported.
    from mapanything.utils.image import preprocess_inputs
    from mapanything.utils.inference import validate_input_views_for_inference, preprocess_input_views_for_inference, ALLOWED_VIEW_KEYS
    from mapanything.utils.geometry import normalize_depth_using_non_zero_pixels, apply_log_to_norm
    import open3d as o3d
    D=load(R/'provenance/INPUT_ELIGIBILITY.json');C={c['id']:c for c in D['references']};gn=legacy_geometry_namespace(D)
    cfg=conventions();pointns=dict(globals(),camera=lambda t:SameCameraScene(ring(t['ring_kind']),np.asarray(t['K']),np.asarray(t['c2w']),(640,360),str(VENDOR)),cfg=lambda:dict(CAD_tolerance_mm=.05))
    pointproj=extract(GROW/'code/geometry.py',['projection'],pointns)['projection']
    render=extract(Path('/home/liu/ring_first_3d_view_eval/experiments/TASK-VIEW-OBSERVABILITY-GT-EVAL-001/code/reprojection.py'),['render'],dict(globals(),o3d=o3d))['render']
    official_files=[MAP/'mapanything'/p for p in ['models/mapanything/model.py','utils/image.py','utils/cropping.py','utils/geometry.py','utils/inference.py']]
    save('provenance/MAP_BEFORE_TEST_FREEZE.json',dict(code=asset(Path(__file__)),common=asset(R/'code/common.py'),
         official_sources=[asset(p)for p in official_files],official_revision=git(MAP,'rev-parse','HEAD'),config=asset(R/'config/CPU_CONTRACT.json'),weights_opened=False))
    # Record source excerpts proving both API validation and actual consumption.
    proof=[]
    needles={'utils/inference.py':['ALLOWED_VIEW_KEYS','def validate_input_views_for_inference','def preprocess_input_views_for_inference','pts3d_cam = depth_z'],
             'utils/geometry.py':['def normalize_depth_using_non_zero_pixels','valid_depth_mask = depth > 0','def apply_log_to_norm'],
             'models/mapanything/model.py':['def infer(','depth_for_curr_view_input = views[view_idx]','normalize_depth_using_non_zero_pixels','depths = apply_log_to_norm','self.depth_encoder'],
             'utils/cropping.py':['interpolation=cv2.INTER_NEAREST','def camera_matrix_of_crop']}
    for rel,terms in needles.items():
        p=MAP/'mapanything'/rel;s=p.read_text().splitlines()
        for term in terms:
            for i,line in enumerate(s):
                if term in line:
                    proof.append(dict(path=str(p),SHA256=sha(p),term=term,line=i+1,excerpt='\n'.join(s[max(0,i-2):i+6])))
    save('provenance/MAP_OFFICIAL_INTERFACE_EVIDENCE.json',dict(allowed_view_keys=sorted(ALLOWED_VIEW_KEYS),proof=proof,
        raw_preprocessor='depth_z HxW numpy -> BxHxW CPU tensor',
        infer_doc_caveat='docstring BxHxWx1 differs from actual image/preprocess pair; actual BxHxW gets expanded by depth_z[...,None]',
        invalid='nonpositive must be sanitized BEFORE abs norm; NaN not legal; zero encodes missing depth',
        forward_N=0))
    # Model-free invalid-value and forbidden-field regression controls.
    zero=torch.tensor([[[[.03],[0]],[[.04],[0]]]],dtype=torch.float32)
    scaled,norm=normalize_depth_using_non_zero_pixels(zero,True);encoded=apply_log_to_norm(scaled)
    nan=zero.clone();nan[0,0,1,0]=float('nan');bad,_=normalize_depth_using_non_zero_pixels(nan,True)
    tests=[dict(test='zero_is_missing_not_depth_truth',N=4,positive_N=2,normalization_m=float(norm[0]),
           invalid_output_zero=bool((encoded[zero==0]==0).all()),status='PASS' if bool(torch.isfinite(encoded).all() and (encoded[zero==0]==0).all()) else 'FAIL'),
           dict(test='NaN_pollutes_normalization_EXPECTED_REJECT',N=4,nonfinite_output_N=int((~torch.isfinite(bad)).sum()),status='PASS' if not bool(torch.isfinite(bad).all()) else 'FAIL')]
    base=dict(img=torch.zeros(1,3,28,28),data_norm_type=['dinov2'],intrinsics=torch.eye(3)[None])
    for field in ['valid','validity','pts3d','pointcloud','ply','glb','confidence','depth_layers']:
        try:validate_input_views_for_inference([dict(base,**{field:torch.ones(1)})]);ok=False
        except ValueError:ok=True
        tests.append(dict(test='reject_unsupported_'+field,status='PASS' if ok else 'FAIL'))
    try:validate_input_views_for_inference([dict(base,ray_directions=torch.ones(1,28,28,3))]);ok=False
    except ValueError:ok=True
    tests.append(dict(test='reject_K_plus_ray_directions',status='PASS' if ok else 'FAIL'))
    try:validate_input_views_for_inference([dict(img=base['img'],data_norm_type=['dinov2'],depth_z=torch.ones(1,28,28))]);ok=False
    except ValueError:ok=True
    tests.append(dict(test='reject_depth_without_calibration',status='PASS' if ok else 'FAIL'))
    table('metrics/MAP_INPUT_NEGATIVE_TESTS.csv',tests)
    native_tests=[]
    for sid,ids in load(R/'provenance/G01_PROPOSED_INPUTS.json')['proposals'].items():
        for mode in ['M0','M1','M2','M3']:
            raw=[]
            for cid in ids:
                c=C[cid];p=np.load(c['pack']);T=p['pose'].copy();T[:3,3]/=1000
                v=dict(img=np.asarray(Image.open(c['RGB']).convert('RGB')))
                if mode!='M0':v['intrinsics']=p['K'].copy()
                if mode in ['M2','M3']:v.update(camera_poses=T,is_metric_scale=torch.tensor([True]))
                if mode=='M3':
                    depth=p['depth_mm'];v['depth_z']=np.where(np.isfinite(depth)&(depth>0),depth/1000,0).astype(np.float32)
                raw.append(v)
            vv=preprocess_inputs(raw,resize_mode='fixed_size',size=(280,154))
            validate_input_views_for_inference(vv);processed=preprocess_input_views_for_inference(vv)
            native_tests.append(dict(scene=sid,mode=mode,actual_reference_ids=ids,real_view_N=len(vv),status='LEGAL_NATIVE',
                raw_depth_chain='archived frame-aligned HERO pack; actual native chain independently audited in C0',
                processed_keys=[sorted(v)for v in processed],device='CPU',model_run_N=0))
    table('metrics/MAP_NATIVE_CPU_CONTRACT.csv',native_tests)

    def geometry(sid,kind,cid):
        p,colors,faces,uv=gn['points'](cid)
        if kind=='Raw':
            return dict(P=p,C=colors,F=faces,refs=np.full(len(p),cid),point_ids=np.arange(len(p)),face_refs=np.full(len(faces),cid),face_ids=np.arange(len(faces)),parents=[cid])
        if kind=='F3':
            out=gn['f3'](sid);z=np.load(GROW/f'local_results/glb/{sid}_Joint_sources.npz');fr=[];fi=[]
            for block in load(GROW/f'local_results/scenes/{sid}_Final.json')['blocks']:
                fr.extend([block['reference']]*len(block['face_ids']));fi.extend(block['face_ids'])
            return dict(out,refs=z['source_reference'],point_ids=z['original_point_id'],face_refs=np.array(fr),face_ids=np.array(fi),parents=out['input_refs'])
        ids=[cid] if kind=='Cleaned' else [x['id']for x in D['references'][:14]if x['scene_id']==sid]
        mode='F2' if kind=='F2' else 'Cleaned_F1';out=gn['combine'](sid,mode,ids)
        pr=[];pi=[];fr=[];fi=[]
        for ref in out['input_refs']:
            P,_,F,_=gn['points'](ref)
            keep=np.load(PART/f'local_results/pointcloud_blocks/{sid}/ViewPartition_Cleaned_F2/{ref}.npz')['accepted'] if kind=='F2' else ~np.load(C[ref]['cleaned_flags']['path'])['clean_removed']
            fid=np.flatnonzero(keep[F].all(1));pid=np.flatnonzero(keep)
            pr.extend([ref]*len(pid));pi.extend(pid);fr.extend([ref]*len(fid));fi.extend(fid)
        return dict(out,refs=np.array(pr),point_ids=np.array(pi),face_refs=np.array(fr),face_ids=np.array(fi),parents=out['input_refs'])

    records=[];examples=[];deps=[];matrix=[]
    cases=[('G01_004','G01_004_ref03'),('G01_005','G01_005_raw00057')]
    cases +=[(sid,next(c['id'] for c in D['references']if c['scene_id']==sid))for sid in ['G06_004','G08_005','G07_004']]
    for sid,cid in cases:
        c=C[cid];p=np.load(c['pack']);K=p['K'].copy();T=p['pose'].copy();sourceK=K.tobytes();sourceT=T.tobytes();frame=np.asarray(Image.open(c['RGB']).convert('RGB'))
        target=dict(K=K,c2w=T,ring_kind=c['ring']);cad=SameCameraScene(ring(c['ring']),K,T,(640,360),str(VENDOR))
        for kind in (['Raw','Cleaned','F1','F2','F3'] if sid.startswith('G01') else ['Raw','Cleaned']):
            z=geometry(sid,kind,cid);P=z['P'];F=z['F'];assert len(P)==len(z['refs']) and len(F)==len(z['face_ids'])
            uv,zz=vis.project_camera(P,K,T);good=np.isfinite(uv).all(1)&(zz>0)&(uv[:,0]>=-.5)&(uv[:,0]<639.5)&(uv[:,1]>=-.5)&(uv[:,1]<359.5)
            ii=np.flatnonzero(good);hit=cad.cast(uv[ii])['t_hit'].numpy();occ=zz[ii]>hit+.05
            occmap=np.zeros((360,640),bool);xy=np.floor(uv[ii[occ]]+.5).astype(int);occmap[xy[:,1],xy[:,0]]=True
            deps.append(dict(scene=sid,source_view=cid,geometry=kind,parents=z['parents'],
                source_RGBs=[C[x]['files']['RGB']['sha256']for x in z['parents']],
                HERO_parent_RGBs=sorted({h for x in z['parents']for h in C[x]['source_alias_hashes']}),
                new_independent_camera_N=0,same_RGB_multi_prior='MUTUALLY_EXCLUSIVE_ABLATIONS_NOT_MULTIPLE_VIEWS'))
            for mode in ['points','triangles']:
                key=sid+'_'+kind+'_'+mode
                if mode=='points':
                    out=pointproj(P,z['C'],target);depth=out['z'];valid=out['source_id']>=0;source_index=out['source_id'];tri_id=np.full(depth.shape,-1,int)
                    original_ids=np.full(depth.shape,-1,int);original_ids[valid]=z['point_ids'][source_index[valid]]
                    ref=np.full(depth.shape,'',dtype='U40');ref[valid]=z['refs'][source_index[valid]]
                    # Exact selected 3D point, not a pixel-neighbour interpolant.
                    error=abs(depth[valid]-zz[source_index[valid]])
                    bary=np.full(depth.shape+(2,),np.nan)
                else:
                    out=render(P,F,z['C'],K,T,np.eye(4),c['ring']);depth=out['z_mm'];valid=out['valid'];tri_id=np.where(valid,out['face_id'],-1).astype(np.int64)
                    bary=out['source_barycentric'];source_index=np.full(depth.shape,-1,int);original_ids=np.full(depth.shape,-1,int)
                    ref=np.full(depth.shape,'',dtype='U40');ref[valid]=z['face_refs'][tri_id[valid]];original_ids[valid]=z['face_ids'][tri_id[valid]]
                    b=bary[valid];w=np.c_[1-b.sum(1),b];XYZ=(P[F[tri_id[valid]]]*w[:,:,None]).sum(1)
                    error=abs(depth[valid]-vis.project_camera(XYZ,K,T)[1]);occmap=np.isfinite(depth)&(depth>out['known_CAD_z_mm']+.05)
                axial=np.where(valid,depth,np.nan);dm=np.where(valid,depth/1000,0).astype(np.float32)
                assert np.isfinite(dm).all() and (dm>=0).all()
                pose_m=T.copy();pose_m[:3,3]/=1000
                raw=dict(img=frame,intrinsics=K.copy(),depth_z=dm,camera_poses=pose_m.copy(),is_metric_scale=torch.tensor([True]))
                views=preprocess_inputs([raw],resize_mode='fixed_size',size=(280,154))
                validate_input_views_for_inference(views);processed=preprocess_input_views_for_inference(views)
                dep=processed[0]['depth_along_ray'];scaled,norm=normalize_depth_using_non_zero_pixels(dep,True);enc=apply_log_to_norm(scaled)
                hh,ww=views[0]['img'].shape[-2:];kp=views[0]['intrinsics'][0].numpy()
                # Replay exact official depth resize on an index image. This
                # proves each selected depth retains an original source pixel.
                index=np.arange(360*640,dtype=np.float32).reshape(360,640)+1
                idxviews=preprocess_inputs([dict(img=frame,intrinsics=K.copy(),depth_z=index)],resize_mode='fixed_size',size=(280,154))
                origin=idxviews[0]['depth_z'][0].numpy().astype(int)-1
                pp=views[0]['depth_z'][0].numpy();expected=dm.ravel()[origin]
                resize_err=float(np.max(abs(pp-expected)))
                invalid_zero=bool((pp[expected==0]==0).all());pose_ok=np.array_equal(views[0]['camera_poses'][0].numpy(),pose_m)
                source_ok=K.tobytes()==sourceK and T.tobytes()==sourceT
                status='LEGAL_DERIVED_DEPTH' if np.isfinite(enc.numpy()).all() and invalid_zero and source_ok and pose_ok and resize_err<1e-8 and (np.max(error) if len(error)else 0)<.002 and valid.any() else 'ADAPTER_INVALID'
                source_uv=np.full(depth.shape+(2,),np.nan)
                for parent in sorted(set(ref[valid])):
                    selected=valid&(ref==parent);_,_,original_faces,original_uv=gn['points'](parent)
                    if mode=='points': source_uv[selected]=original_uv[original_ids[selected]]
                    else:
                        b=bary[selected];w=np.c_[1-b.sum(1),b]
                        source_uv[selected]=(original_uv[original_faces[original_ids[selected]]]*w[:,:,None]).sum(1)
                # Source-supported XYZ is still conditional on estimated HERO.
                # Historical joint shifts and triangle interiors remain priors.
                support=np.full(depth.shape,'UNKNOWN',dtype='U40')
                support[valid]='SINGLE_VIEW_OBSERVED_SUPPORTED' if mode=='points' and kind!='F3' else 'PRIOR_ONLY'
                support[occmap&~valid]='RING_OCCLUDED'
                path=R/'local_results/depth_conditions'/f'{key}.npz';path.parent.mkdir(exist_ok=True)
                np.savez_compressed(path,axial_Z_mm=axial,depth_z_m=dm,validity=valid,source_index=source_index,
                    source_original_point_or_triangle_id=original_ids,source_reference=ref,triangle_id=tri_id,source_barycentric=bary,
                    ring_occluded=occmap,unknown=~valid,surface_origin=np.array(kind),source_K=K,source_c2w_mm=T,
                    source_original_uv=source_uv,support_evidence=support,
                    processed_depth_z_m=pp,processed_K=kp,processed_source_pixel_linear_index=origin,
                    original_point_references=z['refs'],original_point_ids=z['point_ids'],original_face_references=z['face_refs'],original_face_ids=z['face_ids'])
                records.append(dict(scene=sid,source_view=cid,geometry=kind,raster=mode,geometry_point_N=len(P),geometry_triangle_N=len(F),
                    all_pixel_N=360*640,valid_depth_N=int(valid.sum()),valid_fraction=float(valid.mean()),
                    positive_after_official_resize_N=int((pp>0).sum()),processed_pixel_N=hh*ww,
                    Ring_occluded_N=int(occmap.sum()),unknown_N=int((~valid).sum()),
                    axial_Z_error_mm=stats(error),resize_depth_max_error_m=resize_err,
                    invalid_zero_not_filled=invalid_zero,K_c2w_frozen=source_ok,pose_metric_roundtrip_error_mm=np.max(abs(pose_m[:3,3]*1000-T[:3,3])),
                    official_input_keys=sorted(views[0]),official_processed_shape=list(dep.shape),
                    status=status,output=str(path),output_SHA256=sha(path),model_run_N=0,
                    camera_qualification=c['condition'],metric_eligibility='DIAGNOSTIC_ONLY_UNQUALIFIED' if 'UNQUALIFIED'in c['condition'] else 'CONDITIONAL'))
                examples.append(dict(key=key,scene=sid,view=cid,geometry=kind,raster=mode,artifact=str(path),SHA256=sha(path),
                    parents=z['parents'],units='mm archived, m official input',invalid='zero missing, validity metadata NOT sent as native field',
                    sources=[asset(C[x]['source_points'])for x in z['parents']],K_pose_source=asset(c['camera_file'])))
                print('MAP_CONTRACT',key,status,int(valid.sum()),flush=True)
    # Preserve mutually inconsistent priors as separate layers, never fuse them.
    conflicts=[]
    for sid,cid in cases[:2]:
        layers={kind:np.load(R/'local_results/depth_conditions'/f'{sid}_{kind}_triangles.npz')for kind in ['Raw','Cleaned','F1','F2','F3']}
        for i,a in enumerate(layers):
            for b in list(layers)[i+1:]:
                za,zb=layers[a],layers[b];v=za['validity']&zb['validity'];dz=abs(za['axial_Z_mm'][v]-zb['axial_Z_mm'][v]);tau=np.maximum(.5,3*za['axial_Z_mm'][v]/min(C[cid]['K_raw'][0][0],C[cid]['K_raw'][1][1]))
                conflict=np.zeros((360,640),bool);conflict[v]=dz>tau
                np.savez_compressed(R/'local_results/depth_conditions'/f'{sid}_{a}_vs_{b}_conflict.npz',conflict=conflict,common=v,unknown=~v)
                conflicts.append(dict(scene=sid,prior_A=a,prior_B=b,common_N=int(v.sum()),conflict_N=int((dz>tau).sum()),
                    conflict_fraction=float((dz>tau).mean())if len(dz)else None,delta_mm=stats(dz),independent_camera_increment=0))
    for mode in ['M0','M1','M2','M3']:
        matrix.append(dict(family='M-native',configuration=mode,status='LEGAL_NATIVE',scope='CPU validation/static consumption only; E0 failures preserved',model_run_N=0))
    for kind in ['Raw','Cleaned','F1','F2','F3','Multiple_different_HERO_reference_views']:
        matrix.append(dict(family='M-geometry-conditioned',configuration=kind,status='LEGAL_DERIVED_DEPTH' if kind!='Multiple_different_HERO_reference_views' else 'LEGAL_NATIVE',
            scope='one depth per real RGB/source view; correlated priors disclosed',model_run_N=0,formal_M4_M5_name='NOT_ASSIGNED_BEFORE_C2'))
    for field in ['PLY/GLB','arbitrary_confidence','validity_channel','same_RGB_multiple_depth_layers','MASt3R_unverified_registered_geometry','photo_metric_camera','cross_video_fused_geometry']:
        matrix.append(dict(family='unsupported_or_unqualified',configuration=field,status='UNSUPPORTED_NATIVE_INPUT' if field in ['PLY/GLB','arbitrary_confidence','validity_channel','same_RGB_multiple_depth_layers'] else 'BLOCKED',scope='do not feed to infer',model_run_N=0))
    table('metrics/MAP_GEOMETRY_ADAPTER_CONTRACT.csv',records);table('metrics/MAP_LEGAL_INPUT_MATRIX.csv',matrix)
    table('MAP_LEGAL_INPUT_MATRIX.csv',matrix);table('metrics/MAP_PRIOR_DEPENDENCY.csv',deps);table('MAP_PRIOR_DEPENDENCY.csv',deps)
    table('metrics/MAP_PRIOR_CONFLICTS.csv',conflicts);save('provenance/MAP_SOURCE_VIEW_DEPTH_EXAMPLES.json',examples)
    # Only frozen historical M3 output; no inferred camera is adopted as input.
    hist=[];surface=np.load(E0/'local_results/map/M3/surface.npz');gauge=surface['evaluation_gauge_to_frozen_first_camera']
    ids=load(E0/'config/map_minimal.json')['input_ids']
    for j,cid in enumerate(ids):
        old=np.load(E0/f'local_results/map/M3/view{j}_official_outputs.npz');P=old['pts3d'][0].reshape(-1,3);pose=old['camera_poses'][0]
        world=(P@gauge[:3,:3].T+gauge[:3,3])*1000;labels=old['source_Mask'].reshape(-1)
        valid=np.isfinite(world).all(1)&(old['depth_z'][0,...,0].reshape(-1)>0)&(old['mask'][0,...,0].reshape(-1)>.5)&(labels==2)
        signed=cad_scene('R10').compute_signed_distance(o3d.core.Tensor(world[valid].astype(np.float32)),nthreads=2,nsamples=3).numpy()
        pred=gauge@pose;predmm=pred.copy();predmm[:3,3]*=1000;frozen=np.asarray(C[cid]['c2w_mm']);delta=np.linalg.inv(frozen)@predmm
        hist.append(dict(source=cid,status='E0_OLD_FAILURE_NOT_NEW_RUN',Ring_input_pixel_N=int((labels==2).sum()),Ring_output_valid_N=int(valid.sum()),
            CAD_distance_mm=stats(abs(signed)),output_pose_raw_m=pose,condition_pose_frozen_mm=frozen,preexisting_gauge=gauge,
            pose_translation_residual_mm=np.linalg.norm(predmm[:3,3]-frozen[:3,3]),
            pose_rotation_residual_deg=np.degrees(np.arccos(np.clip((np.trace(delta[:3,:3])-1)/2,-1,1))),
            output_pose_used_as_input=False,source_cache=asset(E0/f'local_results/map/M3/view{j}_official_outputs.npz')))
    table('metrics/E0_M3_FAILURE_RECHECK.csv',hist)
    save('metrics/MAP_GATE_STATUS.json',dict(configurations_tested_N=len(records),legal_derived_depth_N=sum(r['status']=='LEGAL_DERIVED_DEPTH'for r in records),
        native_configuration_contract_N=len(native_tests),real_views_per_native_contract=3,
        invalid_N=sum(r['status']!='LEGAL_DERIVED_DEPTH'for r in records),negative_tests_pass=all(r['status']=='PASS'for r in tests),
        C1_Map='GATE_PASS' if all(r['status']=='LEGAL_DERIVED_DEPTH'for r in records) and all(r['status']=='PASS'for r in tests) else 'ADAPTER_INVALID',
        qualification_limit='G07 CPU conversion pass is not camera qualification; correlated priors not independent observations',
        model_run_N=0,scientific_success='NOT_EVALUATED',GPU_used=False))
    save('provenance/MAP_EXECUTED_REUSE.json',REUSE)
    print('MAP_COMPLETE',len(records),'raster contracts; no model imported/forwarded',flush=True)

if __name__=='__main__':main()
