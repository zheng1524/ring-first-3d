"""Static PNGs for TASK-E4-UNIFIED-RING-RGB-CAMERA-MAINLINE-005. Real frozen data only."""
import json
from pathlib import Path
import numpy as np
import cv2
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import unified_camera as U

FIG = U.TASK / 'visualization/figures'
T001 = U.WS / 'experiments/TASK-E4-UNIFIED-RING-FIRST-HERO-DEPTH-001'
FIG.mkdir(parents=True, exist_ok=True)


def _views():
    return {x['meta']['id']: x for x in U.all_views()}


def _cam(path):
    return np.asarray(json.loads(Path(path).read_text())['c2w_mm'], float)


def fig_ring_cad():
    V = _views()
    picks = [('G01', '004'), ('G02', '005'), ('G03', '005'), ('G05', '005'), ('G06', '005')]
    fig, axes = plt.subplots(1, len(picks), figsize=(4 * len(picks), 4))
    for ax, (g, v) in zip(axes, picks):
        root = U.RUNS / g / v / 'camera'
        cid = sorted(p.name for p in root.glob('*'))[0] if root.exists() else None
        if cid is None:
            ax.axis('off'); ax.set_title(f'{g}/{v}: NOT_RUN', fontsize=9); continue
        cache = U.load_cache(V[cid])
        C = _cam(root / cid / 'CAMERA_RESULT.json'); K = cache['K']
        cr = U.torus_contours(C, K).reshape(-1, 2)
        ax.imshow(cache['RGB'])
        ax.plot(cr[:, 0], cr[:, 1], '.', ms=1, color='yellow')
        q = dict(np.load(U.RUNS / g / v / 'observations' / (cid + '_ring.npz')))['q_train']
        ax.plot(q[:, 0], q[:, 1], '.', ms=1, color='cyan')
        mae = json.loads((root / cid / 'CAMERA_RESULT.json').read_text())['ring_boundary_MAE_px']
        ax.set_title(f'{g}/{v}\n{cid}  Ring MAE={mae:.2f} px', fontsize=8)
        ax.axis('off')
    fig.suptitle('Figure 1  Unified camera: Ring observation (cyan) vs CAD projection (yellow), one FIT view per group', fontsize=11)
    fig.tight_layout(); fig.savefig(FIG / 'fig1_ring_vs_cad.png', dpi=130); plt.close(fig)


def fig_camera_layout():
    inst = sorted((p.parent for p in U.RUNS.glob('*/*/camera')))
    fig, axes = plt.subplots(2, 5, figsize=(18, 7))
    for ax, d in zip(axes.ravel(), inst):
        g, v = d.parent.parent.name, d.parent.name
        cams = []
        for c in sorted(d.glob('*/CAMERA_RESULT.json')):
            cams.append(_cam(c))
        if not cams:
            ax.axis('off'); continue
        cams = np.array(cams)
        ax.scatter(cams[:, 0], cams[:, 2], c='#c33', s=30, label='camera')
        ax.scatter([0], [0], marker='*', s=180, c='gold', label='Ring origin')
        for i, t in enumerate(cams):
            ax.text(t[0], t[2], str(i), fontsize=6)
        ax.set_aspect('equal'); ax.grid(alpha=.3)
        ax.set_title(f'{g}/{v}  n={len(cams)}', fontsize=9)
        ax.set_xlabel('x (mm)'); ax.set_ylabel('z (mm)')
    axes.ravel()[0].legend(fontsize=7)
    fig.suptitle('Figure 3  Recovered FIT camera layout (world = Ring frame, mm); camera indices are view order', fontsize=11)
    fig.tight_layout(); fig.savefig(FIG / 'fig3_camera_layout.png', dpi=130); plt.close(fig)


def fig_consistency():
    q = __import__('pandas').read_csv(U.TASK / 'CAMERA_QUALITY_MATRIX.csv')
    inst = q.groupby(['group', 'video'])
    fig, axes = plt.subplots(1, 2, figsize=(15, 5))
    for (g, v), d in inst:
        axes[0].scatter(d.held_MAE_px, d.ring_MAE_px, s=22, label=f'{g}/{v}')
    axes[0].axvline(3, ls='--', color='k', lw=.8); axes[0].axhline(3, ls='--', color='k', lw=.8)
    axes[0].set_xlabel('held-out reprojection MAE (px)'); axes[0].set_ylabel('Ring MAE (px)')
    axes[0].set_title('per-view: Ring vs independent RGB consistency', fontsize=9)
    axes[0].legend(fontsize=6, ncol=2)
    names = [f'{g}\n{v}' for (g, v), _ in inst]
    valid = [int((d.per_view_status == 'VALIDATED').sum()) for _, d in inst]
    caution = [int((d.per_view_status == 'USABLE_WITH_CAUTION').sum()) for _, d in inst]
    x = np.arange(len(names))
    axes[1].bar(x, valid, color='#2a7', label='VALIDATED')
    axes[1].bar(x, caution, bottom=valid, color='#e8a', label='USABLE_WITH_CAUTION')
    axes[1].set_xticks(x); axes[1].set_xticklabels(names, fontsize=7)
    axes[1].set_ylabel('FIT views'); axes[1].axhline(8, ls=':', color='k', lw=.7)
    axes[1].legend(fontsize=7); axes[1].set_title('per-view status (max 8 FIT)', fontsize=9)
    fig.suptitle('Figure 4  Unified quality: Ring admission vs independent RGB consistency, and per-view status', fontsize=11)
    fig.tight_layout(); fig.savefig(FIG / 'fig4_consistency_and_status.png', dpi=130); plt.close(fig)


def fig_vs_history():
    """Compare this round's final cameras with 002's per-view recover cameras."""
    import pandas as pd
    rows = []
    for cp in sorted(U.RUNS.glob('*/*/camera/*/CAMERA_RESULT.json')):
        vid = cp.parent.name; v = cp.parent.parent.parent.name; g = cp.parent.parent.parent.parent.name
        old = U.T002 / 'runs/RF_ONLY_V1' / g / v / 'camera' / vid / 'CAMERA_RESULT.json'
        if not old.exists():
            old = T001 / 'runs/RF_ONLY_V1' / g / v / 'camera' / vid / 'CAMERA_RESULT.json'
        if not old.exists():
            continue
        A = _cam(cp); B = np.asarray(json.loads(old.read_text())['c2w_mm'])
        rot = np.degrees(np.arccos(np.clip((np.trace(A[:3, :3].T @ B[:3, :3]) - 1) / 2, -1, 1)))
        rows.append(dict(group=g, video=v, view=vid, rot_deg=float(rot),
                         dcenter=float(np.linalg.norm(A[:3, 3] - B[:3, 3]))))
    df = pd.DataFrame(rows)
    df.to_csv(U.TASK / 'FINAL_VS_HISTORY_CAMERAS.csv', index=False)
    if df.empty:
        return
    fig, axes = plt.subplots(1, 2, figsize=(14, 4.6))
    lab = [f'{a}/{b}' for a, b in zip(df.group, df.video)]
    axes[0].bar(range(len(df)), df.rot_deg, color='#468')
    axes[0].set_xticks(range(len(df))); axes[0].set_xticklabels(lab, rotation=60, fontsize=6)
    axes[0].set_ylabel('rotation difference (deg)'); axes[0].axhline(30, ls='--', color='k', lw=.7)
    axes[0].set_title('unified BA camera vs 002 per-view recover (rotation)', fontsize=9)
    axes[1].bar(range(len(df)), df.dcenter, color='#a35')
    axes[1].set_xticks(range(len(df))); axes[1].set_xticklabels(lab, rotation=60, fontsize=6)
    axes[1].set_ylabel('camera centre difference (mm)')
    axes[1].set_title('unified BA camera vs 002 per-view recover (translation)', fontsize=9)
    fig.suptitle('Figure 5  Final cameras vs the historical per-view recover result (same frozen inputs)', fontsize=11)
    fig.tight_layout(); fig.savefig(FIG / 'fig5_vs_history.png', dpi=130); plt.close(fig)


def fig_g03_g05():
    q = __import__('pandas').read_csv(U.TASK / 'CAMERA_QUALITY_MATRIX.csv')
    fig, axes = plt.subplots(1, 2, figsize=(14, 4.6))
    for ax, (g, v) in zip(axes, [('G03', '005'), ('G05', '005')]):
        d = q[(q.group == g) & (q.video == v)]
        if d.empty:
            ax.axis('off'); ax.set_title(f'{g}/{v}: NOT_RUN', fontsize=9); continue
        x = np.arange(len(d))
        ax.bar(x, d.ring_MAE_px, color='#468', label='Ring MAE (px)')
        ax.bar(x, d.held_MAE_px, color='#c33', alpha=.6, label='held RGB MAE (px)')
        ax.axhline(3, ls='--', color='k', lw=.8)
        ax.set_xticks(x); ax.set_xticklabels([s.replace('G05_v005_', '').replace('G03_v005_', '') for s in d.view], rotation=45, fontsize=7)
        ax.set_ylabel('px'); ax.legend(fontsize=7)
        ax.set_title(f'{g}/{v}: unified pipeline per view', fontsize=9)
    fig.suptitle('Figure 6  Failure cases after unification: Ring stays inside gate while RGB consistency is reported separately', fontsize=11)
    fig.tight_layout(); fig.savefig(FIG / 'fig6_g03_g05_status.png', dpi=130); plt.close(fig)


def fig_matches():
    """Project a few training matches onto one view (real SIFT pairs from tracks005)."""
    picks = [('G01', '005'), ('G03', '005')]
    V = _views()
    fig, axes = plt.subplots(1, 2, figsize=(16, 4.5))
    for ax, (g, v) in zip(axes, picks):
        root = U.RUNS / g / v
        tr = np.load(root / 'observations/tracks005.npz')
        ids = list(tr['ids']); xy = tr['xy']
        if len(ids) < 2:
            ax.axis('off'); continue
        a = U.load_cache(V[ids[0]])['RGB']; b = U.load_cache(V[ids[1]])['RGB']
        h, w = a.shape[:2]
        canvas = np.concatenate([a, b], axis=1)
        ax.imshow(canvas)
        n = 0
        for t in range(xy.shape[0]):
            p, q = xy[t, 0], xy[t, 1]
            if not (np.isfinite(p[0]) and np.isfinite(q[0])):
                continue
            ax.plot([p[0], q[0] + w], [p[1], q[1]], '-', lw=.4, c='lime')
            n += 1
            if n >= 60:
                break
        ax.set_title(f'{g}/{v}: {ids[0]} | {ids[1]}  ({n} training tracks shown)', fontsize=8)
        ax.axis('off')
    fig.suptitle('Figure 2  RGB multi-view tracks used by the unified solver (SIFT mutual, category-consistent)', fontsize=11)
    fig.tight_layout(); fig.savefig(FIG / 'fig2_rgb_matches.png', dpi=130); plt.close(fig)


if __name__ == '__main__':
    fig_ring_cad(); fig_matches(); fig_camera_layout(); fig_consistency(); fig_vs_history(); fig_g03_g05()
    print('figures:', sorted(p.name for p in FIG.glob('*.png')))
