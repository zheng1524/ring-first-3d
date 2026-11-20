"""Visualisations for the raw-video v2 pipeline (all inputs from the same source chain)."""
import json
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa
from ring_first_3d.mainline.native.camera import torus_contours

T = Path(__file__).resolve().parents[1]
FIG = T / 'visualization'; [ (FIG/d).mkdir(parents=True, exist_ok=True) for d in ('ring_projection','camera_network','density_comparison') ]
SUM = pd.read_csv(T/'metrics/CAMERA_DENSITY_SUMMARY.csv')
RAW = pd.read_csv(T/'metrics/CAMERA_DENSITY_RAW.csv')
K = np.array([[490.,0,319.5],[0,490.,179.5],[0,0,1]])
K_RING = np.array([[490.,0,319.5],[0,490.,179.5],[0,0,1]])

def cam(p): return np.asarray(json.loads(Path(p).read_text())['c2w_mm'], float)

# ---- fig1: metric curves
fig, ax = plt.subplots(1, 2, figsize=(13, 4.6))
for (g, v), s in SUM.groupby(['group','video']):
    s = s.sort_values('density')
    ax[0].plot(s.density, s.held, '-o', ms=3, label=f'{g}/{int(v):03d}')
    ax[1].plot(s.density, s.npass/s.n, '-o', ms=3)
ax[0].set_xlabel('calibration views N'); ax[0].set_ylabel('held RGB MAE median (px)')
ax[0].set_title('independent RGB consistency', fontsize=9); ax[0].legend(fontsize=6, ncol=2); ax[0].grid(alpha=.3)
ax[1].set_xlabel('calibration views N'); ax[1].set_ylabel('fraction passing 3px Ring gate')
ax[1].set_title('Ring coverage', fontsize=9); ax[1].grid(alpha=.3)
for a in ax: a.set_xticks([8,16,22,32])
fig.suptitle('Figure 1  Raw-video v2 pipeline: density sweep 8/16/22/32 (all inputs from one source chain)', fontsize=11)
fig.tight_layout(); fig.savefig(FIG/'density_comparison'/'fig1_metric_curves.png', dpi=130); plt.close(fig)

# ---- fig2: ring projection panels
def pick_view(g, v, n, worst=False):
    prep = T/'runs/prepared'/f'{g}_{int(v):03d}'
    have = {p.stem for p in prep.glob('*.npz')}
    cams = {p.parent.name for p in (T/'runs'/f'N{n}'/g/f'{int(v):03d}'/'camera').glob('*/CAMERA_RESULT.json')}
    ok = sorted(have & cams)
    if not ok:
        return None
    q = pd.read_csv(T/'metrics/CAMERA_DENSITY_RAW.csv')
    sub = q[(q.group==g)&(q.video==int(v))&(q.density==n)&(q.view.isin(ok))]
    if sub.empty:
        return ok[0]
    return sub.sort_values('held_MAE_px', ascending=worst).iloc[0]['view']

picks = [('G03','005',32,pick_view('G03','005',32),'good (best held)'),
         ('G02','005',22,pick_view('G02','005',22),'medium'),
         ('G03','004',22,pick_view('G03','004',22,worst=True),'bad (unresolved)')]
fig, axes = plt.subplots(len(picks), 3, figsize=(15, 4.2*len(picks)))
for row,(g,v,n,cid,tag) in zip(axes, picks):
    vv = f'{int(v):03d}'
    d = T/'runs'/f'N{n}'/g/vv
    if not d.exists(): 
        for a in row: a.axis('off')
        continue
    cams = sorted((d/'camera').glob('*/CAMERA_RESULT.json'))
    if cid is None:
        q = pd.read_csv(T/'metrics/CAMERA_DENSITY_RAW.csv')
        sub = q[(q.group==g)&(q.video==int(v))&(q.density==n)].sort_values('held_MAE_px', ascending=False)
        cid = sub.iloc[0]['view']
    cache = np.load(T/'runs/prepared'/f'{g}_{vv}'/(cid+'.npz'))
    rgb, lab = cache['RGB'], cache['labels']
    cp = d/'camera'/cid/'CAMERA_RESULT.json'
    if not cp.exists():
        for a in row: a.axis('off')
        continue
    C = cam(cp); res = json.loads(cp.read_text())
    qd = dict(np.load(d/'observations'/(cid+'_ring.npz')))
    row[0].imshow(rgb); row[0].set_title(f'{cid}  [{tag}]', fontsize=8)
    row[1].imshow(rgb)
    m = (lab>0).astype(np.uint8)
    row[1].imshow(np.dstack([m*0,m*255,m*60]).astype(np.uint8), alpha=.45)
    for cu in torus_contours(C, K):
        row[1].plot(np.asarray(cu)[:,0], np.asarray(cu)[:,1], ':', lw=1.2, c='yellow')
    row[1].plot(qd['q_train'][:,0], qd['q_train'][:,1], '.', ms=1.2, c='red')
    row[1].set_title('Ring mask + CAD projection + observations', fontsize=8)
    row[2].imshow(rgb); row[2].plot(qd['q_train'][:,0], qd['q_train'][:,1], '.', ms=1.2, c='lime')
    row[2].set_title(f"Ring MAE={res['ring_boundary_MAE_px']:.2f}px  N={n}", fontsize=8)
    for a in row: a.axis('off')
fig.suptitle('Figure 2  Ring projection on raw-video v2 masks: good / medium / unresolved', fontsize=11)
fig.tight_layout(); fig.savefig(FIG/'ring_projection'/'fig2_ring_panels.png', dpi=120); plt.close(fig)

# ---- fig3: camera networks
def net(g, v, n, fname, title):
    d = T/'runs'/f'N{n}'/g/v/'camera'
    fs = sorted(d.glob('*/CAMERA_RESULT.json'))
    if not fs: return
    cs = np.array([cam(p) for p in fs])
    fig = plt.figure(figsize=(6.5,5.5)); ax = fig.add_subplot(111, projection='3d')
    ax.scatter(cs[:,0], cs[:,2], cs[:,1], c='#c33', s=26, depthshade=False)
    th = np.linspace(0,2*np.pi,140)
    ax.plot(5.6*np.cos(th), 5.6*np.sin(th), np.zeros_like(th), c='k', lw=1.6)
    ax.set_xlabel('X (mm)'); ax.set_ylabel('Z (mm)'); ax.set_zlabel('Y (mm)')
    ax.set_title(title, fontsize=9)
    fig.tight_layout(); fig.savefig(FIG/'camera_network'/fname, dpi=120); plt.close(fig)
net('G03','005',32,'fig3a_G03_005_N32.png','G03/005 N=32: 6 VALIDATED, held 2.47 px')
net('G03','004',22,'fig3b_G03_004_N22.png','G03/004 N=22: unresolved, held 97 px')
net('G02','005',22,'fig3c_G02_005_N22.png','G02/005 N=22: held 6.61 px')

# ---- fig4: density layout comparison (G02/005)
fig, axes = plt.subplots(1, 4, figsize=(17, 4.2))
for ax, n in zip(axes, (8,16,22,32)):
    d = T/'runs'/f'N{n}'/'G02'/'005'/'camera'
    fs = sorted(d.glob('*/CAMERA_RESULT.json'))
    if not fs: ax.axis('off'); continue
    cs = np.array([cam(p) for p in fs])
    ax.scatter(cs[:,0], cs[:,2], s=26, c='#468'); ax.scatter([0],[0], marker='*', s=150, c='gold')
    ax.set_aspect('equal'); ax.grid(alpha=.3); ax.set_title(f'N={n} ({len(cs)} cams)', fontsize=9)
    ax.set_xlabel('x (mm)'); ax.set_ylabel('z (mm)')
fig.suptitle('Figure 4  G02/005: camera layout vs view density (same source chain, nested sets)', fontsize=11)
fig.tight_layout(); fig.savefig(FIG/'density_comparison'/'fig4_G02_005_layout.png', dpi=130); plt.close(fig)

# ---- fig5: per-view held error contrast
fig, ax = plt.subplots(figsize=(9,4.2))
for (g,v,n,c) in [('G03','005',32,'#2a7'),('G03','004',22,'#c33'),('G02','005',22,'#468')]:
    s = RAW[(RAW.group==g)&(RAW.video==int(v))&(RAW.density==n)].sort_values('held_MAE_px', ascending=False)
    ax.bar(np.arange(len(s))+(0.25 if g=='G02' else (0 if g=='G03' and v==4 else -0.25)), s.held_MAE_px,
           width=.25, color=c, label=f'{g}/{int(v):03d} N={n}')
ax.set_yscale('log'); ax.set_xlabel('view rank (worst first)'); ax.set_ylabel('held MAE (px, log)')
ax.legend(fontsize=8); ax.grid(alpha=.3, axis='y')
ax.set_title('Figure 5  Per-view RGB held error: G03/005 (good) vs G03/004 (unresolved) vs G02/005', fontsize=9)
fig.tight_layout(); fig.savefig(FIG/'ring_projection'/'fig5_perview_held.png', dpi=130); plt.close(fig)
print('figures:', sorted(p.name for p in FIG.rglob('*.png')))
