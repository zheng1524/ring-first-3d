#!/usr/bin/env python3
"""P6: figures from the actual numbers computed in this task (sources labelled on every axis/title)."""
import json
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
WS = Path('/home/liu/ring_first_3d_workspace')
B = WS/'experiments/TASK-E4-W0-CROSSVIDEO-027-RING-ANCHORED-BA-PILOT'
OUT = B/'runs/G03'; FIG = OUT/'FIGURES'; FIG.mkdir(parents=True, exist_ok=True)
views = {v['id']: v for v in json.loads((B/'replay'/'config'/'VIEWS.json').read_text())}
split = json.loads((OUT/'SPLIT.json').read_text())
abc = pd.read_csv(OUT/'ABC_EVALUATION.csv'); upd = pd.read_csv(OUT/'PER_CAMERA_UPDATES.csv')
ctl = pd.read_csv(OUT/'CONTROLLED'/'CONTROLLED_BA_RESULTS.csv'); pair = pd.read_csv(OUT/'RING_3D_PAIRED_SENSITIVITY.csv')


def main():
    # 1 architecture
    fig, ax = plt.subplots(figsize=(11, 5.5)); ax.axis('off')
    ax.text(.5, .95, '1: Ring-anchored BA graph (variables vs factors)', ha='center', fontsize=12, fontweight='bold')
    ax.text(.08, .72, 'FIXED\nRing CAD (G03 RING.npz)\n005 Ring world frame', fontsize=9, bbox=dict(boxstyle='round', fc='#e8f5e9'))
    ax.text(.08, .42, 'VARIABLES\nH (6 DoF)\ncam dxi (6 x n_released)\nlandmarks X_j (3 x 12)', fontsize=9, bbox=dict(boxstyle='round', fc='#e3f2fd'))
    ax.text(.55, .72, 'FACTORS\nRGB reprojection (real uv)\nRing per-point distance (frozen edges)\nW0 pose prior (0.5 deg / 0.25 mm)\nweak landmark prior', fontsize=9, bbox=dict(boxstyle='round', fc='#fff3e0'))
    ax.text(.55, .42, 'GAUGE\n005 anchor camera fixed\n004 video placement carried by H\nRing yaw unobservable', fontsize=9, bbox=dict(boxstyle='round', fc='#fce4ec'))
    ax.text(.08, .12, f'observations: {len(pd.read_csv(OUT/"FROZEN_BA_OBSERVATIONS.csv"))} (12 identities, 11 FIT cameras)\nsolver: scipy.optimize.least_squares TRF + huber(f_scale=3), numerical sparse Jacobian', fontsize=8)
    fig.tight_layout(); fig.savefig(FIG/'01_ring_anchored_ba_graph.png', dpi=140); plt.close(fig)
    # 2 trajectories
    fig, ax = plt.subplots(figsize=(6.4, 5.4))
    for c, v in views.items():
        p = np.asarray(v['T'])[:3, 3]
        col = '#2980b9' if v['video'] == '004' else '#c0392b'
        m = 'o' if c in split['fit4'] or c in split['fit5'] else 'x'
        ax.scatter(p[0], p[1], c=col, marker=m, s=30)
    t = np.linspace(0, 2*np.pi, 200); ax.plot(5.6*np.cos(t), 5.6*np.sin(t), 'k--', lw=.7, label='Ring centreline R=5.6 mm')
    ax.set_xlabel('x (mm)'); ax.set_ylabel('y (mm)'); ax.set_aspect('equal')
    ax.set_title('2: W0 camera positions (o=FIT, x=HOLDOUT); BA kept every camera within priors', fontsize=8)
    ax.legend(fontsize=7); fig.tight_layout(); fig.savefig(FIG/'02_camera_trajectories_ABC.png', dpi=140); plt.close(fig)
    # 3 per-camera updates
    fig, ax = plt.subplots(figsize=(10, 4))
    x = np.arange(len(upd)); w = .38
    ax.bar(x-w/2, upd.rot_deg, w, label='rotation update (deg)', color='#8e44ad')
    ax.bar(x+w/2, upd.trans_mm, w, label='translation update (mm)', color='#16a085')
    ax.set_xticks(x, [c.split('raw')[-1] + ':' + str(v) for c, v in zip(upd.cam, upd.video)], rotation=70, fontsize=6)
    ax.set_yscale('log'); ax.legend(fontsize=7); ax.grid(alpha=.2)
    ax.set_title('3: released 004 camera updates (C config). Ring_A vs Ring_C below', fontsize=8)
    fig.tight_layout(); fig.savefig(FIG/'03_per_camera_pose_updates.png', dpi=140); plt.close(fig)
    # 4 RGB before/after
    fig, ax = plt.subplots(figsize=(8, 4))
    for i, (lab, col) in enumerate((('A_W0_single', '#2980b9'), ('B1_H_only_lam10', '#e67e22'), ('C_BA', '#c0392b'))):
        row = abc[abc.label == lab]
        if len(row):
            ax.bar(i, row.rgb_median.iloc[0], color=col, width=.6)
            ax.text(i, row.rgb_median.iloc[0], f"med {row.rgb_median.iloc[0]:.2f}\np90 {row.rgb_p90.iloc[0]:.1f}", ha='center', va='bottom', fontsize=7)
    ax.set_xticks(range(3), ['A W0 per-video', 'B H+landmarks', 'C BA (004 released)'])
    ax.set_ylabel('RGB reprojection (px)'); ax.set_title('4: FIT RGB reprojection of the 106 frozen observations', fontsize=8)
    fig.tight_layout(); fig.savefig(FIG/'04_rgb_reprojection_before_after.png', dpi=140); plt.close(fig)
    # 5 ring before/after
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(np.arange(3)-.2, [abc.ring_MIO_004.iloc[i] for i in range(3)], .4, label='004 Ring MIO', color='#2980b9')
    ax.bar(np.arange(3)+.2, [abc.ring_MIO_005.iloc[i] for i in range(3)], .4, label='005 Ring MIO', color='#c0392b')
    ax.set_xticks(range(3), abc.label, rotation=15, fontsize=7); ax.set_yscale('log')
    ax.set_ylabel('Ring MIO (historical Huber/3 mean)'); ax.legend(fontsize=7); ax.grid(alpha=.2)
    ax.set_title('5: Ring must NOT be sacrificed — B/C move 004 cameras ~50x off the Ring', fontsize=8)
    fig.tight_layout(); fig.savefig(FIG/'05_ring_constraints_before_after.png', dpi=140); plt.close(fig)
    # 6 shared landmark geometry
    ident = pd.read_csv(WS/'experiments/TASK-E4-W0-CROSSVIDEO-025-IDENTITY-RECOVERY/runs/G03/IDENTITIES/HISTORICAL_020_IDENTITIES.csv')
    X4 = ident[['X004_x', 'X004_y', 'X004_z']].values; X5 = ident[['X005_x', 'X005_y', 'X005_z']].values
    fig = plt.figure(figsize=(14, 4.2))
    for k, (i1, i2) in enumerate(((0, 1), (0, 2), (1, 2))):
        ax = fig.add_subplot(1, 3, k+1)
        ax.scatter(X4[:, i1], X4[:, i2], s=22, c='#2980b9', label='X004 (019)')
        ax.scatter(X5[:, i1], X5[:, i2], s=22, c='#c0392b', marker='x', label='X005 (019)')
        for a, b in zip(X4, X5): ax.plot([a[i1], b[i1]], [a[i2], b[i2]], c='#bdc3c7', lw=.7)
        ax.set_xlabel('XYZ'[i1]); ax.set_ylabel('XYZ'[i2]); ax.grid(alpha=.2)
        if k == 0: ax.legend(fontsize=7)
    fig.suptitle('6: the 12 real identities in their own (unregistered) frames — the gap BA had to close', fontsize=8)
    fig.tight_layout(); fig.savefig(FIG/'06_shared_landmark_geometry.png', dpi=140); plt.close(fig)
    # 7 diagnostics
    st = json.loads((OUT/'BA_RUN_STATE.json').read_text())
    fig, axs = plt.subplots(1, 2, figsize=(11, 4))
    axs[0].bar(['B1 (H+lm)', 'C (BA)'], [st['B_cost'], st['C_cost']], color=['#e67e22', '#c0392b'])
    axs[0].set_title('7a: final cost (sum of squares); per-iteration history NOT_RECORDED by scipy TRF', fontsize=7)
    axs[1].bar(['B1', 'C'], [st['B_nfev'], st['C_nfev']], color=['#e67e22', '#c0392b'])
    axs[1].set_title('7b: function evaluations', fontsize=8)
    fig.tight_layout(); fig.savefig(FIG/'07_optimization_diagnostics.png', dpi=140); plt.close(fig)
    # 8 holdout
    fig, ax = plt.subplots(figsize=(7, 4)); ax.axis('off')
    ax.text(.02, .85, '8: HOLDOUT evaluation for BA — NOT_EVALUABLE', fontsize=11, fontweight='bold')
    ax.text(.02, .62, 'Reason: the BA was rejected by the Ring gate before any candidate was\n'
                      'accepted (see fig 5). Evaluating HOLDOUT for a model that already\n'
                      'violates the fixed Ring geometry would produce a cherry-picked number.\n'
                      'The frozen 025 HOLDOUT statistics remain the reference:\n'
                      '52 matched / 24 >10 px / 80 unmatched; median 7.91 px, p90 83.74 px.', fontsize=8, va='top')
    fig.tight_layout(); fig.savefig(FIG/'08_holdout_before_after.png', dpi=140); plt.close(fig)
    # 9 dashboard
    fig, axs = plt.subplots(2, 2, figsize=(13, 7))
    axs[0, 0].scatter(pair.ring_mio_median, pair.dr_p50, c='#8e44ad')
    for _, r in pair.iterrows(): axs[0, 0].annotate(f"{r.video}:{r['mode']}", (r.ring_mio_median, r.dr_p50), fontsize=5)
    axs[0, 0].set_xlabel('Ring MIO (same cameras)'); axs[0, 0].set_ylabel('3D displacement p50 (mm)')
    axs[0, 0].set_title('9a: PAIRED sensitivity (same camera matrices)', fontsize=8); axs[0, 0].grid(alpha=.2)
    axs[0, 1].bar(ctl.scenario, ctl.cam_rot_max_deg, color='#2980b9'); axs[0, 1].tick_params(axis='x', rotation=80, labelsize=5)
    axs[0, 1].set_yscale('log'); axs[0, 1].set_title('9b: controlled BA camera rotation error (deg)', fontsize=8)
    axs[1, 0].bar(abc.label, abc.ring_MIO_004, color='#c0392b'); axs[1, 0].tick_params(axis='x', rotation=20, labelsize=6)
    axs[1, 0].set_yscale('log'); axs[1, 0].set_title('9c: 004 Ring MIO — BA dragged cameras off the Ring', fontsize=8)
    axs[1, 1].axis('off')
    axs[1, 1].text(.02, .9, 'VERDICT\nRing-anchored BA pilot: FAILED the Ring-preservation gate.\n'
                            'A (W0 per-video): RGB med 0.45 px, Ring 0.160\nB (H+lm): RGB 3.80 px, Ring004 53.2\n'
                            'C (BA): RGB 0.59 px, Ring004 54.2\n'
                            '=> no accepted camera set; CROSS_VIDEO_GEOMETRY_ACCEPT = NO\n'
                            'controlled: well-posed <=0.03 deg; outliers/unidentifiable fail as expected', fontsize=8, va='top')
    fig.suptitle('9: BA comparison dashboard (027)', fontsize=10)
    fig.tight_layout(); fig.savefig(FIG/'09_ba_comparison_dashboard.png', dpi=140); plt.close(fig)
    print('figures', len(list(FIG.glob('*.png'))))


if __name__ == '__main__':
    main()
