"""Run once before candidate discovery and projective decisions."""
from common import *

def main():
    assert not (R/'config/A2_PREREGISTERED.json').exists(), 'DO_NOT_REWRITE_PROTOCOL'
    assert git(REPO,'rev-parse','HEAD') == '4b60db5d9402c2bb87692ba3b2b7819f3c7c1423'
    assert git(BASE.parents[1],'status','--porcelain=v1','--untracked-files=all') == ''
    expected=[]
    for r in MANIFEST['sources']:
        for a in r['assets'].values():
            assert sha(a['path']) == a['sha256']; expected.append(asset(a['path']))
    expected.append(asset(CAD))
    previous=load(BASE/'DELIVERY_INDEX.json')
    historical=[]
    for a in previous['files']:
        assert sha(a['path']) == a['sha256']; historical.append(asset(a['path']))
    baseline_files=[]
    for row in LINEAGE['sources']:
        for key in ['derived_depth_and_valid','crop']:
            a=row[key]; assert sha(a['path']) == a['sha256']; baseline_files.append(asset(a['path']))
        for path in [BASE/'local_results'/(row['source']+'_native_raw_diagnostic.npz'),BASE/'derived_projective_v1/local_results/crops'/(row['source']+'_identities.npz')]:
            baseline_files.append(asset(path))
    task=Path('/home/liu/.codex/attachments/a73ac241-abc9-4761-9a10-4448345b3c80/Pasted text.txt')
    (R/'docs/APPROVED_TASK.md').write_bytes(task.read_bytes())
    p=dict(task=R.name, parent_commit=git(REPO,'rev-parse','HEAD'),source_order=IDS,
        original_denominator=106144, baseline_denominator=106098, historical_excluded_N=46,
        candidate_generation=dict(previous_unresolved_9='mandatory first', per_source_axis_extrema='all unique argmin/argmax points; mandatory',
            global_boundary_band_mm=.25, native_4neighbour_jump_mm=1., native_mask_boundary_px=2.,
            raw_face_distance_mm=1., rules=['within0.25mm of retained input global axis bounds','native legal4-neighbour jump>=1mm','own Raw distance>1mm AND native Mask boundary<=2px'],
            max_review_pool_per_source=512, sort='previous9, source_axis_extrema, global_boundary, depth_jump, raw_edge; native_pixel_ID ascending within priority',
            unreviewed_anomalies='listed in full discovery CSV; never removed', threshold_basis='reuse0.25mm support, D0 raw1mm diagnostic; jump4x0.25; bounded candidate-only flags, never deletion criteria'),
        projection=dict(observer_order=IDS,silhouette_margin_archived_px=8., support_tolerance_mm=.25,CAD_epsilon_mm=.002,
            independent_opposing_blocks=2,negative_voters=IDS[:5], r14='positive/unknown observations only, never negative voter',
            archived_depth_sampling='exact original archival depth pack, as Gate A; native baseline validity must also hold; either native or archived near depth is a conservative support veto',
            categories='D near support -> retain; B any eligible Polyp layer competition -> retain; A >=2 distinct block silhouette contradictions and no support/layer competition -> derived exclude; C otherwise retain Unknown',
            legal_negative='inside real RGB, positive axial Z, BG>8px outside Polyp, no Ring CAD first-hit occlusion, no Ring Mask, inherited conditional camera, no known visibility/order conflict',
            camera_truth='same inherited conditional usage; pilot INSUFFICIENT_EVIDENCE preserved; engineering proxy, not physicalGT',
            occlusion='CAD/Ring/field/boundary/invalid-depth/known layer occlusion never negative votes; unknown true background geometry remains a limitation',
            same_block='ref08 and r04=B3 count once; RGB correlation not statistical independence',
            protected_CORE='CORE native interior>2px AND own original Raw distance<=1mm retained even if silhouette votes disagree; signal camera/visibility ambiguity instead',
            r14_near='uncertified positive near-depth vetoes removal but does not certify support'),
        domain=dict(exact_function=asset(BASE/'code/metric_domain.py'),rule='make_domain, all retained XYZ + unchanged CAD, margin=max(2mm,10% maximum span), cube round up0.001mm',N=128, target_size='no25.735mm target', all_unresolved_retained=True),
        crop=dict(exact_prior_protocol=asset(BASE/'config/GATE_A_PREREGISTERED.json'), rule_changed=False, thin_hard_gate_px=3., thin_alternative='diagnostic proposal only, cannot change frozen gate',analytic_max_mm=1e-5,projection_max_px=1e-4),
        resampling=dict(extremes='top1 maximum per source, all three downsampled sources; fixed original identities', jump_threshold_mm=1.,method='diagnose forward original-to-output pairing separately from actual inverse NN sampling',candidate_revision='proposal only; no interpolation, no automatic extra filtering'),
        forbidden=['GPU','NeuralFusion.forward','training','newHERO','newTSDF','pose_optimization','GT/Oracle','original_mask_or_HERO_mutation'],cleanup_rounds=1,allowed_output='new task derived copies only')
    save('config/A2_PREREGISTERED.json',p)
    save('config/PROTECTED_START.json',dict(worktrees=protected_state(), original_assets=expected,prior_delivery=historical,prior_local=baseline_files,approved_task=asset(task),prior_gate_status=asset(BASE/'GATE_A_STATUS.json')))
    save('config/BEFORE_CANDIDATES.json',dict(protocol=asset(R/'config/A2_PREREGISTERED.json'),code=[asset(f)for f in sorted((R/'code').glob('*.py'))],utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
    print('FROZEN_A2',sha(R/'config/A2_PREREGISTERED.json'),flush=True)

if __name__=='__main__': main()
