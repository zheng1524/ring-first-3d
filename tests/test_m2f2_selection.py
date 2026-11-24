import numpy as np

from ring_first_3d.views.pipeline_adapter import (
    admission_tiers, direction_blocks, validate_t13, select_target_sets)


def metrics(**changes):
    row = dict(pose_valid=True, cad_valid=True, ring_raw_mae=1.0,
               held_n=30, held_median=1.0, held_p95=3.0,
               big_error_fraction=0.01, positive_depth=1.0,
               rotation_to_previous_deg=2.0, center_to_previous_mm=1.0,
               admission_status="ACCEPT")
    row.update(changes)
    return row


def test_s2_never_admits_rejected_or_branch_camera():
    assert admission_tiers(metrics(admission_status="REJECT"), 3, "T0_CONTINUOUS") == (False, False, False)
    assert admission_tiers(metrics(), 3, "T2_ISOLATED_BRANCH") == (False, False, False)
    assert admission_tiers(metrics(), 1, "T0_CONTINUOUS") == (True, True, True)  # S2 independent local tier


def test_s0_s1_use_recorded_thresholds():
    assert admission_tiers(metrics(ring_raw_mae=2.5), 2, "T1_SAMPLING_GAP") == (False, True, True)
    assert admission_tiers(metrics(held_p95=31), 2, "T0_CONTINUOUS") == (False, False, True)  # S2 local-only


def test_complete_link_direction_blocks_use_model_center():
    poses = []
    for x in ([10., 0., 0.], [10., 1., 0.], [-10., 0., 0.]):
        C = np.eye(4); C[:3, 3] = x; poses.append(C)
    blocks = direction_blocks(poses, np.array([1., 0., 0.]))
    assert blocks[0] == blocks[1]
    assert blocks[2] != blocks[0]


def test_t13_requires_measured_geometry_for_every_support():
    C = np.eye(4)
    target = dict(id="t", C=C)
    supports = []
    for i, x in enumerate(([3., 0., 0.], [0., 3., 0.], [-3., 0., 0.])):
        P = np.eye(4); P[:3, 3] = x; supports.append(dict(id=str(i), C=P))
    candidates = [dict(id=str(i), geometric_inliers=20, direction_deg=20.,
                       epipolar_px=dict(median=1.), parallax_deg=dict(median=4.)) for i in range(3)]
    assert validate_t13(target, supports, candidates) == (True, "PASS")
    candidates[1]["geometric_inliers"] = 0
    assert validate_t13(target, supports, candidates)[0] is False


def test_t10_and_t11_both_execute_with_distinct_honest_labels():
    pool = []
    for i in range(9):
        a = np.deg2rad(i * 10)
        pool.append(dict(id=str(i), video="004", role="FIT", direction=[float(np.cos(a)),
                         float(np.sin(a)), 0.], direction_block=i // 2,
                         raw_frame=i * 100, sharpness=float(i + 1),
                         mask_complete_proxy=.9,
                         thin_structure_visibility_proxy=.5,
                         Ring_free_fraction=.8))
    result = select_target_sets(pool, ["0"], ["8"])
    assert result["T10"]["strategy"] == "quality_diversity"
    assert result["T11"]["strategy"] == "direction_quota"
    assert result["T10"]["ids"][0] == "0"
    assert result["T11"]["ids"][0] == "8"
    assert len(result["T10"]["ids"]) == len(result["T11"]["ids"]) == 8
