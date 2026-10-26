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


def main():
    import argparse
    import trimesh
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--points', required=True, help='Frozen NPZ: XYZ_mm, source_u/v')
    parser.add_argument('--rgb', required=True)
    parser.add_argument('--ring', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--marks', help='New NPZ containing candidate_C/M/A masks')
    parser.add_argument('--tier', choices=['C', 'M', 'A'], default='M')
    parser.add_argument('--state', choices=['raw', 'marked', 'cleaned'], default='raw')
    parser.add_argument('--angle', nargs=2, type=float, default=DEFAULT_ANGLE)
    args = parser.parse_args()
    a = np.load(args.points)
    points = a['XYZ_mm']; color = source_colors(args.rgb, a['source_u'], a['source_v'])
    ring = trimesh.load(args.ring, process=False)
    bounds = limits([points], ring, angle=args.angle)
    keep = np.ones(len(points), bool)
    if args.state != 'raw':
        if not args.marks:
            parser.error('--marks required for marked/cleaned')
        candidate = np.load(args.marks)['candidate_' + args.tier]
        if args.state == 'marked':
            color[candidate] = [0.85, 0.08, 0.08]
        else:
            keep = ~candidate
    plt = configure(); fig, ax = plt.subplots(figsize=(8, 8))
    view(ax, points[keep], color[keep], ring, bounds, angle=args.angle,
         title=f'{args.state} / {args.tier}; actual P0, mm, no GT')
    fig.tight_layout(); Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=160, facecolor='white'); plt.close(fig)


if __name__ == '__main__':
    main()
