"""Input adapters for the frozen M2C admission and historical view selectors."""
import numpy as np
from scipy.cluster.hierarchy import fcluster, linkage


def _finite_le(value, limit):
    try:
        return bool(np.isfinite(float(value)) and float(value) <= limit)
    except (TypeError, ValueError):
        return False


def _finite_ge(value, limit):
    try:
        return bool(np.isfinite(float(value)) and float(value) >= limit)
    except (TypeError, ValueError):
        return False


def admission_tiers(row, graph_support_count, trajectory_class):
    """Independent S0/S1/S2 semantics.

    S0 = complete frozen YAML; S1 = frame/local-graph evidence, not merely
    relaxed S0; S2 = frame-valid local candidate, with the real multi-view
    combination gate applied later by validate_t13.
    """
    pose_ok = bool(row["pose_valid"]) and bool(row["cad_valid"])
    not_reject = row["admission_status"] not in ("REJECT", "REJECTED")
    not_branch = trajectory_class not in ("T2_ISOLATED_BRANCH", "T3_CONSECUTIVE_BRANCH")
    if not (pose_ok and not_reject):
        return False, False, False
    # Frozen YAML S0: ring 2 px, held 20/4/8, positive 0.95,
    # big-error 0.10, neighbour 10 deg/5 mm.  The 2 mm triangulation
    # baseline is checked when the W0 admission row carries it.
    baseline_ok = True
    if "triangulation_min_baseline_mm" in row:
        try:
            baseline_ok = float(row["triangulation_min_baseline_mm"]) >= 2.0
        except (TypeError, ValueError):
            baseline_ok = False
    s0 = bool(not_branch and baseline_ok and
              _finite_le(row["ring_raw_mae"], 2.) and
              _finite_ge(row["held_n"], 20) and
              _finite_le(row["held_median"], 4.) and
              _finite_le(row["held_p95"], 8.) and
              _finite_le(row["big_error_fraction"], .10) and
              _finite_ge(row["positive_depth"], .95) and
              _finite_le(row.get("rotation_to_previous_deg", 0), 10.) and
              _finite_le(row.get("center_to_previous_mm", 0), 5.))
    # S1 uses frame/trajectory evidence; a held count alone is not enough.
    s1 = bool(not_branch and graph_support_count >= 1 and
              _finite_le(row["ring_raw_mae"], 4.) and
              (_finite_ge(row["held_n"], 4) or graph_support_count >= 2) and
              _finite_le(row["held_median"], 8.) and
              _finite_le(row["held_p95"], 30.) and
              _finite_le(row["big_error_fraction"], .25) and
              _finite_ge(row["positive_depth"], .90))
    # S2 is local: do not require S1 global thresholds.  It only admits a
    # frame-valid, non-branch local candidate; validate_t13 then requires a
    # real four-camera geometry.
    s2 = bool(not_branch and graph_support_count >= 1 and
              _finite_ge(row["positive_depth"], .90))
    return s0, s1, s2


def direction_blocks(poses, center_mm):
    """Historical 014 complete-link .26 direction partition, with a supplied model centre."""
    center = np.asarray(center_mm, float)
    if center.shape != (3,) or not np.isfinite(center).all():
        raise ValueError("INVALID_MODEL_CENTER")
    vectors = np.asarray([np.asarray(C, float)[:3, 3] - center for C in poses])
    if vectors.ndim != 2 or vectors.shape[1] != 3 or not np.isfinite(vectors).all():
        raise ValueError("INVALID_CAMERA_DIRECTIONS")
    lengths = np.linalg.norm(vectors, axis=1)
    if np.any(lengths <= 0):
        raise ValueError("ZERO_MODEL_CENTER_DIRECTION")
    directions = vectors / lengths[:, None]
    return [int(x) for x in (fcluster(linkage(directions, method="complete"),
                                    t=.26, criterion="distance") if len(directions) > 1
                             else np.ones(len(directions), int))]


def _angle(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    na = np.linalg.norm(a); nb = np.linalg.norm(b)
    if min(na, nb) <= 1e-9:
        return 0.
    return float(np.degrees(np.arccos(np.clip(np.dot(a, b) / (na * nb), -1., 1.))))


def validate_t13(target, supports, candidates):
    """Recheck historical T13 evidence and three-way camera diversification."""
    if len(supports) != 3 or len({target["id"], *(x["id"] for x in supports)}) != 4:
        return False, "TUPLE_MEMBERSHIP"
    by_id = {c["id"]: c for c in candidates}
    t = np.asarray(target["C"], float)
    if t.shape != (4, 4) or not np.isfinite(t).all():
        return False, "TARGET_POSE"
    directions = []
    for support in supports:
        c = by_id.get(support["id"])
        C = np.asarray(support["C"], float)
        if C.shape != (4, 4) or not np.isfinite(C).all():
            return False, "SUPPORT_POSE"
        if c is None or c.get("geometric_inliers", 0) < 12:
            return False, "T13_GEOMETRIC_INLIERS"
        if not (_finite_ge(c.get("direction_deg"), 1.) and
                _finite_le(c.get("direction_deg"), 60.) and
                _finite_le(c.get("epipolar_px", {}).get("median"), 3.) and
                _finite_ge(c.get("parallax_deg", {}).get("median"), 0.)):
            return False, "T13_GEOMETRY_EVIDENCE"
        # T13 already enforces direction 1-60 deg, >=12 geometric inliers,
        # epipolar <=3 px and a measured parallax.  The frozen 2 mm value is a
        # triangulation baseline, not a camera-centre distance gate.
        if np.linalg.norm(C[:3, 3] - t[:3, 3]) <= 1e-9:
            return False, "ZERO_TARGET_BASELINE"
        directions.append(C[:3, 3])
    for i in range(3):
        for j in range(i + 1, 3):
            if _angle(directions[i], directions[j]) < 1.:
                return False, "T13_SUPPORT_DIRECTION_DUPLICATE"
            if float(np.linalg.norm(directions[i] - directions[j])) <= 1e-9:
                return False, "ZERO_SUPPORT_BASELINE"
    return True, "PASS"


def select_target_sets(pool, baseline_ids, mandatory_ids):
    """Call the SHA-locked T10 and T11 blocks independently on one FIT pool."""
    from .selection import select_views

    if not pool:
        raise ValueError("EMPTY_ADMITTED_FIT_POOL")
    cap = min(8, len(pool))
    return {
        "T10": select_views(pool, strategy="quality_diversity", max_views=cap,
                            baseline_ids=baseline_ids),
        "T11": select_views(pool, strategy="direction_quota", max_views=cap,
                            mandatory_ids=mandatory_ids),
    }
