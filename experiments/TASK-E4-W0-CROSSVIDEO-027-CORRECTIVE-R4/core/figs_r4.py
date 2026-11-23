#!/usr/bin/env python3
"""R4 figures + aggregation, all read from runs/controlled_error_ablation/*/METRICS.json."""
import glob, json
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
R4 = Path('/home/liu/ring_first_3d_workspace/experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R4')
ROOT = R4/'runs/controlled_error_ablation'; FIG = R4/'runs/FIGURES'; FIG.mkdir(parents=True, exist_ok=True)
rows = []
for f in sorted(glob.glob(str(ROOT/'*/*/METRICS.json'))):
    d = json.loads(open(f).read()); d['dir'] = str(Path(f).parent.relative_to(ROOT)); rows.append(d)
df = pd.DataFrame(rows)
if len(df):
    df.to_csv(R4/'runs/SUMMARY_ALL_RUNS.csv', index=False)
    df['plan'] = df['group'].str.extract(r'^([A-Z0-9]+)')
print('runs', len(df))

def sav(fig, name):
    fig.tight_layout(); fig.savefig(FIG/name, dpi=140); plt.close(fig)

if len(df):
    # 1 initial geometry per group
    fig = plt.figure(figsize=(15, 4.4))
    for k, (i1, i2) in enumerate(((0, 1), (0, 2), (1, 2))):
        ax = fig.add_subplot(1, 3, k+1)
        rep = {}
        for _, r in df[df['mode'] == 'M0'].iterrows():
            z = np.load(ROOT/r['dir']/'RESULT.npz')
            rep.setdefault(r['group'].split('_')[0], []).append((z['X_init'], r['group']))
        for g, lst in rep.items():
            X = lst[0][0]
            ax.scatter(X[:, i1], X[:, i2], s=14, label=f'{g} init')
        z = np.load(ROOT/df['dir'].iloc[0]/'RESULT.npz')
        ax.scatter(z['X_gt'][:, i1], z['X_gt'][:, i2], s=40, c='k', marker='*', label='GT')
        ax.set_xlabel('XYZ'[i1]); ax.set_ylabel('XYZ'[i2]); ax.grid(alpha=.2)
        if k == 0: ax.legend(fontsize=6)
    fig.suptitle('1: initial landmark sets A–E vs GT (same axes)', fontsize=8); sav(fig, '01_initial_geometry_A_to_E.png')
    # 2 triangulation error vectors C vs E1
    fig = plt.figure(figsize=(13, 5))
    for k, (gname, i1, i2) in enumerate((('C_landmark_only_3', 0, 2), ('E1_retri_005', 0, 2))):
        ax = fig.add_subplot(1, 2, k+1)
        d = df[(df.group == gname) & (df['mode'] == 'M0')]
        if len(d):
            z = np.load(ROOT/d['dir'].iloc[0]/'RESULT.npz')
            X0, Xg = z['X_init'], z['X_gt']
            for a, b in zip(X0, Xg):
                ax.plot([a[i1], b[i1]], [a[i2], b[i2]], '-', c='#e74c3c' if k else '#2980b9', lw=1)
            ax.scatter(Xg[:, i1], Xg[:, i2], s=18, c='k', label='GT')
        ax.set_title(f'{gname}: init->GT vectors', fontsize=8); ax.grid(alpha=.2)
    sav(fig, '02_triangulation_error_vectors.png')
    # 3 camera vs landmark sensitivity
    d = df[df['mode'] == 'M0'].groupby('group').agg(H_rot=('H_rot', 'first'), lm=('lm_init_err', 'first'),
                                                     cam=('cam_rot_max', 'first')).reset_index()
    fig, axs = plt.subplots(1, 2, figsize=(13, 4))
    axs[0].bar(d.group, d.lm, color='#2980b9'); axs[0].set_ylabel('initial landmark error (mm)'); axs[0].tick_params(axis='x', rotation=80, labelsize=5)
    axs[1].bar(d.group, d.H_rot, color='#e74c3c'); axs[1].set_ylabel('initial H error (deg)'); axs[1].tick_params(axis='x', rotation=80, labelsize=5)
    fig.suptitle('3: initial perturbation magnitudes (mm and deg separated, not mixed)', fontsize=8); sav(fig, '03_camera_vs_landmark_sensitivity.png')
    # 4 M0-M3 comparison
    fig, ax = plt.subplots(figsize=(12, 4.4))
    piv = df.pivot_table(index='group', columns='mode', values='H_rot', aggfunc='first')
    piv.plot(kind='bar', ax=ax, logy=True); ax.set_ylabel('final H rotation error (deg)')
    ax.tick_params(axis='x', rotation=80, labelsize=5); ax.grid(alpha=.2)
    ax.set_title('4: M0 (no opt) / M1 (landmarks) / M2 (H) / M3 (H then landmarks); M4 NOT_EXECUTED', fontsize=8)
    sav(fig, '04_M0_to_M4_comparison.png')
    # 5 ring vs rgb
    fig, ax = plt.subplots(figsize=(7.5, 4.4))
    for g, d in df[df['mode'].isin(['M2', 'M3'])].groupby('group'):
        ax.scatter(d.rgb_median1, np.maximum(d.ring1, 1e-16), label=g, s=30)
    ax.set_xlabel('RGB median reprojection (px)'); ax.set_ylabel('Ring energy (I+C+O)')
    ax.set_yscale('log'); ax.legend(fontsize=5); ax.grid(alpha=.2)
    ax.set_title('5: Ring vs RGB after optimisation (does RGB improve by breaking Ring?)', fontsize=8)
    sav(fig, '05_ring_rgb_geometry_conflict.png')
    # 6 summary heatmap
    fig, ax = plt.subplots(figsize=(10, 4.6))
    hm = df.pivot_table(index='group', columns='mode', values='lm_err', aggfunc='first')
    im = ax.imshow(hm.values.astype(float), aspect='auto', cmap='viridis')
    ax.set_xticks(range(hm.shape[1]), hm.columns); ax.set_yticks(range(hm.shape[0]), hm.index, fontsize=5)
    fig.colorbar(im, ax=ax, label='final landmark error (mm)')
    ax.set_title('6: landmark recovery across groups and optimisation modes', fontsize=8)
    sav(fig, '06_error_source_summary.png')
print('figures', len(list(FIG.glob('*.png'))))
