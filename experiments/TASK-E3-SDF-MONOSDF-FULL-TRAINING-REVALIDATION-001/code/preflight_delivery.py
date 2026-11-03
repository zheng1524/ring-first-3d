"""CPU-only resource summary, history receipts and explicitly pre-training figure.

No model is created, no optimizer is called, and no learned geometry is claimed.
The resource question must be answered before implementing/starting formal runs.
"""
from common import *
import difflib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    plan = protocol()
    measurements = []
    for stage in ('single', 'three_CORE'):
        for arm in ('M0', 'M1'):
            record = load(R / f'metrics/BENCHMARK_{stage}_{arm}.json')
            steps = rows(R / f'metrics/BENCHMARK_{stage}_{arm}_STEPS.csv')
            timed = [float(r['step_seconds']) for r in steps if r['timed'] == 'True']
            assert len(timed) == 20 and record['resource_benchmark_updates'] == 25
            assert record['formal_training_updates'] == 0
            assert all(n == 25 for n in record['official_chain_calls'].values())
            measurements.append(dict(
                stage=stage, arm=arm, measured_updates=25, timed_updates=20,
                mean_seconds=float(np.mean(timed)), median_seconds=float(np.median(timed)),
                p95_seconds=float(np.percentile(timed, 95)),
                estimated_200k_train_hours=float(np.mean(timed) * 200000 / 3600),
                peak_allocated_MiB=record['peak_allocated_MiB'],
                peak_reserved_MiB=record['peak_reserved_MiB'],
                timed_scope='GPU forward/loss/backward/Adam; excludes packet preparation and extraction',
                scientific_status='NOT_EVALUABLE_RESOURCE_TEST_ONLY'))
    table('metrics/RESOURCE_ESTIMATE.csv', measurements)
    available = os.statvfs(R)
    bare = sum(r['estimated_200k_train_hours'] for r in measurements)
    resources = dict(
        status='AWAITING_RESEARCHER_RESOURCE_DECISION',
        trigger='user task section IV: estimate and pause if full training resource requirement exceeds environment',
        GPU='RTX 3060 Laptop, 6144 MiB', primary_runs=4,
        updates_per_run=200000, planned_primary_updates=800000,
        measured_disposable_optimizer_updates=100, formal_optimizer_updates=0,
        extra_post_port_GPU_forward_backward_without_update=1,
        observed_bare_train_hours=bare, planning_wall_hours=[80, 110],
        planning_range_is_not_a_statistical_confidence_interval=True,
        limitations=['20 timed early updates per arm; not late-training thermal or sampler validation',
                     'CPU input preparation, checkpoint and extraction outside timed scope',
                     'larger late-stage adaptive queries can still cause OOM; full run not guaranteed'],
        available_disk_bytes=available.f_bavail * available.f_frsize,
        local_storage_plan=dict(
            model_and_Adam_per_checkpoint_MiB_approx=670395 * 12 / 2**20,
            checkpoint_count_per_run=12,
            four_final_512_cubed_fp32_fields_GiB=4 * 512**3 * 4 / 2**30,
            note='mesh size and temporary fields remain data-dependent; keep only indexed large local outputs'),
        hardware_not_claimed_incapable=True, further_GPU_work_before_decision=False,
        measurements=measurements)
    save('metrics/RESOURCE_DECISION_GATE.json', resources)

    # Read-only historical file identities, separate reports from selected code review.
    tasks = ['TASK-E3-A-SOURCE-AUDIT-AND-PROBLEM-DEFINITION-001',
             'TASK-E3-B-LOCAL-HERO-FIELDS-001',
             'TASK-E3-C-VISIBILITY-CONSENSUS-001',
             'TASK-E3-D0-OPEN3D-TSDF-BASELINE-001',
             'TASK-CAMERA-GATE-G01-004-PILOT-001',
             'TASK-VIEW-PARTITION-MAST3R-FUSION-001',
             'TASK-NEURAL-E2P5-DEPTH-AND-NEURAL-WIRING-001',
             'TASK-NEURAL-E2P6-INITIALIZATION-AND-STABLE-LOSS-001',
             'TASK-NEURAL-E2P7-BOUNDED-LEARNING-PILOT-001',
             'TASK-E3-N0-NEURALFUSION-EIGHT-VIEW-001']
    documents = [dict(kind='technical_version', **asset(REPO/'docs/KEY_TECHNICAL_VERSION_v1.0.md'))]
    for task in tasks:
        documents.append(dict(kind='historical_report', **asset(REPO/'experiments'/task/'TECHNICAL_REPORT.md')))
    for relative in ('config/CAMERA_GATE_RULES.json', 'config/CAMERA_GATE_RESULTS.json',
                     'config/VIEW_SELECTION_FROZEN.json', 'config/EXPERIMENT_FROZEN.json',
                     'NEURALFUSION_OFFICIAL_PIPELINE_AUDIT.md', 'FAILURE_LEDGER.md',
                     'provenance/SCRIPT_VERSION_AUDIT.json'):
        documents.append(dict(kind='current_N0_contract', **asset(N0/relative)))
    v6 = Path('/home/liu/ring_first_3d_e3n0_a3/experiments/TASK-E3-N0-GATE-A3-MASK-BOUNDARY-CLEANUP-001/V6_LOCAL_REPORT.md')
    documents.append(dict(kind='human_accepted_cleanup_report', **asset(v6)))
    code_paths = [REPO/'experiments/TASK-NEURAL-E2P7-BOUNDED-LEARNING-PILOT-001/code/train_arm.py',
                  REPO/'experiments/TASK-E3-B-LOCAL-HERO-FIELDS-001/code/projective_local_field.py',
                  REPO/'experiments/TASK-E3-B-LOCAL-HERO-FIELDS-001/code/mesh_local_field.py',
                  REPO/'experiments/TASK-E3-C-VISIBILITY-CONSENSUS-001/code/visibility.py',
                  N0/'code/common.py', REPO/'visualization/real_p0_renderer.py']
    save('provenance/HISTORY_AND_INTERFACE_RECEIPTS.json', dict(
        parent_commit=subprocess.check_output(['git', '-C', str(REPO), 'rev-parse', 'HEAD'], text=True).strip(),
        reports_and_contracts=documents,
        code_review_scope='relevant source/coordinate/visibility/training functions, not a claim of exhaustive review of every historical script',
        selected_code=[asset(x) for x in code_paths],
        input_mesh_predictions_from_other_routes_used_in_training=False))
    exact = R/'runtime/official_exact/code/model/network.py'
    ported = R/'runtime/monosdf_import/code/model/network.py'
    (R/'provenance/OFFICIAL_IMPORT_PORT.diff').write_text(''.join(difflib.unified_diff(
        exact.read_text().splitlines(True), ported.read_text().splitlines(True),
        fromfile='official/model/network.py', tofile='adapted/model/network.py')))

    denominator = []
    for cid in SOURCES:
        n = native(cid)
        original_valid = (n['native_labels'] == 1) & np.isfinite(n['depth']) & (n['depth'] > 0)
        ids = np.flatnonzero(original_valid)
        uv = np.c_[ids % n['depth'].shape[1], ids // n['depth'].shape[1]]
        cad, _ = cast(ringscene(SCENE), uv, n['Kn'], n['T'])
        # Same separate physical occlusion diagnostic as N0, not the .05mm learning clearance.
        cad_occluded = np.isfinite(cad) & (n['depth'].ravel()[ids] > cad + .002)
        current = np.load(N0/'frozen_inputs/native'/(cid+'.npz'))['valid']
        f = frozen(cid)
        crop_ids = f['native_pixel_ID'][f['eligible_HERO']]
        denominator.append(dict(
            source=cid, original_native_Polyp_N=len(ids), original_CAD_occluded_N=int(cad_occluded.sum()),
            fixed_visible_native_N=int((~cad_occluded).sum()), current_clean_native_N=int(current.sum()),
            crop_eligible_observations_N=int(f['eligible_HERO'].sum()),
            distinct_original_native_IDs_in_eligible_crop_N=int(len(np.unique(crop_ids))),
            evaluation_N_is_not_resampled_crop_N=True,
            camera_qualification='INSUFFICIENT_EVIDENCE', GT='NOT_EVALUABLE'))
    table('metrics/FIXED_NATIVE_DENOMINATORS.csv', denominator)

    # Resource figure uses measured timings and real RGB/real source masks only.
    fig, axes = plt.subplots(2, 3, figsize=(14, 8), constrained_layout=True)
    for ax, cid in zip(axes[0], SOURCES):
        f = frozen(cid)
        ax.imshow(f['RGB'])
        ax.contour(f['eligible_HERO'], levels=[.5], colors=['#32e6a0'], linewidths=.5)
        ax.set_title(cid.replace('G01_004_', '') + '\nreal RGB + legal cleaned HERO scope')
        ax.set_axis_off()
    labels = [f"{r['stage']}\n{r['arm']}" for r in measurements]
    axes[1, 0].bar(labels, [r['mean_seconds'] for r in measurements], color=['#477bad', '#a46525']*2)
    axes[1, 0].set_ylabel('Measured GPU update seconds (early resource test)')
    axes[1, 0].set_ylim(0, .4)
    axes[1, 1].bar(labels, [r['estimated_200k_train_hours'] for r in measurements], color=['#477bad', '#a46525']*2)
    axes[1, 1].set_ylabel('Extrapolated bare training hours / 200k updates')
    axes[1, 2].axis('off')
    axes[1, 2].text(0, .95,
        f"4 runs x 200,000 = 800,000 planned updates\n"
        f"{bare:.1f} h bare training; 80-110 h planning allowance\n"
        "100 disposable resource updates; 0 formal updates\n"
        "Peak model allocation: 4.22 GiB (6 GiB GPU)\n\n"
        "NOT a reconstruction or convergence result.\n"
        "No learned Mesh extracted in this preflight.\n"
        "All 3 cameras: INSUFFICIENT_EVIDENCE.\n"
        "Physical GT: NOT_EVALUABLE.", va='top', fontsize=11, linespacing=1.6)
    fig.suptitle('G01_004 official MonoSDF resource preflight - formal training NOT_RUN', fontsize=15)
    fig.savefig(R/'figures/PREFLIGHT_Inputs_And_Resources.png', dpi=140)
    plt.close(fig)

    save('provenance/PREFLIGHT_CODE_INDEX.json', dict(
        files=[asset(x) for x in sorted((R/'code').glob('*.py'))],
        formal_runner_implemented=False, formal_training_updates=0,
        ready_scope='input/coordinate and full computational-chain resource preflight only',
        pending_scope=['formal long-run entry and resume/checkpoint integration',
                       'actual official extraction execution on learned fields',
                       'fixed-denominator complete model evaluation and four final figures']))
    print('CPU_DELIVERY_PREPARED; formal updates 0; resource decision still required')


if __name__ == '__main__':
    main()
