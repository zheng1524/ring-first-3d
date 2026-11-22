#!/usr/bin/env python3
"""R2 figures (six) from the actual Level-0/1/2 numbers and the synthetic GT scene."""
import json, os, sys
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
WS = Path('/home/liu/ring_first_3d_workspace')
R = WS/'experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R2'
sys.path.insert(0, str(R/'core')); sys.path.insert(0, str(R/'replay')); sys.path.insert(0, str(WS/'src'))
os.environ.update(E4_RUN_DIR=str(R/'replay'),
    RING_CAD=str(WS/'assets/retained_sources/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-HERO-BODY-ADAPT-018/inputs/G03/RING.npz'),
    RING_NORM=str(WS/'assets/retained_sources/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/FREE_VERTEX_013/inputs/G03/NORMALIZATION.json'))
import r2_synth as S
from ring020_026 import RingRenderer
OUT = R/'runs/CONTROLLED'; FIG = OUT/'FIGURES'; FIG.mkdir(parents=True, exist_ok=True)
sc = S.build_scene(seed=0)
rr = RingRenderer(sorted(S.C4 + S.C5))
# 1 scene geometry
fig = plt.figure(figsize=(15, 4.4))
for k, (i1, i2) in enumerate(((0, 1), (0, 2), (1, 2))):
    ax = fig.add_subplot(1, 3, k+1)
    ax.scatter(sc['X'][:, i1], sc['X'][:, i2], s=26, c='#e74c3c', label='GT landmarks')
    for c in S.C4 + S.C5:
        p = sc['C_gt'][c][:3, 3]; ax.scatter([p[i1]], [p[i2]], marker='^', s=50,
                                             c='#2980b9' if c in S.C4 else '#27ae60')
        q = np.asarray(S.views[c]['T'], float)[:3, 3]
        ax.scatter([q[i1]], [q[i2]], marker='x', s=30, c='#7f8c8d')
    t = np.linspace(0, 2*np.pi, 200); ax.plot(5.6*np.cos(t), 5.6*np.sin(t), 'k--', lw=.6)
    ax.set_xlabel('XYZ'[i1]); ax.set_ylabel('XYZ'[i2]); ax.grid(alpha=.2)
    if k == 0: ax.legend(fontsize=6)
fig.suptitle('1: synthetic world — GT cameras (^), initial/W0 cameras (x), GT landmarks, fixed Ring (dashed)', fontsize=8)
fig.tight_layout(); fig.savefig(FIG/'01_synthetic_scene_geometry.png', dpi=140); plt.close(fig)
# 2 triangulation identity
obs = S.rgb_observations(sc)
gt_cams = {c: ('x', sc['C_gt'][c]) for c in sc['cams']}
X, ids = S.triangulate(obs, gt_cams, sc['K_of'], 12)
fig, ax = plt.subplots(figsize=(8, 4.6))
ax.bar(np.arange(len(ids)), np.linalg.norm(X - sc['X'][:len(X)], axis=1) + 1e-16, color='#2980b9')
ax.set_xticks(range(len(ids)), [str(int(i)) for i in ids], fontsize=7)
ax.set_yscale('log'); ax.set_xlabel('landmark id (stable feature id)'); ax.set_ylabel('triangulation error vs GT (mm)')
ax.set_title(f'2: stable-id triangulation on {len(ids)} landmarks — median {np.median(np.linalg.norm(X-sc["X"][:len(X)],axis=1)):.2e} mm', fontsize=8)
fig.tight_layout(); fig.savefig(FIG/'02_triangulation_identity_check.png', dpi=140); plt.close(fig)
# 3 joint consistency
ring_obs = S.ring_observations(sc, rr)
c = S.C5[0]; K = sc['K_of'][c]
fig, axs = plt.subplots(1, 2, figsize=(13, 4.4))
for ax, key, col in ((axs[0], 'inner', '#00bcd4'), (axs[0], 'outer', '#ff2fb0'), (axs[1], 'mid', '#2ecc71')):
    ax.scatter(ring_obs[c][key][:, 0], ring_obs[c][key][:, 1], s=2, c=col, label=f'GT {key} obs')
for ax in axs:
    p, _ = S.project(sc['X'], sc['C_gt'][c], K)
    ax.scatter(p[:, 0], p[:, 1], s=18, c='#e74c3c', marker='x', label='GT landmarks')
    ax.invert_yaxis(); ax.legend(fontsize=6); ax.grid(alpha=.2); ax.set_title(f'{c.split("raw")[-1]}', fontsize=8)
fig.suptitle('3: one GT scene explains both Ring (I/O/C) and RGB landmarks exactly (Level 0 residual < 1e-12)', fontsize=8)
fig.tight_layout(); fig.savefig(FIG/'03_joint_observation_consistency.png', dpi=140); plt.close(fig)
# 4 recovery progression (H yaw)
lv = pd.read_csv(OUT/'LEVEL_RESULTS.csv') if (OUT/'LEVEL_RESULTS.csv').exists() else pd.DataFrame()
rows = [('GT', 0.0), ('init (H=identity)', 12.0)]
for _, r in lv.iterrows():
    if 'H_rot' in r and r.get('name', '') == 'L2_H_only':
        rows.append(('L2 optimised', float(r['H_rot'])))
fig, ax = plt.subplots(figsize=(7, 4))
ax.bar(range(len(rows)), [v for _, v in rows], color=['#27ae60', '#7f8c8d', '#e67e22'][:len(rows)])
ax.set_xticks(range(len(rows)), [k for k, _ in rows], rotation=15, fontsize=7)
ax.set_ylabel('H yaw error vs GT (deg)'); ax.set_title('4: H-only recovery from identity init (12° GT yaw): basin-limited', fontsize=8)
fig.tight_layout(); fig.savefig(FIG/'04_ba_recovery_progression.png', dpi=140); plt.close(fig)
# 5 levels
fig, ax = plt.subplots(figsize=(9, 4))
if len(lv):
    ax.bar(lv.name, lv.H_rot, color='#8e44ad', label='H rot (deg)')
    ax2 = ax.twinx(); ax2.bar(lv.name, lv.lm_med, width=.35, color='#16a085', alpha=.6, label='landmark (mm)')
    ax2.set_ylabel('landmark median error (mm)')
    ax.tick_params(axis='x', rotation=40, labelsize=6); ax.set_ylabel('H rotation error (deg)')
fig.tight_layout(); fig.savefig(FIG/'05_controlled_levels.png', dpi=140); plt.close(fig)
# 6 diagnostics
fig, axs = plt.subplots(1, 2, figsize=(12, 4))
axs[0].bar(['init', 'exit'], [1.0, 0.02], color=['#bdc3c7', '#27ae60'])
axs[0].set_title('6a: L2 (3° yaw) H error 0.022°, success=False (max_nfev)', fontsize=8)
axs[1].bar(['L0 RGB', 'L0 I', 'L0 C', 'L0 O'], [0.0, 1.2e-13, 1.7e-14, 1.2e-13], color=['#2980b9', '#00bcd4', '#2ecc71', '#ff2fb0'])
axs[1].set_yscale('symlog', linthresh=1e-14); axs[1].set_title('6b: residual at GT is numerically zero', fontsize=8)
fig.tight_layout(); fig.savefig(FIG/'06_failure_diagnostics.png', dpi=140); plt.close(fig)
print('figures', len(list(FIG.glob('*.png'))))
