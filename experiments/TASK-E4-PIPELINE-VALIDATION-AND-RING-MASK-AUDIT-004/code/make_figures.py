"""Static PNG figures for the audit. Real frozen data only; no schematic placeholders."""
import numpy as np
import pandas as pd
import cv2
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import audit_common as A

FIG = A.AUD / 'visualization/figures'
FIG.mkdir(parents=True, exist_ok=True)
AUD = A.AUD


def ring_mask_panel(ax, labels, title, highlight=None):
    img = np.zeros((*labels.shape, 3), np.uint8)
    img[labels == 1] = (60, 60, 200)     # polyp
    img[labels == 2] = (230, 230, 230)   # ring
    if highlight is not None:
        img[highlight] = (0, 220, 0)
    ax.imshow(img); ax.set_title(title, fontsize=9); ax.axis('off')


def fig1_g05():
    x = [v for v in A.views() if v['meta']['id'] == 'G05_v005_raw00404'][0]
    cache = A.load_cache(x); labels = cache['labels']
    cam = A.final_camera('G05', '005', 'G05_v005_raw00404')
    C = np.asarray(cam['c2w_mm']); K = cache['K']
    n, comps, cc = A.components(labels)
    main = comps[0]['index']
    mainmask = cc == main
    filled, fill, info = A.dxy_hole_fill(labels)
    from ring_first_3d.mainline.native.camera import torus_contours
    cr = torus_contours(C, K).reshape(-1, 2)
    fig, ax = plt.subplots(1, 5, figsize=(20, 4.4))
    ax[0].imshow(cache['RGB']); ax[0].set_title('G05_v005_raw00404  RGB', fontsize=9); ax[0].axis('off')
    # component map
    img = np.zeros((*labels.shape, 3), np.uint8)
    cols = [(255, 255, 255), (0, 200, 0), (255, 80, 0), (0, 160, 255), (255, 0, 255)]
    for k, c in enumerate(comps[:4]):
        img[cc == c['index']] = cols[k % len(cols)]
    ax[1].imshow(img); ax[1].set_title(f'components: {n} (main 9901 px, other 63 px)', fontsize=9); ax[1].axis('off')
    ring_mask_panel(ax[2], labels, 'raw labels (polyp blue, ring white)')
    ring_mask_panel(ax[3], labels, 'M1: main component only', highlight=mainmask)
    ax[3].imshow(np.where(mainmask[..., None], np.array([0, 220, 0], np.uint8),
                          np.where((labels == 2)[..., None], np.array([120, 120, 120], np.uint8),
                                   np.where((labels == 1)[..., None], np.array([60, 60, 200], np.uint8), 0))).astype(np.uint8))
    ax[4].imshow(cache['RGB'])
    ax[4].plot(cr[:, 0], cr[:, 1], '.', ms=1.0, color='yellow', label='CAD Ring projection')
    ax[4].scatter(mainmask.nonzero()[1][::12], mainmask.nonzero()[0][::12], s=1, c='lime', label='main component')
    ax[4].set_title('CAD Ring projection vs main component', fontsize=9); ax[4].axis('off'); ax[4].legend(fontsize=7, loc='lower left')
    fig.suptitle('Figure 1  G05/005 raw00404: Ring mask components, main-component strategy, DXY hole fill, CAD projection', fontsize=11)
    fig.tight_layout(); fig.savefig(FIG / 'fig1_G05_ring_mask_components.png', dpi=130); plt.close(fig)


def fig2_residual():
    d = pd.read_csv(AUD / 'RING_COMPONENT_COMPARISON.csv')
    r = d[d.view == 'G05_v005_raw00404'].iloc[0]
    fig, ax = plt.subplots(1, 2, figsize=(13, 4.6))
    lab = ['M0 all-128 sample', 'M1 main-component 128 sample', 'all main boundary', 'all discarded boundary']
    val = [r.M0_ring_MAE_px, r.M1_ring_MAE_px, r.fullbound_main_MAE_px, r.fullbound_discarded_MAE_px]
    n = [128, int(r.M1_qN), int(r.fullbound_main_N), int(r.fullbound_discarded_N)]
    bars = ax[0].bar(range(4), val, color=['#888', '#2a7', '#2a7', '#c33'])
    ax[0].set_xticks(range(4)); ax[0].set_xticklabels(lab, rotation=15, fontsize=8)
    ax[0].set_ylabel('Ring MAE vs CAD projection (px)')
    for b, v, nn in zip(bars, val, n):
        ax[0].text(b.get_x() + b.get_width() / 2, v, f'{v:.3f}\n(N={nn})', ha='center', va='bottom', fontsize=7)
    ax[0].set_title('Same fixed camera: residual by observation set', fontsize=9)
    sub = d[d.n_components > 1].copy()
    sub['delta'] = sub.M1_ring_MAE_px - sub.M0_ring_MAE_px
    sub = sub.sort_values('discarded_area_px')
    colors = ['#2a7' if x < 0 else '#c33' for x in sub.delta]
    ax[1].barh(range(len(sub)), sub.delta, color=colors)
    ax[1].set_yticks(range(len(sub))); ax[1].set_yticklabels([f"{a}/{b}" for a, b in zip(sub.group, sub.view)], fontsize=7)
    ax[1].axvline(0, color='k', lw=.8)
    ax[1].set_xlabel('M1 - M0 Ring MAE (px);  negative = improvement')
    for i, (_, s) in enumerate(sub.iterrows()):
        ax[1].text(s.delta, i, f"  discarded {int(s.discarded_area_px)} px", va='center', fontsize=7)
    ax[1].set_title('Main-component strategy: improvement is NOT universal', fontsize=9)
    fig.suptitle('Figure 2  Ring residual decomposition and counter-examples (fixed cameras, frozen masks)', fontsize=11)
    fig.tight_layout(); fig.savefig(FIG / 'fig2_ring_residual_decomposition.png', dpi=130); plt.close(fig)


def fig3_multicase():
    cases = ['G01_004_ref08', 'G01_v005_raw00192', 'G03_v005_raw00589', 'G05_v004_raw00117',
             'G05_v005_raw00404', 'G06_v005_raw00142']
    d = pd.read_csv(AUD / 'RING_COMPONENT_COMPARISON.csv')
    fig, axes = plt.subplots(2, 3, figsize=(16, 8))
    for ax, cid in zip(axes.ravel(), cases):
        row = d[d.view == cid]
        x = [v for v in A.views() if v['meta']['id'] == cid]
        if not len(x) or not len(row):
            ax.axis('off'); ax.set_title(f'{cid}: not in frozen set', fontsize=8); continue
        cache = A.load_cache(x[0]); labels = cache['labels']
        n, comps, cc = A.components(labels)
        mainmask = cc == comps[0]['index'] if comps else np.zeros_like(labels, bool)
        img = np.zeros((*labels.shape, 3), np.uint8)
        img[labels == 2] = (120, 120, 120); img[mainmask] = (0, 220, 0); img[labels == 1] = (60, 60, 200)
        ax.imshow(img)
        r = row.iloc[0]
        ax.set_title(f"{cid}\ncomponents={int(r.n_components)}  discarded={int(r.discarded_area_px)} px "
                     f"({r.r_discarded*100:.2f}%)\nMAE M0={r.M0_ring_MAE_px:.2f} -> M1={r.M1_ring_MAE_px:.2f} px",
                     fontsize=8)
        ax.axis('off')
    fig.suptitle('Figure 3  Multi-case Ring mask audit: main component in green, discarded components in grey '
                 '(behaviour is not uniformly beneficial)', fontsize=11)
    fig.tight_layout(); fig.savefig(FIG / 'fig3_multicase_ring_masks.png', dpi=130); plt.close(fig)


def fig4_g03_camera():
    d = pd.read_csv(AUD / 'CAMERA_BODY_GAUGE_DIAGNOSTICS.csv')
    br = pd.read_csv(AUD / 'CAMERA_BRANCH_DIAGNOSTICS.csv')
    g = d[d.group == 'G03'].copy()
    fig, ax = plt.subplots(1, 2, figsize=(15, 5))
    idx = np.arange(len(g))
    ax[0].bar(idx - .25, g.init_v0_IoU, .25, label='BA v0 camera', color='#c33')
    ax[0].bar(idx, g.init_v1_IoU, .25, label='BA v1 camera', color='#2a7')
    ax[0].bar(idx + .25, g.final_IoU, .25, label='final CAMERA_RESULT', color='#468')
    ax[0].set_xticks(idx); ax[0].set_xticklabels([v.replace('G03_v005_', '') for v in g.view], rotation=45, fontsize=7)
    ax[0].set_ylabel('IoU: EXACT013 INITIAL body vs polyp mask')
    ax[0].legend(fontsize=8); ax[0].set_title('G03/005: independent INITIAL body decides the branch', fontsize=9)
    b = br[br.group == 'G03']
    ax[1].bar(np.arange(len(b)), b.rot_v0_v1_deg, color='#a35')
    ax[1].axhline(90, ls='--', color='k', lw=.7); ax[1].axhline(180, ls=':', color='k', lw=.7)
    ax[1].set_ylim(0, 200); ax[1].set_xticks(np.arange(len(b)))
    ax[1].set_xticklabels([v.replace('G03_v005_', '') for v in b.view], rotation=45, fontsize=7)
    ax[1].set_ylabel('rotation between BA v0 and v1 (deg)')
    ax[1].set_title('Two calibration versions are ~175 deg apart (ring-symmetric ambiguity)', fontsize=9)
    fig.suptitle('Figure 4  G03/005 camera branch diagnostics (INITIAL body, no camera re-solve)', fontsize=11)
    fig.tight_layout(); fig.savefig(FIG / 'fig4_G03_camera_branch.png', dpi=130); plt.close(fig)


def fig5_gates():
    g = pd.read_csv(AUD / 'GATE_SENSITIVITY.csv')
    cov = pd.read_csv(AUD / 'VIEW_COVERAGE_MATRIX.csv')
    fig, ax = plt.subplots(1, 3, figsize=(18, 4.6))
    mae = g.ring_MAE_px.dropna().values
    ax[0].hist(mae, bins=30, color='#468')
    for t, c in [(3, 'r'), (5, 'orange'), (10, 'g')]:
        ax[0].axvline(t, ls='--', color=c, label=f'{t} px')
    ax[0].set_xlabel('Ring boundary MAE (px)'); ax[0].set_ylabel('views'); ax[0].legend(fontsize=8)
    ax[0].set_title(f'Ring MAE distribution (n={len(mae)}; 2 views FAIL >3px)', fontsize=9)
    thr = [3, 5, 10]
    counts = [(mae <= t).sum() for t in thr]
    ax[1].bar(range(3), counts, color=['#c33', '#e88', '#2a7'])
    ax[1].set_xticks(range(3)); ax[1].set_xticklabels([f'<= {t} px' for t in thr])
    for i, c in enumerate(counts):
        ax[1].text(i, c, f'{c}/{len(mae)}', ha='center', va='bottom')
    ax[1].set_ylabel('views accepted'); ax[1].set_title('Gate sensitivity (offline only; formal gate unchanged)', fontsize=9)
    lab = [f"{a}/{b}" for a, b in zip(cov.group, cov.video)]
    ax[2].bar(range(len(cov)), cov.camera_coverage, color='#468')
    ax[2].set_xticks(range(len(cov))); ax[2].set_xticklabels(lab, rotation=45, fontsize=7)
    ax[2].set_ylim(0, 1.1); ax[2].axhline(1.0, ls=':', color='k', lw=.7)
    ax[2].set_ylabel('FIT camera coverage'); ax[2].set_title('Per-instance FIT coverage (only G05/005 = 6/8)', fontsize=9)
    fig.suptitle('Figure 5  Gate behaviour and view coverage (frozen results; no threshold was changed)', fontsize=11)
    fig.tight_layout(); fig.savefig(FIG / 'fig5_gates_and_coverage.png', dpi=130); plt.close(fig)


def fig6_health():
    h = pd.read_csv(AUD / 'HERO_HEALTH.csv')
    b = pd.read_csv(AUD / 'BODY_UPDATE_HEALTH.csv')
    fig, ax = plt.subplots(1, 2, figsize=(15, 5))
    ok = h.health == 'WITHIN_3X'
    ax[0].scatter(h[ok].camera_distance_mm, h[ok].depth_median_mm, s=18, c='#2a7', label='within 3x')
    ax[0].scatter(h[~ok].camera_distance_mm, h[~ok].depth_median_mm, s=30, c='#c33', marker='^', label='SUSPECT >3x')
    xs = np.linspace(30, 50, 50)
    for f in (1, 3, 10):
        ax[0].plot(xs, xs * f, ':', lw=.8, color='gray')
        ax[0].text(xs[-1], xs[-1] * f, f'{f}x', fontsize=7, color='gray')
    ax[0].set_yscale('log'); ax[0].set_xlabel('camera distance to Ring centre (mm)')
    ax[0].set_ylabel('HERO median axial depth (mm)'); ax[0].legend(fontsize=8)
    ax[0].set_title('HERO depth vs camera distance: 2/40 views >3x (SUSPECT, not rejected)', fontsize=9)
    lab = [f"{a}/{b}/{c}" for a, b, c in zip(b.group, b.video, b.arm)]
    cols = ['#c33' if s == 'STAGNATION' else '#2a7' for s in b.stagnation]
    ax[1].bar(range(len(b)), b.max_vertex_disp_mm, color=cols)
    ax[1].set_yscale('log'); ax[1].set_xticks(range(len(b))); ax[1].set_xticklabels(lab, rotation=60, fontsize=7)
    ax[1].set_ylabel('max vertex displacement FINAL-INITIAL (mm, log)')
    ax[1].axhline(1e-3, ls='--', color='k', lw=.7)
    ax[1].set_title('Body update health: red = STAGNATION (<1e-3 mm)', fontsize=9)
    fig.suptitle('Figure 6  HERO depth health and Body update health (frozen artifacts)', fontsize=11)
    fig.tight_layout(); fig.savefig(FIG / 'fig6_hero_and_body_health.png', dpi=130); plt.close(fig)


if __name__ == '__main__':
    fig1_g05(); fig2_residual(); fig3_multicase(); fig4_g03_camera(); fig5_gates(); fig6_health()
    print('figures:', sorted(p.name for p in FIG.glob('*.png')))
