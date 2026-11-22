#!/usr/bin/env python3
"""P6: ten corrective figures, each labelled with its real source function and sample count."""
import json, os, sys
from pathlib import Path
import numpy as np, pandas as pd, cv2
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
WS = Path('/home/liu/ring_first_3d_workspace')
K = WS/'experiments/TASK-E4-W0-CROSSVIDEO-026-CORRECTIVE'
REP = K/'replay'; OUT = K/'runs/G03'; FIG = OUT/'FIGURES'; FIG.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(REP)); sys.path.insert(0, str(WS/'src'))
os.environ.update(E4_RUN_DIR=str(REP),
    RING_CAD=str(WS/'assets/retained_sources/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-HERO-BODY-ADAPT-018/inputs/G03/RING.npz'),
    RING_NORM=str(WS/'assets/retained_sources/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/FREE_VERTEX_013/inputs/G03/NORMALIZATION.json'))
views = {v['id']: v for v in json.loads((REP/'config'/'VIEWS.json').read_text())}
split = json.loads((OUT/'SPLIT.json').read_text())
PREP = WS/'experiments/TASK-E4-UNIFIED-RING-CONTOUR-REFINEMENT-005/runs/prepared'


def rgb(view):
    for v in ('004', '005'):
        for x in json.loads((PREP/f'G03_{v}'/'PREPARED.json').read_text())['views']:
            if x['view'] == view:
                return np.asarray(np.load(x['cache'])['RGB'])[:, :, :3]
    raise KeyError(view)


def main():
    from ring020_026 import RingRenderer
    rr = RingRenderer(sorted(views))
    v = split['fit5'][0]; C = np.asarray(views[v]['T'], float); Kk = np.asarray(views[v]['K'], float)
    im = rgb(v)
    ev = rr.data[v]['evidence']
    segs = rr.curves.segments(C, Kk)
    io = pd.read_csv(OUT/'RING_IO_CORRECTIVE.csv'); r = io[io.view == v].iloc[0]
    # 1 historical I/O actual overlay (CAD edges + participating observations)
    fig, ax = plt.subplots(figsize=(10, 5.6)); ax.imshow(im); ax.axis('off')
    for key, col, ls in (('inner', '#00e5ff', '-'), ('outer', '#ff2fb0', '-')):
        e = np.asarray(segs[key], int)
        if len(e):
            X = rr.curves.V[e].reshape(-1, 3)
            P = rr.curves.project(X, C, Kk).reshape(-1, 2)
            for k in range(0, len(P), 2):
                ax.plot(P[k:k+2, 0], P[k:k+2, 1], ls, c=col, lw=.9, label=f'CAD {key} visible edge' if k == 0 else None)
        q = np.asarray(ev[key], float)
        ax.scatter(q[:, 0], q[:, 1], s=1.4, c=col, alpha=.65, label=f'{key} obs actually used (n={len(q)})')
    ax.set_title(f'1: historical RingRenderer actual edges vs actual observations — {v.split("raw")[-1]}\n'
                 f'M={r.M:.3f} I={r.I:.3f} O={r.O:.3f} (Huber/3), MIO={r.MIO:.3f}; CAD from G03 RING.npz', fontsize=8)
    ax.legend(fontsize=6, loc='upper right', markerscale=4)
    fig.tight_layout(); fig.savefig(FIG/'01_historical_io_actual_overlay.png', dpi=145); plt.close(fig)
    # 2 W0 analytic vs mask
    from ring_first_3d.mainline.native.camera import torus_contours
    lab = np.asarray(np.load(views[v]['cache'])['labels']); ring = (lab == 2).astype(np.uint8)
    cc, hh = cv2.findContours(ring, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    cs = torus_contours(C, Kk); cs = sorted(cs, key=lambda c: cv2.contourArea(np.asarray(c, np.float32).reshape(-1, 1, 2)))
    fig, ax = plt.subplots(figsize=(10, 5.6)); ax.imshow(im); ax.axis('off')
    for c in cc: ax.plot(c[:, 0, 0], c[:, 0, 1], '.', ms=.7, c='#ffd400', label='mask edge (labels==2)')
    ax.plot(np.asarray(cs[0])[:, 0], np.asarray(cs[0])[:, 1], '-', c='#00e5ff', lw=1.0, label='W0 torus_contours (small area)')
    ax.plot(np.asarray(cs[1])[:, 0], np.asarray(cs[1])[:, 1], '-', c='#ff2fb0', lw=1.0, label='W0 torus_contours (large area)')
    ax.set_title('2: W0 analytic contours (torus_contours) vs mask edge — separate implementation, NOT the historical loss', fontsize=8)
    ax.legend(fontsize=6); fig.tight_layout(); fig.savefig(FIG/'02_w0_analytic_vs_mask.png', dpi=145); plt.close(fig)
    # 3 centerline audit
    ca = json.loads((OUT/'CENTERLINE_AUDIT.json').read_text())
    rr_ = [x for x in ca if x['view'] == v][0]
    def ell(e, n=360):
        t = np.linspace(0, 2*np.pi, n)
        c, s = np.cos(np.deg2rad(e['angle_deg'])), np.sin(np.deg2rad(e['angle_deg']))
        x, y = e['major_radius']*np.cos(t), e['minor_radius']*np.sin(t)
        return np.c_[c*x-s*y+e['cx'], s*x+c*y+e['cy']]
    OLD = json.loads((WS/'experiments/TASK-E4-W0-CROSSVIDEO-026-RING-GEOMETRY-AND-UNCERTAINTY/replay_020/runs/ring'/(v+'.json')).read_text())
    fig, axs = plt.subplots(1, 2, figsize=(15, 5))
    for ax, e, t in ((axs[0], OLD, '026 old adapters: centerline = inner (WRONG)'), (axs[1], rr_, 'corrective: real DXY centerline')):
        ax.imshow(im); ax.axis('off')
        for key, col in (('inner', '#00e5ff'), ('outer', '#ff2fb0'), ('centerline', '#2ecc71')):
            if e.get(key): ax.plot(*ell(e[key]).T, '-', c=col, lw=1.0, label=f"{key}: maj={e[key]['major_radius']:.1f} min={e[key]['minor_radius']:.1f}")
        ax.set_title(t, fontsize=8); ax.legend(fontsize=6)
    fig.suptitle(f'3: centerline source audit — C went {r.C:.3f} (old fake C) -> see corrected run (real C); historical ring019.recover(labels,RGB,10.)', fontsize=8)
    fig.tight_layout(); fig.savefig(FIG/'03_centerline_source_audit.png', dpi=145); plt.close(fig)
    # 4 corrected H025 ring projection
    H = np.load(WS/'experiments/TASK-E4-W0-CROSSVIDEO-025-IDENTITY-RECOVERY/runs/G03/CONSISTENCY/H_HYPOTHESIS.npz')['H']
    hh_ = pd.read_csv(OUT/'H025_REEVALUATION.csv'); rh = hh_[hh_.view == v].iloc[0]
    fig, axs = plt.subplots(1, 2, figsize=(15, 5))
    for ax, Cc, t, m in ((axs[0], C, 'W0 camera (baseline)', r.MIO), (axs[1], np.linalg.inv(H) @ C, 'H025^-1 applied (005 side)', rh.MIO)):
        ax.imshow(im); ax.axis('off')
        sg = rr.curves.segments(Cc, Kk)
        for key, col in (('inner', '#00e5ff'), ('outer', '#ff2fb0')):
            e = np.asarray(sg[key], int)
            if len(e):
                P = rr.curves.project(rr.curves.V[e].reshape(-1, 3), Cc, Kk).reshape(-1, 2)
                for k in range(0, len(P), 2): ax.plot(P[k:k+2, 0], P[k:k+2, 1], '-', c=col, lw=.9)
        ax.set_title(f'{t}: MIO={m:.3f}', fontsize=8)
    fig.suptitle('4: corrected H025 evaluation (increment passed once; camera = H^-1 T005). Same image scale.', fontsize=8)
    fig.tight_layout(); fig.savefig(FIG/'04_corrected_H_ring_projection.png', dpi=145); plt.close(fig)
    # 5 identifiability
    s = pd.read_csv(OUT/'RING_POSE_SENSITIVITY_CORRECTED.csv'); sv = s[s.view == split['fit5'][0]]
    fig, ax = plt.subplots(figsize=(8, 4.6))
    for axis, mk in (('world_ring_axis', 'o-'), ('world_x_tilt', 's-'), ('world_y_tilt', '^-'), ('local_yaw', 'd-'), ('local_pitch', 'v-'), ('local_roll', 'x-')):
        d = sv[sv.axis == axis]
        ax.plot(d.value, d.MIO, mk, label=axis, ms=3)
    ax.set_xlabel('perturbation (deg)'); ax.set_ylabel('MIO Ring loss'); ax.set_yscale('log'); ax.grid(alpha=.25); ax.legend(fontsize=7)
    ax.set_title('5: corrected identifiability — world Ring-axis rotation is EXACTLY flat (symmetry); local rotation is penalised', fontsize=8)
    fig.tight_layout(); fig.savefig(FIG/'05_corrected_pose_identifiability.png', dpi=140); plt.close(fig)
    # 6 track-aligned triangulation
    L26 = WS/'experiments/TASK-E4-W0-CROSSVIDEO-026-RING-GEOMETRY-AND-UNCERTAINTY/replay_020/runs/landmarks'
    Xb = np.load(L26/'REL_BASE_005.npz')['X']; Xp = np.load(L26/'REL_005_independent_0.5_0.0.npz')['X']
    Ob = json.loads((L26/'REL_BASE_005_OBSERVATIONS.json').read_text()); Op = json.loads((L26/'REL_005_independent_0.5_0.0_OBSERVATIONS.json').read_text())
    kb = {tuple(sorted((x['view'], int(x['feature_id'])) for x in o['observations'])): i for i, o in enumerate(Ob)}
    kp = {tuple(sorted((x['view'], int(x['feature_id'])) for x in o['observations'])): i for i, o in enumerate(Op)}
    common = [k for k in kb if k in kp]
    fig, ax = plt.subplots(figsize=(7.6, 5))
    for k in common:
        a, b = Xb[kb[k]], Xp[kp[k]]
        ax.plot([a[0], b[0]], [a[2], b[2]], '-', c='#bdc3c7', lw=.5)
    ax.scatter(Xb[[kb[k] for k in common], 0], Xb[[kb[k] for k in common], 2], s=4, c='#2980b9', label=f'baseline (n={len(common)})')
    ax.scatter(Xp[[kp[k] for k in common], 0], Xp[[kp[k] for k in common], 2], s=4, c='#e74c3c', label='perturbed')
    ax.set_xlabel('x (mm)'); ax.set_ylabel('z (mm)')
    ax.set_title(f'6: same-track displacement under 005 independent 0.5° (common tracks {len(common)}, lost {len(kb)-len(common)})', fontsize=8)
    ax.legend(fontsize=7); ax.grid(alpha=.2)
    fig.tight_layout(); fig.savefig(FIG/'06_track_aligned_triangulation.png', dpi=140); plt.close(fig)
    # 7 survival
    ta = pd.read_csv(OUT/'TRIANGULATION_TRACK_ALIGNED.csv')
    fig, ax = plt.subplots(figsize=(10, 4))
    x = np.arange(len(ta)); ax.bar(x-0.2, ta.n_common, width=.4, label='survived', color='#27ae60')
    ax.bar(x+0.2, ta.lost, width=.4, label='lost', color='#c0392b')
    ax.set_xticks(x, [f"{r.video}:{r.run}" for _, r in ta.iterrows()], rotation=25, ha='right', fontsize=6)
    ax.set_yscale('log'); ax.set_ylabel('tracks'); ax.legend(fontsize=7); ax.grid(alpha=.2)
    ax.set_title('7: landmark survival after historical 019 quality gate (same cameras perturbed)', fontsize=8)
    fig.tight_layout(); fig.savefig(FIG/'07_landmark_survival.png', dpi=140); plt.close(fig)
    # 8 pairwise
    pw = pd.read_csv(WS/'experiments/TASK-E4-W0-CROSSVIDEO-026-RING-GEOMETRY-AND-UNCERTAINTY/runs/G03/PAIRWISE_DISTANCES_12.csv')
    fig, axs = plt.subplots(1, 2, figsize=(12, 4))
    axs[0].scatter(pw.d004, pw.d005, s=12, c='#2980b9'); lim = [pw[['d004','d005']].min().min(), pw[['d004','d005']].max().max()]
    axs[0].plot(lim, lim, 'k--', lw=.7); axs[0].set_xlabel('D004 (mm)'); axs[0].set_ylabel('D005 (mm)')
    axs[0].set_title(f'8a: 66 identity pairs, median |Δ| {pw.diff_mm.median():.2f} mm')
    axs[1].hist(pw.diff_mm, bins=14, color='#e67e22'); axs[1].set_xlabel('|D004-D005| (mm)'); axs[1].set_title('8b: distance disagreement (triangulated, not truth)')
    fig.tight_layout(); fig.savefig(FIG/'08_corrected_pairwise_distances.png', dpi=140); plt.close(fig)
    # 9 ring vs 3D
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.2))
    d = sv[sv.axis == 'world_ring_axis']; axs[0].plot(d.value, d.MIO, 'o-', c='#00bcd4'); axs[0].set_yscale('log')
    cm = ta[ta.run.str.startswith('PERT_')]
    axs[1].bar(range(len(cm)), cm.disp_p50, color='#8e44ad'); axs[1].set_xticks(range(len(cm)), [f"{r.video}:{r.run.replace('PERT_','')}" for _, r in cm.iterrows()], rotation=25, ha='right', fontsize=6)
    axs[0].set_title('9a: Ring MIO under world Ring-axis rotation (paired, same cameras)'); axs[1].set_title('9b: 3D displacement, common-mode runs (separate experiment)')
    fig.suptitle('9: NOT a paired scatter — 9a and 9b are two different experiments, shown separately on purpose', fontsize=8)
    fig.tight_layout(); fig.savefig(FIG/'09_ring_vs_triangulation_sensitivity.png', dpi=140); plt.close(fig)
    # 10 audit summary
    fig, ax = plt.subplots(figsize=(13, 5.2)); ax.axis('off')
    lines = [
        '026 -> 026-CORRECTIVE audit',
        f'1 Centerline: centre=inner -> real DXY centerline; C 1.974 -> {io.C.median():.3f}; MIO med {io.MIO.median():.3f}',
        f'2 SE(3): double H application removed; max matrix diff {pd.read_csv(OUT/"SE3_COMPOSITION_TESTS.csv").matrix_diff.max():.2e}',
        f'3 Perturbation: wrong conjugation -> correct increment; world-axis rotation MIO flat at {sv[sv.axis=="world_ring_axis"].MIO.iloc[0]:.3f}',
        f'4 Track identity: row-index matching -> stable keys; 0.5 deg relative p50 0.99 mm (was 10-38 mm)',
        f'H025 Ring MIO: 178.7 (INVALID) -> {hh_.MIO.median():.3f} vs baseline {io.MIO.median():.3f}',
        'JOINT OPTIMISATION: NOT EXECUTED (no validated Ring-compatible candidate); no BA started',
    ]
    for i, t in enumerate(lines):
        ax.text(0.01, 0.94-0.12*i, t, fontsize=9 if i else 12, fontweight='bold' if i == 0 else 'normal')
    fig.tight_layout(); fig.savefig(FIG/'10_corrective_audit_summary.png', dpi=140); plt.close(fig)
    print('figures', len(list(FIG.glob('*.png'))))


if __name__ == '__main__':
    main()
