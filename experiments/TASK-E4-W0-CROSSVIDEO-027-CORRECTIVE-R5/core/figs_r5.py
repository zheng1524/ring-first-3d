#!/usr/bin/env python3
"""R5 figures (7) — all values read from runs/*.csv; nothing hard-coded."""
from pathlib import Path
import numpy as np, pandas as pd, json
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
R5 = Path('/home/liu/ring_first_3d_workspace/experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R5')
OUT = R5/'runs'; FIG = OUT/'FIGURES'; FIG.mkdir(parents=True, exist_ok=True)
def rd(n):
    p = OUT/n
    return pd.read_csv(p) if p.exists() else pd.DataFrame()
hc = rd('H_CANDIDATES.csv'); tri = rd('TRIANGULATION_BY_H.csv'); cg = rd('C_GROUP.csv')
pl = rd('PIPELINES.csv'); bc = rd('B_CAMERA.csv')
def sav(fig, n):
    fig.tight_layout(); fig.savefig(FIG/n, dpi=140); plt.close(fig)
# 1 cameras under candidates
fig, ax = plt.subplots(figsize=(6.8, 5.4))
if len(hc):
    for _, r in hc.head(8).iterrows():
        ax.scatter(r.yaw, r.ring, s=20, label=None)
ax.set_xlabel('initial yaw of the H candidate (deg)'); ax.set_ylabel('Ring energy after refinement')
ax.set_title('1: Ring-only candidates (each dot = one refined H); Ring is flat in yaw by symmetry', fontsize=8)
sav(fig, '01_ring_coordinate_and_H_candidates.png')
# 2 ring symmetry vs RGB selection
fig, axs = plt.subplots(1, 2, figsize=(13, 4))
if len(hc):
    axs[0].plot(hc.yaw, hc.ring, 'o-', c='#00bcd4'); axs[0].set_xlabel('candidate yaw (deg)'); axs[0].set_ylabel('Ring energy')
    axs[0].set_title('2a: Ring energy is flat in yaw (unidentifiable)', fontsize=8)
    axs[1].plot(hc.yaw, hc.epi, 'o-', c='#e74c3c'); axs[1].set_xlabel('candidate yaw (deg)'); axs[1].set_ylabel('median Sampson (px)')
    axs[1].set_title('2b: cross-video 2D epipolar error selects yaw', fontsize=8)
    for a in axs: a.grid(alpha=.25)
sav(fig, '02_ring_symmetry_and_rgb_selection.png')
# 3 triangulation under H
fig, ax = plt.subplots(figsize=(7.6, 4))
if len(tri):
    x = np.arange(len(tri)); ax.bar(x-0.2, tri.lm_T1, 0.4, label='T1 triangulated', color='#2980b9')
    ax.bar(x+0.2, tri.lm_T2, 0.4, label='T2 refined', color='#27ae60')
    ax.set_xticks(x, tri.init); ax.set_ylabel('landmark error vs GT (mm)'); ax.legend(fontsize=7)
    ax.set_title('3: joint triangulation quality under different H initialisations', fontsize=8)
sav(fig, '03_H_initialization_vs_triangulation.png')
# 4 C group
fig, ax = plt.subplots(figsize=(9, 4))
if len(cg):
    x = np.arange(len(cg)); ax.bar(x-0.2, cg.lm_init, 0.4, label='init', color='#bdc3c7')
    ax.bar(x+0.2, cg.lm_final, 0.4, label='final', color='#8e44ad')
    ax.set_xticks(x, cg.tag, fontsize=7); ax.set_ylabel('landmark error (mm)'); ax.legend(fontsize=7)
    ax.set_title('4: X-only recovery with correct H (C0/C1/C3/C3-depth/C3-perp/C3-wrongH/C3-H2)', fontsize=8)
sav(fig, '04_correct_H_landmark_recovery.png')
# 5 rgb reprojection
fig, ax = plt.subplots(figsize=(7, 4))
if len(tri):
    ax.bar(tri.init, tri.lm_T1, color='#16a085')
    ax.set_ylabel('T1 landmark error (mm)'); ax.set_title('5: RGB consistency by H (proxy: T1 landmark error)', fontsize=8)
sav(fig, '05_rgb_reprojection_by_H_candidate.png')
# 6 ring vs rgb diagnostics
fig, ax = plt.subplots(figsize=(7, 4.4))
if len(hc):
    ax.scatter(hc.ring, hc.epi, c=hc.yaw, cmap='viridis', s=40)
    ax.set_xlabel('Ring energy'); ax.set_ylabel('median Sampson (px)'); ax.set_title('6: Ring vs RGB diagnostics per candidate (colour = yaw)', fontsize=8)
    ax.grid(alpha=.2)
sav(fig, '06_ring_rgb_joint_diagnostics.png')
# 7 pipeline comparison
fig, axs = plt.subplots(1, 2, figsize=(13, 4))
if len(tri):
    axs[0].bar(tri.init, pd.to_numeric(tri.H_rot, errors='coerce'), color='#e67e22')
    axs[0].set_ylabel('H error of the initialisation (deg)')
    axs[1].bar(tri.init, pd.to_numeric(tri.lm_T1, errors='coerce'), color='#8e44ad')
    axs[1].set_ylabel('joint triangulation error (mm)')
    fig.suptitle('7: H initialisation -> joint triangulation. PIPELINES.csv INVALID (script bug), NOT_EXECUTED', fontsize=8)
sav(fig, '07_pipeline_comparison.png')
print('figures', len(list(FIG.glob('*.png'))), 'tables', {k: len(v) for k, v in dict(hc=hc, tri=tri, cg=cg, pl=pl, bc=bc).items()})
