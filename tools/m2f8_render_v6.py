#!/usr/bin/env python3
"""Render all existing V6 target meshes in their measured world coordinates."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np
import trimesh
from scipy.spatial import cKDTree

WS = Path('/home/liu/ring_first_3d_workspace')
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from ring_first_3d.mainline.native._mesh_renderer import actual_mesh_image


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def render_video(root, out_dir):
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
    image_path = out_dir / f'{group}_{video}_SIX_VIEWS.png'
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
    parser.add_argument('--v6-root', type=Path, required=True)
    parser.add_argument('--out-dir', type=Path, required=True)
    args = parser.parse_args()
    rows = []
    for root in sorted(args.v6_root.glob('*_*')):
        if root.is_dir() and ((root / 'inputs/ledger005.json').is_file() or
                              (root / 'inputs/ledger_actual.json').is_file()):
            result = render_video(root, args.out_dir)
            if result is not None:
                rows.append(result)
                print('RENDERED', root.name, len(result['surfaces']), result['image'], flush=True)
    print('RENDER_DONE', len(rows), flush=True)


if __name__ == '__main__':
    main()
