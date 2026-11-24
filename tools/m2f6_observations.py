"""M2F6 observation choice from real 2-D frames and RGB matches.

The pixel-quality expressions are executed from the SHA-locked T10 source.
No camera pose, reconstructed point, Body fit or historical frame list enters
this adapter.  Its graph edges are the M2A features019 RGB RANSAC counts.
"""
import ast
import json
from pathlib import Path

import cv2
import numpy as np
from scipy.ndimage import distance_transform_edt

from ring_first_3d._legacy import definitions, source


def quality_2d(arrays):
    """Execute only the original T10 pixel statements before camera direction."""
    ns = dict(np=np, cv2=cv2, distance_transform_edt=distance_transform_edt,
              a=arrays)
    definitions('T10', ['skeleton_proxy'], ns)
    nodes = [node for node in ast.walk(source('T10'))
             if isinstance(node, ast.stmt) and node.lineno == 28 and node.end_lineno == 28]
    nodes.sort(key=lambda node: node.col_offset)
    pixel = nodes[1:9]
    if len(pixel) != 8 or ast.unparse(nodes[9].targets[0]) != 'D':
        raise RuntimeError('T10_PIXEL_AST_CHANGED')
    exec(compile(ast.Module(body=pixel, type_ignores=[]), '<locked T10 pixels>', 'exec'), ns)
    return dict(sharpness=ns['sharp'], mask_complete_proxy=1-ns['border'],
                thin_structure_visibility_proxy=ns['thin'], Ring_free_fraction=ns['ringfree'])


def appearance_2d(labels):
    """Ring ellipse and polyp centroid in image coordinates only."""
    h, w = labels.shape
    yy, xx = np.where(labels == 2)
    if len(xx) < 20:
        return [0.0] * 7
    ellipse = cv2.fitEllipse(np.column_stack([xx, yy]).astype(np.float32))
    (cx, cy), axes, angle = ellipse
    ratio = min(axes) / max(max(axes), 1e-9)
    py, px = np.where(labels == 1)
    pcx = float(px.mean() / w) if len(px) else 0.5
    pcy = float(py.mean() / h) if len(py) else 0.5
    angle = np.deg2rad(2 * angle)
    return [float(cx / w), float(cy / h), float(ratio),
            float(np.cos(angle)), float(np.sin(angle)), pcx, pcy]


def candidate_frames(frame_count):
    """A bounded raw-video candidate sweep; selection later decides its size."""
    if frame_count < 80:
        raise ValueError('VIDEO_TOO_SHORT')
    count = min(40, max(20, int(np.ceil((frame_count - 40) / 18))))
    return sorted(set(int(x) for x in np.linspace(20, frame_count - 21, count)))


def select_observations(candidates, edge_counts):
    """M2A-style connected graph growth with 2-D coverage and quality ties.

    The >=12 RGB inlier condition is the existing M2A/frozen pair_data rule.
    Candidate frames without sufficient Ring training observations are retained
    in the receipt for a later real-frame recovery attempt.
    """
    rows = [dict(row, index=i) for i, row in enumerate(candidates)]
    valid = {i for i, row in enumerate(rows) if row['ring_train_points'] >= 20}
    adjacency = {i: {} for i in valid}
    for (i, j), count in edge_counts.items():
        if i in valid and j in valid and count >= 12:
            adjacency[i][j] = int(count)
            adjacency[j][i] = int(count)
    components, unseen = [], set(valid)
    while unseen:
        seed = min(unseen); component = {seed}; frontier = [seed]; unseen.remove(seed)
        while frontier:
            i = frontier.pop()
            for j in adjacency[i]:
                if j in unseen:
                    unseen.remove(j); component.add(j); frontier.append(j)
        components.append(component)
    if not components:
        raise RuntimeError('NO_RING_OBSERVATION_COMPONENT')
    component = max(components, key=lambda part: (len(part),
                     max(rows[i]['frame'] for i in part) - min(rows[i]['frame'] for i in part)))
    frames = sorted(rows[i]['frame'] for i in component)
    step = float(np.median(np.diff(frames))) if len(frames) > 1 else 1.0
    def covers(i, j):
        return (abs(rows[i]['frame'] - rows[j]['frame']) <= 1.5 * step
                and np.linalg.norm(np.asarray(rows[i]['proxy']) - rows[j]['proxy']) <= .25)
    seed = max(component, key=lambda i: (rows[i]['quality'], len(adjacency[i]), -i))
    chosen = {seed}; covered = {j for j in component if covers(seed, j)}
    while covered != component:
        frontier = {j for i in chosen for j in adjacency[i] if j not in chosen and j in component}
        if not frontier:
            raise RuntimeError('OBSERVATION_GRAPH_GROWTH_FAILED')
        best = max(frontier, key=lambda i: (
            sum(covers(i, j) for j in component - covered), rows[i]['quality'],
            sum(adjacency[i].get(j, 0) for j in chosen), -i))
        chosen.add(best)
        covered |= {j for j in component if covers(best, j)}
    # Coverage can leave adjacent selected observations without a direct RGB
    # match.  Restore those actual missing links from the same real graph.
    # A fixed temporal threshold once converted 49-frame gaps to extra frames
    # despite a strong direct match (G03/004: 14 graph views -> 38 views).
    while True:
        ordered = sorted(chosen, key=lambda i: rows[i]['frame'])
        unlinked = [(rows[b]['frame'] - rows[a]['frame'], a, b)
                    for a, b in zip(ordered, ordered[1:])
                    if b not in adjacency[a]]
        if not unlinked:
            break
        _, a, b = max(unlinked)
        between = [i for i in component - chosen
                   if rows[a]['frame'] < rows[i]['frame'] < rows[b]['frame']
                   and a in adjacency[i] and b in adjacency[i]]
        if not between:
            raise RuntimeError('OBSERVATION_TEMPORAL_BRIDGE_MISSING')
        midpoint = (rows[a]['frame'] + rows[b]['frame']) / 2
        bridge = max(between, key=lambda i: (-abs(rows[i]['frame'] - midpoint),
                                              rows[i]['quality'], -i))
        chosen.add(bridge)
    selected = [rows[i] for i in sorted(chosen, key=lambda i: rows[i]['frame'])]
    receipt = dict(policy='current_2d_quality_ring_rgb_graph', candidate_count=len(rows),
                   ring_valid_count=len(valid), component_size=len(component),
                   component_indices=sorted(component), selected=[dict(index=i, frame=rows[i]['frame'],
                       quality=float(rows[i]['quality']), proxy=rows[i]['proxy'],
                       ring_train_points=rows[i]['ring_train_points']) for i in sorted(chosen)],
                   edge_count=sum(len(neighbours) for neighbours in adjacency.values()) // 2,
                   unselected_indices=sorted(set(range(len(rows))) - chosen))
    return selected, receipt


def choose_real_supplements(candidates, current_views, components, match_counts,
                            reason, budget=4):
    """M2A C2/B1R bridge choice over current real-frame candidates."""
    current = set(current_views)
    eligible = [row for row in candidates
                if row['view'] not in current and row['ring_train_points'] >= 20]
    component_hits = {}
    for row in eligible:
        component_hits[row['view']] = {k for k, part in enumerate(components)
                                       if any(match_counts.get((row['view'], view), 0) >= 12
                                              for view in part)}
    selected, covered = [], set()
    if reason == 'RGB_GRAPH_DISCONNECTED':
        # C2's component-covering choice: only a frame joining distinct pieces
        # is useful once those pieces have already been connected.
        while len(selected) < budget:
            options = [(len(component_hits[row['view']] - covered),
                        len(component_hits[row['view']]), row['quality'], row)
                       for row in eligible if row not in selected
                       and len(component_hits[row['view']]) >= 2]
            if not options:
                break
            gain, _, _, best = max(options, key=lambda x: (x[0], x[1], x[2], -x[3]['frame']))
            if gain == 0:
                break
            selected.append(best); covered |= component_hits[best['view']]
    else:
        # B1R's Ring-visible, RGB-connected real observations.  Quality and
        # image appearance rank candidates; they are never a post-HERO gate.
        while len(selected) < budget:
            options = [row for row in eligible if row not in selected
                       and component_hits[row['view']]]
            if not options:
                break
            def rank(row):
                diversity = (min(np.linalg.norm(np.asarray(row['proxy']) - x['proxy'])
                                 for x in selected) if selected else 0.0)
                return (len(component_hits[row['view']]), diversity,
                        row['quality'], row['ring_train_points'], -row['frame'])
            selected.append(max(options, key=rank))
    receipt = dict(reason=reason, budget=int(budget), eligible_count=len(eligible),
                   selected=[row['view'] for row in selected],
                   RGB_component_hits={row['view']: sorted(component_hits[row['view']])
                                       for row in eligible},
                   rule='M2A_C2_COMPONENT_COVER_OR_B1R_RING_RGB_VISIBLE')
    return selected, receipt


def recovery_reason_from_evidence(error_type=None, quality=None, rows=None):
    """Use existing W0 and T13 evidence to request more real observations."""
    if error_type in ('REFERENCE_GRAPH_DISCONNECTED', 'RING_POSE_GRAPH_DISCONNECTED'):
        return 'RGB_GRAPH_DISCONNECTED'
    if error_type == 'INSUFFICIENT_RING_OBSERVATION':
        return 'RING_OBSERVATION_INSUFFICIENT'
    if error_type in ('NO_BA_VERSION', 'INSUFFICIENT_SCENE_POINTS'):
        return 'INITIALIZATION_INSUFFICIENT'
    if rows is not None and (not rows or any(not row['ready'] for row in rows)):
        return 'SUPPORT_INSUFFICIENT'
    # S2 already specifies when QUARANTINE cameras may form geometric tuples.
    # n_accept alone is a diagnostic, not a new observation admission gate.
    return None


def bounded_recovery(initial_prepared, run_attempt, add_real_frames, max_rounds=2):
    """Run the same W0+selection callback after every bounded real addition."""
    prepared, attempts = initial_prepared, []
    for attempt in range(max_rounds + 1):
        outcome = run_attempt(prepared, attempt)
        attempts.append(dict(attempt=attempt, status=outcome['status'],
                             recovery_reason=outcome.get('recovery_reason')))
        reason = outcome.get('recovery_reason')
        if reason is None:
            return dict(status=outcome['status'], final_attempt=attempt,
                        attempts=attempts, final_prepared=prepared)
        if attempt == max_rounds:
            return dict(status='RECOVERY_BUDGET_EXHAUSTED', final_attempt=attempt,
                        attempts=attempts, final_prepared=prepared,
                        failure_reason=reason)
        new_prepared, receipt = add_real_frames(prepared, reason, attempt + 1)
        attempts[-1]['supplement'] = receipt
        if not receipt.get('added'):
            return dict(status='NO_REAL_SUPPLEMENT', final_attempt=attempt,
                        attempts=attempts, final_prepared=prepared,
                        failure_reason=reason)
        prepared = new_prepared
    raise AssertionError('unreachable recovery budget')


def render_observation_evidence(prepared_path, clean_labels_root, w0_path, output_dir):
    """Show actual selected RGB/clean Mask frames and the W0 camera path."""
    from PIL import Image, ImageDraw
    import matplotlib.pyplot as plt
    prepared = json.loads(Path(prepared_path).read_text())
    views = prepared['views']
    output_dir = Path(output_dir); output_dir.mkdir(parents=True, exist_ok=True)
    width, height, columns = 192, 108, 6
    rows = int(np.ceil(len(views) / columns))
    products = {}
    for kind in ('RGB', 'Mask'):
        canvas = Image.new('RGB', (columns * width, rows * (height + 20)), (24, 24, 24))
        draw = ImageDraw.Draw(canvas)
        for i, view in enumerate(views):
            with np.load(view['cache']) as data:
                rgb = data['RGB']
            if kind == 'RGB':
                pixels = rgb
            else:
                labels = np.load(Path(clean_labels_root) / (view['view'] + '.npz'))['labels']
                pixels = np.zeros((*labels.shape, 3), np.uint8)
                pixels[labels == 1] = (70, 190, 85)
                pixels[labels == 2] = (238, 95, 75)
            tile = Image.fromarray(pixels).resize((width, height), Image.Resampling.BILINEAR
                                                      if kind == 'RGB' else Image.Resampling.NEAREST)
            x, y = (i % columns) * width, (i // columns) * (height + 20)
            canvas.paste(tile, (x, y))
            draw.text((x + 3, y + height + 2), f"raw {view['raw_frame']}", fill=(255, 255, 255))
        dest = output_dir / f'SAMPLED_{kind}.png'
        canvas.save(dest)
        products[kind] = str(dest)
    if Path(w0_path).is_file():
        packet = np.load(w0_path)
        poses = np.asarray(packet['c2w'], float)
        xyz = poses[:, :3, 3]
        fig = plt.figure(figsize=(8, 7))
        ax = fig.add_subplot(111, projection='3d')
        ax.plot(xyz[:, 0], xyz[:, 1], xyz[:, 2], 'o-', color='#276fbb', markersize=3)
        ax.scatter([0], [0], [0], c='#d24d38', s=80, label='Ring CAD centre')
        for i, pose in enumerate(poses):
            if i % max(1, len(poses) // 10) == 0:
                ax.text(*pose[:3, 3], str(views[i]['raw_frame']), fontsize=7)
        ax.set(xlabel='World X (mm)', ylabel='World Y (mm)', zlabel='World Z (mm)',
               title='Current W0 cameras and Ring centre')
        ax.legend(loc='upper right')
        fig.tight_layout()
        dest = output_dir / 'W0_TRAJECTORY.png'; fig.savefig(dest, dpi=150); plt.close(fig)
        products['trajectory'] = str(dest)
    return products
