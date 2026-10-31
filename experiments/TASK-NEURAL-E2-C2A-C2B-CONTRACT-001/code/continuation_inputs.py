"""Classify retained HERO conflicts and prepare equal-depth-information inputs."""
from continuation_context import *
from opacity import sphere_interval


def main():
    gate=load(CROOT/'metrics/JOINT_WIRING_GATE.json');assert gate['status']=='PASS_ANALYTIC_CPU_WIRING_ONLY'
    sys.path[:0]=[str(E0/'runtime/python'),str(MAP)]
    import torch
    from mapanything.utils.image import preprocess_inputs
    from mapanything.utils.inference import validate_input_views_for_inference,preprocess_input_views_for_inference
    C={c['id']:c for c in registry()['references']};tests=[];conflicts=[];evidence=[];common=[];artifacts=[]
    def check(name,ok,detail=None):
        tests.append(dict(test=name,pass_=bool(ok),detail=detail))
        if not ok:
            csave('metrics/CONTINUATION_INPUT_GATE.json',dict(status='FAIL',tests=tests));raise AssertionError((name,detail))
    domain=load(BASE/'config/SDF_INITIALIZATION_CANDIDATE.json')['scenes']
    old_manifest=load(BASE/'provenance/C2B_DATA_MANIFEST.json')
    folder=R/'local_results/continuation_cpu';folder.mkdir(exist_ok=True)
    grid=np.c_[np.tile(np.arange(640),360),np.repeat(np.arange(360),640)]
    for scene,refs in selected().items():
        views=[];viewmeta=[]
        for ref in refs:
            z=np.load(baseline_asset('local_results/rays/'+ref+'.npz'));c=C[ref]
            source=asset(c['pack'],'source pack',c['files']['pack']['sha256']);check('source pack unchanged '+ref,source['hash_match'])
            p=np.load(c['pack']);r=vis.camera_rays(grid,z['K'],z['c2w_mm']);d=r[:,3:]/z['ray_length_factor'][:,None]
            # E2 ROI_center differs from network origin in some protocols. Use
            # the exact frozen domain for intersection; never derive from GT.
            dd=next(x for x in load(E1/'config/SDF_DOMAIN_CANDIDATES.json')['candidates'][scene] if x['id']=='VISIBLE_ROI_CENTER_ENVELOPE')
            entry,exit=sphere_interval(r[:,:3],d,np.array(dd['ROI_center_mm']),dd['ROI_radius_mm'])
            t=z['native_axial_Z_mm']*z['ray_length_factor'];flag=z['HERO_visibility_conflict'];n=len(t)
            category=np.full(n,'NOT_CONFLICT',dtype='U40')
            category[flag]='UNRESOLVED'
            category[flag&(t<z['ROI_start_t_mm'])]='BEFORE_ROI_ENTRY'
            behind=flag&(t>z['ROI_end_t_mm']);ring_limited=z['ring_first_t_mm']<exit
            category[behind&~ring_limited]='AFTER_ROI_EXIT'
            category[behind&ring_limited&(t<z['ring_first_t_mm'])]='RING_FRONT_MARGIN'
            category[behind&ring_limited&(t>=z['ring_first_t_mm'])]='BEHIND_FIRST_RING_HIT'
            counts={k:int((category==k).sum()) for k in np.unique(category[flag])}
            check('all HERO visibility conflicts classified '+ref,int((category=='UNRESOLVED').sum())==0,counts)
            check('positive Mask retained in every conflict '+ref,np.all(z['mask_weight'][flag]>0) and np.all(z['mask_target'][flag]==1) and np.all(z['depth_weight'][flag]==0))
            conflicts.append(dict(scene=scene,source=ref,positive_Mask_N=int((z['labels']==1).sum()),conflict_N=int(flag.sum()),
                BEFORE_ROI_ENTRY=counts.get('BEFORE_ROI_ENTRY',0),AFTER_ROI_EXIT=counts.get('AFTER_ROI_EXIT',0),
                RING_FRONT_MARGIN=counts.get('RING_FRONT_MARGIN',0),BEHIND_FIRST_RING_HIT=counts.get('BEHIND_FIRST_RING_HIT',0),
                UNRESOLVED=counts.get('UNRESOLVED',0),Mask_kept_N=int(flag.sum()),HERO_depth_rejected_N=int(flag.sum()),
                policy='qualification fixed before any prediction; no GT; do not select a winner by rejection count'))
            rel=np.load(baseline_asset('local_results/'+ref+'_depth_reliability.npz'));seen=rel['comparison_N'];bad=rel['conflict_N'];pix=rel['eligible_pixel']
            evidence.append(dict(scene=scene,source=ref,eligible_HERO_N=len(pix),single_view_no_comparison_N=int((seen==0).sum()),
                co_visible_agree_all_N=int(((seen>0)&(bad==0)).sum()),co_visible_some_conflict_N=int(((bad>0)&(bad<seen)).sum()),
                co_visible_all_compared_conflict_N=int(((seen>0)&(bad==seen)).sum()),
                source_component_N=1,dependency_weight=1/3,conflict_weight=.25,
                no_prediction_used=True,single_view_weight_remains_1=True))
            check('source evidence bins preserve full eligible denominator '+ref,sum(evidence[-1][k] for k in ['single_view_no_comparison_N','co_visible_agree_all_N','co_visible_some_conflict_N','co_visible_all_compared_conflict_N'])==len(pix))
            check('single-view observations not erased '+ref,np.all(rel['pixel_weight'][pix[seen==0]]==1))
            # Matched geometry payload: EXACT same qualified native HERO pixels
            # as SDF's fixed source eligibility, no extra Ring CAD depth pixels.
            qualified=z['depth_weight']>0;depth=np.where(qualified,z['native_axial_Z_mm']/1000,0).reshape(360,640).astype(np.float32)
            aligned=np.zeros(n,np.float32);aligned[pix]=rel['pixel_weight'][pix]
            check('matched SDF/Map HERO support exactly equal '+ref,np.array_equal(qualified,aligned>0))
            check('matched payload keeps native source metric Z '+ref,np.allclose(depth.ravel()[qualified]*1000,z['native_axial_Z_mm'][qualified],rtol=1e-7,atol=1e-5))
            check('matched payload contains no Ring CAD condition '+ref,not np.any(depth.ravel()[z['labels']==2]>0))
            path=folder/(ref+'_COMMON_HERO.npz')
            np.savez_compressed(path,depth_z_m=depth,SDF_eligibility=qualified.reshape(360,640),
                source_reliability=aligned.reshape(360,640),source_K=z['K'],source_c2w_mm=z['c2w_mm'],
                HERO_conflict_category=category.reshape(360,640))
            artifacts.append(asset(path));T=z['c2w_mm'].copy();T[:3,3]/=1000
            views.append(dict(img=np.asarray(Image.open(c['RGB']).convert('RGB')),intrinsics=z['K'].copy(),camera_poses=T,is_metric_scale=torch.tensor([True]),depth_z=depth))
            viewmeta.append(dict(source=ref,RGB=c['files']['RGB'],HERO=c['E1_actual_native'],camera=c['files']['camera_file'],
                payload=asset(path),source_qualified_depth_N=int(qualified.sum()),Mask_supplied_to_official_API=False,
                note='eligibility uses frozen Mask/ROI/CAD qualification in both arms; not segmentation-free or CAD-unaware'))
        official=preprocess_inputs(views,resize_mode='fixed_size',size=(280,154));validate_input_views_for_inference(official)
        normalized=preprocess_input_views_for_inference(official)
        check('common three-view official legal input '+scene,len(official)==len(normalized)==3)
        for i,ref in enumerate(refs):
            check('common official K/pose unchanged '+ref,np.array_equal(official[i]['camera_poses'][0].numpy(),views[i]['camera_poses']))
            check('common input has no invented fields '+ref,not any(k in official[i] for k in ['mask','Mask','valid','confidence','CAD','depth_layers']))
            check('official resized unknown depths stay zero '+ref,bool((normalized[i]['depth_along_ray'][official[i]['depth_z'][...,None]==0]==0).all()))
        common.append(dict(scene=scene,name='COMMON_QUALIFIED_HERO_GEOMETRY',source_reference_N=3,view_ids=refs,views=viewmeta,
            comparison_status='GEOMETRY_PAYLOAD_MATCHED; not a claim of identical model information use',
            SDF_RGB_role='P_INTERIOR front-hit only',Map_RGB_role='official full source image',
            pixel_resolution='source640x360; Map official resize280x154; SDF source ray samples',
            confidence_role='SDF frozen conflict weights; Map official API has no arbitrary confidence field',
            common_qualification='same existing source Mask/ROI/Ring eligibility used by BOTH; Ring CAD is not an explicit extra input here',
            best_legal_information='previous RA M0-M4 preserved unchanged, separate comparison tier',
            full_matched_information_status='MODEL_ENCODING_AND_RESOLUTION_DIFFER; qualify interpretation before scientific comparison',
            strict_holdout_N=0,official_model_forward_N=0,GPU='NOT_GRANTED'))
    check('all2763 retained HERO visibility conflicts preserved',sum(x['conflict_N'] for x in conflicts)==2763)
    check('original two-video source identity preserved',all(x['view_ids']==selected()[x['scene']] for x in common))
    ctable('metrics/HERO_CONFLICT_CATEGORIES.csv',conflicts);ctable('metrics/SOURCE_EVIDENCE_DENOMINATORS.csv',evidence)
    ctable('metrics/CONTINUATION_INPUT_TESTS.csv',tests)
    csave('provenance/COMMON_HERO_GEOMETRY_MANIFEST.json',common)
    csave('provenance/COMMON_HERO_ARTIFACTS.json',artifacts)
    csave('metrics/CONTINUATION_INPUT_GATE.json',dict(status='PASS_CPU_INPUT_CONTRACT',check_N=len(tests),tests=tests,
        classified_visibility_conflict_N=2763,matched_geometry_scene_N=2,official_neural_forward_N=0,
        weight_update_N=0,strict_holdout_N=0,GPU='NOT_GRANTED',formal_GPU_ready=False))
    print('CONTINUATION_INPUT_COMPLETE',len(tests),'checks; six source conflict ledgers and2 matched geometry profiles')


if __name__=='__main__':main()
