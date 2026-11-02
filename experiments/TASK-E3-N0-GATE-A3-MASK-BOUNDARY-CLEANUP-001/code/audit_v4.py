"""Verify user-targeted260 removal, fixed geometry, lineage and residuals."""
from analyze import *

def main():
    rows=[]
    def ck(name,ok,detail):rows.append(dict(test=name,status='PASS' if ok else 'FAIL',detail=detail))
    targets=read_csv(R/'V4_260_CANDIDATES.csv');before=load(R/'config/V4_260_BEFORE_RESULTS.json');ck('FROZEN260_IDS',len(targets)==260 and sha(R/'V4_260_CANDIDATES.csv')==before['targets']['sha256'],'fixed Native Pixel IDs, no expanded search')
    ck('FROZEN260_PROTOCOL',sha(R/'config/V4_260_PREREGISTERED.json')==before['protocol']['sha256'],'formal V4=V3 minus260; not withdrawn5px')
    for a in before['code']:
        if Path(a['path']).name in ['common.py','mask_cleanup.py','analyze.py','v4.py']:ck('FROZEN_SCIENCE_CODE_'+Path(a['path']).name,sha(a['path'])==a['sha256'],'rendering may be extended, selection and geometry frozen')
    classes={(a['source'],int(a['native_id'])):a['category'] for a in read_csv(A2/'PROJECTIVE_CLEANUP_DECISIONS.csv')};total=0
    for cid in IDS:
        v3=cohort(cid,'V3');v4=cohort(cid,'V4');d=np.load(R/'local_results/inputs/V4'/(cid+'.npz'));mask=d['V4_from_V3_excluded'];ids=np.flatnonzero(mask);wanted=np.array([int(a['native_id'])for a in targets if a['source']==cid]);total+=len(ids)
        ck(cid+'_EXACT_TARGETS',np.array_equal(ids,wanted) and np.all(v3['valid'].ravel()[ids]) and len(v3['native_id'])-len(v4['native_id'])==len(ids),'exact requested subset of V3, no additional removal')
        ck(cid+'_UNCHANGED_OTHER_VALUES',np.array_equal(v4['depth'][~mask],v3['depth'][~mask]) and np.array_equal(v4['valid'][~mask],v3['valid'][~mask]),'all other depth/valid values bitwise unchanged')
        back=v4['depth'].copy();back.flat[d['incremental_native_ids']]=d['incremental_original_depth_mm'];ck(cid+'_REVERSIBLE_TO_V3',np.array_equal(back,v3['depth']),'suppressed source values stored')
        ck(cid+'_PREVIOUS_CD_PROTECTED',all((cid,int(i)) not in classes for i in ids),'none of the original A2 C/D/B/A reviewed candidates altered by this increment')
        ck(cid+'_NO_UNKNOWN_FILL',np.all(v4['depth'][mask]==0) and not v4['valid'][mask].any(),'new region remains Unknown, no invented depth')
    ck('EXACT260_INCREMENT',total==260 and sum(len(cohort(cid,'V4')['native_id']) for cid in IDS)==103686,'V3 103946 -> V4 103686; cumulative2189 vsV1')
    same=all(sha(a['path'])==a['sha256'] for a in before['protected_three_version_tables']+before['protected_three_version_arrays']);ck('V1_V2_V3_UNCHANGED',same,'31 protected previous tables/arrays unchanged')
    geo=read_csv(R/'FOUR_VERSION_GEOMETRY_VALIDATION.csv');ck('ALL24_GEOMETRY_CONTRACTS',len(geo)==24 and all(float(a['analytic_XYZ_max_mm'])<=1e-5 and float(a['camera_scale_max_mm'])<=1e-5 and a['out_of_grid_N']=='0' and a['exact_selected_depth']=='True' for a in geo),'same crop,K,c2w and common27.959mm cube across four variants')
    remaining=read_csv(R/'V4_REMAINING_ANOMALY_PROXIES.csv');ck('REMAINDER_TRACEABLE',len(remaining)==121 and sum(a['A2_category']=='C_UNKNOWN_RETAIN' for a in remaining)==89 and sum(a['A2_category']=='D_SUPPORTED_RETAIN' for a in remaining)==32,'remaining proxies are original C89/D32; unreviewed>1mm proxy remainder0')
    ev=read_csv(R/'V4_260_MULTIVIEW_EVIDENCE.csv');ck('MULTIVIEW_AUDIT1300',len(ev)==1300 and all(sum(e['candidate_id']==t['candidate_id']for e in ev)==5 for t in targets),'exact reused A2 projection/CAD loop; no reliability claim')
    old=load(R/'config/PROTECTED_START.json');samehist=protected_state()==old['worktrees'];hashes=all(sha(a['path'])==a['sha256'] for a in old['assets']);ck('HISTORICAL_BRANCHES_AND_RAW_SHA',samehist and hashes,'all protected earlier raw inputs/results/worktrees unchanged')
    ck('NO_NEURAL_EXECUTION',not any(n.startswith(('torch','tensorflow','training','graphics')) for n in sys.modules),'CPU geometry only, no model weights/forward/GPU')
    table('V4_CONTRACT_TESTS.csv',rows)
    original=load(R/'GATE_A3_ACCEPTANCE.json');save('config/A3_BEFORE_FORMAL_V4_ACCEPTANCE.json',original)
    mv=load(R/'config/V4_MULTIVIEW_REUSE.json');engine=all(r['status']=='PASS' for r in rows)
    original.update(status='A3_ENGINEERING_PASS_WITH_LIMITATIONS' if engine and original['tests_FAIL']==0 else 'A3_ENGINEERING_FAIL',versions=['V1','V2','V3','V4'],V4_definition='V3 minus user-approved260 previously unreviewed Raw-distance proxies',V4_is_5px=False,V4_from_V3_excluded_N=260,V4_retained_N=103686,V4_remaining_raw_proxy_N=121,V4_remaining_classes={'C':89,'D':32},V4_multiview_near_support_target_N=mv['targets_with_near_support'],V4_multiview_depth_layer_target_N=mv['targets_with_layer_competition'],V4_physical_error_truth='NOT_CERTIFIED',V4_tests_PASS=sum(r['status']=='PASS'for r in rows),V4_tests_FAIL=sum(r['status']=='FAIL'for r in rows),GateB_recommendation='V2 useful controlled input ablation; V3/V4 aggressive controls with explicit missing-surface and manual-proxy risks; researcher review required',GateB_authorized=False,automatic_promotion_to_baseline=False)
    save('GATE_A3_ACCEPTANCE.json',original);save('config/FINAL_V4_PROTECTION.json',dict(historical_worktrees_unchanged=samehist,historical_worktree_N=len(old['worktrees']),old_source_asset_SHA_checks=len(old['assets']),all_old_SHA_unchanged=hashes,V1_V2_V3_unchanged=same,originals_modified=0,formal_V4_increment260=True,model_imports=[],GPU=0,NNforward=0,GT_read=False,old3px_not_a_blocker=True))
    print('V4_AUDIT',sum(r['status']=='PASS'for r in rows),'PASS',sum(r['status']=='FAIL'for r in rows),'FAIL',flush=True)

if __name__=='__main__':main()
