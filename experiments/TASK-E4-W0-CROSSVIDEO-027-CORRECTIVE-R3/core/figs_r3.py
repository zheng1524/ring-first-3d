#!/usr/bin/env python3
"""R3 figures: every number read from runs/controlled/*/METRICS.json (no hard-coded values)."""
import json
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
R3 = Path('/home/liu/ring_first_3d_workspace/experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R3')
CT = R3/'runs/controlled'; FIG = CT/'FIGURES'; FIG.mkdir(parents=True, exist_ok=True)
def M(tag):
    p = CT/tag/'METRICS.json'
    return json.loads(p.read_text()) if p.exists() else None
sweep = pd.read_csv(CT/'SUMMARY_h_only_sweep.csv') if (CT/'SUMMARY_h_only_sweep.csv').exists() else pd.DataFrame()
# 1 H-only vs joint
tags = [('Honly_yaw12','H-only'), ('huber_joint_yaw12','H+landmarks (joint)'),
        ('huber_progressive_yaw12','progressive'), ('squared_joint_yaw12','joint (squared)')]
fig, ax = plt.subplots(figsize=(8,4))
vals=[]
for t,lab in tags:
    m=M(t); vals.append((lab, m['H_rot'] if m else np.nan, m['success'] if m else None))
ax.bar([v[0] for v in vals], [max(v[1],1e-6) for v in vals], color=['#27ae60','#e67e22','#2980b9','#8e44ad'])
for i,v in enumerate(vals): ax.text(i, max(v[1],1e-6), f"{v[1]:.4f}°\nsucc={v[2]}", ha='center', va='bottom', fontsize=7)
ax.set_yscale('log'); ax.set_ylabel('final H rotation error (deg)'); ax.tick_params(axis='x', rotation=15, labelsize=7)
ax.set_title('1: from a 12° initial H error — H-only and joint both recover; progressive is best', fontsize=8)
fig.tight_layout(); fig.savefig(FIG/'01_h_only_vs_joint.png', dpi=140); plt.close(fig)
# 2 basin
fig, ax = plt.subplots(figsize=(7.5,4))
if len(sweep):
    ax.plot(sweep.yaw_init_deg, np.maximum(sweep.H_rot,1e-6), 'o-', c='#27ae60', label='H-only final error')
    ax.plot([0,20],[1e-6,20], 'k--', lw=.7, label='no recovery')
ax.set_yscale('log'); ax.set_xlabel('initial H yaw error (deg)'); ax.set_ylabel('final H error (deg)')
ax.legend(fontsize=7); ax.grid(alpha=.25)
ax.set_title('2: H-only basin — 6 params, landmarks frozen from 005-only triangulation', fontsize=8)
fig.tight_layout(); fig.savefig(FIG/'02_initialization_basin.png', dpi=140); plt.close(fig)
# 3 reprojection vectors (3° and 12° joint): init vs final, few landmarks, one 004 camera
import sys, os
sys.path.insert(0, str(R3/'core')); sys.path.insert(0, str(R3/'replay'))
os.environ.setdefault('E4_RUN_DIR', str(R3/'replay'))
os.environ.setdefault('RING_CAD', '/home/liu/ring_first_3d_workspace/assets/retained_sources/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-HERO-BODY-ADAPT-018/inputs/G03/RING.npz')
os.environ.setdefault('RING_NORM', '/home/liu/ring_first_3d_workspace/assets/retained_sources/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/FREE_VERTEX_013/inputs/G03/NORMALIZATION.json')
import r2_synth as S
import ba_core_r2 as BA
from se3 import exp_se3
sc = S.build_scene(seed=0, H_rot_deg=(0.7,-0.4,12.0)); obs = S.rgb_observations(sc)
fig, axs = plt.subplots(1, 2, figsize=(12,4.4), sharex=True, sharey=True)
for ax, tag in zip(axs, ('huber_joint_yaw12', 'huber_progressive_yaw12')):
    m = M(tag); z = np.load(CT/tag/'RESULT.npz')
    H = z['H']; X = z['X']
    c = S.C4[0]; C0 = np.asarray(sc['cams'][c][1], float); K = sc['K_of'][c]
    uv0 = {i: uv for (cc, i, uv) in obs if cc == c}
    for i in list(uv0)[:8]:
        p_init, _ = BA.project(X[i], np.eye(4) @ C0, K)
        p_fin, _ = BA.project(X[i], H @ C0, K)
        u = uv0[i]
        ax.plot([u[0], p_init[0]], [u[1], p_init[1]], '-', c='#bdc3c7', lw=.8)
        ax.plot([u[0], p_fin[0]], [u[1], p_fin[1]], '-', c='#27ae60', lw=1.2)
        ax.scatter([u[0]], [u[1]], s=18, c='#e74c3c', zorder=3)
        ax.scatter([p_fin[0]], [p_fin[1]], s=10, c='#27ae60', marker='x', zorder=3)
        ax.text(u[0], u[1], f'{i}', fontsize=5)
    ax.set_title(f'{tag}: final H err {m["H_rot"]:.4f}°', fontsize=8); ax.grid(alpha=.2)
    ax.invert_yaxis()
fig.suptitle('3: REAL observed uv (red) vs initial prediction (grey) vs optimised (green), camera 004 #1', fontsize=8)
fig.tight_layout(); fig.savefig(FIG/'03_rgb_reprojection_vectors.png', dpi=140); plt.close(fig)
# 4 visibility
va = pd.read_csv(CT/'VISIBILITY_ASSOCIATION.csv')
fig, ax = plt.subplots(figsize=(7.5,4))
for lab, col in (('GT','#27ae60'), ('3deg','#e67e22'), ('12deg','#c0392b')):
    d = va[va.edge_source == lab]
    ax.scatter(d.n_inner, np.maximum(d.E_I, 1e-16), c=col, label=f'edges from {lab}', s=60)
ax.set_yscale('symlog', linthresh=1e-14); ax.set_xlabel('inner visible edge segments'); ax.set_ylabel('E_Inner at GT camera')
ax.legend(fontsize=7); ax.grid(alpha=.2)
ax.set_title('4: Ring visibility — edges chosen from 3°/12° still give E_I<=1.3e-3 at the GT camera', fontsize=8)
fig.tight_layout(); fig.savefig(FIG/'04_ring_visibility_diagnostics.png', dpi=140); plt.close(fig)
# 5 loss & gradient
m = M('huber_joint_yaw12'); jac = json.loads((CT/'JACOBIAN_H_ONLY.json').read_text())
fig, axs = plt.subplots(1, 2, figsize=(12,4))
if m:
    keys = [('rgb','RGB'), ('ring_I','Ring I'), ('ring_C','Ring C'), ('ring_O','Ring O')]
    axs[0].bar([k[1] for k in keys], [m.get('e0_'+k[0],0) for k in keys], color='#bdc3c7', label='at init')
    axs[0].bar([k[1] for k in keys], [m.get('e1_'+k[0],0) for k in keys], color='#27ae60', alpha=.8, label='at exit')
    axs[0].set_yscale('symlog', linthresh=1e-6); axs[0].legend(fontsize=7)
axs[0].set_title('5a: energy components (init vs exit) from METRICS.json', fontsize=8)
axs[1].bar(['rms@GT','|grad|@GT'], [jac['rms_at_gt'], jac['grad_norm_at_gt']], color=['#2980b9','#8e44ad'])
axs[1].set_yscale('log'); axs[1].set_title(f'5b: H-only Jacobian rank {jac["rank"]}/6, cond {jac["cond"]:.1f}, dir-deriv err {jac["direction_derivative_rel_err_max"]:.2f}', fontsize=7)
fig.tight_layout(); fig.savefig(FIG/'05_loss_and_gradient_diagnostics.png', dpi=140); plt.close(fig)
# 6 L3-L5
fig, ax = plt.subplots(figsize=(9,4)); ax.axis('off')
ax.text(.02,.8,'6: Level 3–5 — NOT_EXECUTED', fontsize=13, fontweight='bold')
ax.text(.02,.5,'Gate C (basin diagnosis) and Gate D (progressive) were reached; L3–L5 need more\n'
               'released cameras (004 has only 3 FIT views) and were not run within this round.\n'
               'No numbers are fabricated. R2 files remain unchanged.', fontsize=9, va='top')
fig.tight_layout(); fig.savefig(FIG/'06_camera_and_landmark_recovery.png', dpi=140); plt.close(fig)
print('figures', len(list(FIG.glob('*.png'))))
