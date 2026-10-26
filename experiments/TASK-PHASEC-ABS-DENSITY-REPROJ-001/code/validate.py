"""Meaningful identity, exact deletion, source-color and protected-asset checks."""
from reprojection import *
import subprocess
def main():
    checks=[]
    def check(name,ok):assert bool(ok),name;checks.append(dict(check=name,passed=True))
    verify();cc=cases();check('8_groups_9_videos_13_refs_213654_points',len(cc)==13 and len(set(c['group']for c in cc))==8 and len(set((c['group'],c['video'])for c in cc))==9 and sum(c['points']for c in cc)==213654)
    freeze=load(R/'provenance/P1_CODE_AND_RULES_FROZEN.json')
    for x in freeze['files']:
        p=Path(x['path']);old=subprocess.check_output(['git','show','8166656:'+str(p.relative_to(REPO))],cwd=REPO);check('P1_source_archive_'+p.name,hashlib.sha256(old).hexdigest()==x['sha256'])
        if p.name!='reprojection.py':check('P1_scientific_rule_unchanged_'+p.name,sha(p)==x['sha256'])
    for name in ['P1_OUTPUT_FREEZE.json','P2_INPUTS.json','P2_EXECUTION_FROZEN.json']:
        for x in load(R/'provenance'/name)['files']:check(name+'_'+Path(x['path']).name,sha(x['path'])==x['sha256'])
    rows=load(R/'metrics/P1_candidate_damage.json');check('bounded_34_trials_not_large_search',len(rows)==34)
    for c in cc:
        a,p,rgb,m=data(c);P=a['XYZ_mm'];root=R/'local_results'/c['id'];raw=dict(np.load(root/'Raw_exact.npz'));check(c['id']+'_Raw_exact_XYZ_RGB_faces',np.array_equal(raw['XYZ_mm'],P)and np.array_equal(raw['RGB'],rgb)and np.array_equal(raw['faces'],m.faces));check(c['id']+'_rho_count_units',np.allclose(a['rho_surface_radius'],a['radius_neighbor_count']/(np.pi*.4**2),rtol=1e-14,atol=1e-12));uv,z=vis.project_camera(P,p['K'],p['pose']);check(c['id']+'_A_to_A_engineering_only',np.max(abs(uv-np.c_[a['source_u'],a['source_v']]))<1e-8)
        for row in [x for x in rows if x['id']==c['id']]:
            t=dict(np.load(root/(row['tier']+'_exact.npz')));deleted=a['rho_surface_radius']<row['threshold_points_per_mm2'];keep=~deleted;facekeep=keep[m.faces].all(1);check(c['id']+'_'+row['tier']+'_strict_rho_only_and_original_indices',np.array_equal(t['deleted_original_indices'],np.flatnonzero(deleted))and np.array_equal(t['kept_original_indices'],np.flatnonzero(keep))and np.array_equal(t['XYZ_mm'],P[keep])and np.array_equal(t['RGB'],rgb[keep]));check(c['id']+'_'+row['tier']+'_original_faces_only',np.array_equal(t['kept_original_face_indices'],np.flatnonzero(facekeep))and np.array_equal(t['faces_original_indices'],m.faces[facekeep])and row['deleted_points']==int(deleted.sum()))
        final=dict(np.load(root/'Final_Cleaned_exact.npz'));check(c['id']+'_final_Raw_preserved_no_false_success',np.array_equal(final['XYZ_mm'],P)and np.array_equal(final['RGB'],rgb))
        lay=dict(np.load(R/'local_results/visuals'/c['id']/'actual_layers_exact.npz'));B,bRGB,buv=background(c);check(c['id']+'_L1_L2_original_coordinates_and_source_RGB',np.array_equal(lay['P0_XYZ_mm'],P)and np.array_equal(lay['P0_RGB'],rgb)and np.array_equal(lay['background_XYZ_mm'],B)and np.array_equal(lay['background_RGB'],bRGB));check(c['id']+'_source_camera_unchanged_and_real_diagnostic_baseline',np.array_equal(lay['source_c2w'],p['pose'])and np.allclose(lay['diagnostic_left_c2w'][:3,3]-p['pose'][:3,3],-p['pose'][:3,0])and np.allclose(lay['diagnostic_right_c2w'][:3,3]-p['pose'][:3,3],p['pose'][:3,0]))
    for stage in ['P2','P3']:
        rows2=load(R/f'metrics/{stage}_results.json');check(stage+'_all_frozen_pairs_accounted',len(rows2)==(7 if stage=='P2'else 4))
        for row in rows2:
            c=next(c for c in cc if c['id']==row['A']);a,p,rgb,m=data(c);B,bRGB,buv=background(c);allRGB=np.r_[rgb,bRGB];outs=[]
            for tier in ['RAW','CLEANED']:
                pred=dict(np.load(Path(row['local_output'])/tier/'projection_exact.npz'));valid=pred['kind']>0;ids=pred['source_original_id'][valid];expected=np.rint(allRGB[ids]*255).astype(np.uint8);check(stage+'_'+row['A']+'_'+row['candidate']+'_'+tier+'_all_winning_colors_from_A_only',np.array_equal(pred['RGBA'][:,:,:3][valid],expected)and not pred['target_RGB_used_for_prediction']and np.all(pred['z'][valid]>0));outs.append(pred)
            raw,cl=outs;same=(raw['kind']>0)&(cl['kind']>0)&(raw['source_original_id']==cl['source_original_id']);check(stage+'_'+row['A']+'_'+row['candidate']+'_same_original_pixel_color_invariant',np.array_equal(raw['RGBA'][same],cl['RGBA'][same]));check(stage+'_'+row['A']+'_'+row['candidate']+'_no_geometry_accuracy_claim',row['geometry_accuracy']is None and not row['whole_pipeline_independent'])
            if stage=='P2':check(row['A']+'_B_excluded_from_A_HERO_inputs',row['target_not_in_A_HERO_inputs'])
            else:check(row['candidate']+'_'+row['A']+'_no_H_optimization_or_fusion',row['status']=='NO_VERIFIED_REGISTRATION'and not row['transform_updated']and row['background_matches_used_for_new_fit']==0)
    images=[]
    for path in sorted((R/'figures').glob('*.png')):
        im=Image.open(path);im.verify();images.append(dict(path=str(path.relative_to(R)),sha256=sha(path),bytes=path.stat().st_size))
    check('10_public_core_PNG_4_plus3_plus3',len(images)==10)
    replay=load(R/'metrics/REPLAY_CHECK.json');check('fresh_directory_replay_four_metric_tables_exact',replay['status']=='PASS'and len(replay['exact_scientific_metrics'])==4 and replay['upstream_runs']==0 and replay['original_assets_overwritten']==0)
    independent=load(R/'metrics/INDEPENDENT_LAYER_REPLAY.json');check('XYZ_only_L1_L4_replay_without_source_images',independent['source_images_mask_depth_video_reads_blocked']and all(x['byte_identical']and x['complete_SHA256']==x['XYZ_only_SHA256']==sha(R/'local_results/visuals/G01_005_raw00057'/x['file'])for x in independent['comparisons']))
    scenes=load(R/'metrics/LAYER_SCENES.json');check('all_13_scenes_have_complete_layers_and_six_views',len(scenes)==13 and all((Path(s['local_folder'])/name).exists()for s in scenes for name in ['Layers_L1-L5.png','Camera_3Views.png','XYZ_3Views.png','Raw_Marked_Final.png','Real_vs_3D.png']))
    for root,snap in load(R/'runtime/protected_start.json').items():
        def git(*args):return subprocess.check_output(['git','-C',root,*args])
        idx=Path(git('rev-parse','--git-path','index').decode().strip());idx=idx if idx.is_absolute()else Path(root)/idx
        check(root+'_user_work_preserved',git('rev-parse','HEAD').decode().strip()==snap['HEAD']and sha(idx)==snap['index_SHA256']and hashlib.sha256(git('status','--porcelain=v1','-uall','-z')).hexdigest()==snap['status_SHA256']and all(sha(Path(root)/p)==h for p,h in snap['modified_files'].items()))
    save('metrics/VALIDATION.json',dict(status='PASS',checks=checks,total_checks=len(checks),GT_used=False,scientific_accuracy_evaluated=False));save('provenance/FIGURE_MANIFEST.json',dict(public_images=images))
    files=list((R/'local_results').rglob('*'));csvsave('metrics/LOCAL_ASSET_INDEX.csv',[dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size,public=False)for p in files if p.is_file()]);save('provenance/EXECUTED_SOURCES.json',stamp(list((R/'code').glob('*.py'))+[R/'config.json',R/'PROTOCOL.md']));print('VALIDATED',len(checks),'checks; 10 public core images; all frozen originals preserved',flush=True)
if __name__=='__main__':main()
