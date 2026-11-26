"""Differences between frozen camera solutions; neither solution is GT."""

import numpy as np

from . import run
from .core import validate_frozen_similarity


UNITS = 'R_scale_normalized_units; R one unit = one mm; not independent S metric scale'


def _valid(pose):
    return pose is not None and np.shape(pose) == (4, 4) and np.isfinite(pose).all()


def _missing(reason):
    return dict(status='NOT_EVALUABLE', reason=reason, position_delta=None,
                position_norm=None, rotation_deg=None)


def pose_delta(a, b):
    """Compare two c2w poses; signed translation is B minus A in world axes."""
    if not _valid(a) or not _valid(b):
        return _missing('R_CAMERA_MISSING' if not _valid(a) else 'S_CAMERA_MISSING')
    a, b = np.asarray(a), np.asarray(b)
    delta = b[:3, 3] - a[:3, 3]
    cosine = (np.trace(a[:3, :3].T @ b[:3, :3]) - 1) / 2
    return dict(status='OK', reason='', position_delta=delta.tolist(),
                position_norm=float(np.linalg.norm(delta)),
                rotation_deg=float(np.rad2deg(np.arccos(np.clip(cosine, -1, 1)))))


def relative_pose_delta(targetR, supportR, targetS, supportS):
    """Compare inv(target c2w) @ support c2w, in each target's camera axes."""
    poses = [targetR, supportR, targetS, supportS]
    names = ['R_TARGET_CAMERA_MISSING', 'R_SUPPORT_CAMERA_MISSING',
             'S_TARGET_CAMERA_MISSING', 'S_SUPPORT_CAMERA_MISSING']
    reason = next((name for pose, name in zip(poses, names) if not _valid(pose)), '')
    if reason:
        return dict(_missing(reason), relative_R=None, relative_S=None,
                    baseline_R=None, baseline_S=None, translation_error_percent=None,
                    percentage_status='NOT_EVALUABLE', percentage_reason=reason)
    r = np.linalg.inv(targetR) @ supportR
    s = np.linalg.inv(targetS) @ supportS
    result = pose_delta(r, s)
    baseline_r = float(np.linalg.norm(r[:3, 3]))
    baseline_s = float(np.linalg.norm(s[:3, 3]))
    nonzero = baseline_r > 1e-12
    return dict(result, relative_R=r.tolist(), relative_S=s.tolist(),
                baseline_R=baseline_r, baseline_S=baseline_s,
                translation_error_percent=100 * result['position_norm'] / baseline_r if nonzero else None,
                percentage_status='OK' if nonzero else 'NOT_EVALUABLE',
                percentage_reason='' if nonzero else 'ZERO_R_BASELINE')


def summarize(rows, total=None):
    """Preserve all selected rows in denominators, including unavailable values."""
    total = len(rows) if total is None else total
    count = sum(row['status'] == 'OK' for row in rows)
    result = dict(status='EVALUABLE' if count else 'NOT_EVALUABLE', count=count, total=total)
    fields = ['position_norm', 'rotation_deg']
    if any('translation_error_percent' in row for row in rows):
        fields += ['baseline_R', 'baseline_S', 'translation_error_percent']
    for field in fields:
        values = np.array([row[field] for row in rows if row.get(field) is not None], dtype=float)
        values = values[np.isfinite(values)]
        result[field] = dict(count=len(values), total=total,
                             median=float(np.median(values)) if len(values) else None,
                             P95=float(np.quantile(values, .95)) if len(values) else None,
                             max=float(np.max(values)) if len(values) else None)
    result['reasons'] = {reason: sum(row.get('reason') == reason for row in rows)
                         for reason in {row.get('reason') for row in rows} if reason}
    return result


def _load_poses(path):
    if not path.exists():
        return None
    with np.load(path) as archive:
        return archive['c2w'].copy()


def _at(poses, index):
    return poses[index] if poses is not None and 0 <= index < len(poses) else None


def evaluate_pose(case):
    """Read and validate the existing alignment; write small comparison artifacts."""
    common = run.verify_common(case)
    root = run.BASE / case
    frames = run.read(common / 'meta.json')['frames']
    tuples = run.read(common / 'TUPLES_FROZEN.json')['tuples']
    paths = dict(R=root / 'R/cameras.npz', S=root / 'S/cameras.npz',
                 S_normalized=root / 'S/cameras_normalized.npz',
                 normalization=root / 'NORMALIZATION_FROZEN.json')
    r, s_raw, s = (_load_poses(paths[key]) for key in ['R', 'S', 'S_normalized'])
    normal = run.read(paths['normalization']) if paths['normalization'].exists() else dict(
        status='NOT_EVALUABLE', reason='NORMALIZATION_MISSING')
    missing_files = [key for key, path in paths.items() if not path.exists()]
    reason = ''
    if missing_files:
        reason = 'MISSING_FILES:' + ','.join(missing_files)
    elif normal.get('status') != 'FROZEN':
        reason = normal.get('reason') or 'NORMALIZATION_NOT_FROZEN'
    else:
        validate_frozen_similarity(normal, {a: run.sha(paths[a]) for a in ['R', 'S']}, s_raw, s)

    rgb_paths = {a: root / a / 'RGB_CHECKS.json' for a in ['R', 'S']}
    rgb = {a: {int(row['frame']) for row in run.read(path) if row['passed']} if path.exists() else set()
           for a, path in rgb_paths.items()}
    rgb_ids = rgb['R'] & rgb['S']
    hero_ids = {int(i) for t in tuples for i in [t['reference']] + t['sources']}
    # Membership remains frozen even when a pose or alignment is unavailable.
    rows = []
    for i, frame in enumerate(frames):
        delta = _missing(reason) if reason else pose_delta(_at(r, i), _at(s, i))
        rows.append(dict(delta, frame=i, frame_id=frame.get('id', i), raw_frame=frame['raw_frame'],
                         common_numeric=bool(_valid(_at(r, i)) and _valid(_at(s_raw, i))),
                         common_rgb_pass=i in rgb_ids, hero_frame=i in hero_ids))
    summary = {}
    for name, selected in [('all_common', rows),
                           ('common_rgb_pass', [row for row in rows if row['common_rgb_pass']]),
                           ('frozen_hero_union', [row for row in rows if row['hero_frame']])]:
        summary[name] = summarize(selected)
        summary[name]['frame_ids'] = [row['frame'] for row in selected
                                      if name != 'all_common' or row['common_numeric']]
    roles = []
    for index, t in enumerate(tuples):
        target = int(t['reference'])
        for slot, source in enumerate(t['sources']):
            source = int(source)
            if reason:
                delta = relative_pose_delta(None, None, None, None)
                delta.update(reason=reason, percentage_reason=reason)
            else:
                delta = relative_pose_delta(_at(r, target), _at(r, source), _at(s, target), _at(s, source))
            roles.append(dict(delta, tuple_index=index, tuple_tag=t.get('tag', f'B_target_{index}'),
                              support_slot=slot, target_frame=target, support_frame=source,
                              target_frame_id=frames[target].get('id', target),
                              support_frame_id=frames[source].get('id', source),
                              target_raw_frame=frames[target]['raw_frame'],
                              support_raw_frame=frames[source]['raw_frame']))
    role_summary = summarize(roles)
    provenance_paths = list(paths.values()) + list(rgb_paths.values()) + [
        common / 'INPUT_MANIFEST.json', common / 'meta.json', common / 'TUPLES_FROZEN.json']
    hashes = {str(path): run.sha(path) for path in provenance_paths if path.exists()}
    metadata = dict(case=case, not_GT=True, units=UNITS, source_hashes=hashes, evaluator_sha256=run.sha(__file__), execution_commit=run.route.head(),
                    interpretation='Symmetric inter-solution position and rotation differences; neither solution is GT. '
                    'Signed vectors use S minus R; percentage denominator is R baseline.',
                    position_delta_convention='S_minus_R', rotation_units='degrees')
    role_output = dict(metadata, status=role_summary['status'], total=len(roles), count=role_summary['count'],
                       relative_transform_convention='inverse(target_c2w) @ support_c2w',
                       per_role=roles, summary=role_summary)
    output = dict(metadata, status=summary['all_common']['status'], reason=reason,
                  normalization=normal, per_frame=rows, summary=summary,
                  role_pose_differences=role_output)
    run.save(root / 'ROLE_POSE_DIFFERENCES.json', role_output)
    run.save(root / 'POSE_DIFFERENCES.json', output)
    return output
