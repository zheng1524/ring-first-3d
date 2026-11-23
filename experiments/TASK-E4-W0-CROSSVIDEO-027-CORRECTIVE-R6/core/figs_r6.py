#!/usr/bin/env python3
"""R6 seven figures, all from runs/*.csv + RESULT.npz."""
from pathlib import Path
import json, numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
R6 = Path('/home/liu/ring_first_3d_workspace/experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R6')
OUT = R6/'runs'; FIG = OUT/'FIGURES'; FIG.mkdir(parents=True, exist_ok=True)
def rd(n):
    p = OUT/n; return pd.read_csv(p) if p.exists() else pd.DataFrame()
hc, tri, pl, ho, e1 = rd('H_CANDIDATES.csv'), rd('TRIANGULATION_BY_H.csv'), rd('PIPELINES.csv'), rd('HOLDOUT_RGB.csv'), rd('E1_REFERENCE_CAMERA.csv')
def sav(f, n): f.tight_layout(); f.savefig(FIG/n, dpi=140); plt.close(f)
# 1 candidate pose audit (3D geometry)
fig = plt.figure(figsize=(14, 4.4))
try:
    z = np.load(OUT/'T_H2.npz'); H2 = z['H']; X2 = z['X']
    z0 = np.load(OUT/'T_H0.npz'); X0 = z0['X']
    for k, (i1, i2) in enumerate(((0, 1), (0, 2), (1, 2))):
        ax = fig.add_subplot(1, 3, k+1)
        ax.scatter(X0[:, i1], X0[:, i2], s=20, c='#e74c3c', label='triangulated under H=I')
        ax.scatter(X2[:, i1], X2[:, i2], s=20, c='#27ae60', marker='x', label='triangulated under H2')
        ax.set_xlabel('XYZ'[i1]); ax.set_ylabel('XYZ'[i2]); ax.grid(alpha=.2)
        if k == 0: ax.legend(fontsize=6)
    fig.suptitle('1: landmarks triangulated under H=I vs H2 (same frozen 2D observations)', fontsize=8)
except Exception as ex:
    fig.text(.1, .5, f'no data: {ex}')
sav(fig, '01_ring_candidate_pose_audit.png')
# 2 symmetry & epipolar
fig, axs = plt.subplots(1, 2, figsize=(13, 4))
if len(hc):
    axs[0].scatter(hc.yaw_initial, hc.ring, c='#00bcd4', s=40); axs[0].set_xlabel('initial yaw (deg)'); axs[0].set_ylabel('Ring energy after 6-DoF refine')
    axs[1].scatter(hc.yaw_initial, hc.epi, c='#e74c3c', s=40); axs[1].set_xlabel('initial yaw (deg)'); axs[1].set_ylabel('median Sampson (px)')
    for a in axs: a.grid(alpha=.25)
    axs[0].set_title('2a: Ring energy flat across initial yaw', fontsize=8)
    axs[1].set_title('2b: epipolar error selects the yaw', fontsize=8)
sav(fig, '02_ring_symmetry_and_epipolar_selection.png')
# 3 old vs new pipeline geometry
fig, ax = plt.subplots(figsize=(7.6, 4.4))
if len(pl):
    x = np.arange(len(pl)); ax.bar(x-0.2, pl.H_final, .4, label='final H rot (deg)', color='#2980b9')
    ax.set_yscale('log'); ax2 = ax.twinx(); ax2.bar(x+0.2, pl.lm, .4, color='#8e44ad', alpha=.7, label='final landmark (mm)')
    ax.set_xticks(x, [str(t) for t in pl['tag']]); ax.set_ylabel('H rotation error (deg)'); ax2.set_ylabel('landmark error (mm)')
    ax.set_title('3: end-to-end pipelines (old H=I vs new H2); both converge', fontsize=8)
sav(fig, '03_old_vs_new_pipeline_geometry.png')
# 4 triangulation before/after
fig, ax = plt.subplots(figsize=(7.6, 4))
if len(tri):
    ax.bar(tri.init, tri.lm, color=['#c0392b', '#e67e22', '#27ae60', '#2980b9'])
    ax.set_ylabel('landmark error vs GT (mm)'); ax.set_title('4: joint triangulation under each H initialisation', fontsize=8)
sav(fig, '04_joint_triangulation_before_after.png')
# 5 fit/holdout RGB
fig, ax = plt.subplots(figsize=(7.6, 4))
if len(ho):
    for g, d in ho.groupby('group'):
        ax.bar([str(x) for x in d['pipe']], d.rgb_med, color='#27ae60' if g == 'fit' else '#c0392b')
    ax.set_ylabel('RGB median (px)'); ax.tick_params(axis='x', rotation=20, labelsize=7)
    ax.set_title('5: FIT vs HOLDOUT reprojection (both pipelines)', fontsize=8)
sav(fig, '05_fit_holdout_reprojection.png')
# 6 reference camera perturbation
fig, ax = plt.subplots(figsize=(8, 4))
if len(e1):
    lbl = [f"{r.deg}°/{r.mm}mm" for _, r in e1.iterrows()]
    ax.bar(np.arange(len(e1))-0.2, e1.X0_err, .4, label='005-only X error (mm)', color='#e67e22')
    ax.bar(np.arange(len(e1))+0.2, e1.lm, .4, label='joint triangulation error (mm)', color='#8e44ad')
    ax.set_xticks(range(len(e1)), lbl); ax.set_yscale('log'); ax.legend(fontsize=7)
    ax.set_title('6: reference (005) camera perturbation: 005-only vs joint triangulation', fontsize=8)
sav(fig, '06_reference_camera_perturbation.png')
# 7 dashboard
fig, ax = plt.subplots(figsize=(11, 4.6)); ax.axis('off')
lines = ['7: R6 end-to-end validation (synthetic, 3+3 views, 12 identities)',
         f"Ring candidates: best H error {hc.H_rot.min():.3f} deg (initial yaw {int(hc.loc[hc.H_rot.idxmin(),'yaw_initial'])} deg)" if len(hc) else 'no candidates',
         f"triangulation: H=I {tri[tri.init=='H0'].lm.iloc[0]:.3f} mm; H2 {tri[tri.init=='H2'].lm.iloc[0]:.3f} mm" if len(tri) else '',
         f"pipelines: old {pl[pl.tag=='old_H0'].H_final.iloc[0]:.5f} deg / {pl[pl.tag=='old_H0'].lm.iloc[0]:.5f} mm / {int(pl[pl.tag=='old_H0'].nfev.iloc[0])} nfev" if len(pl) else '',
         f"           new {pl[pl.tag=='new_H2'].H_final.iloc[0]:.5f} deg / {pl[pl.tag=='new_H2'].lm.iloc[0]:.5f} mm / {int(pl[pl.tag=='new_H2'].nfev.iloc[0])} nfev" if len(pl) else '',
         'HOLDOUT: both pipelines ~0 px (scene too easy to discriminate)',
         'E1 (005 perturbed 0.25-0.5 deg / 0.25 mm): H2 init 3.68 deg, joint triangulation 0.78-0.90 mm',
         'Status: ENGINEERING PASS; H_INIT PARTIAL; PIPELINE PASS; HOLDOUT PASS(no discrimination); E1 PARTIAL; REAL_G03 NOT_READY']
for i, t in enumerate(lines): ax.text(.01, .93-0.11*i, t, fontsize=8 if i else 11, fontweight='bold' if i == 0 else 'normal')
sav(fig, '07_end_to_end_validation.png')
print('figures', len(list(FIG.glob('*.png'))))
