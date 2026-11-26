"""Independent SIFT-only COLMAP interchange; no Ring or R-arm inputs.

Public entry point: solve(common_dir, output_dir) -> receipt dictionary.
Only training observations and the original stored match edges enter COLMAP.
"""
from pathlib import Path
import hashlib
import json
import platform
import time
import traceback

import numpy as np
import pycolmap

K = np.array([[490., 0., 319.5], [0., 490., 179.5], [0., 0., 1.]])
SEED = 20261126


def _sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for data in iter(lambda: f.read(1024 * 1024), b''):
            h.update(data)
    return h.hexdigest()


def _jsonable(value):
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(v) for v in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _save(path, data):
    Path(path).write_text(json.dumps(_jsonable(data), indent=2, ensure_ascii=False))


def fixed_options():
    options = pycolmap.IncrementalPipelineOptions()
    options.num_threads = 2
    options.random_seed = SEED
    options.extract_colors = False
    options.ba_refine_focal_length = False
    options.ba_refine_principal_point = False
    options.ba_refine_extra_params = False
    options.ba_refine_sensor_from_rig = False
    options.ba_use_gpu = False
    options.structure_less_registration_fallback = False
    options.mapper.num_threads = 2
    options.mapper.random_seed = SEED
    options.mapper.abs_pose_refine_focal_length = False
    options.mapper.abs_pose_refine_extra_params = False
    options.triangulation.random_seed = SEED
    return options


def c2w_from_cam_from_world(pose):
    """COLMAP Rigid3d is world-to-camera, with no pixel convention involved."""
    matrix = np.eye(4)
    matrix[:3] = pose.inverse().matrix()
    if not np.allclose(matrix[:3, :3].T @ matrix[:3, :3], np.eye(3), atol=1e-7):
        raise ValueError('INVALID_CAMERA_ROTATION')
    if not np.isclose(np.linalg.det(matrix[:3, :3]), 1., atol=1e-7):
        raise ValueError('CAMERA_REFLECTION')
    return matrix


def import_database(common_dir, database_path):
    """Import train-track observations and exact stored edges, verify with COLMAP.

    Returns (receipt, per_image_original_track_ids). Feature indices are local
    indices into these arrays, not original keypoint extractor indices.
    """
    common_dir, database_path = Path(common_dir), Path(database_path)
    if database_path.exists():
        raise FileExistsError(database_path)
    tracks = np.load(common_dir / 'tracks.npz', allow_pickle=False)
    pairs = np.load(common_dir / 'pairs.npz', allow_pickle=False)
    split = json.loads((common_dir / 'split.json').read_text())
    ledger = json.loads((common_dir / 'ledger.json').read_text())
    xy = tracks['xy']
    train = np.asarray(split['train'], int)
    if len(set(train)) != len(train) or np.any(train < 0) or np.any(train >= len(xy)):
        raise ValueError('INVALID_TRAIN_IDS')
    if set(train) & (set(split['validation']) | set(split['test'])):
        raise ValueError('SPLIT_LEAKAGE')
    if xy.shape[1:] != (len(ledger), 2):
        raise ValueError('LEDGER_TRACK_SHAPE')
    if 'frame_raw' in tracks:
        np.testing.assert_array_equal(tracks['frame_raw'], [r['raw_frame'] for r in ledger])
    for row in ledger:
        if not np.array_equal(np.asarray(row['K']), K):
            raise ValueError('INPUT_K_CHANGED')
    maps, local, keypoints = [], [], []
    for frame in range(len(ledger)):
        tids = np.sort(train[np.isfinite(xy[train, frame]).all(axis=1)])
        maps.append(tids)
        local.append({int(tid): i for i, tid in enumerate(tids)})
        keypoints.append((xy[tids, frame] + .5).astype(np.float32))
    camera = pycolmap.Camera(camera_id=1, model='PINHOLE', width=640, height=360,
                            params=[490., 490., 320., 180.])
    camera.has_prior_focal_length = True
    geometry_options = pycolmap.TwoViewGeometryOptions()
    geometry_options.ransac.random_seed = SEED
    geometry_options.ransac.num_threads = 1
    edge_records = []
    with pycolmap.Database.open(database_path) as database:
        database.write_camera(camera, use_camera_id=True)
        for i, row in enumerate(ledger):
            image = pycolmap.Image(image_id=i+1, name=row['id']+'.png', camera_id=1)
            database.write_image(image, use_image_id=True)
            database.write_keypoints(i+1, keypoints[i])
        for edge, (i0, j0) in enumerate(pairs['ij']):
            i, j = int(i0), int(j0)
            if i == j:
                raise ValueError('SELF_PAIR')
            rows = pairs[f'pair{edge}'].reshape(-1, 5)
            selected = rows[np.isin(rows[:, 0].astype(int), train)]
            matches = []
            for tid_float, x1, y1, x2, y2 in selected:
                tid = int(tid_float)
                if tid != tid_float or tid not in local[i] or tid not in local[j]:
                    raise ValueError('PAIR_TRACK_IDENTITY')
                if not np.allclose([x1, y1, x2, y2], xy[tid, [i, j]].ravel(), rtol=0, atol=1e-6):
                    raise ValueError('PAIR_COORDINATE_IDENTITY')
                matches.append((local[i][tid], local[j][tid]))
            matches = np.array(matches, dtype=np.uint32).reshape(-1, 2)
            if len(np.unique(matches, axis=0)) != len(matches):
                raise ValueError('DUPLICATE_ORIGINAL_MATCH')
            database.write_matches(i+1, j+1, matches)
            geometry = pycolmap.estimate_calibrated_two_view_geometry(
                camera, keypoints[i].astype(float), camera, keypoints[j].astype(float),
                matches, geometry_options)
            database.write_two_view_geometry(i+1, j+1, geometry)
            edge_records.append(dict(edge=edge, frame_i=i, frame_j=j,
                                     raw_i=ledger[i]['raw_frame'], raw_j=ledger[j]['raw_frame'],
                                     original_rows=len(rows), training_matches=len(matches),
                                     verified_matches=len(geometry.inlier_matches),
                                     config=str(geometry.config),
                                     original_training_track_ids=selected[:, 0].astype(int).tolist()))
    receipt = dict(training_matches=sum(e['training_matches'] for e in edge_records),
                   verified_matches=sum(e['verified_matches'] for e in edge_records),
                   pair_count=len(edge_records), edges=edge_records,
                   train_tracks=len(train), frame_count=len(ledger),
                   keypoint_count=sum(map(len, maps)),
                   keypoints_by_frame=[len(x) for x in maps],
                   original_track_ids_by_frame=[x.tolist() for x in maps],
                   frame_id_map=[dict(frame_index=i, image_id=i+1, raw_frame=r['raw_frame'],
                                      name=r['id']+'.png') for i, r in enumerate(ledger)],
                   geometry_options=geometry_options.todict(),
                   keypoint_convention='OpenCV original xy + 0.5; float32 database storage',
                   matching='Original train edge rows only; no re-extraction/rematching/clique closure',
                   descriptor_import='Not required: explicit matches and two_view_geometries supplied',
                   K_opencv=K.tolist(), camera_params_colmap=camera.params.tolist())
    return receipt, maps


def _export_component(reconstruction, maps, nframes, model_id, output):
    c2w = np.full((nframes, 4, 4), np.nan)
    component = np.full(nframes, -1, int)
    image_ids = sorted(reconstruction.reg_image_ids())
    for camera in reconstruction.cameras.values():
        if camera.model_name != 'PINHOLE' or not np.array_equal(camera.params, [490., 490., 320., 180.]):
            raise ValueError('COLMAP_K_REFINED')
    for iid in image_ids:
        c2w[iid-1] = c2w_from_cam_from_world(reconstruction.images[iid].cam_from_world())
        component[iid-1] = model_id
    candidates, positive, total = {}, 0, 0
    for point_id, point in sorted(reconstruction.points3D.items()):
        tids = {int(maps[e.image_id-1][e.point2D_idx]) for e in point.track.elements}
        if len(tids) != 1:
            raise ValueError('RECONSTRUCTION_TRACK_IDENTITY_MERGE')
        tid = tids.pop()
        candidate = (len(point.track.elements), -point_id, point.xyz.copy())
        if tid not in candidates or candidate[:2] > candidates[tid][:2]:
            candidates[tid] = candidate
        for element in point.track.elements:
            pc = reconstruction.images[element.image_id].cam_from_world() * point.xyz
            positive += int(pc[2] > 0)
            total += 1
    tids = sorted(candidates)
    points = np.array([candidates[t][2] for t in tids], float).reshape(-1, 3)
    np.savez_compressed(output, c2w=c2w, K=K, component=component, points=points,
                        point_track_ids=np.array(tids, int), units='arbitrary',
                        registered_indices=np.array(image_ids, int)-1)
    return dict(model_id=model_id, registered_count=len(image_ids),
                registered_indices=[i-1 for i in image_ids],
                points3D=reconstruction.num_points3D(), unique_original_tracks=len(tids),
                duplicate_track_fragments=reconstruction.num_points3D()-len(tids),
                fragment_selection='longest COLMAP point track, then smallest point3D ID',
                positive_training_observations=positive, training_observations=total,
                positive_fraction=positive/total if total else None,
                fixed_intrinsics_verified=True, exported_cameras=str(output))


def solve(common_dir, output_dir):
    """Run the frozen CPU-only independent SfM arm, recording honest failures.

    A started directory cannot be rerun silently. Largest component goes into
    cameras.npz; all components stay in models/ and component_<ID>.npz. An empty
    reconstruction exports NaN cameras and returns NOT_EVALUABLE.
    """
    common_dir, output_dir = Path(common_dir), Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    if (output_dir/'STARTED.json').exists():
        raise FileExistsError('S_ARM_ALREADY_STARTED: use an explicitly new attempt directory')
    names = ['tracks.npz', 'pairs.npz', 'split.json', 'ledger.json']
    inputs = {str(common_dir/n): _sha(common_dir/n) for n in names}
    options = fixed_options()
    receipt = dict(status='STARTED', independent_rgb_solve=True,
                   uses_R_pose_or_ring_geometry=False, input_sha256=inputs,
                   source_sha256=_sha(__file__), python=platform.python_version(),
                   pycolmap=pycolmap.__version__, numpy=np.__version__,
                   options=options.todict(), started_epoch=time.time(),
                   units='arbitrary until a later, external whole-video similarity',
                   maximum_frame_denominator=len(json.loads((common_dir/'ledger.json').read_text())))
    _save(output_dir/'STARTED.json', receipt)
    try:
        imported, maps = import_database(common_dir, output_dir/'database.db')
        _save(output_dir/'IMPORT_RECEIPT.json', imported)
        receipt['import'] = imported
        model_dir = output_dir/'models'
        model_dir.mkdir()
        # extract_colors=False: the mapper consumes database geometry only.
        models = pycolmap.incremental_mapping(output_dir/'database.db', common_dir,
                                              model_dir, options=options)
        records = []
        for mid, model in sorted(models.items()):
            record = _export_component(model, maps, len(maps), mid,
                                       output_dir/f'component_{mid}.npz')
            records.append(record)
        receipt['components'] = records
        receipt['registered_union_indices'] = sorted({i for r in records for i in r['registered_indices']})
        receipt['registered_union_count'] = len(receipt['registered_union_indices'])
        receipt['component_sizes'] = [r['registered_count'] for r in records]
        if records:
            largest = min(records, key=lambda r: (-r['registered_count'], r['model_id']))
            chosen = largest['model_id']
            # Preserve byte-identical selected model evidence rather than transforming it.
            (output_dir/'cameras.npz').write_bytes((output_dir/f'component_{chosen}.npz').read_bytes())
            receipt.update(status='COMPLETED', primary_component=chosen,
                           largest_component_count=largest['registered_count'])
        else:
            np.savez_compressed(output_dir/'cameras.npz', c2w=np.full((len(maps),4,4),np.nan),
                                K=K, component=np.full(len(maps),-1,int), points=np.empty((0,3)),
                                point_track_ids=np.empty(0,int), units='arbitrary',
                                registered_indices=np.empty(0,int))
            receipt.update(status='NOT_EVALUABLE', reason='NO_INCREMENTAL_MODEL',
                           primary_component=None, largest_component_count=0)
        receipt['outputs_sha256'] = {str(p): _sha(p) for p in output_dir.rglob('*')
                                     if p.is_file() and p.name not in ['STARTED.json','receipt.json']}
    except Exception as error:
        receipt.update(status='FAILED', reason=repr(error), traceback=traceback.format_exc())
        _save(output_dir/'receipt.json', receipt)
        raise
    receipt['seconds'] = time.time()-receipt['started_epoch']
    _save(output_dir/'receipt.json', receipt)
    return receipt
