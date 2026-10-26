"""Verify source preservation, exact index subsets and public plot identities."""
import subprocess
from PIL import Image
import run as r
np=r.np;R=r.R;checks=[]
def check(name,ok,**detail):
    assert bool(ok),name;checks.append(dict(check=name,passed=True,**detail))
def main():
    r.verify();check('frozen_inputs_and_detector_source_unchanged',True,files=len(r.load(R/'provenance/INPUT_MANIFEST.json')['files']))
    frozen=r.load(R/'provenance/OUTPUTS_FROZEN.json');check('143_local_outputs_unchanged',len(frozen['files'])==143 and all(r.sha(R/x['path'])==x['sha256']for x in frozen['files']))
    cc=r.cases();check('8_groups_9_videos_13_references',len(cc)==13 and len(set(c['group']for c in cc))==8 and len(set((c['group'],c['video'])for c in cc))==9 and sum(c['points']for c in cc)==213654)
    results=r.load(R/'metrics/reference_results.json');check('exactly_39_reference_tier_rows',len(results)==39 and len(set((x['id'],x['tier'])for x in results))==39)
    for c in cc:
        base=R/f'local_results/{c["id"]}';a=dict(np.load(base/'Raw_Marked_Cleaned_identities.npz'));old=r.fields(c);m=r.trimesh.load(c['mesh'],process=False);cid=c['id'];pack=dict(np.load(c['pack']));uv=np.c_[a['source_u'],a['source_v']]
        check(cid+'_raw_coordinates_source_identity_and_original_faces_exact',np.array_equal(a['XYZ_mm'],old['XYZ_mm'])and np.array_equal(a['source_u'],old['source_u'])and np.array_equal(a['source_v'],old['source_v'])and np.array_equal(a['original_faces'],m.faces)and str(a['actual_video'])==c['video']and str(a['reference_frame'])==c['reference'])
        check(cid+'_D0_D1_preserved',all(np.allclose(a['original_'+k],old[k],equal_nan=True)for k in ['D0','D1']))
        check(cid+'_depth_normalized_spacing_reuses_previous_field',np.array_equal(a['spacing_depth_normalized'],old['knn_k_distance_mm']/pack['depth_mm'][uv[:,1],uv[:,0]]))
        check(cid+'_three_masks_nested',not np.any(a['candidate_C']&~a['candidate_M'])and not np.any(a['candidate_M']&~a['candidate_A']))
        check(cid+'_raw_display_all_points',len(r.trimesh.load(base/'Raw.ply',process=False).vertices)==len(old['XYZ_mm']))
        for tier,preset in r.config()['presets'].items():
            d=a['candidate_'+tier];ids=np.flatnonzero(~d);fids=np.flatnonzero(~d[m.faces].any(1));mapback=np.full(len(d),-1,int);mapback[ids]=np.arange(len(ids));out=r.trimesh.load(base/f'Cleaned_{tier}_original_faces.ply',process=False);row=next(x for x in results if x['id']==cid and x['tier']==tier)
            check(cid+'_'+tier+'_candidate_rule_and_exact_kept_indices',np.array_equal(d,r.candidates(a['spacing_ratio'],a['stretch_ratio'],preset))and np.array_equal(ids,a['cleaned_'+tier+'_original_point_indices'])and np.array_equal(fids,a['cleaned_'+tier+'_original_face_indices']))
            check(cid+'_'+tier+'_cleaned_mesh_is_original_subset_only',np.array_equal(out.vertices,m.vertices[ids])and np.array_equal(out.faces,mapback[m.faces[fids]])and row['deleted_points']==int(d.sum())and row['kept_faces']==len(fids))
            check(cid+'_'+tier+'_raw_marked_cleaned_counts',len(r.trimesh.load(base/f'Candidate_Marked_{tier}.ply',process=False).vertices)==len(d)and len(r.trimesh.load(base/f'Cleaned_{tier}.ply',process=False).vertices)==len(ids))
    strata=r.load(R/'metrics/stratified_results.json');check('normal_and_stress_macro_groups_separate',all(len(set(c['condition']for c in cc if c['group']in x['groups']))==1 for x in strata))
    check('compact_control_unchanged_in_all_presets',all(x['compact_sampling_control_deleted']==0 for x in results))
    for root,snapshot in r.load(R/'provenance/protected_worktrees.json').items():
        def git(*args):return subprocess.check_output(['git','-C',root,*args])
        status=git('status','--porcelain=v1','-uall','-z');idx=r.Path(git('rev-parse','--git-path','index').decode().strip());idx=idx if idx.is_absolute()else r.Path(root)/idx
        check(root+'_protected_HEAD_index_status_and_user_edits',git('rev-parse','HEAD').decode().strip()==snapshot['HEAD']and r.hashlib.sha256(status).hexdigest()==snapshot['status_sha256']and r.sha(idx)==snapshot['index_sha256']and all(r.sha(r.Path(root)/p)==h for p,h in snapshot['modified_sha256'].items()))
    small=r.load(R/'metrics/small_tests.json');check('13_numeric_and_original_renderer_checks',small['count']==13 and all(x['passed']for x in small['tests']))
    meta=r.load(R/'provenance/FIGURE_CONFIG.json');check('all_panels_use_original_parameters',all(x['point_size']==.8 and x['source_RGB']for x in meta['panels'])and meta['draw_functions_unchanged'])
    png=sorted((R/'figures').glob('*.png'));check('exactly_four_core_PNGs',len(png)==4);images=[]
    for p in png:
        im=Image.open(p);im.verify();im=Image.open(p).convert('RGB');check(p.name+'_valid_nonblank_actual_PNG',im.width>=2000 and im.height>=1500 and np.ptp(np.asarray(im))>100)
        images.append(dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=r.sha(p),width=im.width,height=im.height))
    r.save('provenance/FIGURE_MANIFEST.json',dict(images=images,original_drawing_functions_reused=True,GT_used=False))
    src=[*sorted((R/'code').glob('*.py')),*sorted((r.REPO/'visualization').glob('*.py'))]
    r.save('provenance/EXECUTION_SOURCES.json',dict(files=[dict(path=str(p),sha256=r.sha(p),bytes=p.stat().st_size)for p in src],detector_code_matches_run_freeze=True,renderer_function_pixel_regression=True))
    r.save('metrics/validation.json',dict(status='PASS',checks=checks,total_checks=len(checks),GT_used=False,original_point_count=213654,original_assets_changed=False))
    print('VALIDATED',len(checks),'checks; exact subsets/no original asset changes')
if __name__=='__main__':main()
