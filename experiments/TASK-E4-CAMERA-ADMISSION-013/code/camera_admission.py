"""Unified camera admission gate (one implementation for every group / video)."""
import json
from pathlib import Path
import numpy as np
import yaml

STATUSES = ('ACCEPT', 'QUARANTINE', 'REJECT', 'INSUFFICIENT_EVIDENCE')
POLICY_PATH = Path('/home/liu/ring_first_3d_workspace/experiments/TASK-E4-CAMERA-ADMISSION-013/policy/CAMERA_ADMISSION_POLICY.yaml')


def load_policy(path=POLICY_PATH):
    return yaml.safe_load(Path(path).read_text())


def classify(m, pol):
    """m: dict of measured metrics. Returns (status, reasons, hard_fail)."""
    hard, soft = [], []
    r, g = pol['ring'], pol['rgb']
    if m.get('pose_valid') is False:
        hard.append('NONFINITE_OR_NONRIGID_POSE')
    if m.get('cad_valid') is False:
        hard.append('CAD_PROJECTION_INVALID')
    pos = m.get('positive_depth')
    if pos is not None and pos < pol['hard_fail']['positive_depth_min']:
        hard.append(f'SIGN_FLIP_POSITIVE_DEPTH={pos:.2f}')
    if hard:
        return 'REJECT', hard, True
    if m.get('ring_raw_mae') is not None and m['ring_raw_mae'] > r['raw_mae_max_px']:
        soft.append(f'RING_RAW_MAE={m["ring_raw_mae"]:.2f}>{r["raw_mae_max_px"]}')
    n = m.get('held_n') or 0
    if n < g['min_tracks']:
        return 'INSUFFICIENT_EVIDENCE', soft + [f'HELD_TRACKS={n}<{g["min_tracks"]}'], False
    if m.get('held_median') is not None and m['held_median'] > g['held_median_max_px']:
        soft.append(f'HELD_MEDIAN={m["held_median"]:.2f}>{g["held_median_max_px"]}')
    if m.get('held_p95') is not None and m['held_p95'] > g['held_p95_max_px']:
        soft.append(f'HELD_P95={m["held_p95"]:.2f}>{g["held_p95_max_px"]}')
    if pos is not None and pos < g['positive_depth_min']:
        soft.append(f'POSITIVE_DEPTH={pos:.2f}<{g["positive_depth_min"]}')
    frac = m.get('big_error_fraction')
    if frac is not None and frac > g['big_error_fraction_max']:
        soft.append(f'BIG_ERROR_FRACTION={frac:.2f}>{g["big_error_fraction_max"]}')
    if m.get('center_jump_mm') is not None and m['center_jump_mm'] > pol['neighbour']['max_center_jump_mm']:
        soft.append(f'CENTER_JUMP={m["center_jump_mm"]:.1f}mm')
    if m.get('rotation_jump_deg') is not None and m['rotation_jump_deg'] > pol['neighbour']['max_rotation_jump_deg']:
        soft.append(f'ROTATION_JUMP={m["rotation_jump_deg"]:.1f}deg')
    if not soft:
        return 'ACCEPT', [], False
    # a single isolated-track artefact must not condemn the view
    if frac is not None and frac <= g['big_error_fraction_max'] and m.get('held_median', 9e9) <= g['held_median_max_px']:
        return 'QUARANTINE', soft + ['ISOLATED_TRACKS_EXPLAIN_FAILURE'], False
    return 'QUARANTINE', soft, False


def diagnose_once(m, pol, artefact):
    """One targeted diagnostic: if the failure is explained by degenerate / isolated tracks -> ACCEPT."""
    if artefact in ('DEGENERATE_TRIANGULATION', 'ISOLATED_TRACKS'):
        m2 = dict(m)
        m2.pop('held_p95', None)
        if (m2.get('held_median') or 0) <= pol['rgb']['held_median_max_px'] and \
           (m2.get('ring_raw_mae') or 0) <= pol['ring']['raw_mae_max_px']:
            return 'ACCEPT', dict(m, artefact=artefact)
    return 'REJECT', dict(m, artefact=artefact)


def summarise(rows):
    out = {}
    for s in STATUSES:
        out[s] = int(sum(1 for r in rows if r['status'] == s))
    return out
