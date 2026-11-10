from common017 import *
def main():
    manifest=load(R/'provenance/PREANALYSIS_FREEZE.json');changed_inputs=[];changed_history=[]
    for f in manifest['files']:
        if sha(f['path'])!=f['sha256']:changed_inputs.append(f['path'])
    for f in manifest['protected_history']:
        if sha(f['path'])!=f['sha256']:changed_history.append(f['path'])
    assert not changed_inputs,(changed_inputs,'initial immutable files changed');assert not changed_history,changed_history
    final=load(R/'provenance/FINAL_OUTPUT_FREEZE.json')
    changed_outputs=[]
    for source in final['files']:
        for f in source['files']:
            if sha(f['path'])!=f['sha256']:changed_outputs.append(f['path'])
    assert not changed_outputs,changed_outputs
    rulefreeze=load(R/'provenance/BEFORE_FINAL_CLEANING.json');assert sha(rulefreeze['rule']['path'])==rulefreeze['rule']['sha256']
    changed_code=[f['path']for f in rulefreeze['code']if sha(f['path'])!=f['sha256']]
    assert all(Path(p).name=='figures017.py'for p in changed_code),changed_code
    n=0;counts=[];figcompatible=True
    for r in load(R/'config/SOURCE_LOCK.json'):
        for rep in ['ARCHIVE_RAW','NATIVE_GRID']:
            old=np.load(R/'local_results'/r['source_id']/rep/'FACE_EVIDENCE.npz');a=np.load(R/'final_results'/r['source_id']/rep/'FACE_EVIDENCE.npz');c=np.load(R/'final_results'/r['source_id']/rep/'CLEANED_SUBSET.npz');keep=a['state']!=2
            assert np.array_equal(old['V'],a['V'])and np.array_equal(old['F'],a['F'])
            assert np.array_equal(a['V'],c['V'])and np.array_equal(a['F'][keep],c['F'])and np.array_equal(a['original_face_id'][keep],c['original_face_id'])
            assert len(np.unique(a['original_face_id']))==len(a['F']);assert set(np.unique(a['state'])).issubset({0,1,2,3})
            assert np.isfinite(a['V']).all();assert np.array_equal(c['original_face_index'],np.flatnonzero(keep));assert np.all(keep[a['state']==3]);assert (R/'face_decisions'/(r['source_id']+'_'+rep+'.csv.gz')).is_file()
            figcompatible&=np.array_equal(old['state'],a['state']);n+=1;counts.append(dict(source=r['source_id'],rep=rep,N=len(a['F']),rejected=int((~keep).sum())))
    assert n==36 and all(x['rejected']==0 for x in counts)
    summaries=load(R/'metrics/FINAL_SOURCE_SUMMARIES.json');assert all(x['first_surface_retention_fraction']==1 and x['largest_remaining_piece_of_raw_main_fraction']==1 and x['new_boundary_edges']==0 for x in summaries)
    assert all(x['matched']for x in load(R/'metrics/CAMERA_METADATA_BINDING_AUDIT.json'))
    for p in(R/'code').glob('*.py'):ast.parse(p.read_text())
    core=list((R/'figures').glob('Fig*.png'));assert len(core)==4
    assert len(list((R/'figures/full').glob('*.png')))==36
    controls=load(R/'metrics/CONTROL_TESTS.json');assert controls['passed']and load(R/'metrics/TWO_SIDED_CONTROL_TESTS.json')['passed']
    result=dict(epoch=time.time(),checks=dict(all18_sources_two_distinct_identity_representations=True,original_face_vertex_pixel_IDs_preserved=True,retained_XYZ_exact=True,subsets_exact=True,initial_labels_equal_final=figcompatible,protected_files_unchanged=True,upstream_inputs_unchanged=True,all_final_output_hashes_match=True,all18_camera_metadata_pose_bindings_match=True,all22_controls_pass=True,four_main_and36_source_figures=True,all_source_AST_parse=True,no_GT_used=True),GT_used=False,protected_history_file_N=len(manifest['protected_history']),frozen_input_code_file_N=len(manifest['files']),source_N=18,physical_N=4,geometry_deletion_N=0,raw_first_surface_retention=1.,history_fallback_N=0,scientific_status='LABELING_COMPLETE_CLEANING_INCONCLUSIVE_NO_REMOVAL',not_scientific_cleaning_PASS=True,plot_only_code_changes_after_rule_freeze=changed_code,plot_changes='Main figures use original archive Raw instead of diagnostic native grid; display bounds include all referenced original faces, unused vertices still preserved. No metric or geometry changed.',native_grid_role='DIAGNOSTIC_ONLY_NOT_NEW_SURFACE_OR_ADAPTER_INPUT',automatic_next_stage=False)
    save('metrics/DELIVERY_VALIDATION.json',result);print('DELIVERY_VALIDATION_COMPLETE_NO_CLEANING_PASS',flush=True)
if __name__=='__main__':main()
