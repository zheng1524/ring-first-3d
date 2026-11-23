#!/usr/bin/env python3
"""Per-group 8-panel real-data figure + cross-group summary. All values read from saved runs."""
import json
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
F = Path('/home/liu/ring_first_3d_workspace/experiments/TASK-E4-W0-CROSSVIDEO-028-CORRECTIVE-FINAL')
def rd(p):
    p = Path(p); return pd.read_csv(p) if p.exists() and p.stat().st_size else pd.DataFrame()
allrows = []
for g in ('G01','G03','G06'):
    R = F/'runs'/g; FIG = R/'figures'; FIG.mkdir(parents=True, exist_ok=True)
    try: S = json.loads((R/'SUMMARY.json').read_text())
    except Exception: S = {}
    onw = rd(R/'evaluation'/'OLD_VS_NEW.csv'); hc = rd(R/'h_initialization'/'H_CANDIDATES.csv')
    ring = rd(R/'ring'/'RING_SCORES.csv'); ids = rd(R/'identities'/'IDENTITIES.csv')
    fit = rd(R/'evaluation'/'REPROJ_FIT_old.csv'); ho = rd(R/'evaluation'/'REPROJ_HOLDOUT_old.csv')
    tri = rd(R/'triangulation'/'TRI_old.csv')
    fig, axs = plt.subplots(2, 4, figsize=(22, 9))
    ax = axs.flat
    # (a) view selection: camera centres + Ring circle
    import glob
    for v in ('004','005'):
        sel = rd(R/'view_selection'/f'SELECT_{v}.csv')
        if len(sel): ax[0].scatter(sel.index, sel.n_sift, s=30, label=f'{v} SIFT')
    ax[0].set_title('(a) view selection: SIFT counts per candidate'); ax[0].legend(fontsize=6); ax[0].grid(alpha=.2)
    # (b) identities
    if len(ids): ids.status.value_counts().plot.bar(ax=ax[1]); ax[1].tick_params(axis='x', rotation=20, labelsize=6)
    ax[1].set_title(f'(b) identities ({len(ids)})')
    # (c) H candidates ring vs epi
    if len(hc):
        ax[2].scatter(hc.ring, hc.epi, c=hc.get('valid', np.ones(len(hc))).astype(float), s=30, cmap='RdYlGn')
        ax[2].set_xlabel('Ring energy'); ax[2].set_ylabel('Sampson px'); ax[2].set_title('(c) H candidates (green=epi valid)')
        ax[2].grid(alpha=.2)
    else:
        ax[2].text(.1, .5, 'no H candidates'); ax[2].axis('off')
    # (d) triangulation diagnostics
    if len(tri):
        ax[3].scatter(tri.parallax_deg, tri.reproj_max, s=30); ax[3].set_xlabel('parallax (deg)'); ax[3].set_ylabel('max reproj px')
        ax[3].set_title(f'(d) {len(tri)} FIT identities triangulated'); ax[3].grid(alpha=.2)
    # (e) reprojection hist
    for d, lab, c in ((fit, 'FIT', '#2980b9'), (ho, 'HOLDOUT', '#c0392b')):
        e = d[d.get('neg', 0) == 0].err.dropna() if len(d) and 'err' in d else pd.Series(dtype=float)
        if len(e): ax[4].hist(e, bins=20, alpha=.6, color=c, label=lab)
    ax[4].set_yscale('log'); ax[4].set_xlabel('reproj px'); ax[4].legend(fontsize=6); ax[4].set_title('(e) old-route reprojection')
    # (f) ring per view
    if len(ring):
        for v, d in ring.groupby('view'):
            pass
        ax[5].scatter(range(len(ring)), ring.MIO, s=25); ax[5].set_ylabel('Ring MIO'); ax[5].set_title('(f) Ring per selected view'); ax[5].grid(alpha=.2)
    # (g) old vs new
    if len(onw):
        x = np.arange(len(onw)); ax[6].bar(x-0.2, onw.fit_median, .4, label='FIT', color='#2980b9')
        ax[6].bar(x+0.2, onw.ho_median, .4, label='HOLDOUT', color='#c0392b'); ax[6].set_yscale('log')
        ax[6].set_xticks(x, [str(t) for t in onw.pipeline]); ax[6].legend(fontsize=6); ax[6].set_title('(g) old vs new (median px)')
    # (h) status
    ax[7].axis('off')
    txt = [f"{g} status: {S.get('status')}",
           f"ref={S.get('ref')} other={S.get('other')} views={S.get('n_views')}",
           f"identities={S.get('n_identities')} fit={S.get('n_fit')} hold={S.get('n_holdout')}",
           f"epi_available={S.get('epi_available')}",
           f"ring MIO median={S.get('ring_MIO_median')}"]
    if len(onw):
        for _, r in onw.iterrows():
            txt.append(f"{r.pipeline}: FIT {r.fit_median:.2f} px, HOLD {r.ho_median:.2f} px, ring {r.ring_energy:.3f}")
    ax[7].text(0, .95, '\n'.join(txt), va='top', fontsize=8)
    fig.suptitle(f'{g}: unified real-data pipeline (panels a-h)', fontsize=12)
    fig.tight_layout(); fig.savefig(FIG/f'{g}_unified_8panel.png', dpi=120); plt.close(fig)
    if len(onw) and (S.get('n_fit_used') or S.get('n_fit')):
        for _, r in onw.iterrows():
            allrows.append(dict(group=g, pipeline=r.pipeline, fit=r.fit_median, hold=r.ho_median,
                                ring=r.ring_energy, n_fit=S.get('n_fit_used', S.get('n_fit')), n_hold=S.get('n_holdout_used', S.get('n_holdout')),
                                status=S.get('status'), epi=S.get('epi_available')))
pd.DataFrame(allrows).to_csv(F/'runs'/'CROSS_GROUP.csv', index=False)
fig, ax = plt.subplots(figsize=(9, 4.5))
if allrows:
    x = np.arange(len(allrows)); ax.bar(x-0.2, [r['fit'] for r in allrows], .4, label='FIT', color='#2980b9')
    ax.bar(x+0.2, [r['hold'] for r in allrows], .4, label='HOLDOUT', color='#c0392b')
    ax.set_xticks(x, [f"{r['group']}:{r['pipeline']}" for r in allrows], rotation=20, fontsize=7)
    ax.set_yscale('log'); ax.set_ylabel('median reprojection px'); ax.legend()
fig.suptitle('cross-group old vs new (real data, same code)'); fig.tight_layout()
fig.savefig(F/'runs'/'CROSS_GROUP.png', dpi=130); plt.close(fig)
print('groups with results:', sorted({r['group'] for r in allrows}))
