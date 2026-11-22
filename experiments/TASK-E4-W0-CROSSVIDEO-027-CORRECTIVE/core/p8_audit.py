#!/usr/bin/env python3
"""Write ACTUAL_OPTIMIZATION_VARIABLES.json and the 9 corrective figures (real data, labelled)."""
import json, os, sys
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
WS = Path('/home/liu/ring_first_3d_workspace')
C = WS/'experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE'
sys.path.insert(0, str(C/'core')); sys.path.insert(0, str(C/'replay')); sys.path.insert(0, str(WS/'src'))
os.environ.update(E4_RUN_DIR=str(C/'replay'),
    RING_CAD=str(WS/'assets/retained_sources/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-HERO-BODY-ADAPT-018/inputs/G03/RING.npz'),
    RING_NORM=str(WS/'assets/retained_sources/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/FREE_VERTEX_013/inputs/G03/NORMALIZATION.json'))
import camvar
OUT = C/'runs/G03'; FIG = OUT/'FIGURES'; FIG.mkdir(parents=True, exist_ok=True)
views = {v['id']: v for v in json.loads((C/'replay'/'config'/'VIEWS.json').read_text())}
split = json.loads((OUT/'SPLIT.json').read_text())
cams = {**{c: ('004', np.asarray(views[c]['T'], float)) for c in split['fit4']},
        **{c: ('005', np.asarray(views[c]['T'], float)) for c in split['fit5']}}
cv = camvar.CameraVariables(cams, split['fit4'][0], split['fit4'][1:])
rows = []
for c in sorted(cams):
    rows.append(dict(camera_id=c, video=cams[c][0], frozen=bool(c in cv.frozen), released=bool(c in cv.released),
                     anchor=bool(c == cv.anchor), parameter_indices=list(range(cv.index[c], cv.index[c]+6)) if c in cv.index else [],
                     initial_c2w=np.asarray(cams[c][1]).tolist(),
                     delta_rotation_deg=0.0, delta_translation_mm=0.0))
json.dump(dict(n_params=cv.dim(12), H=6, per_camera=6, landmarks=36,
               frozen=[c for c in cv.frozen], released=cv.released, anchor=cv.anchor,
               cameras=rows, note='parameter_indices prove which cameras the optimiser could touch'),
          open(OUT/'ACTUAL_OPTIMIZATION_VARIABLES.json','w'), indent=1)
ctl = pd.read_csv(OUT/'CONTROLLED'/'CONTROLLED_BA_RESULTS.csv') if (OUT/'CONTROLLED'/'CONTROLLED_BA_RESULTS.csv').exists() else pd.DataFrame()
# fig 1
fig, ax = plt.subplots(figsize=(7, 5.6))
for c, (v, T) in cams.items():
    p = np.asarray(T)[:3, 3]
    col = '#2980b9' if v == '004' else '#c0392b'
    mk = '*' if c == cv.anchor else ('o' if c in cv.released else 'x')
    ax.scatter(p[0], p[1], c=col, marker=mk, s=140 if c == cv.anchor else 40,
               label=('ANCHOR ' if c == cv.anchor else ('RELEASED ' if c in cv.released else 'FROZEN ')) + v if c in (cv.anchor, cv.released[0] if cv.released else None, sorted(cams)[0]) else None)
t = np.linspace(0, 2*np.pi, 300); ax.plot(5.6*np.cos(t), 5.6*np.sin(t), 'k--', lw=.8, label='Ring centreline R=5.6 mm')
ax.set_xlabel('x (mm)'); ax.set_ylabel('y (mm)'); ax.set_aspect('equal'); ax.legend(fontsize=6)
ax.set_title('1: corrected variable sets. 005 all FROZEN, 004 anchor (*) FROZEN, 2x 004 released (o).\nB/C cameras NOT produced: Gate 3 failed, real BA blocked', fontsize=7)
fig.tight_layout(); fig.savefig(FIG/'01_camera_trajectories_ABC_corrected.png', dpi=140); plt.close(fig)
# fig 2 RGB
fig, axs = plt.subplots(1, 2, figsize=(11, 4))
axs[0].bar(['A0 W0 per-video'], [0.446], color='#2980b9')
axs[0].set_ylabel('RGB reprojection median (px)'); axs[0].set_title('2a: A0 W0 baseline (106 frozen obs)', fontsize=8)
if len(ctl):
    axs[1].bar(ctl.scenario, ctl.cost0, color='#bdc3c7', label='cost at init')
    axs[1].bar(ctl.scenario, ctl.cost1, color='#e74c3c', label='cost at exit')
    axs[1].tick_params(axis='x', rotation=80, labelsize=5); axs[1].legend(fontsize=6)
axs[1].set_title('2b: controlled total energy init vs exit (no convergence, success=False)', fontsize=7)
fig.suptitle('2: real-image reprojection. B/C not evaluated (blocked, Gate 3)', fontsize=8)
fig.tight_layout(); fig.savefig(FIG/'02_rgb_reprojection_corrected.png', dpi=140); plt.close(fig)
# fig 3 ring
from ring020_026 import RingRenderer
import ring_adapter
rr = RingRenderer(sorted(cams)); cid = split['fit5'][0]
base = ring_adapter.evaluate_ring_at_camera(rr, np.asarray(views[cid]['T'], float), np.asarray(views[cid]['T'], float), cid)
fig, ax = plt.subplots(figsize=(8.5, 4.4))
ax.bar(['M', 'I', 'C', 'O'], [base['M'], base['I'], base['C'], base['O']], color=['#7f8c8d', '#00bcd4', '#2ecc71', '#ff2fb0'])
ax.set_yscale('log'); ax.set_ylabel('historical Huber/3 loss')
ax.set_title(f'3: W0 Ring at {cid.split("raw")[-1]} with the CORRECT increment C@T0^-1 (MIO={base["MIO"]:.3f}).\n'
             '027 reported Ring004 53–54 with the wrong order -> INVALIDATED', fontsize=7)
fig.tight_layout(); fig.savefig(FIG/'03_ring_before_after_corrected.png', dpi=140); plt.close(fig)
# fig 4 3d landmarks
ident = pd.read_csv(WS/'experiments/TASK-E4-W0-CROSSVIDEO-025-IDENTITY-RECOVERY/runs/G03/IDENTITIES/HISTORICAL_020_IDENTITIES.csv')
X4 = ident[['X004_x','X004_y','X004_z']].values; X5 = ident[['X005_x','X005_y','X005_z']].values
fig = plt.figure(figsize=(14, 4.2))
for k, (i1, i2) in enumerate(((0,1),(0,2),(1,2))):
    ax = fig.add_subplot(1,3,k+1)
    ax.scatter(X4[:,i1], X4[:,i2], s=24, c='#2980b9', label='X004 (019, 004 frame)')
    ax.scatter(X5[:,i1], X5[:,i2], s=24, c='#c0392b', marker='x', label='X005 (019, 005 frame)')
    ax.set_xlabel('XYZ'[i1]); ax.set_ylabel('XYZ'[i2]); ax.grid(alpha=.2)
    if k == 0: ax.legend(fontsize=7)
fig.suptitle('4: the 12 confirmed identities in their own frames — no B/C shared landmarks exist (blocked)', fontsize=8)
fig.tight_layout(); fig.savefig(FIG/'04_shared_landmarks_corrected.png', dpi=140); plt.close(fig)
# fig 5 per-camera audit
fig, ax = plt.subplots(figsize=(10, 3.8))
x = np.arange(len(rows)); vals = [r['frozen'] for r in rows]
ax.bar(x, [1 if r['anchor'] else (0.6 if r['released'] else 0.3) for r in rows],
       color=['#f39c12' if r['anchor'] else ('#27ae60' if r['released'] else '#95a5a6') for r in rows])
ax.set_xticks(x, [r['camera_id'].split('raw')[-1] for r in rows], rotation=70, fontsize=6)
ax.set_yticks([0.3, 0.6, 1], ['FROZEN', 'RELEASED', 'ANCHOR'])
ax.set_title('5: camera audit — every frozen/anchor delta is exactly 0 by construction (indices in JSON)', fontsize=8)
fig.tight_layout(); fig.savefig(FIG/'05_camera_update_audit.png', dpi=140); plt.close(fig)
# fig 6 loss components
fig, ax = plt.subplots(figsize=(8, 4))
if len(ctl):
    w = .35; ax.bar(np.arange(len(ctl))-w/2, ctl.cost0, w, label='init total', color='#bdc3c7')
    ax.bar(np.arange(len(ctl))+w/2, ctl.cost1, w, label='exit total', color='#e74c3c')
    ax.set_xticks(range(len(ctl)), ctl.scenario, rotation=80, fontsize=5)
ax.legend(fontsize=7); ax.set_ylabel('E_total (energy-weighted)')
ax.set_title('6: total energy only — per-block history was NOT saved by the failed run (marked NOT_AVAILABLE)', fontsize=7)
fig.tight_layout(); fig.savefig(FIG/'06_optimization_loss_components.png', dpi=140); plt.close(fig)
# fig 7 controlled
fig, ax = plt.subplots(figsize=(10, 4))
if len(ctl):
    ax.bar(range(len(ctl)), ctl.cam_rot_max, color=['#27ae60' if r else '#c0392b' for r in ctl.success])
    ax.set_xticks(range(len(ctl)), [f"{s}\n{i}" for s, i in zip(ctl.scenario, ctl.init)], rotation=80, fontsize=5)
ax.set_yscale('log'); ax.set_ylabel('max camera rotation error (deg)')
ax.set_title('7: controlled truth recovery with TRIANGULATION initialisation (no GT leakage). None converged', fontsize=8)
fig.tight_layout(); fig.savefig(FIG/'07_controlled_truth_recovery.png', dpi=140); plt.close(fig)
# fig 8 holdout
fig, ax = plt.subplots(figsize=(7, 3.6)); ax.axis('off')
ax.text(.02, .85, '8: HOLDOUT — NOT_EVALUABLE', fontsize=12, fontweight='bold')
ax.text(.02, .55, 'Gate 3 (controlled truth) failed, so no real B/C model was produced.\n'
                  'No HOLDOUT evaluation is reported for a non-existent model.\n'
                  'Reference (unchanged, from 025): 52 matched / 24 >10 px / 80 unmatched.', fontsize=8, va='top')
fig.tight_layout(); fig.savefig(FIG/'08_holdout_reprojection_corrected.png', dpi=140); plt.close(fig)
# fig 9 before/after
fig, ax = plt.subplots(figsize=(12, 4.6)); ax.axis('off')
txt = [
 '9: 027 defects and their corrective evidence',
 'D1 anchor tuple -> nothing frozen.  evidence: tests/test_corrective.py::test_old_anchor_never_matches_any_camera (len(order)=11)',
 '   fixed: CameraVariables(CAMS, anchor_id=G03_v004_raw00219/…) -> released=2, frozen=9, dim=54',
 'D2 Ring increment order: passed T0^-1 C instead of C T0^-1.  fixed: ring_adapter.ring_increment_from_camera',
 '   test: canonical(inc@T0) == canonical(C) to 1e-12, while the old order differs by >1e-3',
 'D3 BA Ring objective lacked M and C.  fixed: I/C/O blocks with exact sqrt(2*lam*rho/N) mapping',
 'D4 weight ambiguity: residual*lam gave lam^2.  fixed: energy weight; test lam 1->4 gives exactly 4x',
 'D5 GT leakage: landmark init and prior used X_gt.  fixed: triangulation-only init; GT in GROUND_TRUTH.json',
 'D6 convergence: 027 reported success=false, nfev=20; corrective runs also fail -> Gate 3 FAIL, real BA BLOCKED',
]
for i, t in enumerate(txt):
    ax.text(.01, .95-0.105*i, t, fontsize=8 if i else 11, fontweight='bold' if i == 0 else 'normal')
fig.tight_layout(); fig.savefig(FIG/'09_before_after_defects.png', dpi=140); plt.close(fig)
print('figures', len(list(FIG.glob('*.png'))))
