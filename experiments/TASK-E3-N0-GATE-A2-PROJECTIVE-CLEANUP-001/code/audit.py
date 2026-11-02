"""Evidence contracts and preservation, with failures retained as results."""
from validate_inputs import *

def main():
    rows=[]
    def check(name,ok,detail):rows.append(dict(test=name,status='PASS' if ok else 'FAIL',detail=detail,criterion_type='INHERITED_HARD_GATE' if name=='FROZEN_3PX_GATE' else 'DIAGNOSTIC_OPEN_ISSUE_NOT_A_NEW_HARD_GATE' if name=='RESAMPLING_COMPETING_LAYERS_RESOLVED' else 'ENGINEERING_CONTRACT'))
    frozen=load(R/'config/BEFORE_CANDIDATES.json');check('PREREGISTRATION_UNCHANGED',sha(R/'config/A2_PREREGISTERED.json')==frozen['protocol']['sha256'],'no result-driven threshold revisions')
    for a in frozen['code']:
        check('FROZEN_DECISION_CODE_'+Path(a['path']).name,sha(a['path'])==a['sha256'],'decision pipeline hash frozen before candidate discovery')
    dec=read_csv(R/'PROJECTIVE_CLEANUP_DECISIONS.csv');ev=read_csv(R/'PROJECTIVE_CLEANUP_EVIDENCE.csv');sm=load(R/'CLEANUP_SUMMARY.json');geom=read_csv(R/'INCREMENTAL_GEOMETRY_VALIDATION.csv'); topology=[]; lineage=[]; P=[];uids=[];origin=[]; kept=[]
    check('THREE_DENOMINATORS',sm['original_N']==106144 and sm['baseline_N']==106098 and sm['final_N']==105875, '106144 ->106098 ->105875; historical46 + incremental223')
    check('ONE_ROUND',sm['cleanup_rounds']==1,'no threshold search or iterative erasure')
    removed=[r for r in dec if r['action']=='DERIVED_EXCLUDE']; eidx={r['candidate_id']:[] for r in dec}
    for r in ev:eidx[r['candidate_id']].append(r)
    check('EXCLUSION_PROOF',all(len({e['observer_block'] for e in eidx[d['candidate_id']] if e['negative_vote']=='True'})>=2 and not any(e['near_support_veto']=='True' or e['depth_layer_veto']=='True' for e in eidx[d['candidate_id']]) for d in removed),'each excluded point has >=2 distinct unoccluded conditional blocks, no support/layer veto')
    check('R14_NO_NEGATIVE_VOTE',not any(e['negative_vote']=='True' for e in ev if e['observer']==IDS[-1]),'unqualified observer cannot deny another source')
    check('B3_CORRELATION',all(len(json.loads(d['opposing_blocks']))==len(set(json.loads(d['opposing_blocks']))) for d in dec),'ref08 and r04 shareB3, counted once')
    check('RING_AND_LAYER_NEVER_NEGATIVE',not any(e['negative_vote']=='True' for e in ev if e['CAD_occluded']=='True' or e['target_Mask_label'] in ['1','2']),'no CAD-hidden/Ring/Polyp layer observation used as negative vote')
    check('SUPPORT_AND_LAYER_RETAINED',all(d['action']=='RETAIN' for d in dec if d['category'].startswith(('B_','D_'))),'all recognized support/competing layers retained')
    previous=[r for r in dec if r['previous_review_id']];check('PREVIOUS_9_RETAINED',len(previous)==9 and all(d['action']=='RETAIN' for d in previous),'P47-P55 never removed merely to shrink ROI')
    discover=read_csv(R/'CANDIDATE_DISCOVERY_ALL_FLAGS.csv');reviewed={(r['source'],int(r['native_id'])) for r in dec}
    check('UNREVIEWED_RETAINED',all(r['selected_for_projection']=='True' or (r['source'],int(r['native_id'])) not in {(d['source'],int(d['native_id'])) for d in removed} for r in discover),'1641 anomaly flags outside bounded review remain unchanged')
    for k,cid in enumerate(IDS):
        o=native(cid);b=baseline(cid);s=final_native(cid);d=np.load(R/'local_results/derived_inputs'/(cid+'.npz'));mask=d['incremental_excluded'];history=d['historical_excluded']
        check(cid+'_COPY_ONLY',np.array_equal(s['depth'][~mask],b['depth'][~mask]) and np.array_equal(s['valid'][~mask],b['valid'][~mask]),'all non-excluded depth/valid values bitwise unchanged')
        check(cid+'_NO_DOUBLE_EXCLUSION',not (mask&history).any() and int(history.sum())==next(r['historical_excluded_N'] for r in sm['per_source'] if r['source']==cid),'previous46 not counted or removed again')
        core_bad=[d for d in removed if d['source']==cid and d['CORE_interior_protection']=='True'];check(cid+'_PROTECTED_INTERIOR',not core_bad,'no CORE interior with own-Raw agreement removed')
        for stage,a in [('BASELINE',b),('A2',s)]:
            c=make_crop(a);n,lab,st,_=cv2.connectedComponentsWithStats(a['valid'].astype(np.uint8),8);cn,clab,cst,_=cv2.connectedComponentsWithStats(c['valid'].astype(np.uint8),8);dt,rr=ridge_proxy(c['valid'])
            topology.append(dict(source=cid,stage=stage,native_valid_N=int(a['valid'].sum()),native_component_N=n-1,native_largest_component_N=int(st[1:,4].max()),native_small_components_lt10px_N=int((st[1:,4]<10).sum()),crop_valid_N=int(c['valid'].sum()),crop_component_N=cn-1,crop_largest_component_N=int(cst[1:,4].max()),crop_small_components_lt10px_N=int((cst[1:,4]<10).sum()),output_sub3px_ridge_N=int((rr&(2*dt<3)).sum()),note='effective validity topology proxy, not anatomical truth'))
        lineage.append(dict(source=cid,original_native=next(r['original_native'] for r in LINEAGE['sources'] if r['source']==cid),baseline=next(r['derived_depth_and_valid'] for r in LINEAGE['sources'] if r['source']==cid),incremental=asset(R/'local_results/derived_inputs'/(cid+'.npz')),incremental_native_ids=np.flatnonzero(mask),original_Mask_camera_CAD_modified=False))
        P.append(o['X']);uids.append(o['native_id']);origin.append(np.full(len(o['X']),k,np.uint8));kept.append(s['valid'].ravel()[o['native_id']])
    np.savez_compressed(R/'local_results/ALL_ORIGINAL_IDENTITIES.npz',source_index=np.concatenate(origin),native_id=np.concatenate(uids),original_X_mm=np.concatenate(P),final_valid=np.concatenate(kept))
    table('VALIDITY_TOPOLOGY_COMPARISON.csv',topology);save('DERIVED_INPUT_LINEAGE.json',dict(sources=lineage,all_original_identity_ledger=asset(R/'local_results/ALL_ORIGINAL_IDENTITIES.npz'),original_denominator=106144,baseline=106098,final=105875))
    check('SIX_ANALYTIC_COORDINATES',all(r['analytic_PASS']=='True' and r['crop_A_K_bitwise_unchanged']=='True' for r in geom),'exact inherited A/K/c2w; prior all-original24 pairs apply unchanged')
    check('SIX_ACTUAL_NN_IDENTITIES',all(r['actual_NN_source_ID_and_depth_exact']=='True' for r in geom),'no interpolation or synthesized depth')
    domains=load(R/'MODEL_DOMAIN_COMPARISON.json')['cohorts'];check('COMMON_METRIC_DOMAIN',all(d['all_points_enclosed'] and max(r['camera_scale_max_mm'] for r in d['per_source'])<1e-5 for d in domains),'all retained and Unknown points included, shared invertible metric scale')
    thin=load(R/'R14_THIN_STRUCTURE_DIAGNOSIS.json');check('R14_PIXEL_ID_PROTECTED',not thin['incremental_excluded_at_thin_pixel'] and thin['native_depth_mm']==thin['output_depth_mm'],'same real(282,215) native depth retained in crop(99,144)')
    check('FROZEN_3PX_GATE',all(int(r['output_sub3px_ridge_N'])==0 for r in geom),'r14 remains1; A2 effective validity introduces5 r04 and65 r00 sub3px ridge proxies; FAIL retained')
    check('RESAMPLING_COMPETING_LAYERS_RESOLVED',not any(r['crosses_1mm_depth_jump']=='True' for r in read_csv(R/'RESAMPLING_FAILURE_DIAGNOSIS.csv') if r['stage']=='A2_INCREMENTAL'),'correct exact NN implementation, but three competing native layers remain; unresolved input limitation')
    before=load(R/'config/PROTECTED_START.json');unchanged=protected_state()==before['worktrees'];assets=before['original_assets']+before['prior_delivery']+before['prior_local'];hashes=all(sha(a['path'])==a['sha256'] for a in assets)
    check('HISTORY_AND_ORIGINALS_PROTECTED',unchanged and hashes,'original six assets, prior Gate A delivery/local outputs and historical worktrees unchanged')
    save('config/FINAL_PROTECTION_CHECK.json',dict(worktree_N=len(before['worktrees']),worktrees_unchanged=unchanged,asset_checks_N=len(assets),all_SHA_unchanged=hashes,old_gate_fail_preserved=load(BASE/'GATE_A_STATUS.json')['overall_status'] if 'overall_status' in load(BASE/'GATE_A_STATUS.json') else load(BASE/'GATE_A_STATUS.json'),neural_modules=[n for n in sys.modules if n.startswith(('torch','tensorflow','training','graphics'))],GPU=0,neural_forward=0,GT_read=False,camera_updates=0,cleanup_rounds=1))
    table('A2_CONTRACT_TESTS.csv',rows)
    save('GATE_A2_ACCEPTANCE.json',dict(status='GATE_A2_FAIL',engineering_execution='COMPLETED',original_N=106144,baseline_N=106098,final_N=105875,incremental_excluded_N=223,current_L_mm=domains[-1]['L_mm'],current_voxel_mm=domains[-1]['voxel_mm'],old_Gate_A='GATE_A_FAIL_PRESERVED',Gate_A_overall_PASS=False,Gate_B_recommended_now=False,Gate_B_authorized=False,decision_basis='existing3px hard gate remains failed; source-layer ambiguity is a diagnostic limitation, not a new numerical hard gate',derived_candidate_promoted_to_baseline=False,active_input_baseline_N=106098,failures=[r for r in rows if r['status']=='FAIL'],limitations=['conditional cameras and uncertified real background visibility','bounded review1641 anomaly flags retained','no anatomical GT for independent surface/side protection','exact NN but source-layer ambiguity','old3px width gate remains; new effective-validity edge ridges also below3px'],proposed_followup='PM review r14 source-traced anatomical width criterion and discontinuity validity proposal; no automatic crop/Mask revision or inference'))
    print('A2_AUDIT',sum(r['status']=='PASS' for r in rows),'PASS',sum(r['status']=='FAIL' for r in rows),'FAIL; history',unchanged,hashes,flush=True)

if __name__=='__main__': main()
