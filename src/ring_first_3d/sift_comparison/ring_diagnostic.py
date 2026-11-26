"""Frozen-camera observability diagnostics, never camera selection or fitting."""
from collections import Counter

import numpy as np
from scipy.spatial import cKDTree

SCALES = (.5, .75, 1., 1.25, 1.5)
CONTOUR_SAMPLES = 2048


def transform_global_similarity(poses, points, scale=1., rotation=None):
    """Transform c2w cameras and their points about the fixed Ring origin."""
    rotation = np.eye(3) if rotation is None else np.asarray(rotation, float)
    if not np.isfinite(scale) or scale <= 0:
        raise ValueError('NONPOSITIVE_SCALE')
    if (rotation.shape != (3, 3) or not np.isfinite(rotation).all()
            or not np.allclose(rotation.T @ rotation, np.eye(3), atol=1e-10)
            or not np.isclose(np.linalg.det(rotation), 1.)):
        raise ValueError('INVALID_GLOBAL_ROTATION')
    out = np.array(poses, dtype=float, copy=True)
    out[:, :3, :3] = rotation @ out[:, :3, :3]
    out[:, :3, 3] = scale * out[:, :3, 3] @ rotation.T
    return out, scale * np.asarray(points, float) @ rotation.T


def _camera_reason(pose):
    if np.shape(pose) != (4, 4) or not np.isfinite(pose).all():
        return 'CAMERA_MISSING_OR_NONFINITE'
    rotation = pose[:3, :3]
    if (not np.allclose(rotation.T @ rotation, np.eye(3), atol=1e-5)
            or not np.isclose(np.linalg.det(rotation), 1., atol=1e-5)):
        return 'INVALID_CAMERA_ROTATION'
    if not np.allclose(pose[3], [0, 0, 0, 1], atol=1e-8):
        return 'INVALID_CAMERA_HOMOGENEOUS_ROW'
    return ''


def ring_frame(pose, held, contours):
    """One-way held contour-to-authoritative-CAD nearest distance, pixels."""
    held = np.asarray(held, float).reshape(-1, 2)
    finite = held[np.isfinite(held).all(axis=1)]
    row = dict(status='NOT_EVALUABLE', reason='', held_points=len(held),
               finite_held_points=len(finite), residual_points=0, MAE_px=None,
               P95_px=None, max_px=None)
    reason = _camera_reason(pose)
    if not reason and not len(finite):
        reason = 'EMPTY_HELD_RING' if not len(held) else 'NO_FINITE_HELD_RING'
    if reason:
        row['reason'] = reason
        return row
    try:
        predicted = np.asarray(contours(pose, n=CONTOUR_SAMPLES), float).reshape(-1, 2)
        if not len(predicted):
            raise ValueError('EMPTY_RING_CONTOUR')
        if not np.isfinite(predicted).all():
            raise ValueError('NONFINITE_RING_CONTOUR')
        residual = cKDTree(predicted).query(finite)[0]
        row.update(status='EVALUABLE', residual_points=len(residual),
                   MAE_px=float(residual.mean()), P95_px=float(np.quantile(residual, .95)),
                   max_px=float(residual.max()))
    except (ValueError, AssertionError, np.linalg.LinAlgError, FloatingPointError) as error:
        row['reason'] = str(error) or type(error).__name__
    return row


def ring_summary(rows):
    valid = [row for row in rows if row['status'] == 'EVALUABLE']
    return dict(status='EVALUABLE' if valid else 'NOT_EVALUABLE',
                total_frames=len(rows), evaluable_frames=len(valid),
                held_points=sum(row['held_points'] for row in rows),
                finite_held_points=sum(row['finite_held_points'] for row in rows),
                residual_points=sum(row['residual_points'] for row in rows),
                median_frame_MAE_px=float(np.median([r['MAE_px'] for r in valid])) if valid else None,
                median_frame_P95_px=float(np.median([r['P95_px'] for r in valid])) if valid else None,
                reasons=dict(Counter(row['reason'] for row in rows if row['reason'])),
                per_frame=rows)


def projection_invariance(poses, points, changed_poses, changed_points, track_ids, xy, K, project):
    """Use the same saved training point and observed frame before/after."""
    differences, reasons, total = [], Counter(), 0
    for index, track in enumerate(track_ids):
        track = int(track)
        if track < 0 or track >= len(xy):
            raise ValueError('SAVED_POINT_TRACK_OUT_OF_RANGE')
        for frame in np.flatnonzero(np.isfinite(xy[track]).all(axis=1)):
            total += 1
            reason = _camera_reason(poses[frame]) or _camera_reason(changed_poses[frame])
            if reason:
                reasons[reason] += 1
                continue
            if not (np.isfinite(points[index]).all() and np.isfinite(changed_points[index]).all()):
                reasons['NONFINITE_SAVED_POINT'] += 1
                continue
            try:
                uv, z = project(points[index:index+1], poses[frame], K)
                other_uv, other_z = project(changed_points[index:index+1], changed_poses[frame], K)
                if not (np.isfinite(uv).all() and np.isfinite(other_uv).all()
                        and np.isfinite(z).all() and np.isfinite(other_z).all()):
                    raise ValueError('NONFINITE_PROJECTION')
                if np.min(z) <= 0 or np.min(other_z) <= 0:
                    raise ValueError('NONPOSITIVE_DEPTH')
                differences.append(float(np.linalg.norm(uv - other_uv)))
            except (ValueError, AssertionError, np.linalg.LinAlgError, FloatingPointError) as error:
                reasons[str(error) or type(error).__name__] += 1
    return dict(status='EVALUABLE' if differences else 'NOT_EVALUABLE',
                reason=('' if differences else 'NO_SAVED_TRAIN_POINTS' if not len(points)
                        else 'NO_OBSERVED_TRAIN_POINTS' if not total else 'NO_EVALUABLE_PROJECTIONS'),
                saved_points=len(points), total_observed_pairs=total,
                evaluable_observations=len(differences),
                max_change_px=max(differences) if differences else None, reasons=dict(reasons))


def diagnose_ring(case):
    """Write BASE/case/RING_DIAGNOSTIC.json from existing frozen artifacts only."""
    from . import run
    from .core import validate_frozen_similarity

    common = run.verify_common(case)
    root = run.BASE / case
    meta = run.read(common / 'meta.json')
    _, mods = run.kernels(root / 'R', meta)
    kernel = mods['v6']
    with np.load(common / 'tracks.npz') as archive:
        xy = archive['xy']
    training_ids = set(run.read(common / 'split.json')['train'])
    frames = meta['frames']; n = len(frames)
    observed, observation_reasons = [], []
    source_hashes = {str(common / name): run.sha(common / name)
                     for name in ['meta.json', 'tracks.npz', 'split.json']}
    for frame in frames:
        path = root / 'R/observations' / (frame['id'] + '_ring.npz')
        try:
            with np.load(path) as archive:
                held = np.asarray(archive['q_held'], float).reshape(-1, 2)
            observed.append(held); observation_reasons.append('')
            source_hashes[str(path)] = run.sha(path)
        except (OSError, KeyError, ValueError) as error:
            observed.append(np.empty((0, 2)))
            observation_reasons.append('HELD_RING_UNAVAILABLE: ' + type(error).__name__)
    rgb_ids, rgb_status = {}, {}
    for arm in ['R', 'S']:
        path = root / arm / 'RGB_CHECKS.json'
        if path.exists():
            rgb_ids[arm] = {int(r['frame']) for r in run.read(path) if r['passed']}
            rgb_status[arm] = 'AVAILABLE'; source_hashes[str(path)] = run.sha(path)
        else:
            rgb_ids[arm] = set(); rgb_status[arm] = 'RGB_CHECKS_MISSING'
    common_rgb = rgb_ids['R'] & rgb_ids['S'] & set(range(n))

    def evaluate_frames(poses, unavailable=''):
        rows = []
        for index, frame in enumerate(frames):
            row = ring_frame(poses[index], observed[index], kernel.contours)
            reason = unavailable or observation_reasons[index]
            if reason:
                row.update(status='NOT_EVALUABLE', reason=reason, residual_points=0,
                           MAE_px=None, P95_px=None, max_px=None)
            row.update(frame=index, frame_id=frame['id'], common_rgb_pass=index in common_rgb)
            rows.append(row)
        return ring_summary(rows)

    normalization_path = root / 'NORMALIZATION_FROZEN.json'
    normalization = run.read(normalization_path) if normalization_path.exists() else {
        'status': 'NOT_EVALUABLE', 'reason': 'NORMALIZATION_MISSING'}
    if normalization_path.exists():
        source_hashes[str(normalization_path)] = run.sha(normalization_path)
    arms = {}
    for arm in ['R', 'S']:
        reason = ''; camera_path = root / arm / ('cameras.npz' if arm == 'R' else 'cameras_normalized.npz')
        try:
            if arm == 'S' and normalization.get('status') != 'FROZEN':
                raise ValueError(normalization.get('reason', 'NORMALIZATION_NOT_FROZEN'))
            with np.load(camera_path) as archive:
                cam = dict(archive)
            source_hashes[str(camera_path)] = run.sha(camera_path)
            poses, points, ids, K = cam['c2w'], cam['points'], cam['point_track_ids'], cam['K']
            if poses.shape != (n, 4, 4) or points.shape != (len(ids), 3):
                raise ValueError('CAMERA_EXPORT_SHAPE_MISMATCH')
            if not set(map(int, ids)).issubset(training_ids):
                raise ValueError('SAVED_POINTS_NOT_ALL_TRAINING')
            if arm == 'S':
                hashes = {a: run.sha(root / a / 'cameras.npz') for a in ['R', 'S']}
                with np.load(root / 'S/cameras.npz') as original:
                    validate_frozen_similarity(normalization, hashes, original['c2w'], poses)
                    expected = (normalization['scale'] * original['points'] @
                                np.asarray(normalization['rotation']).T + normalization['translation'])
                    if (not np.array_equal(ids, original['point_track_ids']) or
                            not np.allclose(expected, points, rtol=0, atol=1e-12, equal_nan=True)):
                        raise ValueError('NORMALIZED_POINTS_DRIFT')
        except (OSError, KeyError, ValueError, AssertionError) as error:
            reason = str(error) or type(error).__name__
            poses = np.full((n, 4, 4), np.nan); points = np.empty((0, 3)); ids = np.array([], int); K = np.eye(3)
        nominal = evaluate_frames(poses, reason)

        def transformed_result(scale=1., rotation=None):
            changed, shifted = transform_global_similarity(poses, points, scale, rotation)
            invariant = projection_invariance(poses, points, changed, shifted, ids, xy, K, kernel.project)
            if reason:
                invariant.update(reason=reason)
            return dict(ring=evaluate_frames(changed, reason), rgb_invariance=invariant)

        sweep = [dict(scale=scale, **transformed_result(scale)) for scale in SCALES]
        angle = np.deg2rad(30.)
        rotation = np.array([[np.cos(angle), -np.sin(angle), 0.],
                             [np.sin(angle), np.cos(angle), 0.], [0., 0., 1.]])
        yaw = dict(degrees=30., **transformed_result(rotation=rotation))
        pairs = [(a, b) for a, b in zip(nominal['per_frame'], yaw['ring']['per_frame'])
                 if a['status'] == b['status'] == 'EVALUABLE']
        yaw['ring_residual_delta'] = dict(common_frames=len(pairs),
            max_abs_frame_MAE_change_px=max((abs(a['MAE_px']-b['MAE_px']) for a,b in pairs), default=None),
            max_abs_frame_P95_change_px=max((abs(a['P95_px']-b['P95_px']) for a,b in pairs), default=None))
        common_rows = [row for row in nominal['per_frame'] if row['common_rgb_pass']]
        evaluable = [row for row in common_rows if row['status'] == 'EVALUABLE']
        conflicts = [row['frame'] for row in evaluable if row['MAE_px'] > 3 or row['P95_px'] > 6]
        arms[arm] = dict(status=nominal['status'], reason=reason, nominal=nominal,
                        scale_sweep=sweep, yaw_control=yaw,
                        common_rgb_ring_conflict=dict(common_rgb_pass_frames=len(common_rgb),
                            evaluable_ring_frames=len(evaluable), conflict_frames=len(conflicts),
                            conflict_frame_ids=conflicts, not_evaluable_frames=len(common_rows)-len(evaluable),
                            criterion='held Ring MAE > 3 px OR P95 > 6 px; diagnostic only'))
    result = dict(schema_version=1, case=case, GT=False, total_frames=n, evaluator_sha256=run.sha(__file__), execution_commit=run.route.head(),
        status='EVALUABLE' if any(a['status']=='EVALUABLE' for a in arms.values()) else 'NOT_EVALUABLE',
        physical_groups=1, diagnostic_only=True, used_for_selection=False,
        ring_inner_mm=meta['ring_inner_mm'], ring_tube_radius_mm=.6,
        contour_samples=CONTOUR_SAMPLES, distance_definition='held contour to nearest projected CAD contour point',
        aggregation='median of per-frame MAE and median of per-frame P95; no pooled-point weighting',
        common_rgb_pass_ids=sorted(common_rgb), rgb_checks_status=rgb_status,
        normalization_status=normalization.get('status'), source_hashes=source_hashes, arms=arms,
        limitations=[
            'Known-size Ring adds metric scale and range/tilt information; it cannot prove full 6DoF pose correct.',
            'Axisymmetric Ring leaves absolute world yaw unresolved; 30 degree control has contour sampling error.',
            'Nominal scale 1 is not necessarily optimal or correct; this sweep never changes cameras, scale, HERO or selection.',
            'Ring held observations were historically used in earlier gates; this is not a new blind test.',
            'S uses the existing training-point whole-video normalization and is sensitive to that registration.',
            'RGB-pass/Ring-conflict can reflect pose, segmentation, intrinsics, CAD or occlusion; not a truth label or R win.'
        ])
    run.save(root / 'RING_DIAGNOSTIC.json', result)
    return result
