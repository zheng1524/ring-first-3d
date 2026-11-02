"""Retain the original GateA evidence; package user-authorized derived candidate.
The chosen proposal encloses every retained point, including all9 unresolved.
"""
from recheck_cleaned_inputs import *
def cross_source_with_all_original_identities(cid):
    s=derived_native(cid);o=native(cid)
    # Evaluate unchanged continuous geometry for ALL original IDs, including46
    # marked as derived-invalid; no projection failures disappear from denominator.
    return dict(s,X=o['X'],native_uv=o['native_uv'],native_id=o['native_id'])
def prepare_candidate(cid,dom):
    s=derived_native(cid);c=np.load(V/'local_results/crops'/(cid+'.npz'));L=dom['L_mm'];O=np.asarray(dom['O_mm']);T=s['T'].copy();T[:3,3]=(T[:3,3]-O)/L
    return dict(input=(c['depth_mm']/L)[None].astype(np.float32),original_mask=c['valid'][None].astype(np.float32),intrinsics=c['K_crop'][None].astype(np.float32),extrinsics=T[None].astype(np.float32),origin=np.zeros((1,1,3),np.float32),resolution=1/128)
def main():
    cfg=load(ROOT/'config/GATE_A_PREREGISTERED.json');ns=dict(globals(),R=V,native=cross_source_with_all_original_identities,save=lambda p,data:save(V/p,data),table=lambda p,rows:table(V/p,rows));extract(ROOT/'code/cross_view.py',['main'],ns);ns['main']()
    old=load(ROOT/'METRIC_TRANSFORM.json');new=load(V/'METRIC_TRANSFORM.json');dom=new['domains']['ALL_INPUTS'];assert all(r['out_of_grid_N']==0 for r in dom['per_source'])
    if not(ROOT/'config/ORIGINAL_METRIC_TRANSFORM.json').exists():(ROOT/'config/ORIGINAL_METRIC_TRANSFORM.json').write_bytes((ROOT/'METRIC_TRANSFORM.json').read_bytes())
    selection=dict(status='SELECTED_CANDIDATE_FOR_PM_REVIEW_NOT_GATE_A_PASS',candidate='ALL_RETAINED_INPUTS_AFTER_USER_AUTHORIZED_ONE_PASS',transform=dom,reason='Use full enclosure of all remaining inputs; no need to delete9 unresolved points or shrink into diagnostic bbox. Single pass/unchanged crop rule; no further parameter search.',model_domain_scientifically_accepted=False,physical_ROI_formally_frozen=False,thin_structure_gate='FAIL_RETAINED_r14',original_baseline_preserved=asset(ROOT/'config/ORIGINAL_METRIC_TRANSFORM.json'),cleanup=asset(ROOT/'PROJECTIVE_CLEANUP_SUMMARY.json'),Gate_B='NOT_AUTHORIZED')
    save('config/POST_REVIEW_DOMAIN_SELECTION.json',selection);old.update(status='ORIGINAL_STOP_PRESERVED_WITH_POST_REVIEW_CANDIDATE',original_status=old['status'],after_user_authorized_projective_cleanup=new,selected_candidate_for_PM=selection,active_transform=None,physical_ROI_frozen=False);save('METRIC_TRANSFORM.json',old)
    checks=[]
    for cid in IDS:
        s=derived_native(cid);item=prepare_candidate(cid,dom);c=np.load(V/'local_results/crops'/(cid+'.npz'));assert np.all(item['input'][item['original_mask']==0]==0)and np.isfinite(item['input']).all();world=(c['output_X_mm']-np.asarray(dom['O_mm']))/dom['L_mm'];out=((world<0)|(world>=1)).any(1)
        checks.append(dict(source=cid,input_shape=list(item['input'].shape),dtype=str(item['input'].dtype),prepared_device='CPU numpy, no model call',legal_input_N=int(item['original_mask'].sum()),original_legal_N=len(native(cid)['native_id']),projective_excluded_N=int(s['projective_excluded'].sum()),selected_domain_OUT_OF_GRID_N=int(out.sum()),invalid_nonzero_N=int((item['input'][item['original_mask']==0]!=0).sum()),crop_affine_exactly_unchanged=bool(np.array_equal(c['A'],np.load(ROOT/'local_results/crops'/(cid+'.npz'))['A'])),c2w_rotation_unchanged=bool(np.array_equal(item['extrinsics'][0,:3,:3],s['T'][:3,:3].astype(np.float32))),full_original_projection_denominator=len(native(cid)['native_id']),source_camera_qualification_unchanged=True))
    table('POST_REVIEW_INPUT_CONTRACTS.csv',checks)
    if not(ROOT/'config/ORIGINAL_INFERENCE_ONLY_SCHEMA.json').exists():(ROOT/'config/ORIGINAL_INFERENCE_ONLY_SCHEMA.json').write_bytes((ROOT/'INFERENCE_ONLY_SCHEMA.json').read_bytes())
    schema=load(ROOT/'INFERENCE_ONLY_SCHEMA.json');schema.update(status='CANDIDATE_INPUT_SCHEMA_GATE_A_THIN_FAIL_NO_FORWARD',post_review_candidate_metric=dom,post_review_array_preparation_entrypoint='code/finish_scope_update.py:prepare_candidate',post_review_contracts=checks,all_original_denominators_retained=True,active_metric_domain=None,Gate_B='NOT_AUTHORIZED');save('INFERENCE_ONLY_SCHEMA.json',schema)
    save('config/CODE_REUSE_AFTER_SCOPE_UPDATE.json',REUSE);print('POST_REVIEW_CANDIDATE',dom['L_mm'],'mm;',dom['voxel_mm'],'mm/voxel; remaining9 retained',flush=True)
if __name__=='__main__':main()
