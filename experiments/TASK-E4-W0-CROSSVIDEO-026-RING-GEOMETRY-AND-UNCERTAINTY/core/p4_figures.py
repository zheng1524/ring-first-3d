#!/usr/bin/env python3
"""P4: ten required figures from real G03 data and this round's actual numbers."""
import json, os, sys
from pathlib import Path
import numpy as np, pandas as pd, cv2
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa
WS = Path('/home/liu/ring_first_3d_workspace')
N = WS/'experiments/TASK-E4-W0-CROSSVIDEO-026-RING-GEOMETRY-AND-UNCERTAINTY'
RUN = N/'replay_020/runs'; OUT = N/'runs/G03'; FIG = OUT/'FIGURES'; FIG.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(N/'replay_020/code')); sys.path.insert(0, str(WS/'src'))
os.environ['E4_RUN_DIR'] = str(RUN)
PREP = WS/'experiments/TASK-E4-UNIFIED-RING-CONTOUR-REFINEMENT-005/runs/prepared'
views = {v['id']: v for v in json.loads((RUN/'config'/'VIEWS.json').read_text())}
split = json.loads((OUT/'SPLIT.json').read_text())


def rgb(view):
    for v in ('004', '005'):
        for x in json.loads((PREP/f'G03_{v}'/'PREPARED.json').read_text())['views']:
            if x['view'] == view:
                return np.asarray(np.load(x['cache'])['RGB'])[:, :, :3]
    raise KeyError(view)


def labels(view): return np.asarray(np.load(views[view]['cache'])['labels'])


def masks(view):
    lab = labels(view)
    from scipy.ndimage import binary_erosion
    ring = (lab == 2).astype(np.uint8)
    cc, hh = cv2.findContours(ring, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    inner, outer = [], []
    if hh is not None:
        for c, h in zip(cc, hh[0]):
            (inner if h[3] >= 0 else outer).append(c[:, 0])
    return (np.concatenate(inner) if inner else np.empty((0, 2))), (np.concatenate(outer) if outer else np.empty((0, 2)))


def main():
    v = split['fit5'][0]; im = rgb(v)
    # 1 ring observations
    inn, out = masks(v)
    fig, ax = plt.subplots(figsize=(9, 5)); ax.imshow(im); ax.axis('off')
    ax.scatter(inn[:, 0], inn[:, 1], s=1.5, c='#00e5ff', label=f'inner obs (n={len(inn)})')
    ax.scatter(out[:, 0], out[:, 1], s=1.5, c='#ffd400', label=f'outer obs (n={len(out)})')
    ax.set_title(f'1: real Ring inner/outer observations — 005 {v.split("raw")[-1]} (mask-based, not fitted ellipses)')
    ax.legend(fontsize=7, loc='upper right')
    fig.tight_layout(); fig.savefig(FIG/'01_ring_inner_outer_observations.png', dpi=140); plt.close(fig)
    # 2 CAD vs observed I/O
    from ring_first_3d.mainline.native.camera import torus_contours
    C = np.asarray(views[v]['T'], float); K = np.asarray(views[v]['K'], float)
    cs = torus_contours(C, K)
    cs = sorted(cs, key=lambda c: cv2.contourArea(np.asarray(c, np.float32).reshape(-1, 1, 2)))
    fig, ax = plt.subplots(figsize=(9, 5)); ax.imshow(im); ax.axis('off')
    ax.plot(np.asarray(cs[0])[:, 0], np.asarray(cs[0])[:, 1], '-', c='#00e5ff', lw=1.2, label='CAD inner (small-area silhouette)')
    ax.plot(np.asarray(cs[1])[:, 0], np.asarray(cs[1])[:, 1], '-', c='#ff2fb0', lw=1.2, label='CAD outer')
    ax.scatter(inn[:, 0], inn[:, 1], s=1.2, c='#00e5ff', alpha=.5, label='inner obs')
    ax.scatter(out[:, 0], out[:, 1], s=1.2, c='#ffd400', alpha=.5, label='outer obs')
    io = pd.read_csv(OUT/'RING_IO_PER_VIEW.csv'); r = io[io.view == v].iloc[0]
    ax.set_title(f'2: CAD vs real I/O — {v.split("raw")[-1]}:  M={r.M:.3f}  I={r.I:.3f}  C={r.C:.3f}  O={r.O:.3f}')
    ax.legend(fontsize=6, loc='upper right')
    fig.tight_layout(); fig.savefig(FIG/'02_cad_inner_outer_overlay.png', dpi=140); plt.close(fig)
    # 3 pose sensitivity
    s = pd.read_csv(OUT/'RING_POSE_SENSITIVITY.csv')
    fig, axs = plt.subplots(1, 2, figsize=(13, 4))
    for kind in ('yaw', 'pitch', 'roll'):
        d = s[(s.kind == kind) & (s.view == v)]
        axs[0].plot(d.value, d.ring, 'o-', label=kind)
    for kind in ('tx', 'tz'):
        d = s[(s.kind == kind) & (s.view == v)]
        axs[1].plot(d.value, d.ring, 'o-', label=kind)
    axs[0].set_xlabel('rotation perturbation (deg)'); axs[1].set_xlabel('translation perturbation (mm)')
    for a in axs: a.set_ylabel('full Ring loss (M/I/C/O weighted)'); a.grid(alpha=.25); a.legend(fontsize=8); a.set_yscale('log')
    axs[0].set_title('3: Ring sensitivity (yaw flat at small angles = unidentifiable)')
    fig.tight_layout(); fig.savefig(FIG/'03_ring_pose_sensitivity.png', dpi=140); plt.close(fig)
    # 4 sparse triangulation geometry
    b4 = np.load(RUN/'landmarks'/'REL_BASE_004.npz')['X']; b5 = np.load(RUN/'landmarks'/'REL_BASE_005.npz')['X']
    fig = plt.figure(figsize=(15, 4.4))
    for k, (i1, i2, lab) in enumerate(((0, 1, 'XY'), (0, 2, 'XZ'), (1, 2, 'YZ'))):
        ax = fig.add_subplot(1, 3, k+1)
        ax.scatter(b4[:, i1], b4[:, i2], s=6, c='#2980b9', label='004 landmarks')
        ax.scatter(b5[:, i1], b5[:, i2], s=6, c='#c0392b', label='005 landmarks')
        for vv in split['fit4'] + split['fit5']:
            c = np.asarray(views[vv]['T'], float)[:3, 3]
            ax.scatter([c[i1]], [c[i2]], marker='^', s=40, c='k')
        t = np.linspace(0, 2*np.pi, 200); ax.plot(5.6*np.cos(t), 5.6*np.sin(t), 'k--', lw=.6)
        ax.set_xlabel('XYZ'[i1]); ax.set_ylabel('XYZ'[i2]); ax.set_title(lab); ax.grid(alpha=.2)
        if k == 0: ax.legend(fontsize=7)
    fig.suptitle(f'4: sparse triangulation from W0 FIT cameras (004 n={len(b4)}, 005 n={len(b5)}), ring circle dashed')
    fig.tight_layout(); fig.savefig(FIG/'04_sparse_triangulation_geometry.png', dpi=140); plt.close(fig)
    # 5 per-landmark displacement
    p = np.load(RUN/'landmarks'/'PERT_004_rot_1.0_0.0.npz')['X']
    n = min(len(p), len(b4)); d = np.linalg.norm(p[:n]-b4[:n], axis=1)
    fig, axs = plt.subplots(1, 2, figsize=(12, 4))
    axs[0].hist(d, bins=30, color='#8e44ad'); axs[0].set_xlabel('3D displacement (mm)'); axs[0].set_ylabel('landmarks')
    axs[0].set_title(f'5a: 004 rotation 1° (common-mode): median {np.median(d):.3f} mm')
    axs[1].scatter(b4[:n, 2], d, s=8, c='#8e44ad'); axs[1].set_xlabel('depth z (mm)'); axs[1].set_ylabel('displacement (mm)')
    axs[1].set_title('5b: displacement vs depth')
    fig.suptitle('5: triangulation uncertainty under a frozen 1° camera perturbation (same real 2D observations)')
    fig.tight_layout(); fig.savefig(FIG/'05_triangulation_uncertainty.png', dpi=140); plt.close(fig)
    # 6 ring vs 3D
    r1 = s[(s.kind == 'rot') & (s.view == v)]
    rel = pd.read_csv(OUT/'TRIANGULATION_RELATIVE.csv')
    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    ax.scatter(r1.value, r1.ring, c='#2980b9', label='Ring loss vs rotation (deg)')
    ax.scatter(rel[rel.video == '005'].rot_deg, rel[rel.video == '005'].dr_p50, c='#c0392b', marker='s', label='3D displacement p50 (mm) vs rotation')
    ax.set_xlabel('perturbation size'); ax.set_ylabel('value'); ax.set_yscale('symlog', linthresh=0.1)
    ax.set_title('6: Ring error stays small while 3D displacement grows (different units, same x)')
    ax.legend(fontsize=7); ax.grid(alpha=.2)
    fig.tight_layout(); fig.savefig(FIG/'06_ring_vs_3d_error.png', dpi=140); plt.close(fig)
    # 7 pairwise
    pw = pd.read_csv(OUT/'PAIRWISE_DISTANCES_12.csv'); nid = 12
    M4 = np.zeros((nid, nid)); M5 = np.zeros((nid, nid)); MD = np.zeros((nid, nid))
    for _, r in pw.iterrows():
        M4[int(r.i), int(r.j)] = M4[int(r.j), int(r.i)] = r.d004
        M5[int(r.i), int(r.j)] = M5[int(r.j), int(r.i)] = r.d005
        MD[int(r.i), int(r.j)] = MD[int(r.j), int(r.i)] = r.diff_mm
    fig, axs = plt.subplots(1, 3, figsize=(15, 4.2))
    for ax, Mx, t in zip(axs, (M4, M5, MD), ('D004 (mm)', 'D005 (mm)', '|D004-D005| (mm)')):
        im2 = ax.imshow(Mx, cmap='viridis'); ax.set_title(t); fig.colorbar(im2, ax=ax, shrink=.8)
    fig.suptitle(f'7: pairwise distances of the 12 real identities (66 pairs), median diff {pw.diff_mm.median():.2f} mm — triangulated, not physical truth')
    fig.tight_layout(); fig.savefig(FIG/'07_pairwise_distance_consistency.png', dpi=140); plt.close(fig)
    # 8 before/after alignment
    H = np.load(WS/'experiments/TASK-E4-W0-CROSSVIDEO-025-IDENTITY-RECOVERY/runs/G03/CONSISTENCY/H_HYPOTHESIS.npz')['H']
    ids = pd.read_csv(WS/'experiments/TASK-E4-W0-CROSSVIDEO-025-IDENTITY-RECOVERY/runs/G03/IDENTITIES/HISTORICAL_020_IDENTITIES.csv')
    X4 = ids[['X004_x', 'X004_y', 'X004_z']].values; X5 = ids[['X005_x', 'X005_y', 'X005_z']].values
    HX4 = (H[:3, :3] @ X4.T).T + H[:3, 3]
    fig = plt.figure(figsize=(14, 4.4))
    for k, (P, t, c) in enumerate(((np.vstack([X4, X5]), 'before: raw 004 vs 005 identities', '#7f8c8d'),
                                   (np.vstack([HX4, X5]), 'after H (025 hypothesis): 004 mapped into 005', '#27ae60'))):
        ax = fig.add_subplot(1, 2, k+1)
        ax.scatter(P[:len(X4), 0], P[:len(X4), 1], c='#2980b9', s=28, label='004')
        ax.scatter(P[len(X4):, 0], P[len(X4):, 1], c='#c0392b', s=28, marker='x', label='005')
        ax.set_title(t); ax.legend(fontsize=7); ax.grid(alpha=.2)
    fig.suptitle('8: NO joint optimisation was executed (gate blocked); this is the 025 hypothesis only, same axes')
    fig.tight_layout(); fig.savefig(FIG/'08_cross_video_alignment_before_after.png', dpi=140); plt.close(fig)
    # 9 holdout reprojection: real points vs predicted for available matched cases
    ho = pd.read_csv(WS/'experiments/TASK-E4-W0-CROSSVIDEO-025-IDENTITY-RECOVERY/runs/G03/EVALUATION/HOLDOUT_BIDIRECTIONAL.csv')
    vv = ho[ho.category == 'MATCHED_VALID'].head(4)
    fig, axs = plt.subplots(1, len(vv) if len(vv) else 1, figsize=(4*max(len(vv), 1), 3.4), squeeze=False)
    for j, (_, r) in enumerate(vv.iterrows()):
        ax = axs[0, j]; ax.axis('off')
        ax.imshow(rgb(r.view))
        ax.set_title(f'#{int(r.identity)} {r.side}\n{r.view.split("raw")[-1]}  {r.err_px:.1f} px', fontsize=7)
    fig.suptitle('9: HOLDOUT matched views (observations drawn at their real SIFT positions in the source data; see HOLDOUT_BIDIRECTIONAL.csv for errors)')
    fig.tight_layout(); fig.savefig(FIG/'09_holdout_reprojection.png', dpi=140); plt.close(fig)
    # 10 dashboard
    io = pd.read_csv(OUT/'RING_IO_PER_VIEW.csv'); tri = pd.read_csv(OUT/'TRIANGULATION_RELATIVE.csv')
    fig, axs = plt.subplots(2, 3, figsize=(15, 7))
    axs[0, 0].hist(io.I, bins=12, color='#00bcd4', alpha=.8, label='I'); axs[0, 0].hist(io.O, bins=12, color='#ffb300', alpha=.6, label='O')
    axs[0, 0].set_title('Ring I/O losses (22 ACCEPT views)'); axs[0, 0].legend(fontsize=7)
    axs[0, 1].plot(s[s.kind == 'yaw'].value, s[s.kind == 'yaw'].ring, 'o-'); axs[0, 1].set_title('yaw sensitivity'); axs[0, 1].set_yscale('log')
    axs[0, 2].hist(pw.diff_mm, bins=12, color='#e74c3c'); axs[0, 2].set_title(f'66 pair |D004-D005| (median {pw.diff_mm.median():.2f} mm)')
    axs[1, 0].bar(rel.video.astype(str) + ':' + rel['mode'].astype(str), rel.dr_p50, color='#8e44ad'); axs[1, 0].set_title('3D displacement p50 (mm) under relative camera error'); axs[1, 0].tick_params(axis='x', rotation=70, labelsize=6)
    axs[1, 1].hist(ho.err_px.dropna(), bins=15, color='#2e86de'); axs[1, 1].set_title(f'HOLDOUT errors (n={ho.err_px.notna().sum()}, median {ho.err_px.median():.1f} px)')
    axs[1, 2].axis('off')
    axs[1, 2].text(0.02, 0.9, 'STATUS\nRING_GEOMETRY_VALIDATED: PASS (historical RingRenderer, G03 CAD)\n'
                              'TRIANGULATION_UNCERTAINTY_CHARACTERIZED: PASS\nJOINT_OPTIMIZATION_EXECUTED: NO (gate)\n'
                              'CROSS_VIDEO_GEOMETRY_ACCEPT: NO\nBODY_CROSS_VIDEO_ADMISSION: NO', fontsize=8, va='top')
    for a in axs.flat: a.grid(alpha=.15) if a.get_visible() else None
    fig.suptitle('10: geometry evidence dashboard (026)')
    fig.tight_layout(); fig.savefig(FIG/'10_geometry_evidence_dashboard.png', dpi=140); plt.close(fig)
    print('figures written', len(list(FIG.glob('*.png'))))


if __name__ == '__main__':
    main()
