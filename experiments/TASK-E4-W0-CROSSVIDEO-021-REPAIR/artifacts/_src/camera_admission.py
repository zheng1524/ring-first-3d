"""Unified camera admission gate (v2: SO(3) aware, no diagnostic bypass, full-field checks)."""
from pathlib import Path
import yaml

STATUSES = ('ACCEPT', 'QUARANTINE', 'REJECT', 'INSUFFICIENT_EVIDENCE')
POLICY_PATH = Path('/home/liu/ring_first_3d_workspace/camera_mainline/CAMERA_ADMISSION_POLICY.yaml')
REQUIRED = ('pose_valid', 'cad_valid', 'ring_raw_mae', 'held_n', 'held_median', 'held_p95', 'positive_depth')


def load_policy(path=POLICY_PATH):
    return yaml.safe_load(Path(path).read_text())


def _finite(x):
    try:
        return x is not None and float(x) == float(x) and abs(float(x)) != float('inf')
    except Exception:
        return False


def classify(m, pol):
    """ACCEPT iff EvidenceComplete & PoseValid & CADValid & QualityPass. Returns (status, reasons)."""
    missing = [k for k in REQUIRED if m.get(k) is None]
    if missing:
        return 'INSUFFICIENT_EVIDENCE', ['MISSING_FIELD:' + ','.join(missing)]
    bad = [k for k in ('ring_raw_mae', 'held_median', 'held_p95', 'positive_depth') if not _finite(m[k])]
    if bad:
        return 'INSUFFICIENT_EVIDENCE', ['NONFINITE_METRIC:' + ','.join(bad)]

    r, g = pol['ring'], pol['rgb']
    hard = []
    if m['pose_valid'] is not True:
        hard.append('POSE_INVALID')
    if m['cad_valid'] is not True:
        hard.append('CAD_PROJECTION_INVALID')
    if m['positive_depth'] < pol['hard_fail']['positive_depth_min']:
        hard.append(f'SIGN_FLIP_POSITIVE_DEPTH={m["positive_depth"]:.2f}')
    if hard:
        return 'REJECT', hard

    soft = []
    if m['ring_raw_mae'] > r['raw_mae_max_px']:
        soft.append(f'RING_RAW_MAE={m["ring_raw_mae"]:.2f}>{r["raw_mae_max_px"]}')
    if m['held_n'] < g['min_tracks']:
        return 'INSUFFICIENT_EVIDENCE', soft + [f'HELD_TRACKS={m["held_n"]}<{g["min_tracks"]}']
    if m['held_median'] > g['held_median_max_px']:
        soft.append(f'HELD_MEDIAN={m["held_median"]:.2f}>{g["held_median_max_px"]}')
    if m['held_p95'] > g['held_p95_max_px']:
        soft.append(f'HELD_P95={m["held_p95"]:.2f}>{g["held_p95_max_px"]}')
    if m['positive_depth'] < g['positive_depth_min']:
        soft.append(f'POSITIVE_DEPTH={m["positive_depth"]:.2f}<{g["positive_depth_min"]}')
    frac = m.get('big_error_fraction')
    if frac is not None and frac > g['big_error_fraction_max']:
        soft.append(f'BIG_ERROR_FRACTION={frac:.2f}>{g["big_error_fraction_max"]}')
    nb = pol['neighbour']
    if m.get('rotation_to_previous_deg') is not None and m['rotation_to_previous_deg'] > nb['max_rotation_jump_deg']:
        soft.append(f'ROTATION_TO_PREV={m["rotation_to_previous_deg"]:.1f}>{nb["max_rotation_jump_deg"]}')
    if m.get('center_to_previous_mm') is not None and m['center_to_previous_mm'] > nb['max_center_jump_mm']:
        soft.append(f'CENTER_TO_PREV={m["center_to_previous_mm"]:.1f}>{nb["max_center_jump_mm"]}')
    if not soft:
        return 'ACCEPT', []
    return 'QUARANTINE', soft


def apply_diagnostic(m, pol, artefact):
    """Diagnostics may only clear the failure they explain; caller MUST re-run classify."""
    if artefact == 'DEGENERATE_TRIANGULATION' and m.get('held_p95_valid') is not None:
        m2 = dict(m)
        m2['held_p95'] = m2['held_p95_valid']
        m2['held_median'] = m2['held_median_valid']
        return m2, ['TRIANGULATION_DIAGNOSTIC_APPLIED']
    return dict(m), ['NO_DIAGNOSTIC_APPLICABLE']


def decide(m, pol, artefact=None, max_rounds=1):
    """Full pipeline: classify -> (optional) diagnostic -> classify again. Returns dict."""
    trail = []
    s, why = classify(m, pol)
    trail.append(dict(stage='initial', status=s, reasons=why))
    if s == 'QUARANTINE' and artefact and max_rounds > 0:
        m2, why2 = apply_diagnostic(m, pol, artefact)
        s2, why3 = classify(m2, pol)
        trail.append(dict(stage='after_diagnostic', status=s2, reasons=why2 + why3))
        return dict(status=s2, reasons=why3, trail=trail, metrics=m2)
    return dict(status=s, reasons=why, trail=trail, metrics=m)


def summarise(rows):
    return {s: int(sum(1 for r in rows if r['status'] == s)) for s in STATUSES}
