#!/usr/bin/env python3
"""P4: six required visualisations from the real G03 results (no fabricated data)."""
import json, os, sys
from pathlib import Path
import numpy as np, pandas as pd, cv2
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa
WS = Path('/home/liu/ring_first_3d_workspace')
M = WS/'experiments/TASK-E4-W0-CROSSVIDEO-024-LANDMARK-IDENTITY-AND-REPAIR'
RUN = M/'replay_019_020/runs'; OUT = M/'runs/G03'
sys.path.insert(0, str(M/'core')); sys.path.insert(0, str(M/'replay_019_020/code')); sys.path.insert(0, str(WS/'src'))
import common
PREP = WS/'experiments/TASK-E4-UNIFIED-RING-CONTOUR-REFINEMENT-005/runs/prepared'
K_DEF = np.array([[490., 0, 319.5], [0, 490., 179.5], [0, 0, 1.]])


def rgb(view):
    for v in ('004', '005'):
        for x in json.loads((PREP/f'G03_{v}'/'PREPARED.json').read_text())['views']:
            if x['view'] == view:
                return np.asarray(np.load(x['cache'])['RGB'])[:, :, :3]
    raise KeyError(view)


def cams(video):
    d = np.load(WS/'camera_mainline/G03'/f'video{video}'/'camera_result.npz')
    return {str(i): np.asarray(d['c2w'][k], float) for k, i in enumerate(d['ids'])}, np.asarray(d['K'], float)


def main():
    ids = pd.read_csv(OUT/'CONSISTENCY'/'LANDMARK_CONSISTENCY.csv')
    H = np.load(OUT/'CONSISTENCY'/'H_CANDIDATE.npz')['H']
    ring = pd.read_csv(OUT/'CONSISTENCY'/'RING_CHECK.csv')
    O4 = common.load(RUN/'landmarks'/'G03_004_FIT_OBSERVATIONS.json')
    O5 = common.load(RUN/'landmarks'/'G03_005_FIT_OBSERVATIONS.json')
    split = json.loads((OUT/'SPLIT.json').read_text())
    c4, K4 = cams('004'); c5, K5 = cams('005')
    # ---- forward / reverse reprojection on FIT observations (real uv)
    fwd, rev = [], []
    for _, r in ids.iterrows():
        i, j = int(r.landmark_004), int(r.landmark_005)
        X4 = np.array([r.X4_x, r.X4_y, r.X4_z]); X5 = np.array([r.X5_x, r.X5_y, r.X5_z])
        X5p = H[:3, :3] @ X4 + H[:3, 3]; X4p = np.linalg.inv(H)[:3, :3] @ X5 + np.linalg.inv(H)[:3, 3]
        f, b = [], []
        for o in O5[j]['observations']:
            C = c5.get(o['view'])
            if C is None: continue
            q = (X5p - C[:3, 3]) @ C[:3, :3]; p = q @ K5.T
            if p[2] <= 0: continue
            f.append(float(np.linalg.norm(p[:2]/p[2]-np.asarray(o['uv']))))
        for o in O4[i]['observations']:
            C = c4.get(o['view'])
            if C is None: continue
            q = (X4p - C[:3, 3]) @ C[:3, :3]; p = q @ K4.T
            if p[2] <= 0: continue
            b.append(float(np.linalg.norm(p[:2]/p[2]-np.asarray(o['uv']))))
        fwd.append(np.median(f) if f else np.nan); rev.append(np.median(b) if b else np.nan)
    ids['forward_reproj_px'] = fwd; ids['reverse_reproj_px'] = rev
    ids['ring_compatible'] = False       # ring MAE 7.3-8.1 px vs 0.8-1.4 px for W0
    ids['final_identity_status'] = np.where(ids.ransac_inlier, 'GEOMETRY_CONFLICT', 'REJECTED_3D')
    ids.to_csv(OUT/'CONSISTENCY'/'LANDMARK_CONSISTENCY.csv', index=False)
    (OUT/'CONSISTENCY'/'LANDMARK_CONSISTENCY.json').write_text(json.dumps(dict(
        n_candidates=int(len(ids)), n_ransac_inliers=int(ids.ransac_inlier.sum()),
        threshold_mm=1.0, ring_conflict=True,
        ring_mae_w0=float(ring.ring_mae_w0.mean()), ring_mae_ransacH=float(ring.ring_mae_ransacH.mean()),
        forward_px=dict(median=float(np.nanmedian(fwd)), p90=float(np.nanpercentile(fwd, 90))),
        reverse_px=dict(median=float(np.nanmedian(rev)), p90=float(np.nanpercentile(rev, 90))),
        status='GEOMETRY_CONFLICT', note='RANSAC H is rigid and non-degenerate but contradicts the Ring CAD; '
                                         'identities are not accepted and no formal optimisation is run'),
        indent=1))
    # ---- Fig A: contact sheet (real RGB crops)
    n = len(ids); cols = 5; rows = int(np.ceil(n/cols))
    fig, axs = plt.subplots(rows, cols, figsize=(4*cols, 2.6*rows), squeeze=False)
    for ax in axs.flat: ax.axis('off')
    for k, (_, r) in enumerate(ids.iterrows()):
        i, j = int(r.landmark_004), int(r.landmark_005)
        ax = axs.flat[k]
        try:
            o4 = O4[i]['observations'][0]; o5 = O5[j]['observations'][0]
            im4, im5 = rgb(o4['view']), rgb(o5['view'])
            def crop(im, uv):
                x, y = int(round(uv[0])), int(round(uv[1])); q = 40
                return im[max(0, y-q):y+q, max(0, x-q):x+q]
            c4_, c5_ = crop(im4, o4['uv']), crop(im5, o5['uv'])
            h = 80
            canvas = np.zeros((h, 160, 3), np.uint8)
            for idx, cc in ((0, c4_), (1, c5_)):
                if cc.size:
                    z = cv2.resize(cc, (80, 80)); canvas[:, idx*80:(idx+1)*80] = z
            ax.imshow(canvas)
        except Exception:
            ax.text(.5, .5, 'no crop', ha='center')
        col = '#2ecc71' if r.final_identity_status == 'SUPPORTED' else ('#e67e22' if r.final_identity_status != 'GEOMETRY_CONFLICT' else '#c0392b')
        ax.set_title(f'#{k} {r.candidate_id}  {r.final_identity_status}\n3D {r.residual_3d_mm:.2f} mm', fontsize=7, color=col)
    fig.suptitle('A: all candidates (004 crop | 005 crop). green=supported, orange=insufficient, red=geometry conflict')
    fig.tight_layout(); fig.savefig(OUT/'VISUALIZATIONS'/'01_identity_contact_sheet.png', dpi=150); plt.close(fig)
    # ---- Fig B/C: 3D correspondence, before/after RANSAC (3 axes, same limits)
    X4a = ids[['X4_x','X4_y','X4_z']].values; X5a = ids[['X5_x','X5_y','X5_z']].values
    HX4 = (H[:3, :3] @ X4a.T).T + H[:3, 3]
    allp = np.vstack([X4a, X5a, HX4])
    lo, hi = allp.min(0), allp.max(0)
    for tag, fname, title in (('B', '02_3d_identity_correspondences.png', 'B: 004 (blue) -> H X004 (green) vs X005 (red)'),
                              ('C', '03_ransac_before_after.png', 'C: RANSAC inliers vs rejected (all still shown)')):
        fig = plt.figure(figsize=(15, 4.6))
        for idx, (i1, i2, lab) in enumerate(((0, 1, 'XY'), (0, 2, 'XZ'), (1, 2, 'YZ'))):
            ax = fig.add_subplot(1, 3, idx+1)
            ax.scatter(X4a[:, i1], X4a[:, i2], s=12, c='#2980b9', label='X004')
            ax.scatter(HX4[:, i1], HX4[:, i2], s=12, c='#27ae60', marker='^', label='H·X004')
            ax.scatter(X5a[:, i1], X5a[:, i2], s=12, c='#c0392b', marker='x', label='X005')
            for k in range(len(X4a)):
                c = '#27ae60' if ids.ransac_inlier[k] else '#bdc3c7'
                ax.plot([HX4[k, i1], X5a[k, i1]], [HX4[k, i2], X5a[k, i2]], c=c, lw=1.0)
            ax.set_xlabel('XYZ'[i1]); ax.set_ylabel('XYZ'[i2]); ax.set_title(lab)
            ax.set_xlim(lo[i1]-2, hi[i1]+2); ax.set_ylim(lo[i2]-2, hi[i2]+2); ax.grid(alpha=.2)
            if idx == 0: ax.legend(fontsize=7)
        fig.suptitle(f'{title}\ncandidates={len(ids)}, inliers={int(ids.ransac_inlier.sum())}, '
                     f'threshold={1.0} mm, Ring conflict: {ring.ring_mae_ransacH.mean():.1f} px vs W0 {ring.ring_mae_w0.mean():.1f} px')
        fig.tight_layout(); fig.savefig(OUT/'VISUALIZATIONS'/fname, dpi=150); plt.close(fig)
    # ---- Fig D: bidirectional reprojection on real RGB
    sel = ids.assign(err=ids.forward_reproj_px).sort_values('err').iloc[[0, len(ids)//2, len(ids)-1]]
    fig, axs = plt.subplots(len(sel), 2, figsize=(13, 3.2*len(sel)), squeeze=False)
    for row, (_, r) in enumerate(sel.iterrows()):
        i, j = int(r.landmark_004), int(r.landmark_005)
        X4 = np.array([r.X4_x, r.X4_y, r.X4_z]); X5p = H[:3, :3] @ X4 + H[:3, 3]
        o5 = O5[j]['observations'][0]; C = c5[o5['view']]; im = rgb(o5['view'])
        q = (X5p - C[:3, 3]) @ C[:3, :3]; p = q @ K5.T; pred = p[:2]/p[2]
        ax = axs[row, 0]; ax.imshow(im); ax.axis('off')
        ax.scatter([o5['uv'][0]], [o5['uv'][1]], c='#f1c40f', s=50, edgecolor='k', label='observed')
        ax.scatter([pred[0]], [pred[1]], c='#e74c3c', s=50, marker='x', label='predicted')
        ax.annotate('', xy=(o5['uv'][0], o5['uv'][1]), xytext=(pred[0], pred[1]),
                    arrowprops=dict(arrowstyle='->', color='w'))
        ax.set_title(f'004 X -> 005 {o5["view"]}: {r.forward_reproj_px:.1f} px', fontsize=8); ax.legend(fontsize=6)
        o4 = O4[i]['observations'][0]; C = c4[o4['view']]; im = rgb(o4['view'])
        X4p = np.linalg.inv(H)[:3, :3] @ np.array([r.X5_x, r.X5_y, r.X5_z]) + np.linalg.inv(H)[:3, 3]
        q = (X4p - C[:3, 3]) @ C[:3, :3]; p = q @ K4.T; pred = p[:2]/p[2]
        ax = axs[row, 1]; ax.imshow(im); ax.axis('off')
        ax.scatter([o4['uv'][0]], [o4['uv'][1]], c='#f1c40f', s=50, edgecolor='k', label='observed')
        ax.scatter([pred[0]], [pred[1]], c='#e74c3c', s=50, marker='x', label='predicted')
        ax.annotate('', xy=(o4['uv'][0], o4['uv'][1]), xytext=(pred[0], pred[1]),
                    arrowprops=dict(arrowstyle='->', color='w'))
        ax.set_title(f'005 X -> 004 {o4["view"]}: {r.reverse_reproj_px:.1f} px', fontsize=8); ax.legend(fontsize=6)
    fig.suptitle('D: real RGB, observed vs predicted (arrow = error vector). Low / median / high error rows.', fontsize=10)
    fig.tight_layout(); fig.savefig(OUT/'VISUALIZATIONS'/'04_bidirectional_reprojection.png', dpi=150); plt.close(fig)
    # ---- Fig E: distributions (3 units separated)
    fig, axs = plt.subplots(1, 3, figsize=(15, 4))
    axs[0].hist(ids.residual_3d_mm.dropna(), bins=12, color='#8e44ad'); axs[0].set_title('3D identity residual (mm)')
    axs[1].hist(ids.forward_reproj_px.dropna(), bins=12, color='#16a085'); axs[1].set_title('forward reprojection (px)')
    axs[2].hist(ids.reverse_reproj_px.dropna(), bins=12, color='#d35400'); axs[2].set_title('reverse reprojection (px)')
    for ax in axs: ax.set_ylabel('identities'); ax.grid(alpha=.2)
    fig.suptitle(f'E: full candidate statistics (n={len(ids)}), not the supported subset only')
    fig.tight_layout(); fig.savefig(OUT/'VISUALIZATIONS'/'05_identity_residual_distribution.png', dpi=150); plt.close(fig)
    # ---- Fig F: support matrix
    v4 = sorted(split['fit4']) + sorted(split['ho4']); v5 = sorted(split['fit5']) + sorted(split['ho5'])
    Mx = np.zeros((len(v4)+len(v5), len(ids)))
    for k, (_, r) in enumerate(ids.iterrows()):
        for o in O4[int(r.landmark_004)]['observations']:
            if o['view'] in v4: Mx[v4.index(o['view']), k] = 2 if o['view'] in split['fit4'] else 1
        for o in O5[int(r.landmark_005)]['observations']:
            if o['view'] in v5: Mx[len(v4)+v5.index(o['view']), k] = 2 if o['view'] in split['fit5'] else 1
    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(Mx, aspect='auto', cmap='viridis', vmin=0, vmax=2)
    ax.set_yticks(range(len(v4)+len(v5)), [f'004 {x.split("raw")[-1]}' for x in v4] + [f'005 {x.split("raw")[-1]}' for x in v5], fontsize=7)
    ax.set_xticks(range(len(ids)), [f'{k}' for k in range(len(ids))], fontsize=6)
    ax.set_xlabel('candidate identity #')
    fig.colorbar(im, ax=ax, ticks=[0, 1, 2], label='0 none / 1 HOLDOUT observation / 2 FIT (used)')
    ax.set_title('F: which real views observe each identity (2=FIT used, 1=HOLDOUT only, 0=none)')
    fig.tight_layout(); fig.savefig(OUT/'VISUALIZATIONS'/'06_identity_support_matrix.png', dpi=150); plt.close(fig)
    print(json.dumps(dict(candidates=len(ids), inliers=int(ids.ransac_inlier.sum()),
                          ring_w0=float(ring.ring_mae_w0.mean()), ring_ransac=float(ring.ring_mae_ransacH.mean()),
                          fwd_median=float(np.nanmedian(fwd)), rev_median=float(np.nanmedian(rev))), indent=1))


if __name__ == '__main__':
    main()
