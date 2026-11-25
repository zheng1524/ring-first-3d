#!/usr/bin/env python3
"""Render all existing V6 target meshes in their measured world coordinates."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import cv2
import matplotlib.pyplot as plt
import numpy as np
import trimesh
from scipy.spatial import cKDTree
from PIL import Image, ImageDraw

WS = Path('/home/liu/ring_first_3d_workspace')
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from ring_first_3d.mainline.native._mesh_renderer import actual_mesh_image


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def render_observations(root, out_dir):
    """Reuse the M2F6 RGB/clean-Mask montage and draw every V6 status on its path."""
    from m2f6_observations import render_observation_evidence
    root, out_dir = Path(root), Path(out_dir)
    prepared = root.parents[1] / 'current_inputs/prepared' / root.name / 'PREPARED.json'
    clean = root.parents[1] / 'current_inputs/clean_labels' / root.name
    primary = json.loads((root / 'predictions/local005_primary.json').read_text())['primary_version']
    camera_path = root / f'predictions/local005_camera_{primary}.npz'
    products = render_observation_evidence(prepared, clean, camera_path, out_dir)
    validation = json.loads((root / 'metrics/local_validation.json').read_text())
    per = next(version['per_frame'] for version in validation['versions'] if version['version'] == primary)
    with np.load(camera_path) as z:
        xyz = np.asarray(z['c2w'])[:, :3, 3]
    fig = plt.figure(figsize=(8, 7))
    ax = fig.add_subplot(111, projection='3d')
    ax.plot(xyz[:, 0], xyz[:, 1], xyz[:, 2], '-', color='#777777', alpha=.65)
    for status, colour in [('VALIDATED', '#27884c'), ('MODEL_PREDICTED', '#df8a25')]:
        ii = [i for i, frame in enumerate(per) if frame['status'] == status]
        if ii:
            ax.scatter(xyz[ii, 0], xyz[ii, 1], xyz[ii, 2], color=colour, label=f'{status} ({len(ii)})')
    for i, frame in enumerate(per):
        ax.text(*xyz[i], str(frame['raw']), fontsize=6)
    ax.scatter([0], [0], [0], color='#d24d38', s=80, label='Ring CAD centre')
    ax.set(xlabel='World X (mm)', ylabel='World Y (mm)', zlabel='World Z (mm)',
           title=f'{root.name}: all {len(per)} V6 cameras')
    ax.legend(loc='upper right')
    fig.tight_layout()
    path = out_dir / 'V6_TRAJECTORY_STATUS.png'
    fig.savefig(path, dpi=150)
    plt.close(fig)
    products['trajectory_status'] = str(path)
    (out_dir / 'OBSERVATION_RECEIPT.json').write_text(json.dumps(dict(
        prepared_sha256=sha(prepared), camera_sha256=sha(camera_path),
        validation_sha256=sha(root / 'metrics/local_validation.json'),
        output_sha256={key: sha(value) for key, value in products.items()}), indent=2) + '\n')
    return products


def render_rejected_native(root, out_dir):
    """Show original preview depth as diagnosis, without creating an accepted mesh."""
    v6_scripts = Path('/home/liu/polyp_research/ring_anchor_3d/experiments/ring_first_v6_local_reconstruction/scripts')
    if str(v6_scripts) not in sys.path:
        sys.path.insert(0, str(v6_scripts))
    from v6_common import depth_mesh
    root, out_dir = Path(root), Path(out_dir)
    group, video = root.name.rsplit('_', 1)
    kind = 'R5' if '_R5_' in group else 'R10'
    cad_path = WS / 'runs/m2f5_unified/cad' / f'{kind}.npz'
    with np.load(cad_path) as z:
        cad_v, cad_f = np.asarray(z['V']), np.asarray(z['F'])
    ledger = json.loads((root / 'inputs/ledger005.json').read_text())
    primary = json.loads((root / 'predictions/local005_primary.json').read_text())['primary_version']
    with np.load(root / f'predictions/local005_camera_{primary}.npz') as z:
        camera = np.asarray(z['c2w'])
    accepted_cases = json.loads((root / 'inputs/MVS_supported_cases.json').read_text())
    accepted_tags = {case['tag'] for case in accepted_cases}
    preview_cases = json.loads((root / 'inputs/MVS_cases.json').read_text())
    out_dir.mkdir(parents=True, exist_ok=True)
    receipts = []
    for case in preview_cases:
        tag = case['tag']
        if tag in accepted_tags:
            continue
        path = root / 'raw' / f'{tag}.npz'
        if not path.is_file():
            continue
        i = case['reference']
        with np.load(path) as native:
            z = cv2.resize(np.asarray(native['depth_mm'], float), (640, 360),
                           interpolation=cv2.INTER_LINEAR)
        rgb = cv2.imread(ledger[i]['RGB_path'])[:, :, ::-1].copy()
        labels = cv2.imread(ledger[i]['Mask_path'], 0)
        mesh = depth_mesh(z, labels == 1, camera[i], rgb)
        if not len(mesh.faces):
            continue
        v, f = np.asarray(mesh.vertices), np.asarray(mesh.faces)
        centre = (v.min(0) + v.max(0)) / 2
        indices = [i] + case['sources'][:2]
        panels = []
        for j in indices:
            direction = camera[j, :3, 3] - centre
            direction /= np.linalg.norm(direction)
            panels.append((str(ledger[j]['raw_frame']), float(np.degrees(np.arcsin(direction[2]))),
                           float(np.degrees(np.arctan2(direction[1], direction[0])))))
        panels += [('World X', 0., 0.), ('World Y', 0., 90.), ('World Z', 89.9999, 0.)]
        fig, axes = plt.subplots(1, 6, figsize=(18, 3.5))
        for axis, (label, elevation, azimuth) in zip(axes, panels):
            image, px_per_mm = actual_mesh_image(v, f, cad_v, cad_f, v, elevation, azimuth, '#d98989')
            axis.imshow(image)
            axis.set_title(label, fontsize=7)
            axis.axis('off')
            axis.plot([15, 15 + 5 * px_per_mm], [378, 378], color='black', lw=2)
            axis.text(15, 373, '~5 mm at view centre', fontsize=6)
        fig.suptitle(f'DIAGNOSTIC ONLY: {group}/{video} {tag}; unaccepted native HERO, original depth')
        fig.tight_layout()
        image_path = out_dir / f'{group}_{video}_{tag}_REJECTED_NATIVE_SIX_VIEWS.png'
        fig.savefig(image_path, dpi=110)
        plt.close(fig)
        receipts.append(dict(tag=tag, image=str(image_path), image_sha256=sha(image_path),
                             raw_depth_sha256=sha(path), accepted=False,
                             reason='PREVIEW_ONLY_NOT_A_SUPPORTED_TUPLE',
                             source_rgb_sha256=sha(ledger[i]['RGB_path']),
                             source_mask_sha256=sha(ledger[i]['Mask_path'])))
    (out_dir / f'{group}_{video}_REJECTED_RECEIPT.json').write_text(json.dumps(receipts, indent=2) + '\n')
    return receipts


def render_video(root, out_dir, selected_tags=None):
    root, out_dir = Path(root), Path(out_dir)
    group, video = root.name.rsplit('_', 1)
    kind = 'R5' if '_R5_' in group else 'R10'
    cad_path = WS / 'runs/m2f5_unified/cad' / f'{kind}.npz'
    with np.load(cad_path) as z:
        cad_v, cad_f = np.asarray(z['V']), np.asarray(z['F'])
    ledger_path = root / 'inputs/ledger005.json'
    if not ledger_path.is_file():
        ledger_path = root / 'inputs/ledger_actual.json'
    ledger = json.loads(ledger_path.read_text())
    index = {row['id']: i for i, row in enumerate(ledger)}
    primary_path = root / 'predictions/local005_primary.json'
    primary = json.loads(primary_path.read_text())['primary_version'] if primary_path.is_file() else 0
    camera_path = root / f'predictions/local005_camera_{primary}.npz'
    with np.load(camera_path) as z:
        camera = np.asarray(z['c2w'])
    cases = []
    for name in ('MVS_cases.json', 'MVS_supported_cases.json'):
        path = root / 'inputs' / name
        if path.is_file():
            cases.extend(json.loads(path.read_text()))
    by_tag = {case['tag']: case for case in cases}
    meshes = []
    for path in sorted((root / 'meshes').glob('*_Polyp.ply')):
        tag = path.stem.removesuffix('_Polyp')
        if selected_tags is not None and tag not in selected_tags:
            continue
        if tag not in by_tag:
            raise ValueError(f'MESH_CASE_MISSING {tag}')
        mesh = trimesh.load(path, process=False)
        if not isinstance(mesh, trimesh.Trimesh) or not len(mesh.faces):
            raise ValueError(f'EMPTY_MESH {path}')
        meshes.append((tag, path, mesh))
    if not meshes:
        return None
    palette = plt.get_cmap('tab20', max(20, len(meshes)))
    vertices, faces, colours, sources = [], [], [], []
    offset = 0
    for n, (tag, path, mesh) in enumerate(meshes):
        v, f = np.asarray(mesh.vertices), np.asarray(mesh.faces)
        vertices.append(v)
        faces.append(f + offset)
        colours.append(np.tile(palette(n)[:3], (len(f), 1)))
        sources.append(dict(tag=tag, path=str(path), sha256=sha(path), vertices=len(v), faces=len(f)))
        offset += len(v)
    pairs = []
    for i in range(len(meshes)):
        for j in range(i + 1, len(meshes)):
            a, b = np.asarray(meshes[i][2].vertices), np.asarray(meshes[j][2].vertices)
            a = a[::max(1, len(a) // 2000)][:2000]
            b = b[::max(1, len(b) // 2000)][:2000]
            da = cKDTree(b).query(a)[0]
            db = cKDTree(a).query(b)[0]
            distances = np.r_[da, db]
            pairs.append(dict(tag_a=meshes[i][0], tag_b=meshes[j][0],
                              centroid_distance_mm=float(np.linalg.norm(a.mean(0) - b.mean(0))),
                              symmetric_nn_median_mm=float(np.median(distances)),
                              symmetric_nn_p95_mm=float(np.quantile(distances, .95))))
    all_v, all_f, face_colours = np.concatenate(vertices), np.concatenate(faces), np.concatenate(colours)
    centre = (all_v.min(0) + all_v.max(0)) / 2
    first = by_tag[meshes[0][0]]
    ids = [first['reference_id']] + first['source_ids'][:2]
    if len(ids) != 3 or any(cid not in index for cid in ids):
        raise ValueError(f'MISSING_CAMERA_DIRECTIONS {root}')
    panels = []
    for cid in ids:
        direction = camera[index[cid], :3, 3] - centre
        direction /= np.linalg.norm(direction)
        panels.append((cid.rsplit('-raw', 1)[-1], float(np.degrees(np.arcsin(direction[2]))),
                       float(np.degrees(np.arctan2(direction[1], direction[0])))))
    panels += [('World X', 0., 0.), ('World Y', 0., 90.), ('World Z', 89.9999, 0.)]
    fig, axes = plt.subplots(1, 6, figsize=(18, 3.5))
    scales = []
    for axis, (label, elevation, azimuth) in zip(axes, panels):
        image, px_per_mm = actual_mesh_image(all_v, all_f, cad_v, cad_f, all_v,
                                              elevation, azimuth, '#d98989', face_colors=face_colours)
        axis.imshow(image)
        axis.set_title(label, fontsize=7)
        axis.axis('off')
        axis.plot([15, 15 + 5 * px_per_mm], [378, 378], color='black', lw=2)
        axis.text(15, 373, '~5 mm at view centre', fontsize=6)
        scales.append(float(px_per_mm))
    fig.suptitle(f'{group}/{video}: {len(meshes)} independent target meshes + {kind} CAD; GT pose unknown')
    fig.tight_layout()
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = f'_{next(iter(selected_tags))}' if selected_tags is not None else ''
    image_path = out_dir / f'{group}_{video}{suffix}_SIX_VIEWS.png'
    fig.savefig(image_path, dpi=110)
    plt.close(fig)
    receipt = dict(group_id=group, video_id=video, ring=kind, image=str(image_path),
                   image_sha256=sha(image_path), cad_sha256=sha(cad_path),
                   ledger_sha256=sha(ledger_path), camera_sha256=sha(camera_path),
                   view_labels=[x[0] for x in panels], scale_bar_mm=5., pixels_per_mm=scales,
                   surfaces=sources, pair_distances=pairs,
                   all_packaged_surfaces_retained=True, GT_deployment_pose='UNKNOWN')
    image_path.with_suffix('.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return receipt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--v6-root', type=Path)
    parser.add_argument('--run-root', type=Path)
    parser.add_argument('--out-dir', type=Path, required=True)
    parser.add_argument('--single-target', action='store_true')
    parser.add_argument('--observations', action='store_true')
    parser.add_argument('--dual-video', action='store_true')
    parser.add_argument('--rejected-native', action='store_true')
    args = parser.parse_args()
    if bool(args.v6_root) == bool(args.run_root):
        parser.error('provide exactly one of --v6-root and --run-root')
    if args.run_root:
        from m2f8_v6_general import native_video_roots
        roots = native_video_roots(args.run_root)
    else:
        roots = sorted(args.v6_root.glob('*_*'))
    rows = []
    for root in roots:
        if root.is_dir() and ((root / 'inputs/ledger005.json').is_file() or
                              (root / 'inputs/ledger_actual.json').is_file()):
            if args.observations:
                render_observations(root, args.out_dir / 'observations' / root.name)
            if args.rejected_native:
                render_rejected_native(root, args.out_dir / 'diagnostic_native' / root.name)
            result = render_video(root, args.out_dir)
            if result is not None:
                rows.append(result)
                print('RENDERED', root.name, len(result['surfaces']), result['image'], flush=True)
                if args.single_target:
                    for surface in result['surfaces']:
                        render_video(root, args.out_dir / 'individual', {surface['tag']})
    if args.dual_video:
        for group in sorted({row['group_id'] for row in rows}):
            pair = sorted((row for row in rows if row['group_id'] == group),
                          key=lambda row: row['video_id'])
            if len(pair) != 2:
                continue
            images = [Image.open(row['image']).convert('RGB') for row in pair]
            width, height = max(image.width for image in images), sum(image.height for image in images) + 70
            canvas = Image.new('RGB', (width, height), 'white')
            draw = ImageDraw.Draw(canvas)
            draw.text((20, 8), f'{group}: both videos, independent V6 world gauges; no cross-video registration',
                      fill='black')
            y = 35
            for row, image in zip(pair, images):
                canvas.paste(image, (0, y))
                y += image.height
            path = args.out_dir / f'{group}_DUAL_VIDEO_COMPARISON.png'
            canvas.save(path)
            path.with_suffix('.json').write_text(json.dumps(dict(
                video_receipts=[str(Path(row['image']).with_suffix('.json')) for row in pair],
                image_sha256=sha(path), shared_metric_world=False,
                reason='independent V6 Ring gauges; no authorized cross-video registration'), indent=2) + '\n')
    print('RENDER_DONE', len(rows), flush=True)


if __name__ == '__main__':
    main()
