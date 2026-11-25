"""Behavioral boundaries for the M2F9 correction of the existing V6 route."""
import json
import hashlib
import ast
import types
from pathlib import Path

import cv2
import numpy as np
import pytest
import pandas as pd

from tools import m2f8_v6_general as route


def _prepared(tmp_path, monkeypatch):
    group = 'GP_Ip_8.8mm_closed_R5_single_refY'
    video = '004'
    base = tmp_path / 'm2f9'
    inputs = base / 'current_inputs'
    prepared = inputs / 'prepared' / f'{group}_{video}'
    prepared.mkdir(parents=True)
    clean_root = inputs / 'clean_labels' / f'{group}_{video}'
    clean_root.mkdir(parents=True)
    view = f'{group}_{video}-raw00123'
    rgb = np.full((360, 640, 3), 90, np.uint8)
    raw = np.zeros((360, 640), np.uint8)
    raw[40:60, 50:70] = 2
    clean = raw.copy()
    clean[50:55, 55:60] = 0
    K = np.array([[490., 0, 319.5], [0, 490., 179.5], [0, 0, 1.]])
    cache = prepared / f'{view}.npz'
    clean_file = clean_root / f'{view}.npz'
    np.savez_compressed(cache, RGB=rgb, labels=raw, K=K)
    np.savez_compressed(clean_file, labels=clean)
    raw_video = tmp_path / f'{group}_{video}.mp4'
    raw_video.write_bytes(b'raw-fixture')
    candidate_file = prepared / 'CANDIDATE_MANIFEST.json'
    candidate_file.write_text(json.dumps({'candidates': [{
        'view': view, 'cache_sha256': route.h(cache),
        'clean_labels_sha256': route.h(clean_file),
        'RGB_sha256': hashlib.sha256(rgb.tobytes()).hexdigest(),
        'clean_mask_sha256': hashlib.sha256(clean.tobytes()).hexdigest(),
        'K_sha256': hashlib.sha256(K.tobytes()).hexdigest()}]}))
    meta = {'views': [{'view': view, 'raw_frame': 123, 'cache': str(cache),
                       'clean_labels': str(clean_file), 'clean_labels_sha256': route.h(clean_file)}],
            'video_path': str(raw_video), 'video_sha256': route.h(raw_video),
            'candidate_manifest': str(candidate_file),
            'candidate_manifest_sha256': route.h(candidate_file), 'K': K.tolist()}
    (prepared / 'PREPARED.json').write_text(json.dumps(meta))
    monkeypatch.setattr(route, 'BASE', base)
    monkeypatch.setattr(route, 'INP', inputs)
    return group, video, prepared, clean, K


def test_prep_input_uses_clean_mask_and_preserves_real_frame(tmp_path, monkeypatch):
    group, video, prepared, clean, K = _prepared(tmp_path, monkeypatch)
    run, rows, reference, heldout = route.prep_input(group, video, prepared)
    ledger = json.loads((run / 'inputs/ledger005.json').read_text())
    assert rows == ledger
    assert ledger[0]['raw_frame'] == 123
    assert ledger[0]['source_raw_frame'] == 123
    assert np.array_equal(cv2.imread(ledger[0]['Mask_path'], 0), clean)
    assert np.array_equal(np.asarray(ledger[0]['K']), K)
    assert ledger[0]['Mask_SHA256'] == route.h(ledger[0]['Mask_path'])
    assert reference == heldout == 0


def test_prep_input_rejects_stale_clean_mask(tmp_path, monkeypatch):
    group, video, prepared, _, _ = _prepared(tmp_path, monkeypatch)
    meta = json.loads((prepared / 'PREPARED.json').read_text())
    candidate = Path(meta['candidate_manifest'])
    d = json.loads(candidate.read_text())
    d['candidates'][0]['clean_labels_sha256'] = 'bad-hash'
    candidate.write_text(json.dumps(d))
    meta['candidate_manifest_sha256'] = route.h(candidate)
    (prepared / 'PREPARED.json').write_text(json.dumps(meta))
    with pytest.raises(ValueError, match='CLEAN_LABEL_HASH'):
        route.prep_input(group, video, prepared)


def test_ring_status_lookup_uses_full_observation_identity():
    rows = [
        {'source': 'G_R5_004-raw00123', 'geometry': {'centerline': {'major_radius': 60}}},
        {'source': 'G_R5_004-raw00234', 'geometry': {'centerline': {'major_radius': 52}}},
    ]
    by_id = route.ring_status_by_id(rows)
    assert by_id['G_R5_004-raw00123']['geometry']['centerline']['major_radius'] == 60
    assert by_id['G_R5_004-raw00234']['geometry']['centerline']['major_radius'] == 52
    with pytest.raises(ValueError, match='DUPLICATE_RING_OBSERVATION'):
        route.ring_status_by_id(rows + rows[:1])


def test_r5_r10_projection_uses_same_authoritative_torus_formula():
    from scipy.spatial.transform import Rotation
    pose = np.eye(4)
    pose[:3, :3] = Rotation.from_euler('x', 25, degrees=True).as_matrix()
    pose[:3, 3] = [0.5, -0.25, 35.]
    mods10 = route.source_modules(5.6)
    g5 = mods10['g5']
    expected10 = g5.contours(pose[:3, 3], pose[:3, :3], g5.K, R=5.6, r=.6, n=256)
    assert np.allclose(g5.contour_project(pose), expected10, rtol=0, atol=1e-12)
    mods5 = route.source_modules(3.1)
    expected5 = g5.contours(pose[:3, 3], pose[:3, :3], g5.K, R=3.1, r=.6, n=256)
    assert np.allclose(mods5['g5'].contour_project(pose), expected5, rtol=0, atol=1e-12)
    assert not np.allclose(expected5, expected10)


@pytest.mark.parametrize('source,expected', [
    ('local_ring_sfm.py', {'reference': 1, 'heldout': 0}),
    ('validate_select.py', {'reference': 1, 'heldout': 1}),
    ('select_supported_views.py', {'reference': 1, 'heldout': 1}),
])
def test_reference_adapter_replaces_only_protocol_lookups(source, expected):
    tree, receipt = route.adapt_reference_lookups(route.V6S / source, 3, 8, expected)
    assert receipt['replacements'] == expected
    assert receipt['source_sha256'] == route.h(route.V6S / source)
    assert '_M2F9_REFERENCE_INDEX' in ast.dump(tree)
    assert not any(isinstance(node, ast.Compare) and
                   any(isinstance(x, ast.Constant) and x.value in (459, 516)
                       for x in node.comparators) for node in ast.walk(tree))
    assert (route.V6S / source).is_file()


def test_reference_adapter_rejects_unknown_source_contract(tmp_path):
    source = tmp_path / 'changed.py'
    source.write_text('ref = 459\n')
    with pytest.raises(ValueError, match='REFERENCE_LOOKUP_CONTRACT'):
        route.adapt_reference_lookups(source, 0, 1, {'reference': 1, 'heldout': 0})


def test_run_state_refuses_changed_source_and_output(tmp_path):
    source = tmp_path / 'raw.mp4'
    source.write_bytes(b'raw')
    output = tmp_path / 'prepared.json'
    output.write_text('{"frames":4}')
    state = route.new_run_state('M2F9-G-004-20261125-ABCD', 'code-sha', 'config-sha', source)
    route.record_stage(state, 'prepare', source, output)
    route.verify_run_state(state, 'M2F9-G-004-20261125-ABCD', 'code-sha', 'config-sha')
    output.write_text('{"frames":5}')
    with pytest.raises(ValueError, match='OUTPUT_SHA_MISMATCH'):
        route.verify_run_state(state, 'M2F9-G-004-20261125-ABCD', 'code-sha', 'config-sha')
    output.write_text('{"frames":4}')
    source.write_bytes(b'changed')
    with pytest.raises(ValueError, match='RAW_SHA_MISMATCH'):
        route.verify_run_state(state, 'M2F9-G-004-20261125-ABCD', 'code-sha', 'config-sha')


def test_status_distinguishes_raw_hero_and_missing_mesh_prerequisites(tmp_path):
    root = tmp_path / 'video'
    for d in ('raw', 'inputs', 'predictions', 'meshes'):
        (root / d).mkdir(parents=True)
    (root / 'inputs/MVS_cases.json').write_text(json.dumps([{'tag': 'target'}]))
    (root / 'raw/target.npz').write_bytes(b'native-depth')
    status = route.classify_outputs(root, {'target': 'MODEL_PREDICTED'})
    assert status['target']['status'] == 'RAW_HERO'
    assert status['target']['mesh_state'] == 'MISSING_MESH_PREREQUISITE'
    (root / 'predictions/target_surface.npz').write_bytes(b'surface')
    (root / 'meshes/target_Polyp.ply').write_bytes(b'ply')
    status = route.classify_outputs(root, {'target': 'VALIDATED'})
    assert status['target']['status'] == 'PACKAGED_MESH'
    (root / 'raw/target.npz').unlink()
    status = route.classify_outputs(root, {'target': 'MODEL_PREDICTED'})
    assert status['target']['status'] == 'NOT_EVALUABLE'


def test_v6_reference_uses_current_ring_and_graph_without_aliasing_frames():
    rows = [{'raw_frame': x, 'id': str(x)} for x in (20, 459, 700, 920)]
    rings = [{'candidates': [{'loss': x}]} for x in (.5, .1, .3, .4)]
    edges = [{'i': i, 'j': j, 'rows': np.zeros((n, 5))}
             for i, j, n in ((0, 1, 30), (0, 2, 25), (0, 3, 20), (1, 2, 12))]
    reference, heldout, receipt = route.select_v6_reference(rows, rings, edges, [40] * 4)
    assert reference == 0
    assert heldout == 3
    assert receipt['selected_raw_frame'] == 20
    assert receipt['heldout_raw_frame'] == 920
    assert [r['raw_frame'] for r in rows] == [20, 459, 700, 920]


def test_adapted_main_executes_original_body_with_explicit_index(tmp_path):
    source = tmp_path / 'v6.py'
    source.write_text("def main():\n"
                      "    L = ledger()\n"
                      "    return next(i for i,a in enumerate(L) if a['raw_frame']==459)\n")
    module = types.ModuleType('v6_test')
    rows = [{'raw_frame': 100}, {'raw_frame': 459}, {'raw_frame': 700}]
    module.ledger = lambda: rows
    receipt = route.invoke_adapted_v6(module, source, 0, 2,
                                       {'reference': 1, 'heldout': 0})
    assert module.main() == 0
    assert rows[1]['raw_frame'] == 459
    assert receipt['source_sha256'] == route.h(source)


def test_raw_video_enumeration_does_not_consult_prepared_cache(tmp_path):
    raw = tmp_path / 'raw'
    raw.mkdir()
    group = 'GP_Ip_8.8mm_closed_R5_single_refY'
    source = raw / f'{group}_004.mp4'
    source.write_bytes(b'raw')
    selected = route.raw_video_paths(raw, group, {'004', '005'})
    assert selected == [source]


def test_native_depth_metric_uses_unscreened_raw_depth_and_native_k():
    import open3d as o3d
    vertices = np.array([[-10., -10., 10.], [20., -10., 10.],
                         [20., 20., 10.], [-10., 20., 10.]], np.float32)
    faces = np.array([[0, 1, 2], [0, 2, 3]], np.uint32)
    scene = o3d.t.geometry.RaycastingScene(nthreads=1)
    scene.add_triangles(o3d.core.Tensor(vertices), o3d.core.Tensor(faces))
    depth = np.full((2, 2), 10., np.float32)
    labels = np.array([[2, 2], [1, 0]], np.uint8)
    pose = np.eye(4)
    result = route.native_depth_metrics(depth, np.eye(3), pose, labels, scene)
    assert result['ring_pixels'] == 2
    assert result['ring_ratio_median'] == pytest.approx(1., abs=1e-6)
    assert result['ring_mae_mm'] == pytest.approx(0., abs=1e-6)
    assert result['polyp_centroid_mm'] == pytest.approx([0., 10., 10.])


def test_native_summary_keeps_video_and_group_denominators_distinct():
    targets = pd.DataFrame([
        dict(group_id='G',video_id='004',tag='a',raw_sha256='sha-a',
             execution_status='PACKAGED_MESH',camera_status='VALIDATED',ring_ratio_median=1.0,ring_mae_mm=.5),
        dict(group_id='G',video_id='004',tag='b',raw_sha256='sha-b',
             execution_status='RAW_HERO',camera_status='MODEL_PREDICTED',ring_ratio_median=.8,ring_mae_mm=5.),
        dict(group_id='G',video_id='005',tag='c',raw_sha256='sha-c',
             execution_status='RAW_HERO',camera_status='MODEL_PREDICTED',ring_ratio_median=.9,ring_mae_mm=3.),
    ])
    videos, groups = route.summarize_native_metrics(targets)
    assert len(videos) == 2 and len(groups) == 1
    v4 = videos.set_index('video_id').loc['004']
    v5 = videos.set_index('video_id').loc['005']
    assert v4['raw_count'] == 2 and v5['raw_count'] == 1
    assert v4['unfiltered_ratio_median'] == pytest.approx(.9)
    assert v4['packaged_ratio_median'] == pytest.approx(1.)
    assert pd.isna(v5['packaged_ratio_median'])
    assert groups.iloc[0]['raw_count'] == 3


def test_support_shortage_is_not_an_inference_exception(tmp_path):
    root = tmp_path / 'video'
    for d in ('inputs', 'metrics'):(root / d).mkdir(parents=True)
    (root / 'inputs/MVS_supported_cases.json').write_text(json.dumps([{'tag':'short'}]))
    (root / 'metrics/MVS005_supported_runs.json').write_text(json.dumps([{
        'tag':'short','success':False,'failure':'RuntimeError: fewer than three supported source cameras'}]))
    result = route.classify_outputs(root, {'short':'MODEL_PREDICTED'})['short']
    assert result['status'] == 'NOT_EVALUABLE'
    assert result['reason'] == 'SUPPORT_INSUFFICIENT'
