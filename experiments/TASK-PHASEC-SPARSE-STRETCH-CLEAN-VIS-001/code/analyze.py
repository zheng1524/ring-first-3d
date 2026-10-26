"""Read-only summaries of the three frozen cleanup presets."""
import run as r
np=r.np;R=r.R
r.verify();frozen=r.load(R/'provenance/OUTPUTS_FROZEN.json')
assert all(r.sha(R/x['path'])==x['sha256']for x in frozen['files'])
rows=r.load(R/'metrics/reference_results.json');cc=r.cases();groups=[]
for group in sorted(set(c['group']for c in cc)):
    for tier in ['C','M','A']:
        a=[x for x in rows if x['group']==group and x['tier']==tier]
        groups.append(dict(group=group,condition=a[0]['condition'],morphology=a[0]['morphology'],ring=a[0]['ring'],tier=tier,independent_physical_groups=1,videos=len(set(x['video']for x in a)),references=len(a),source_point_exposures=sum(x['original_points']for x in a),deleted_points=sum(x['deleted_points']for x in a),group_mean_reference_deletion_fraction=float(np.mean([x['deleted_fraction']for x in a])),minimum_raw_main_area_retention=min(x['raw_main_area_retained_fraction']for x in a),minimum_largest_piece_retention=min(x['largest_piece_of_raw_main_fraction']for x in a),removed_area_exposure_sum_mm2=sum(x['removed_area_mm2']for x in a),stalk_proxy_denominator=sum(x['possible_stalk_proxy_N']for x in a),stalk_proxy_deleted=sum(x['possible_stalk_proxy_deleted']for x in a),Ring_near_denominator=sum(x['Ring_near_N']for x in a),Ring_near_deleted=sum(x['Ring_near_deleted']for x in a),compact_control_deleted=sum(x['compact_sampling_control_deleted']for x in a),interior_deletion_patches=sum(x['interior_deletion_patches']for x in a),raw_sparse_stretched_proxy_N=sum(x['raw_sparse_stretched_proxy_N']for x in a),raw_sparse_stretched_proxy_deleted=sum(x['raw_sparse_stretched_proxy_deleted']for x in a),guard_pass_references=sum(x['engineering_guard_pass']for x in a),status='DESCRIPTIVE_NOT_RELIABILITY_SUCCESS'))
r.save('metrics/group_results.json',groups);r.csvsave('metrics/group_results.csv',groups)
strata=[]
for attr in ['condition','morphology','ring']:
    for value in sorted(set(x[attr]for x in groups)):
        for condition in sorted(set(x['condition']for x in groups if x[attr]==value)):
            for tier in ['C','M','A']:
                a=[x for x in groups if x[attr]==value and x['condition']==condition and x['tier']==tier]
                strata.append(dict(stratum=attr,value=value,condition=condition,tier=tier,independent_groups=len(a),groups=[x['group']for x in a],references=sum(x['references']for x in a),source_point_exposures=sum(x['source_point_exposures']for x in a),deleted_points=sum(x['deleted_points']for x in a),macro_group_deletion_fraction=float(np.mean([x['group_mean_reference_deletion_fraction']for x in a])),status='DELETION_AMOUNT_ONLY_NOT_ACCURACY'))
r.save('metrics/stratified_results.json',strata);r.csvsave('metrics/stratified_results.csv',strata)
failures=[]
for x in rows:
    failed=[k for k,v in x['engineering_guards'].items()if not v]
    failures.append(dict(id=x['id'],group=x['group'],condition=x['condition'],tier=x['tier'],failed_engineering_guards=failed,stalk_damage_truth='UNKNOWN_PROXY_OVERLAP_NOT_TRUE_FALSE_DELETION',residual_sparse_stretched_proxy=x['raw_sparse_stretched_proxy_N']-x['raw_sparse_stretched_proxy_deleted'],interior_patch_candidates=x['interior_deletion_patches'],independent_geometry_accuracy=None,evidence='Fig1/Fig2/Fig4 and metrics/reference_results.csv',status='NO_CERTIFIED_AUTOMATIC_CLEANUP'))
r.save('metrics/failure_ledger.json',failures);r.csvsave('metrics/failure_ledger.csv',failures)
recommendation=dict(recommended_preview_tier='C',parameters=r.config()['presets']['C'],scope='EXPERIMENTAL_MANUAL_REVIEW_ONLY',stable_automatic_threshold=None,automatic_cleanup_promoted=False,reason='C is the least aggressive tested preset; no tested preset clears all G01 preservation guards, and sparse extensions remain. Inspect stalk/Ring regions before accepting any derived result. M/A are counterexamples, not defaults.',GT_used=False,dense_surface_truth_studied=False)
r.save('metrics/recommendation.json',recommendation)
assert all(r.sha(R/x['path'])==x['sha256']for x in frozen['files'])
print('ANALYZED',len(groups),'group/tier rows;',len(strata),'stratified rows; automatic threshold NONE')
