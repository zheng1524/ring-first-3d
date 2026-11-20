"""Static figures for the DXY-conic Ring observation experiment. Real frozen data only."""
import json
from pathlib import Path
import numpy as np
import cv2
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import conic as C
from ring_first_3d.mainline.native.camera import torus_contours

WS = Path('/home/liu/ring_first_3d_workspace')
T005 = WS / 'experiments/TASK-E4-UNIFIED-RING-RGB-CAMERA-MAINLINE-005'
TASK = WS / 'experiments/TASK-E4-DXY-CONIC-RING-OBSERVATION-REUSE-001'
FIG = TASK / 'visualization/figures'
FIG.mkdir(parents=True, exist_ok=True)
DXY = TASK / 'metrics/DXY_OBSERVATIONS'

K = np.array([[490., 0, 319.5], [0, 490., 179.5], [0, 0, 1]])


def views():
    return {x['meta']['id']: x for x in json.loads(
        (WS / 'experiments/TASK-E4-UNIFIED-PIPELINE-COMPLETION-002/audit/SELECTED_VIEWS.json').read_text())}


def cam(path):
    return np.asarray(json.loads(Path(path).read_text())['c2w_mm'], float)


def ellipse_pts(e, n=200):
    t = np.linspace(0, 2 * np.pi, n)
    c, s = np.cos(np.deg2rad(e['angle_deg'])), np.sin(np.deg2rad(e['angle_deg']))
    x = e['major_radius'] * np.cos(t); y = e['minor_radius'] * np.sin(t)
    return np.c_[c * x - s * y + e['cx'], s * x + c * y + e['cy']]


def fig_overlay():
    V = views()
    picks = ['G05_v005_raw00404', 'G03_v005_raw00589', 'G01_004_ref08']
    fig, axes = plt.subplots(1, len(picks), figsize=(6 * len(picks), 5))
    for ax, cid in zip(np.atleast_1d(axes), picks):
        if cid not in V:
            ax.axis('off'); continue
        cache = np.load(V[cid]['cache']['path'])
        rec = json.loads((DXY / (cid + '.json')).read_text())
        ax.imshow(cache['RGB'])
        if rec.get('inner'):
            p = ellipse_pts(rec['inner']); ax.plot(p[:, 0], p[:, 1], '-', lw=1.2, c='cyan', label='DXY inner')
        if rec.get('outer'):
            p = ellipse_pts(rec['outer']); ax.plot(p[:, 0], p[:, 1], '-', lw=1.2, c='magenta', label='DXY outer')
        if rec.get('centerline'):
            p = ellipse_pts(rec['centerline']); ax.plot(p[:, 0], p[:, 1], '--', lw=.8, c='yellow', label='DXY mid')
        # CAD projection from the A0 camera and, if present, A1 camera
        for arm, col in (('A0', 'lime'), ('A1', 'orange')):
            base = T005 / 'runs' if arm == 'A0' else TASK / 'runs/A1'
            p = Path(base) / rec['group'] / rec['video'] / 'camera' / cid / 'CAMERA_RESULT.json'
            if not p.exists():
                continue
            c = cam(p)
            for k, curve in enumerate(torus_contours(c, K)):
                ax.plot(np.asarray(curve)[:, 0], np.asarray(curve)[:, 1], ':', lw=1.0, c=col)
        ax.set_title(f'{cid}\nbranch={rec.get("branch")}  valid={rec.get("valid")}', fontsize=8)
        ax.axis('off')
    axes[0].legend(fontsize=7, loc='lower left')
    fig.suptitle('Figure 1  DXY fitted inner/outer/mid ellipses (solid) vs projected CAD tube contours '
                 '(dotted: A0 green, A1 orange)', fontsize=11)
    fig.tight_layout(); fig.savefig(FIG / 'fig1_contour_overlay.png', dpi=130); plt.close(fig)


def fig_metrics():
    import pandas as pd
    frames = []
    a0 = pd.read_csv(T005 / 'CAMERA_QUALITY_MATRIX.csv')
    a0 = a0[['group', 'video', 'ring_MAE_px', 'held_MAE_px', 'camera_admission_pass', 'camera_geometry_validated']]
    a0 = a0.rename(columns={'camera_admission_pass': 'admission', 'camera_geometry_validated': 'validated'})
    a0['arm'] = 'A0'
    frames.append(a0[['arm', 'group', 'video', 'ring_MAE_px', 'held_MAE_px', 'admission', 'validated']])
    for arm in ('A1', 'A2'):
        p = TASK / f'ARM_{arm}_VIEW_METRICS.csv'
        if p.exists():
            d = pd.read_csv(p); d['arm'] = arm
            frames.append(d[['arm', 'group', 'video', 'ring_MAE_px', 'held_MAE_px', 'admission', 'geometry_validated']].rename(columns={'geometry_validated': 'validated'}))
    import pandas as pd
    df = pd.concat(frames, ignore_index=True)
    df['video'] = df['video'].astype(str).str.zfill(3)
    g = df.groupby(['arm', 'group', 'video']).agg(ring=('ring_MAE_px', 'mean'), held=('held_MAE_px', 'median'),
                                                  n_pass=('admission', 'sum'), val=('validated', 'sum')).reset_index()
    g.to_csv(TASK / 'ARM_COMPARISON.csv', index=False)
    fig, axes = plt.subplots(1, 3, figsize=(18, 4.6))
    for ax, col, title in zip(axes, ['ring', 'held', 'n_pass'], ['Ring MAE mean (px)', 'held RGB MAE median (px)', 'views passing 3px gate']):
        for arm in g.arm.unique():
            d = g[g.arm == arm]
            ax.bar(np.arange(len(d)) + (list(g.arm.unique()).index(arm) - 1) * 0.27, d[col], width=.27, label=arm)
        ax.set_xticks(np.arange(len(g[g.arm == 'A0'])))
        ax.set_xticklabels([f'{a}/{b}' for a, b in zip(g[g.arm == "A0"].group, g[g.arm == "A0"].video)], rotation=60, fontsize=6)
        ax.set_title(title, fontsize=9); ax.legend(fontsize=7)
    fig.suptitle('Figure 2  A0 (frozen 005) vs A1 (DXY conics) vs A2 (conics + weak boundary): per-instance comparison', fontsize=11)
    fig.tight_layout(); fig.savefig(FIG / 'fig2_arm_comparison.png', dpi=130); plt.close(fig)


def fig_camera_layout():
    pairs = [('G03', '005'), ('G05', '005'), ('G01', '004')]
    fig, axes = plt.subplots(1, len(pairs), figsize=(5.5 * len(pairs), 4.6))
    for ax, (g, v) in zip(np.atleast_1d(axes), pairs):
        for arm, base, col in (('A0', T005 / 'runs', 'k'), ('A1', TASK / 'runs/A1', 'orange'), ('A2', TASK / 'runs/A2', 'green')):
            d = Path(base) / g / v / 'camera'
            if not d.exists():
                continue
            cs = np.array([cam(p) for p in sorted(d.glob('*/CAMERA_RESULT.json'))])
            if not len(cs):
                continue
            ax.scatter(cs[:, 0], cs[:, 2], s=28, c=col, label=arm)
        ax.scatter([0], [0], marker='*', s=160, c='gold')
        ax.set_aspect('equal'); ax.grid(alpha=.3); ax.legend(fontsize=7)
        ax.set_title(f'{g}/{v}', fontsize=9); ax.set_xlabel('x (mm)'); ax.set_ylabel('z (mm)')
    fig.suptitle('Figure 3  Camera layout under A0/A1/A2 (same frozen inputs, same initialization)', fontsize=11)
    fig.tight_layout(); fig.savefig(FIG / 'fig3_camera_layout.png', dpi=130); plt.close(fig)


def fig_dxy_quality():
    idx = json.loads((DXY / 'INDEX.json').read_text())
    recs = [(r['id'], json.loads((DXY / (r['id'] + '.json')).read_text())) for r in idx['views']]
    cov = [r['diagnostics'].get('inner_arc_coverage', np.nan) for _, r in recs]
    res = [r['diagnostics'].get('inner_normalized_residual', np.nan) for _, r in recs]
    ins = [r['diagnostics'].get('inner_sector_instability', np.nan) for _, r in recs]
    w = [C.quality_weight(r) for _, r in recs]
    fig, axes = plt.subplots(1, 4, figsize=(17, 3.8))
    for ax, v, name in zip(axes, [cov, res, ins, w],
                           ['inner arc coverage', 'normalized residual', 'sector instability', 'quality weight']):
        ax.hist(np.asarray(v, float), bins=20, color='#468')
        ax.set_title(name, fontsize=9); ax.set_ylabel('views')
    fig.suptitle('Figure 4  DXY V9.1 quality diagnostics over the 80 frozen FIT views (continuous weights, no hard gate)', fontsize=11)
    fig.tight_layout(); fig.savefig(FIG / 'fig4_dxy_quality.png', dpi=130); plt.close(fig)


def fig_conic_before_after():
    cid = 'G05_v005_raw00404'
    rec = json.loads((DXY / (cid + '.json')).read_text())
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for arm, base, col in (('A0', T005 / 'runs', 'lime'), ('A1', TASK / 'runs/A1', 'orange')):
        p = Path(base) / rec['group'] / rec['video'] / 'camera' / cid / 'CAMERA_RESULT.json'
        if not p.exists():
            continue
        c = cam(p)
        inner, outer = C.split_curves(torus_contours(c, K))
        for curve in (inner, outer):
            pts = np.asarray(curve, float)
            ci = C.sampson(pts, C.conic_from_ellipse(rec['inner']))
            co = C.sampson(pts, C.conic_from_ellipse(rec['outer']))
            d = np.minimum(ci, co)
            ax.plot(np.linspace(0, 1, len(d)), d, lw=1.0, c=col, label=f'{arm}')
            break
    ax.set_xlabel('normalised position along CAD contour')
    ax.set_ylabel('Sampson distance to nearest DXY conic (px)')
    ax.set_title('Conic residual along the projected CAD contour (G05/005 raw00404)', fontsize=9)
    ax.legend(fontsize=8)
    fig.suptitle('Figure 5  What the optimisation changes: conic-level error before (A0) and after (A1)', fontsize=11)
    fig.tight_layout(); fig.savefig(FIG / 'fig5_conic_before_after.png', dpi=130); plt.close(fig)


if __name__ == '__main__':
    fig_overlay(); fig_metrics(); fig_camera_layout(); fig_dxy_quality(); fig_conic_before_after()
    print('figures:', sorted(p.name for p in FIG.glob('*.png')))
