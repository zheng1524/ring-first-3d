"""Default Phase-C real-P0 renderer, wrapping the unchanged C0 plotting functions.

No meshing, interpolation, smoothing or point subsampling is performed. Source
RGB colors and original scatter painter ordering are preserved. See PROVENANCE.
"""
from pathlib import Path
import ast
import hashlib
import json
import numpy as np

HERE = Path(__file__).resolve().parent
__version__ = '1.1.0-camera-preview'
DEFAULT_ANGLE = (-65, 22)
APPROVED_SIDE_ANGLE = (0, 0)
DEFAULT_POINT_SIZE = 0.8


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _functions(ring, data=None):
    meta = json.loads((HERE / 'real_p0_renderer_provenance.json').read_text())
    original = Path(meta['original_script'])
    if original.exists():
        if sha(original) != meta['original_sha256']:
            raise ValueError('Original renderer changed; audit before rendering')
        source = original
    else:
        source = HERE / '_phasec_c0_view_frozen.py'
        if sha(source) != meta['bundled_sha256']:
            raise ValueError('Bundled original drawing functions changed')
    tree = ast.parse(source.read_text())
    nodes = [x for x in tree.body if isinstance(x, ast.FunctionDef)
             and x.name in ('basis', 'view', 'limits')]
    if len(nodes) != 3:
        raise ValueError('Missing original drawing functions')
    namespace = dict(np=np, ring=ring, data=data)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source), 'exec'), namespace)
    return namespace


def configure():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    font = Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
    if font.exists():
        font_manager.fontManager.addfont(str(font))
        plt.rcParams['font.family'] = 'Noto Sans CJK JP'
    plt.rcParams['axes.unicode_minus'] = False
    return plt


def basis(angle=DEFAULT_ANGLE):
    return _functions(None)['basis'](angle)


def limits(point_sets, ring, angle=DEFAULT_ANGLE):
    # Execute the exact original limits() formula with the new caller's points.
    namespace = _functions(ring, lambda index: {'XYZ_mm': point_sets[index]})
    return namespace['limits'](list(range(len(point_sets))), angle=angle)


def view(ax, points_mm, color, ring, bounds, angle=DEFAULT_ANGLE,
         title='', size=DEFAULT_POINT_SIZE, highlight=None):
    return _functions(ring)['view'](ax, points_mm, color, bounds, angle=angle,
                                   title=title, size=size, highlight=highlight)


def source_colors(rgb_path, u, v):
    from PIL import Image
    return np.asarray(Image.open(rgb_path).convert('RGB'))[v, u] / 255.


def scaled_intrinsics(K, source_size, target_size):
    """Pixel-center-preserving scale; neither extrinsic nor focal fit changes."""
    sx, sy = np.asarray(target_size, float) / np.asarray(source_size, float)
    out = np.asarray(K, float).copy()
    out[0, :] *= sx
    out[1, :] *= sy
    out[0, 2] += (sx-1.)/2.
    out[1, 2] += (sy-1.)/2.
    return out


def project_camera(points_mm, K, c2w):
    """Frozen pinhole camera, full rotation including roll; camera axial Z mm."""
    camera = (np.asarray(points_mm)-c2w[:3, 3]) @ c2w[:3, :3]
    homogeneous = camera @ K.T
    with np.errstate(divide='ignore', invalid='ignore'):
        uv = homogeneous[:, :2] / homogeneous[:, 2, None]
    return uv, camera[:, 2]


def camera_rays(uv, K, c2w):
    """Unnormalized world rays: ray parameter equals camera axial Z in mm."""
    camera = np.c_[uv, np.ones(len(uv))] @ np.linalg.inv(K).T
    direction = camera @ c2w[:3, :3].T
    return np.c_[np.broadcast_to(c2w[:3, 3], direction.shape), direction]


def draw_rgb_points(ax, projected_xy, rgb, order_key, size=DEFAULT_POINT_SIZE):
    """The original view() scatter style and painter ordering, shared by layers."""
    order = np.argsort(order_key)
    return ax.scatter(projected_xy[order, 0], projected_xy[order, 1], s=size,
                      c=np.broadcast_to(rgb, (len(projected_xy), 3))[order],
                      linewidths=0, rasterized=True)


def view_camera_rgb(ax, points_mm, rgb, K, c2w, image_size,
                    size=DEFAULT_POINT_SIZE, visibility=None):
    """Both Polyp and Background use this single RGB point drawing interface."""
    uv, z = project_camera(points_mm, K, c2w)
    w, h = image_size
    keep = np.isfinite(uv).all(1) & (z > 0) & (uv[:, 0] >= -.5) & (uv[:, 0] < w-.5)
    keep &= (uv[:, 1] >= -.5) & (uv[:, 1] < h-.5)
    if visibility is not None:
        keep &= visibility
    artist = draw_rgb_points(ax, uv[keep], np.asarray(rgb)[keep], -z[keep], size=size)
    ax.set(xlim=(-.5, w-.5), ylim=(h-.5, -.5))
    ax.set_aspect('equal')
    return artist, keep


def main():
    import argparse
    import trimesh
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--points', required=True, help='Frozen NPZ: XYZ_mm, source_u/v')
    parser.add_argument('--rgb', required=True)
    parser.add_argument('--ring', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--angle', nargs=2, type=float, default=DEFAULT_ANGLE)
    args = parser.parse_args()
    a = np.load(args.points)
    points = a['XYZ_mm']; color = source_colors(args.rgb, a['source_u'], a['source_v'])
    ring = trimesh.load(args.ring, process=False)
    bounds = limits([points], ring, angle=args.angle)
    plt = configure(); fig, ax = plt.subplots(figsize=(8, 8))
    view(ax, points, color, ring, bounds, angle=args.angle,
         title='Raw P0; actual source RGB, mm, no GT')
    fig.tight_layout(); Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=160, facecolor='white'); plt.close(fig)


if __name__ == '__main__':
    main()
