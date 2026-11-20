"""Pilot figures: prior comparison and what changed in the camera set."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

TASK = Path(__file__).resolve().parents[1]
T005 = Path('/home/liu/ring_first_3d_workspace/experiments/TASK-E4-UNIFIED-RING-RGB-CAMERA-MAINLINE-005')
FIG = TASK / 'visualization/figures'; FIG.mkdir(parents=True, exist_ok=True)


def cam(p): return np.asarray(json.loads(Path(p).read_text())['c2w_mm'], float)


def fig_summary():
    g = pd.read_csv(TASK / 'PILOT_SUMMARY.csv')
    g['inst'] = g['group'] + '/' + g['video'].astype(str).str.zfill(3)
    a0 = pd.DataFrame([
        dict(tag='A0', inst='G01/004', ring=1.28, held=8.53, npass=8, val=0),
        dict(tag='A0', inst='G03/004', ring=0.88, held=27.50, npass=8, val=0),
        dict(tag='A0', inst='G03/005', ring=0.749, held=6.126, npass=8, val=2)])
    d = pd.concat([a0, g[['tag', 'inst', 'ring', 'held', 'npass', 'val']]], ignore_index=True)
    d.to_csv(TASK / 'PILOT_COMPARISON.csv', index=False)
    for inst in ['G01/004', 'G03/004', 'G03/005']:
        s = d[d.inst == inst]
        fig, ax = plt.subplots(1, 3, figsize=(13, 3.8))
        ax[0].bar(s.tag, s.held, color=['#222' if t == 'A0' else '#468' for t in s.tag])
        ax[0].set_title('held-out RGB MAE median (px)'); ax[0].axhline(s[s.tag == 'A0'].held.iloc[0], ls=':', c='k', lw=.8)
        ax[1].bar(s.tag, s.npass, color=['#222' if t == 'A0' else '#2a7' for t in s.tag])
        ax[1].set_title('views passing 3 px Ring gate (of 8)'); ax[1].set_ylim(0, 8.5)
        ax[2].bar(s.tag, s.ring, color=['#222' if t == 'A0' else '#a35' for t in s.tag])
        ax[2].set_title('Ring MAE vs raw boundary (px)')
        fig.suptitle(f'{inst}: opt-in DXY priors vs frozen A0 (missing bar = prior not run / NO_BA_VERSION)', fontsize=10)
        fig.tight_layout(); fig.savefig(FIG / f'fig1_{inst.replace("/","_")}_comparison.png', dpi=130); plt.close(fig)


def fig_cameras():
    pairs = [('G01', '004'), ('G03', '005')]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4))
    for ax, (g, v) in zip(axes, pairs):
        for tag, base, col in (('A0', T005 / 'runs', 'k'), ('P1', TASK / 'runs/P1', 'orange'),
                               ('P5', TASK / 'runs/P5', 'green'), ('P3', TASK / 'runs/P3', 'blue')):
            d = Path(base) / g / v / 'camera'
            if not d.exists(): continue
            cs = np.array([cam(p) for p in sorted(d.glob('*/CAMERA_RESULT.json'))])
            if len(cs): ax.scatter(cs[:, 0], cs[:, 2], s=26, c=col, label=tag)
        ax.scatter([0], [0], marker='*', s=150, c='gold')
        ax.set_aspect('equal'); ax.grid(alpha=.3); ax.legend(fontsize=7)
        ax.set_title(f'{g}/{v}'); ax.set_xlabel('x (mm)'); ax.set_ylabel('z (mm)')
    fig.suptitle('Camera layout: A0 vs opt-in priors (same frozen tracks/candidates/BA budget)', fontsize=10)
    fig.tight_layout(); fig.savefig(FIG / 'fig2_camera_layout.png', dpi=130); plt.close(fig)


if __name__ == '__main__':
    fig_summary(); fig_cameras()
    print('figures:', sorted(p.name for p in FIG.glob('*.png')))
