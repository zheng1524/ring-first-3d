"""Meaningful numerical, evidence-ordering, conservation, lineage checks."""
from depth_windows import *
def main():
    allow_manifest();checks=[]
    def ck(name,ok,detail):checks.append(dict(check=name,status='PASS'if ok else'FAIL',detail=clean(detail)))
    own=load(R/'provenance/CANDIDATES_FROZEN.json');cohort=rows(R/'metrics/CANDIDATE_COHORT.csv');ab=load(R/'V0_V3_ABLATION.json');pairN=0;queryN=0;errors=[];native_only=0;withheld=0;strict=0;corr_viol=0;deriv_errors=[];wrong_z_length=[]
    ck('exact17_sources_and_all5_RESERVED',set(r['source_id']for r in cohort)==set(IDS)and sum(r['role']=='RESERVED'for r in cohort)==5,dict(sources=len(cohort),RESERVED=5))
    for origin in IDS:
        c=candidates(origin);s=source(origin);X=s['P'][s['F'][c['face_id']]].mean(1)
        if not np.array_equal(X,c['XYZ']):errors.append((origin,'candidate geometry changed'))
        row=next(r for r in cohort if r['source_id']==origin)
        if row['candidate_XYZ_SHA256']!=array_hash(X)or row['candidate_original_face_ID_SHA256']!=array_hash(c['face_id']):errors.append((origin,'cohort hash mismatch'))
        if len(c['face_id'])>3584:errors.append((origin,'candidate budget'))
        for observer in scene_sources(CC[origin]['scene_id']):
            if observer==origin:continue
            z=np.load(observer_file(origin,observer));q={k:z[k]for k in z.files};pairN+=1;queryN+=len(c['face_id']);native_only+=int(q['native_only'].sum());withheld+=int((q['native_free']&~q['free3']).sum());strict+=int((q['free3']&q['strict_chain']).sum())
            if(q['free3']&q['cad']).any()or(q['native_free']&q['cad']).any():errors.append((origin,observer,'CAD counted free'))
            if(q['free3']&~(q['minimum']&q['raw_free']&q['align']&q['origin_align']&q['mask_safe']&q['target_quality']&c['own_visible'])).any():errors.append((origin,observer,'free admissibility failed'))
            if(q['free3']&q['behind']).any()or(q['free3']&q['native_only']).any():errors.append((origin,observer,'contradictory ordering/discretization'))
            if not all(np.isfinite(q[k]).all()and((q[k]>=0)&(q[k]<=1)).all()for k in ['S','O','F']):errors.append((origin,observer,'kernel nonfinite/range'))
            # Correct transformation of source axial depth perturbation into target axial Z.
            x=X[:8];_,za=vis.project_camera(x,s['K'],s['T']);ra=(x-s['T'][:3,3])/za[:,None];step=1e-3;_,z0=vis.project_camera(x,source(observer)['K'],source(observer)['T']);_,z1=vis.project_camera(x+step*ra,source(observer)['K'],source(observer)['T']);pred=step*(ra@source(observer)['T'][:3,2]);deriv_errors.append(float(abs(z1-z0-pred).max()))
        _,zz=vis.project_camera(X[:8],s['K'],s['T']);ray=X[:8]-s['T'][:3,3];unit=ray/np.linalg.norm(ray,axis=1,keepdims=True);wrong=s['T'][:3,3]+unit*zz[:,None];wrong_z_length.append(float(np.linalg.norm(wrong-X[:8],axis=1).max()))
        for stage in ['REP_OBSERVERS','ALL_OBSERVERS']:
            for v in range(4):
                r=reduced(origin,stage,v);active=[b for b in stages(CC[origin]['scene_id'])[stage]if b!=origin]
                if int(r['observer_N'])!=len(active):errors.append((origin,stage,v,'self counted or wrong observer pool'))
                if any((r[norm]-r[raw]>1e-10).any()for norm,raw in [('normS','rawS'),('normO','rawO'),('normF','rawF')]):corr_viol+=1
    ck('original_candidate_centroids_and_frozen_hashes_unchanged',not errors,errors)
    ck('76_same_video_directed_observer_pairs',pairN==76 and queryN==load(R/'provenance/CONSENSUS_RUN_STATUS.json')['total_candidate_observer_queries'],dict(pair_N=pairN,point_observer_queries=queryN))
    ck('source_axial_to_observer_axial_error_propagation',max(deriv_errors)<1e-10,dict(max_error_mm=max(deriv_errors)))
    ck('Z_depth_not_misused_as_unit_ray_length',all(x>1e-3 for x in wrong_z_length),dict(wrong_unit_ray_controls_mm=wrong_z_length))
    ck('correlation_normalization_never_amplifies_raw_vote_mass',corr_viol==0,corr_viol)
    frozenN={sid:sum(int(r['candidate_N'])for r in cohort if r['scene']==sid)for sid in scene_ids()};countsokay=all(g['candidate_N']==frozenN[sid]and sum(g['class_counts'].values())==frozenN[sid]and g['all_candidates_retained_N']==frozenN[sid]for stage in ['REP_OBSERVERS','ALL_OBSERVERS']for sid,d in ab[stage].items()for v,g in d.items())
    ck('identical_candidate_denominators_all32_stage_scene_variant_cells',countsokay,frozenN)
    ringtests=[]
    for b in IDS:
        a=next(x for x in scene_sources(CC[b]['scene_id'])if x!=b);c=candidates(a);sb=source(b);uv=np.argwhere(sb['labels']==2)[:,::-1];depth=camera(b).cast(uv)['t_hit'].numpy();ii=np.flatnonzero(np.isfinite(depth));ii=ii[np.unique(np.linspace(0,len(ii)-1,min(16,len(ii))).astype(int))];X=unproject(depth[ii]+.5,sb['T'],uv[ii],sb['K']);q=peer_evidence(a,b,X,np.broadcast_to(c['normal'][0],X.shape),np.ones(len(X),bool),origin_anchor=c['XYZ'][0],origin_align=np.full(len(X),c['origin_native_Raw_alignment'][0]));ringtests.append(dict(observer=b,test_N=len(X),CAD_occluded_N=int(q['cad'].sum()),V2_free_N=int(q['native_free'].sum()),V3_free_N=int(q['free3'].sum()),pass_test=bool(q['cad'].all()and not(q['native_free']|q['free3']).any())))
    table('metrics/REAL_RING_ORDERING_TESTS.csv',ringtests);ck('real_Ring_censored_queries_never_free_in_V2_or_V3',all(r['pass_test']for r in ringtests),dict(source_N=len(ringtests),rays=sum(r['test_N']for r in ringtests)))
    ev=rows(R/'VISIBILITY_EVIDENCE.csv');ck('all_candidates_and_unique_regions_retained',len(ev)==own['candidate_N']and all(r['geometry_retained']=='1'for r in ev),dict(candidate_N=len(ev),unique_candidate_N=sum(r['source_unique_proxy']=='1'for r in ev)))
    ck('native_only_free_never_promoted_to_V3_proxy',not any(r['free_V3_admissible_proxy']=='1'and r['native_only']=='1'for r in rows(R/'FREE_SPACE_CONFLICTS.csv')),dict(native_only_point_observer_N=native_only,all_V2_withheld_by_V3_N=withheld,strict_chain_V3_free_point_observer_N=strict))
    windows=rows(R/'metrics/RAY_WINDOWS.csv');modes=rows(R/'MULTIMODAL_DEPTH_CANDIDATES.csv');sep=[r for r in windows if r['selection']=='PREREGISTERED_05_TO_1MM'];ck('all16_windows_keep_original_and_native_modes_without_average',len(windows)==16 and all(r['origin_mode_retained']=='True'and r['native_observer_mode_retained']=='True'and r['mode_average_created']=='False'and r['mode_winner_selected']=='False'for r in windows),dict(ray_N=len(windows),mode_N=len(modes),separated_window_N=len(sep)))
    ck('real_05_to_1mm_alternatives_preserved_all4_videos',len(sep)==8 and all(.5<=float(r['origin_native_separation_mm'])<=1 for r in sep),[(r['ray_id'],r['origin_native_separation_mm'])for r in sep])
    # Correction of native-mode visibility must never alter selected windows/depths.
    old=R/'runtime/MULTIMODAL_DEPTH_CANDIDATES_INITIAL001.csv'
    if old.exists():
        before=rows(old);ck('native_mode_visibility_annotation_fix_preserves_every_mode_position',[(r['ray_id'],r['mode_source_id'],r['mode_kind'],r['axial_depth_in_observer_mm'])for r in before]==[(r['ray_id'],r['mode_source_id'],r['mode_kind'],r['axial_depth_in_observer_mm'])for r in modes],dict(initial_mode_N=len(before),final_mode_N=len(modes)))
    ck('computational_query_budgets',queryN<=1000000 and load(R/'provenance/WINDOW_STATUS.json')['curve_query_N']<=100000,dict(candidate_observer=queryN,ray_curve=load(R/'provenance/WINDOW_STATUS.json')['curve_query_N']))
    input_files={a['path']:a for r in load(R/'HERO_NATIVE_INPUT_MANIFEST.json')['sources']for a in r['assets'].values()};bad=[p for p,a in input_files.items()if sha(p)!=a['sha256']];ck('frozen_HERO_camera_CAD_input_bytes_unchanged',not bad,dict(file_N=len(input_files),mismatches=bad))
    before=load(R/'provenance/PROTECTED_START.json');after=protected_state();ck('historical_worktree_HEAD_status_existing_edits_unchanged',before==after,dict(worktrees=len(before)));save('provenance/PROTECTED_END.json',after)
    ck('three_E3B_field_source_files_byte_identical',all(sha(R/'code'/n)==sha(B/'code'/n)for n in ['hero_native_adapter.py','projective_local_field.py','mesh_local_field.py']),3)
    status=dict(status='PASS_NUMERICAL_EVIDENCE_CONTRACT'if all(c['status']=='PASS'for c in checks)else'FAIL',checks=checks,
        physical_accuracy='NOT_EVALUABLE_NO_INDEPENDENT_SURFACE_TRUTH',same_physical_surface_certified_N=0,GPU=0,new_geometry=0,raw_faces_deleted=0,raw_faces_moved=0,
        native_only_proxy_N=native_only,V2_withheld_by_V3_N=withheld,strict_chain_V3_proxy_N=strict)
    save('metrics/CONSENSUS_VALIDATION.json',status);table('metrics/CONSENSUS_VALIDATION.csv',checks);print('E3C_TESTS',sum(c['status']=='PASS'for c in checks),'/',len(checks),flush=True)
    for c in checks:
        if c['status']=='FAIL':print(c,flush=True)
    assert all(c['status']=='PASS'for c in checks),'CONSENSUS_TEST_FAILURE'
if __name__=='__main__':main()
