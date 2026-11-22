#!/usr/bin/env python3
"""P6: six human-checkable figures from the real 020 identities and hypotheses (read-only)."""
import json, os, sys
from pathlib import Path
import numpy as np, pandas as pd, cv2
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
WS = Path('/home/liu/ring_first_3d_workspace')
N = WS/'experiments/TASK-E4-W0-CROSSVIDEO-025-IDENTITY-RECOVERY'
M24 = WS/'experiments/TASK-E4-W0-CROSSVIDEO-024-LANDMARK-IDENTITY-AND-REPAIR'
RUN = N/'replay_019_020/runs'; OUT = N/'runs/G03'
sys.path.insert(0, str(N/'core')); sys.path.insert(0, str(N/'replay_019_020/code')); sys.path.insert(0, str(WS/'src'))
os.environ['E4_RUN_DIR'] = str(RUN)
import common
from ring_first_3d.mainline.native.camera import torus_contours
PREP = WS/'experiments/TASK-E4-UNIFIED-RING-CONTOUR-REFINEMENT-005/runs/prepared'


def rgb(view):
    for v in ('004', '005'):
        for x in json.loads((PREP/f'G03_{v}'/'PREPARED.json').read_text())['views']:
            if x['view'] == view:
                return np.asarray(np.load(x['cache'])['RGB'])[:, :, :3]
    raise KeyError(view)


def main():
    ids = pd.read_csv(OUT/'IDENTITIES'/'HISTORICAL_020_IDENTITIES_STATUS.csv')
    H = np.load(OUT/'CONSISTENCY'/'H_HYPOTHESIS.npz')['H']
    O4 = common.load(RUN/'landmarks'/'CROSS_004_OBSERVATIONS.json')
    O5 = common.load(RUN/'landmarks'/'INDEPENDENT_005_OBSERVATIONS.json')
    ho = pd.read_csv(OUT/'EVALUATION'/'HOLDOUT_BIDIRECTIONAL.csv')
    ms = pd.read_csv(OUT/'CONSISTENCY'/'MULTISEED_RANSAC.csv')
    # ---- A: 024 vs 020 counts
    fig, ax = plt.subplots(figsize=(8, 4))
    c24 = pd.read_csv(M24/'runs/G03/CONSISTENCY/LANDMARK_CONSISTENCY.csv')
    ax.bar(['024 descriptor candidates', '020 multi-view candidates'], [len(c24), len(ids)], color=['#7f8c8d', '#2980b9'])
    ax.set_ylabel('candidates'); ax.set_title(f'A: 024 n={len(c24)} (0 holdout-verifiable) vs 020 n={len(ids)}; '
                                              f'020 rigid-supported={int((ids.rigid_status=="RIGID_CONSENSUS_SUPPORTED").sum())}')
    for i, v in enumerate([len(c24), len(ids)]): ax.text(i, v+0.2, str(v), ha='center')
    fig.tight_layout(); fig.savefig(OUT/'VISUALIZATIONS'/'01_identity_method_comparison.png', dpi=140); plt.close(fig)
    # ---- B: multi-view evidence crops (2 views per side, SIFT point marked)
    n = len(ids); fig, axs = plt.subplots(n, 4, figsize=(11, 1.5*n), squeeze=False)
    for r, (_, row) in enumerate(ids.iterrows()):
        for col, (obs, side) in enumerate(((O4[int(row.landmark_004)], '004'), (O5[int(row.landmark_005)], '005'))):
            for j in range(2):
                ax = axs[r, col*2+j]; ax.axis('off')
                if j >= len(obs['observations']): continue
                o = obs['observations'][j]
                im = rgb(o['view']); uv = np.asarray(o['uv'], float)
                x, y = int(round(uv[0])), int(round(uv[1])); q = 26
                crop = im[max(0, y-q):y+q, max(0, x-q):x+q]
                if crop.size:
                    ax.imshow(crop)
                    ax.plot([crop.shape[1]/2], [crop.shape[0]/2], '+', c='#2ecc71', ms=10, mew=1.4)
                ax.set_title(f'{side} {o["view"].split("raw")[-1]} f{o["feature_id"]}', fontsize=5)
        axs[r, 0].set_ylabel(f'#{row.identity_id}\nvotes {row.n_votes}\n{row.residual_3d_mm:.2f}mm', fontsize=6)
    fig.suptitle('B: per-identity multi-view evidence (2 views each side, + = exact SIFT point)')
    fig.tight_layout(); fig.savefig(OUT/'VISUALIZATIONS'/'02_multiview_identity_evidence.png', dpi=150); plt.close(fig)
    # ---- C: 3D correspondences
    X4 = ids[['X004_x','X004_y','X004_z']].values; X5 = ids[['X005_x','X005_y','X005_z']].values
    HX4 = (H[:3, :3] @ X4.T).T + H[:3, 3]
    fig = plt.figure(figsize=(15, 4.4))
    for k, (i1, i2, lab) in enumerate(((0, 1, 'XY'), (0, 2, 'XZ'), (1, 2, 'YZ'))):
        ax = fig.add_subplot(1, 3, k+1)
        ax.scatter(X4[:, i1], X4[:, i2], c='#2980b9', s=16, label='X004')
        ax.scatter(HX4[:, i1], HX4[:, i2], c='#27ae60', s=16, marker='^', label='H·X004')
        ax.scatter(X5[:, i1], X5[:, i2], c='#c0392b', s=16, marker='x', label='X005')
        for q in range(len(X4)):
            col = '#27ae60' if ids.rigid_status[q] == 'RIGID_CONSENSUS_SUPPORTED' else '#bdc3c7'
            ax.plot([HX4[q, i1], X5[q, i1]], [HX4[q, i2], X5[q, i2]], c=col, lw=1.2)
        ax.set_xlabel('XYZ'[i1]); ax.set_ylabel('XYZ'[i2]); ax.set_title(lab); ax.grid(alpha=.2)
        if k == 0: ax.legend(fontsize=7)
    fig.suptitle(f'C: 020 identities ({len(ids)}), hypothesis from seed {int(ms.loc[ms.n_inliers.idxmax(),"seed"])}; '
                 'grey links = rigid-consensus conflict (still shown)')
    fig.tight_layout(); fig.savefig(OUT/'VISUALIZATIONS'/'03_3d_track_correspondences.png', dpi=150); plt.close(fig)
    # ---- D: Ring vs hypotheses (real ring observations, best vs W0)
    split = json.loads((OUT/'SPLIT.json').read_text())
    d5 = np.load(WS/'camera_mainline/G03/video005/camera_result.npz')
    c5 = {str(i): np.asarray(d5['c2w'][k], float) for k, i in enumerate(d5['ids'])}
    v = split['fit5'][0]
    rp = WS/'experiments/TASK-E4-W0-MAINLINE-CONSOLIDATION-015/runs/G03_005/observations'/(v+'_ring.npz')
    pts = np.asarray(np.load(rp)['q_train'], float)
    fig, axs = plt.subplots(1, 3, figsize=(15, 4.2))
    for ax, (M, name, col) in zip(axs, ((c5[v], 'W0 camera', '#2ecc71'), (np.linalg.inv(H) @ c5[v], 'H⁻¹·C005', '#e74c3c'),
                                        (np.linalg.inv(np.load(OUT/'CONSISTENCY'/'H_BY_SEED.npz')['H_1']) @ c5[v], 'seed1 H⁻¹·C005', '#8e44ad'))):
        im = rgb(v); ax.imshow(im); ax.axis('off')
        cs = torus_contours(M, np.asarray(d5['K'], float))
        for c in cs: ax.plot(np.asarray(c)[:, 0], np.asarray(c)[:, 1], '-', c=col, lw=1.0)
        ax.scatter(pts[::6, 0], pts[::6, 1], s=2, c='#f1c40f')
        ax.set_title(f'{name}: ring MAE {min(np.linalg.norm(pts[:,None,:]-np.asarray(c,float)[None],axis=2).min(1).mean() for c in cs):.2f} px', fontsize=8)
    fig.suptitle('D: real 005 ring observations (yellow) vs predicted CAD (coloured) — hypothesis conflict')
    fig.tight_layout(); fig.savefig(OUT/'VISUALIZATIONS'/'04_ring_hypothesis_comparison.png', dpi=150); plt.close(fig)
    # ---- E: HOLDOUT bidirectional
    valid = ho[ho.category == 'MATCHED_VALID'].sort_values('err_px')
    pick = pd.concat([valid.head(2), valid.iloc[[len(valid)//2]] if len(valid) else valid, valid.tail(2)]) if len(valid) else ho.head(4)
    fig, axs = plt.subplots(len(pick), 2, figsize=(12, 2.6*len(pick)), squeeze=False)
    for r, (_, row) in enumerate(pick.iterrows()):
        idn = int(row.identity); side = row.side; vid = row.view
        im = rgb(vid); ax = axs[r, 0]; ax.imshow(im); ax.axis('off')
        ax.set_title(f'#{idn} {side} {vid.split("raw")[-1]} {row.category} err={row.err_px:.1f}px', fontsize=7)
        axs[r, 1].axis('off')
        axs[r, 1].text(0.02, 0.5, f"identity {idn}\nside {side}\nview {vid}\ncategory {row.category}\n"
                                  f"error {row.err_px if row.err_px == row.err_px else 'n/a'} px", fontsize=9)
    fig.suptitle('E: HOLDOUT observations (real views; matched by batch descriptors, never used in fitting)')
    fig.tight_layout(); fig.savefig(OUT/'VISUALIZATIONS'/'05_holdout_bidirectional_reprojection.png', dpi=150); plt.close(fig)
    # ---- F: audit summary table
    cols = ['identity_id','n_votes','residual_3d_mm','rigid_status','hypothesis_status','n_valid','median_valid_px','final_identity_status']
    fig, ax = plt.subplots(figsize=(14, 0.35*len(ids)+1.2)); ax.axis('off')
    tab = ax.table(cellText=ids[cols].round(2).astype(str).values, colLabels=cols, loc='center', cellLoc='center')
    tab.auto_set_font_size(False); tab.set_fontsize(7); tab.scale(1, 1.25)
    ax.set_title('F: identity audit summary (020 votes / 3D residual / rigid / Ring / HOLDOUT / final)')
    fig.tight_layout(); fig.savefig(OUT/'VISUALIZATIONS'/'06_identity_audit_summary.png', dpi=150); plt.close(fig)
    ids[cols].to_csv(OUT/'VISUALIZATIONS'/'06_identity_audit_summary.csv', index=False)
    print('visuals done', len(ids))


if __name__ == '__main__':
    main()
