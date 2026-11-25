"""Behavioral contracts for the single M2F10 V6 route."""
import ast
import json
from pathlib import Path

import numpy as np
import pytest

from tools import m2f8_v6_general as route


def test_target_schedule_uses_all_real_cameras_and_diverse_directions():
    poses = np.repeat(np.eye(4)[None], 5, axis=0)
    poses[:, :3, 3] = [[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1]]
    order = route.diverse_target_order(poses, np.zeros(3), reference=0, heldout=4)
    assert order[0] == 0
    assert order[1] == 1  # V6's farthest direction from the current reference
    assert sorted(order) == [0, 1, 2, 3]
    assert len(order) == len(set(order))


def test_original_support_rank_yields_at_most_three_distinct_tuples():
    rows = [{'id': f'video-raw{x:05d}', 'raw_frame': x} for x in range(6)]
    original = [dict(tag='005_supported_ref00000', reference=0, reference_id=rows[0]['id'], sources=[1, 2, 3],
                     source_ids=[rows[i]['id'] for i in (1, 2, 3)],
                     source_diagnostics=[dict(i=i, overlap=100 - i, angle=20 - i) for i in (1, 2, 3, 4)],
                     independent_image_heldout=5, scope='LOCAL005_GEOMETRY_SCREENED_STILL_NO_GT')]
    cases, receipt = route.schedule_supported_tuples(original, rows,
                                                     validated_indices={1, 2, 3, 4}, heldout=5)
    assert len(cases) == 3
    assert len({tuple(c['sources']) for c in cases}) == 3
    assert {c['reference_id'] for c in cases} == {rows[0]['id']}
    assert all(len(c['sources']) == 3 and set(c['sources']) <= {1, 2, 3, 4} for c in cases)
    assert receipt[0]['candidate_support_tuples'] == 3
    assert cases[0]['sources'] == [1, 2, 3]


def test_support_schedule_rejects_source_not_validated_or_overlap_below_v6_limit():
    rows = [{'id': f'v{i}', 'raw_frame': i} for i in range(5)]
    original = [dict(tag='005_supported_ref00000', reference=0, reference_id='v0', sources=[1, 2, 3],
                     source_diagnostics=[dict(i=1, overlap=20, angle=1),
                                         dict(i=2, overlap=14, angle=10),
                                         dict(i=3, overlap=30, angle=10)],
                     independent_image_heldout=4, scope='LOCAL005_GEOMETRY_SCREENED_STILL_NO_GT')]
    with pytest.raises(ValueError, match='V6_SUPPORT_SOURCE_CONTRACT'):
        route.schedule_supported_tuples(original, rows, validated_indices={1, 2, 3}, heldout=4)


def test_supported_selection_adapter_only_expands_target_iterable():
    tree, receipt = route.adapt_all_supported_targets(route.V6S / 'select_supported_views.py',
                                                       reference=0, heldout=5, targets=[0, 3, 1])
    loops = [node for node in ast.walk(tree) if isinstance(node, ast.For) and
             isinstance(node.target, ast.Name) and node.target.id == 'rr']
    assert len(loops) == 1
    assert isinstance(loops[0].iter, ast.Name) and loops[0].iter.id == '_M2F10_TARGET_INDICES'
    assert receipt['source_sha256'] == route.h(route.V6S / 'select_supported_views.py')
    assert receipt['targets'] == [0, 3, 1]
    assert 'min(x[\'angle\'], 25)' in ast.unparse(tree)


def test_supported_hero_adapter_skips_alternatives_after_first_success():
    tree, receipt = route.adapt_supported_hero_schedule(route.V6S / 'run_mvs005_supported.py')
    assert receipt['source_sha256'] == route.h(route.V6S / 'run_mvs005_supported.py')
    source = ast.unparse(tree)
    assert 'ALTERNATE_NOT_NEEDED' in source
    assert '_M2F10_TUPLE_RECEIPT(c)' in source
    assert 'wrapper.preprocess_and_run' in source  # frozen inference body still called
    assert 'if len(c[\'sources\']) != 3' in source


def test_packaging_adapter_keeps_per_case_geometry_and_removes_two_case_tail():
    tree, receipt = route.adapt_independent_package(route.V6S / 'package_surfaces.py')
    assert receipt['source_sha256'] == route.h(route.V6S / 'package_surfaces.py')
    source = ast.unparse(tree)
    assert "cases = load('inputs/MVS_supported_cases.json')" in source
    assert "runs = load('metrics/MVS005_supported_runs.json')" in source
    assert 'depth_mesh(' in source
    assert 'topology(' in source
    assert 'within005_surface_overlap' not in source
    assert "save('metrics/surfaces005.json', records)" in source


def test_formal_accepted_surface_requires_successful_supported_case(tmp_path):
    root = tmp_path / 'video'
    for d in ('inputs', 'metrics', 'raw', 'predictions', 'meshes'):
        (root / d).mkdir(parents=True)
    preview = {'tag': 'preview', 'reference': 0, 'reference_id': 'v0', 'sources': [1, 2, 3]}
    support = {'tag': 'supported', 'reference': 0, 'reference_id': 'v0', 'sources': [1, 2, 3],
               'source_diagnostics': [dict(i=i, overlap=20, angle=10) for i in (1, 2, 3)]}
    (root / 'inputs/MVS_cases.json').write_text(json.dumps([preview]))
    (root / 'inputs/MVS_supported_cases.json').write_text(json.dumps([support]))
    (root / 'metrics/local_validation.json').write_text(json.dumps({
        'primary': 0, 'versions': [{'version': 0, 'per_frame': [
            {'status': 'MODEL_PREDICTED'}, *[{'status': 'VALIDATED'} for _ in (1, 2, 3)]]}]}))
    for tag in ('preview', 'supported'):
        (root / 'raw' / f'{tag}.npz').write_bytes(b'native')
        (root / 'predictions' / f'{tag}_surface.npz').write_bytes(b'surface')
        (root / 'meshes' / f'{tag}_Polyp.ply').write_bytes(b'mesh')
    (root / 'metrics/MVS005_supported_runs.json').write_text(json.dumps([
        {'tag': 'supported', 'reference': 'v0', 'success': False, 'failure': 'model failed'}]))
    assert route.accepted_independent_targets(root) == set()
    runs = [{'tag': 'supported', 'reference': 'v0', 'success': True}]
    (root / 'metrics/MVS005_supported_runs.json').write_text(json.dumps(runs))
    assert route.accepted_independent_targets(root) == {'v0'}


def test_skipped_support_alternative_is_not_an_execution_error(tmp_path):
    root = tmp_path / 'video'
    (root / 'inputs').mkdir(parents=True)
    (root / 'metrics').mkdir()
    (root / 'inputs/MVS_supported_cases.json').write_text(json.dumps([{'tag': 't_alt2'}]))
    (root / 'metrics/MVS005_supported_runs.json').write_text(json.dumps([
        {'tag': 't_alt2', 'success': False, 'failure': 'ALTERNATE_NOT_NEEDED'}]))
    status = route.classify_outputs(root, {'t_alt2': 'MODEL_PREDICTED'})['t_alt2']
    assert status['status'] == 'NOT_EVALUABLE'
    assert status['reason'] == 'ALTERNATE_NOT_NEEDED'


def test_supplemented_preparation_recomputes_raw_candidates_and_keeps_four_real_frames(tmp_path, monkeypatch):
    import sys
    import types
    from tools import m2f5_unified as prep

    source = tmp_path / 'G_004.mp4'
    source.write_bytes(b'current-raw-video')
    visited = []

    class FakeVideo:
        def get(self, _):
            return 120
        def release(self):
            pass

    monkeypatch.setattr(prep.cv2, 'VideoCapture', lambda _: FakeVideo())
    monkeypatch.setattr(prep, 'candidate_frames', lambda _: [20, 40, 60, 80])
    monkeypatch.setattr(prep, 'trace', lambda *a, **k: None)

    def prepare_candidate(group, video, path, frame, root, cleaner):
        visited.append((str(prep.O), frame))
        view = f'{group}_{video}-raw{frame:05d}'
        record = dict(view=view, frame=frame, raw_frame=frame, cache=str(root / f'{view}.npz'),
                      clean_labels=str(prep.O / 'clean_labels' / f'{view}.npz'),
                      RGB_sha256=str(frame), clean_mask_sha256=str(frame),
                      K_sha256=str(frame), cache_sha256=str(frame), clean_labels_sha256=str(frame),
                      ring_train_points=30, quality=1., proxy=[float(frame)], label_counts={})
        return record, dict(id=view, cache=record['cache']), dict(frame=frame)

    monkeypatch.setattr(prep, 'prepare_real_candidate', prepare_candidate)
    monkeypatch.setattr(prep, 'select_observations', lambda rows, edges: (rows[::2], {'edge_count': 3}))
    monkeypatch.setitem(sys.modules, 'features019', types.SimpleNamespace(
        R=None, matches=lambda a, b: {'RGB_RANSAC': np.ones(20, dtype=bool)}))

    prep.O = tmp_path / 'attempt0'
    first, _, first_meta = prep.prepare_one_m2f6('G', source)
    assert [v['raw_frame'] for v in first_meta['views']] == [20, 60]
    prep.O = tmp_path / 'attempt1'
    second, _, second_meta = prep.prepare_one_m2f6('G', source, supplement_frames=[40, 80])
    assert first != second
    assert [v['raw_frame'] for v in second_meta['views']] == [20, 40, 60, 80]
    assert visited == [(str(tmp_path / f'attempt{attempt}'), frame)
                       for attempt in (0, 1) for frame in (20, 40, 60, 80)]


def test_supplemented_preparation_rejects_more_than_four_extra_frames():
    from tools import m2f5_unified as prep
    with pytest.raises(ValueError, match='SUPPLEMENT_BUDGET'):
        prep.prepare_one_m2f6('G', Path('/does/not/matter.mp4'), supplement_frames=[1, 2, 3, 4, 5])


def test_real_supplement_selection_uses_current_candidate_graph_and_four_frame_budget(tmp_path, monkeypatch):
    base = tmp_path / 'attempt0'
    prepared = base / 'current_inputs/prepared/G_004'
    prepared.mkdir(parents=True)
    matches = base / 'current_inputs/observation_matches/G_004/clean_cache'
    matches.mkdir(parents=True)
    rows = []
    for frame in (20, 40, 60, 80, 100, 120, 140):
        view = f'G_004-raw{frame:05d}'
        (matches / f'{view}.npz').write_bytes(b'current-clean-' + str(frame).encode())
        rows.append(dict(view=view, frame=frame, raw_frame=frame, quality=float(frame),
                         proxy=[frame / 140], ring_train_points=30, RGB_sha256=str(frame)))
    manifest = prepared / 'CANDIDATE_MANIFEST.json'
    manifest.write_text(json.dumps({'candidates': rows}))
    (prepared / 'PREPARED.json').write_text(json.dumps({
        'group': 'G', 'video_id': '004', 'candidate_manifest': str(manifest),
        'candidate_manifest_sha256': route.h(manifest),
        'views': [{'view': rows[0]['view']}, {'view': rows[1]['view']}]}))
    monkeypatch.setattr(route, 'INP', base / 'current_inputs')
    calls = []

    def match(a, b):
        calls.append((a['id'], b['id']))
        return {'RGB_RANSAC': np.ones(20, dtype=bool)}

    frames, receipt = route.select_current_real_supplements(prepared, base / 'v6/G_004',
                                                             'SUPPORT_INSUFFICIENT', matcher=match)
    assert 0 < len(frames) <= 4
    assert set(frames) <= {60, 80, 100, 120, 140}
    assert receipt['added_raw_frames'] == frames
    assert calls and all(a not in {rows[0]['view'], rows[1]['view']} for a, _ in calls)
