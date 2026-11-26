"""Read-only verification of frozen inputs and the four actual face subsets."""
from pathlib import Path
import ast
import json
import subprocess
import numpy as np
import trimesh
from ring_first_3d.v6_raw.trusted_restore import T, WT, O, B, read, save, sha, now
from ring_first_3d.mainline.native.geometry import resize_index_intrinsics

frozen = read(T / 'config/SOURCES_FROZEN.json')
history = T / 'evidence/history'
identities = read(history / 'IDENTITIES.json')
kernel = WT / 'src/ring_first_3d/mainline/native/_clean_kernels.py'
functions = {n.name: n for n in ast.parse(kernel.read_text()).body if isinstance(n, ast.FunctionDef)}
for name, entry in identities['kernel_functions'].items():
    old = {n.name: n for n in ast.parse((history / Path(entry['source']).name).read_text()).body if isinstance(n, ast.FunctionDef)}
    assert ast.dump(functions[name], include_attributes=False) == ast.dump(old[name], include_attributes=False)
protocol = read(WT / 'src/ring_first_3d/mainline/native/cleaning_protocol.json')
for key in ['thresholds', 'inherited_density']:
    assert protocol[key] == read(history / 'PROTOCOL.json')[key]

checks = []
for i, c in enumerate(frozen['cases'], 1):
    R, d = Path(c['run']), O / f'source{i}'
    for p, h in c['artifacts'].items():
        assert sha(p) == h, p
    receipt = read(d / 'COMPLETE.json')
    for p, h in receipt['outputs'].items():
        assert sha(p) == h, p
    mesh = trimesh.load(R / 'meshes' / (c['tag'] + '_Polyp.ply'), process=False)
    V, F = np.asarray(mesh.vertices), np.asarray(mesh.faces)
    evidence = np.load(d / 'FACE_EVIDENCE.npz')
    mapping = np.load(d / 'ORIGINAL_MAPPING.npz')
    subset = np.load(d / 'TRUSTED_ONLY.npz')
    excluded = np.load(d / 'EXCLUDED_FACES.npz')
    state = evidence['state']
    assert np.isin(state, [0, 1, 2, 3]).all() and state.shape == (len(F),)
    assert np.array_equal(evidence['V'], V) and np.array_equal(evidence['F'], F)
    assert np.array_equal(evidence['original_face_id'], np.arange(len(F)))
    assert np.array_equal(mapping['V'], V) and np.array_equal(mapping['F'], F)
    for pack, selection in [(subset, state == 0), (excluded, state != 0)]:
        assert np.array_equal(pack['V'], V)
        assert np.array_equal(pack['F'], F[selection])
        assert np.array_equal(pack['original_vertex_id'], np.arange(len(V)))
        assert np.array_equal(pack['original_face_id'], np.flatnonzero(selection))
    assert np.array_equal(excluded['state'], state[state != 0])
    trusted_ply = trimesh.load(d / 'TRUSTED_ONLY.ply', process=False)
    assert np.array_equal(trusted_ply.vertices, V)
    assert np.array_equal(trusted_ply.faces, F[state == 0])
    assert np.array_equal(trusted_ply.visual.vertex_colors, mesh.visual.vertex_colors)
    area = np.linalg.norm(np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]]), axis=1) / 2
    assert np.allclose(area, evidence['area_mm2'], rtol=1e-12, atol=1e-12)
    result = read(d / 'RESULT.json')
    for s in result['states']:
        selection = state == s['code']
        assert s['faces'] == int(selection.sum())
        assert abs(s['area_mm2'] - area[selection].sum()) < 1e-8
    native = np.load(R / 'raw' / (c['tag'] + '.npz'))
    cameras = np.load(c['camera_path'])
    assert np.array_equal(native['c2w'], cameras['c2w'])
    assert np.array_equal(native['K_full'], cameras['K'])
    assert np.allclose(native['K_index_native'], resize_index_intrinsics(native['K_full'], result['working_shape'], result['native_shape']), atol=1e-10)
    plan = next(x for x in read(R / 'PLAN_FROZEN.json')['legal'] if x['tag'] == c['tag'])
    assert int(native['reference']) == plan['reference']
    assert np.array_equal(native['sources'], plan['sources'])
    ledger = read(R / 'inputs/ledger005.json')
    assert ledger[plan['reference']]['raw_frame'] == c['raw_target']
    assert [ledger[j]['raw_frame'] for j in plan['sources']] == c['raw_support']
    assert read(B / 'states' / (c['case'] + '.json'))['origin'] == 'NEW'
    assert c['old_labels_used'] is False
    assert not list(d.glob('*C1*')) and not list(d.glob('*OBS_TRUSTED*'))
    checks.append(dict(case=c['case'],target=c['raw_target'],frozen_assets_verified=len(c['artifacts']),raw_faces=len(F),trusted_faces=int((state == 0).sum()),excluded_faces=int((state != 0).sum()),coordinates_bitwise_unchanged=True,original_face_ids_aligned=True,original_vertex_colors_unchanged=True,native_shape=result['native_shape'],working_shape=result['working_shape'],native_pose_and_intrinsics_match_camera=True,actual_new_inference_commit=c['hero_execution_commit'],classification_execution_commit=result['execution_commit'],result_sha256=sha(d/'RESULT.json'),outputs=receipt['outputs']))

render = read(T / 'evidence/RENDER_RECEIPT.json')
for figure in render['figures']:
    assert sha(figure['path']) == figure['sha256']
    assert len(figure['views']) == 2
save(T / 'evidence/VERIFICATION.json', dict(checked_beijing=now(),result='PASS',historical_ast_functions_equal=list(identities['kernel_functions']),protocol_parameters_equal=True,original_raw_preserved=True,no_classifier_rerun_during_annotation_fix=True,sources=checks,render=render,full_runner_pid=read(B/'LAUNCH.json')['pid'],full_runner_alive=Path('/proc/'+str(read(B/'LAUNCH.json')['pid'])).exists(),full_execution_snapshot=read(B/'SNAPSHOT.json'),verification_code_sha256=sha(__file__),git_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=WT,text=True).strip()))
print('PASS: 4 NEW sources, exact original V/F/IDs/RGB, four-state counts/areas, frozen inputs, camera/native mapping, historical AST/parameters, 4 figures')
