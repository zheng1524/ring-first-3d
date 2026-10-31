"""C2a real adapter: reuse source rays, frozen CAD and qualified cached BG only."""
from context import *
from opacity import visibility_intervals,ray_semantics,sampling_partition,SEMANTICS,RA_CLASSES

def background_proxy(c,p,grid,factor):
    path=INC/f'local_results/background/{c["id"]}.npz'
    n=len(grid);depth=np.full(n,np.inf);ids=np.full(n,-1,np.int64);known=np.zeros(n,bool)
    meta=dict(source=asset(path),status='MISSING_BACKGROUND_DISABLED',not_GT=True,source_frame=c['id'])
    if not path.is_file():return depth,known,ids,meta
    with np.load(path)as z:
        required=['XYZ_mm','source_uv','quality']
        if not all(k in z for k in required):meta['status']='UNRESOLVED_NO_QUALITY_PROVENANCE';return depth,known,ids,meta
        uv=z['source_uv'].astype(int);P=z['XYZ_mm'];quality=z['quality'].astype(bool)
        xy,Z=vis.project_camera(P,p['K'],p['pose']);err=np.max(abs(xy-uv),axis=1)
        eligible=quality&np.isfinite(Z)&(Z>0)&(err<=1e-6)&(p['labels'][uv[:,1],uv[:,0]]==0)
        point_ids=np.flatnonzero(eligible);pix=uv[point_ids,1]*640+uv[point_ids,0]
        assert len(np.unique(pix))==len(pix),'BG source UV duplicated; no implicit fusion'
        depth[pix]=Z[point_ids]*factor[pix];known[pix]=True;ids[pix]=point_ids
        meta.update(status='QUALIFIED_SOURCE_SPARSE_PROXY',raw_point_N=len(P),cached_quality_N=int(quality.sum()),eligible_point_N=len(point_ids),
            projection_max_px=float(err.max()),quality_projection_max_px=float(err[quality].max()),
            source_RGB_SHA256=c['files']['RGB']['sha256'],native_HERO=c['E1_actual_native']['sha256'],
            producer_code=asset(INC/'code/assets.py'),producer_config=asset(INC/'config.json'),
            conditions='archived quality=true; source label0; finite positive Z; original exact UV; no cross-video or hole filling',
            uncertainty='HERO-derived observed geometry proxy, shared-parent error possible; no independent occluder certification')
    return depth,known,ids,meta

def main():
    synthetic=load(R/'metrics/C2A_SYNTHETIC_GATE.json');assert synthetic['mandatory_CPU_tests_passed']
    freeze('C2A_REAL_BEFORE_TEST.json',dict(phase='C2a actual camera/CAD/BG links; not yet C2b'))
    D=registry();C={c['id']:c for c in D['references']};domains=load(E1/'config/SDF_DOMAIN_CANDIDATES.json')['candidates']
    checks=[];rows=[];assets=[];folder=R/'local_results/rays';folder.mkdir(exist_ok=True)
    def check(name,ok,detail=None):
        checks.append(dict(test=name,pass_=bool(ok),detail=detail))
        if not ok:
            save('metrics/C2A_GATE.json',dict(C2a='REAL_LINK_FAIL',mandatory_CPU_tests_passed=False,checks=checks,GPU='NOT_GRANTED'));raise AssertionError(name)
    grid=np.c_[np.tile(np.arange(640),360),np.repeat(np.arange(360),640)]
    for sid,refs in selected().items():
        domain=next(q for q in domains[sid]if q['id']=='VISIBLE_ROI_CENTER_ENVELOPE')
        for cid in refs:
            c=C[cid];p=np.load(c['pack']);K=p['K'].copy();T=p['pose'].copy();r=vis.camera_rays(grid,K,T);factor=np.linalg.norm(r[:,3:],axis=1);d=r[:,3:]/factor[:,None]
            sc=SameCameraScene(ring(c['ring']),K,T,(640,360),str(VENDOR));ring_axial=sc.cast(grid)['t_hit'].numpy();ring_t=ring_axial*factor
            bg_t,bg_known,bg_id,bg_meta=background_proxy(c,p,grid,factor);native=p['depth_mm'].ravel();labels=p['labels'].ravel();target_t=native*factor
            q=visibility_intervals(r[:,:3],d,domain['ROI_center_mm'],domain['ROI_radius_mm'],ring_t,bg_t)
            sem=ray_semantics(labels,q,target_t,bg_known)
            rejected_HERO=(labels==1)&(sem['class_id']==0)&np.isfinite(native)&(native>0)&(sem['depth_weight']==0)
            ra,band=sampling_partition(labels,sem['class_id'],sem['mask_weight'],(360,640),2)
            sem['depth_weight']*=ra==0
            bg_meta.update(role='same-source observed point depth bounds reliable non-Polyp free-space only',opaque_background_mesh_certified=False,
                triangle_occluder_t_B='NOT_AVAILABLE_FOR_REAL_DATA',unknown_pixels='no holes/interpolation or cross-view surface inferred',
                foreground_never_truncated_by_source_background_point=bool(np.all(~bg_known[labels==1])))
            # The dense source-native values are merely observations/priors.
            # Only the emitted semantics/weights authorize a supervised sample.
            with np.load(c['camera_file'])as archive:
                frozenT=archive['c2w'][c['reference_index']]if archive['c2w'].ndim==3 else archive['c2w']
                exact=np.array_equal(T,frozenT)and np.array_equal(K,archive['K'])
            check('frozen actual camera '+cid,exact)
            check('Ring first hit axial/ray closed loop '+cid,np.allclose(ring_t[np.isfinite(ring_t)]/factor[np.isfinite(ring_t)],ring_axial[np.isfinite(ring_t)],atol=.002))
            check('qualified cached background provenance '+cid,bg_meta['status']=='QUALIFIED_SOURCE_SPARSE_PROXY'and bg_meta['quality_projection_max_px']<1e-6,bg_meta['eligible_point_N'])
            check('valid visible positive samples exist '+cid,int((sem['class_id']==0).sum())>0)
            check('unknown/hidden never receive depth loss '+cid,np.all(sem['depth_weight'][sem['class_id']!=0]==0)and not sem['hidden_supervised'].any())
            check('HERO depth only supervises RA P_INTERIOR '+cid,np.all(sem['depth_weight'][ra!=0]==0))
            check('RA boundary sampling class exists '+cid,int((ra==1).sum())>0)
            observed_positive=(labels==1)&q['valid']
            check('positive image Mask survives conflicting HERO '+cid,np.all(sem['mask_target'][observed_positive]==1)and np.all(sem['mask_weight'][observed_positive]==1))
            check('background point proxy never overrides observed Polyp '+cid,not bg_known[labels==1].any())
            count=np.bincount(sem['class_id'],minlength=5);reasons={x:int((sem['reason']==x).sum())for x in np.unique(sem['reason'])}
            path=folder/(cid+'.npz')
            np.savez_compressed(path,K=K,c2w_mm=T,source_linear_pixel=np.arange(len(grid),dtype=np.int32),labels=labels.astype(np.uint8),native_axial_Z_mm=native,
                ray_length_factor=factor,ring_first_t_mm=ring_t,background_first_t_mm=bg_t,background_original_point_id=bg_id,
                background_known=bg_known,ROI_start_t_mm=q['start_mm'],ROI_end_t_mm=q['end_mm'],ROI_valid=q['valid'],
                ray_class=sem['class_id'].astype(np.uint8),sampling_class=ra,boundary_band=band,
                HERO_visibility_conflict=rejected_HERO,
                mask_weight=sem['mask_weight'].astype(np.float32),mask_target=sem['mask_target'].astype(np.uint8),depth_weight=sem['depth_weight'].astype(np.float32))
            meta=dict(scene=sid,source=cid,source_camera_frame=c['coord_frame'],RGB=c['RGB'],Mask=c['Mask'],image_pixel_N=len(grid),
                class_counts=dict(zip(SEMANTICS,count.tolist())),reason_counts=reasons,positive_Mask_pixel_N=int((labels==1).sum()),
                RA_sampling_counts=dict(zip(RA_CLASSES,np.bincount(ra,minlength=5).tolist())),
                positive_Mask_unknown_N=int(((labels==1)&(sem['class_id']==4)).sum()),
                positive_Mask_retained_HERO_rejected_N=int(rejected_HERO.sum()),
                finite_depth_supervision_N=int(sem['depth_weight'].sum()),background=bg_meta,domain=domain,
                ray_artifact=asset(path),camera_source=c['files']['camera_file'],native_source=c['E1_actual_native'],independent_model_output=False)
            rows.append(meta);assets.extend([asset(c['pack']),asset(c['camera_file']),asset(bg_meta['source']['path'])])
            print('C2A_REAL',cid,dict(zip(SEMANTICS,count.tolist())),flush=True)
    save('provenance/REAL_RAY_GEOMETRY.json',rows);save('provenance/C2A_REAL_INPUTS_FROZEN.json',assets)
    table('metrics/C2A_REAL_RAY_CLASSES.csv',[dict(scene=x['scene'],source=x['source'],all_pixel_N=x['image_pixel_N'],**x['class_counts'],positive_mask_N=x['positive_Mask_pixel_N'],positive_mask_unknown_N=x['positive_Mask_unknown_N'],positive_Mask_retained_HERO_rejected_N=x['positive_Mask_retained_HERO_rejected_N'],depth_supervision_N=x['finite_depth_supervision_N'])for x in rows])
    table('metrics/C2A_REAL_LINK_TESTS.csv',checks)
    table('metrics/RA_FIVE_SAMPLING_CLASSES.csv',[dict(scene=x['scene'],source=x['source'],**x['RA_sampling_counts'])for x in rows])
    save('metrics/C2A_GATE.json',dict(C2a='CPU_CONTRACT_PASS_WITH_REAL_BACKGROUND_LIMITS',mandatory_CPU_tests_passed=True,
        synthetic_check_N=synthetic['check_N'],real_link_check_N=len(checks),real_views_N=6,C2b='CPU_DATA_CONTRACT_STAGE_NOW_PERMITTED',
        real_background='qualified cached source geometry; estimated HERO, not independently certified occluder truth',
        real_positive_conflict_N=sum(x['positive_Mask_unknown_N']for x in rows),GPU='NOT_GRANTED',model_forward_N=0,weight_update_N=0,
        positive_Mask_retained_HERO_rejected_N=sum(x['positive_Mask_retained_HERO_rejected_N']for x in rows),
        formal_GPU_science='NOT_READY; official raw-SDF/sampler wiring and source/occlusion review still required'))
    print('C2A_ALL_COMPLETE',synthetic['check_N']+len(checks),'checks; C2b may start',flush=True)

if __name__=='__main__':main()
