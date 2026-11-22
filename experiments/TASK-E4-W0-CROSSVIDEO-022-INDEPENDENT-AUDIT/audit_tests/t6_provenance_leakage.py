"""S4: what stage chain produced the G03 matches; FIT/HOLDOUT leakage; residual tail."""
import sys, json
from pathlib import Path
import numpy as np, pandas as pd
WS = Path('/home/liu/ring_first_3d_workspace')
C21 = WS/'experiments/TASK-E4-W0-CROSSVIDEO-021-CORRECTIVE'
sys.path.insert(0, str(C21/'core')); sys.path.insert(0, '/home/liu/ring_first_3d_workspace/src')
import shared_se3 as S3
K = np.array([[490., 0, 319.5], [0, 490., 179.5], [0, 0, 1.]])


def main():
    r = json.loads((C21/'runs/G03/RESULTS.json').read_text())
    sp = json.loads((C21/'runs/G03/SPLIT.json').read_text())
    ms = np.load(C21/'runs/G03/MATCHES.npz')
    a = [str(x) for x in ms['a']]; b = [str(x) for x in ms['b']]
    off = ms['off']
    fit, ho = set(sp['fit']), set(sp['holdout'])
    # 004 view reuse across fit/holdout pairs
    per4 = {}
    for k in range(len(a)):
        per4.setdefault(a[k], {'fit': 0, 'holdout': 0})
        per4[a[k]]['holdout' if b[k] in ho else 'fit'] += 1
    leaked_004 = {v: c for v, c in per4.items() if c['fit'] > 0 and c['holdout'] > 0}
    # residual tail at the final H
    d4 = np.load(WS/'camera_mainline/G03/video004/camera_result.npz')
    d5 = np.load(WS/'camera_mainline/G03/video005/camera_result.npz')
    c4 = {str(i): d4['c2w'][k] for k, i in enumerate(d4['ids'])}
    c5 = {str(i): d5['c2w'][k] for k, i in enumerate(d5['ids'])}
    H = np.array(r['H'])
    rows = []
    for k in range(len(a)):
        lo, hi = int(off[k]), int(off[k + 1])
        dd = S3.sampson_px(ms['pa'][lo:hi], ms['pb'][lo:hi], H, c4[a[k]], c5[b[k]], K)
        for j, x in enumerate(dd):
            rows.append(dict(v004=a[k], v005=b[k], split=('FIT' if b[k] in fit else 'HOLDOUT'), err=float(x)))
    df = pd.DataFrame(rows)
    top = df.nlargest(5, 'err')[['v004', 'v005', 'split', 'err']].to_dict('records')
    out = dict(
        stage_chain_present=dict(sift=True, ratio=0.75, background_mask=True,
                                 mutual_check=False, rgb_ransac=False, multiview_track=False,
                                 triangulated_landmark=False),
        n_pairs=len(a), n_matches=int(len(ms['pa'])),
        fit_pairs=int(sum(1 for v in b if v in fit)), holdout_pairs=int(sum(1 for v in b if v in ho)),
        fit_004_views=sorted({a[k] for k in range(len(a)) if b[k] in fit}),
        holdout_004_views=sorted({a[k] for k in range(len(a)) if b[k] in ho}),
        views_004_used_in_both_fit_and_holdout=sorted(leaked_004),
        leakage_verdict=('LEAKAGE: %d of %d 004 views contribute to BOTH the FIT-estimated H and the HOLDOUT '
                         'evaluation; only 005 views are split, 004 is never held out.')
                        % (len(leaked_004), len(per4)),
        p95_px=float(np.percentile(df['err'], 95)), median_px=float(np.median(df['err'])),
        big_residual_frac_gt50=float((df['err'] > 50).mean()),
        top5_residuals=top)
    print(json.dumps(out, indent=1))
    Path(C21.parent/'TASK-E4-W0-CROSSVIDEO-022-INDEPENDENT-AUDIT'/'results'/'T6_provenance_leakage.json').write_text(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
