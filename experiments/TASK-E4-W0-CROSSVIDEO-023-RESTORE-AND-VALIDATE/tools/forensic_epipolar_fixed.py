#!/usr/bin/env python3
"""P0: corrected epipolar drawing (022R bug: both panels drew the wrong-side line).

Correct relations (x in image coords, F maps 004 -> 005):
    l_005 = F  x_004        (line drawn on the 005 image for a point of the 004 image)
    l_004 = F^T x_005       (line drawn on the 004 image for a point of the 005 image)
The 022R version drew F x_004 on the 004 image and F^T x_005 on the 005 image.

Read-only: no change to 021 H / W0 / matches. Writes corrected figures + line table.
"""
import json, math
from pathlib import Path
import numpy as np, pandas as pd, cv2
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

WS = Path('/home/liu/ring_first_3d_workspace')
C21 = WS/'experiments/TASK-E4-W0-CROSSVIDEO-021-CORRECTIVE'
PREP = WS/'experiments/TASK-E4-UNIFIED-RING-CONTOUR-REFINEMENT-005/runs/prepared'
OUT = WS/'experiments/TASK-E4-W0-CROSSVIDEO-023-RESTORE-AND-VALIDATE/runs/G03'
OUT.mkdir(parents=True, exist_ok=True)
K = np.array([[490., 0, 319.5], [0, 490., 179.5], [0, 0, 1.]])
FOCUS = [('G03_v004_raw00242', 'G03_v005_raw00114'), ('G03_v004_raw00263', 'G03_v005_raw00114'),
         ('G03_v004_raw00304', 'G03_v005_raw00114'), ('G03_v004_raw00242', 'G03_v005_raw00099')]


def load_rgb(view):
    for v in ('004', '005'):
        d = json.loads((PREP/f'G03_{v}'/'PREPARED.json').read_text())
        for x in d['views']:
            if x['view'] == view:
                return np.asarray(np.load(x['cache'])['RGB'])[:, :, :3]
    raise KeyError(view)


def cams():
    d4 = np.load(WS/'camera_mainline/G03/video004/camera_result.npz')
    d5 = np.load(WS/'camera_mainline/G03/video005/camera_result.npz')
    return ({str(i): d4['c2w'][k] for k, i in enumerate(d4['ids'])},
            {str(i): d5['c2w'][k] for k, i in enumerate(d5['ids'])})


def F_from_pose(H, C4, C5, K):
    T = np.linalg.inv(C5) @ (H @ C4)
    R, t = T[:3, :3], T[:3, 3]
    tx = np.array([[0, -t[2], t[1]], [t[2], 0, -t[0]], [-t[1], t[0], 0.]])
    F = np.linalg.inv(K).T @ (tx @ R) @ np.linalg.inv(K)
    return F/np.linalg.norm(F)


def line_dist(l, p):
    a, b, c = l
    return abs(a*p[0] + b*p[1] + c)/math.hypot(a, b) if math.hypot(a, b) > 1e-12 else float('nan')


def clip_segment(l, w, h):
    """Intersect line a x + b y + c = 0 with the image rectangle; return the two extreme endpoints."""
    a, b, c = l
    pts = []
    if abs(b) > 1e-12:
        for x in (0.0, w - 1.0):
            y = -(a*x + c)/b
            if -1e-6 <= y <= h - 1 + 1e-6: pts.append((x, min(max(y, 0), h - 1)))
    if abs(a) > 1e-12:
        for y in (0.0, h - 1.0):
            x = -(b*y + c)/a
            if -1e-6 <= x <= w - 1 + 1e-6: pts.append((min(max(x, 0), w - 1), y))
    if len(pts) < 2:
        return None
    best, dist = None, -1
    for i in range(len(pts)):
        for j in range(i+1, len(pts)):
            d = (pts[i][0]-pts[j][0])**2 + (pts[i][1]-pts[j][1])**2
            if d > dist: dist, best = d, (pts[i], pts[j])
    return best


def main():
    M = np.load(C21/'runs/G03/MATCHES.npz')
    a = [str(x) for x in M['a']]; b = [str(x) for x in M['b']]; off = M['off']
    pa, pb = M['pa'], M['pb']
    r = json.loads((C21/'runs/G03/RESULTS.json').read_text()); H = np.array(r['H'])
    c4, c5 = cams()
    rows = []
    fig, axs = plt.subplots(len(FOCUS), 2, figsize=(14, 3.6*len(FOCUS)), squeeze=False, constrained_layout=True)
    for row, (u, v) in enumerate(FOCUS):
        k = next(i for i in range(len(a)) if a[i] == u and b[i] == v)
        lo, hi = int(off[k]), int(off[k+1])
        x4, x5 = pa[lo:hi], pb[lo:hi]
        Fp = F_from_pose(H, c4[u], c5[v], K)
        Fimg, mask = cv2.findFundamentalMat(x4.astype(np.float32), x5.astype(np.float32),
                                            cv2.USAC_MAGSAC, 1.5, 0.999, 10000)
        Fimg = None if (Fimg is None or Fimg.shape != (3, 3)) else Fimg/np.linalg.norm(Fimg)
        im4, im5 = load_rgb(u), load_rgb(v)
        # pick 2 spread-out points
        order = np.argsort(-np.abs(x4[:, 0] - 319.5))[:2]
        for j in order:
            p4 = np.r_[x4[j], 1.0]; p5 = np.r_[x5[j], 1.0]
            for (im, ax, p_here, l_here, pts_id, side) in (
                    (im4, axs[row, 0], x4[j], Fp.T @ p5, (u, j, '004'), '004'),
                    (im5, axs[row, 1], x5[j], Fp @ p4, (v, j, '005'), '005')):
                h, w = im.shape[:2]
                seg = clip_segment(l_here, w, h)
                ax.imshow(im); ax.set_xlim(0, w); ax.set_ylim(h, 0); ax.axis('off')
                if seg is not None:
                    ax.plot([seg[0][0], seg[1][0]], [seg[0][1], seg[1][1]], c='#00e0ff', lw=1.4)
                ax.scatter([p_here[0]], [p_here[1]], s=42, c='#ffd400', edgecolor='k', linewidths=.8, zorder=5)
                d = line_dist(l_here, p_here)
                rows.append(dict(pair=f'{u}__{v}', match_index=int(j), side=side,
                                 line_a=float(l_here[0]), line_b=float(l_here[1]), line_c=float(l_here[2]),
                                 point_x=float(p_here[0]), point_y=float(p_here[1]), line_distance_px=d,
                                 F='F_pose', clipped=seg is not None))
                ax.set_title(f'{side} {u if side=="004" else v} | match#{j} | point-line {d:.2f} px', fontsize=8)
            # F_img lines for the same points
            if Fimg is not None:
                for (ax, im, p_here, l_here) in ((axs[row, 0], im4, x4[j], Fimg.T @ p5),
                                                 (axs[row, 1], im5, x5[j], Fimg @ p4)):
                    h, w = im.shape[:2]
                    seg = clip_segment(l_here, w, h)
                    if seg is not None:
                        ax.plot([seg[0][0], seg[1][0]], [seg[0][1], seg[1][1]], c='#ff2fb0', lw=1.1, ls='--')
            # local real crop around the 004 point
            cx, cy = int(round(x4[j, 0])), int(round(x4[j, 1]))
            r0 = 60
            crop = im4[max(0, cy-r0):cy+r0, max(0, cx-r0):cx+r0]
            if crop.size:
                cv2.imwrite(str(OUT/f'crop_{u.split("raw")[-1]}_{j:03d}.png'), crop[:, :, ::-1])
        axs[row, 0].set_ylabel(f'{u.split("raw")[-1]} ↔ {v.split("raw")[-1]}', fontsize=8)
    fig.suptitle('FIXED epipolar drawing: l_004 = Fᵀx_005 drawn on 004, l_005 = F x_004 drawn on 005\n'
                 'cyan = F_pose, magenta dashed = F_img. 022R had these two swapped.', fontsize=10)
    fig.savefig(OUT/'05_Fpose_vs_Fimg_epipolar_FIXED.png', dpi=150); plt.close(fig)
    pd.DataFrame(rows).to_csv(OUT/'epipolar_lines_FIXED.csv', index=False)
    print('wrote', OUT/'05_Fpose_vs_Fimg_epipolar_FIXED.png', 'rows', len(rows))


if __name__ == '__main__':
    main()
