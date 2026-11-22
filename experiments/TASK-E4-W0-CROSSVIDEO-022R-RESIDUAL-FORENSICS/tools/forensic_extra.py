#!/usr/bin/env python3
"""022R S3: F_pose vs F_img, mutual consistency, per-frame normalisation, W0 cross-check.

Read-only: reads MATCHES.npz / RESULTS.json / W0 cameras / PREPARED caches.
Writes diagnostics only; never touches 021, W0, H, thresholds or admission.
"""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd, cv2
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

WS = Path('/home/liu/ring_first_3d_workspace')
C21 = WS/'experiments/TASK-E4-W0-CROSSVIDEO-021-CORRECTIVE'
PREP = WS/'experiments/TASK-E4-UNIFIED-RING-CONTOUR-REFINEMENT-005/runs/prepared'
OUT = WS/'experiments/TASK-E4-W0-CROSSVIDEO-022R-RESIDUAL-FORENSICS/runs/G03'
sys.path.insert(0, str(C21/'core'))
from shared_se3 import sampson_px as official_sampson

FOCUS = [('G03_v004_raw00242','G03_v005_raw00114'), ('G03_v004_raw00263','G03_v005_raw00114'),
         ('G03_v004_raw00304','G03_v005_raw00114'), ('G03_v004_raw00242','G03_v005_raw00099'),
         ('G03_v002' if False else 'G03_v004_raw00242','G03_v005_raw00128'),
         ('G03_key02_raw00327','G03_v005_raw00215')]


def load_rgb(view):
    import json as J
    for g, v in (('G03','004'),('G03','005')):
        p = PREP/f'{g}_{v}'/'PREPARED.json'
        d = J.loads(p.read_text())
        for x in d['views']:
            if x['view'] == view:
                q = Path(x['cache'])
                return np.asarray(np.load(q)['RGB'])[:, :, :3]
    raise KeyError(view)


def cams():
    d4 = np.load(WS/'camera_mainline/G03/video004/camera_result.npz')
    d5 = np.load(WS/'camera_mainline/G03/video005/camera_result.npz')
    c4 = {str(i): d4['c2w'][k] for k, i in enumerate(d4['ids'])}
    c5 = {str(i): d5['c2w'][k] for k, i in enumerate(d5['ids'])}
    return c4, c5, np.asarray(d4['K'], float)


def sampson_px_formula(F, a, b):
    x = np.c_[a, np.ones(len(a))]; y = np.c_[b, np.ones(len(b))]
    Fx = (F @ x.T).T; Fty = (F.T @ y.T).T
    return np.abs(np.einsum('ij,ij->i', y, Fx)) / np.sqrt((Fx[:, :2]**2).sum(1) + (Fty[:, :2]**2).sum(1) + 1e-12)


def sift_feats(img):
    g = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    kp, des = cv2.SIFT_create(nfeatures=6000, contrastThreshold=0.01).detectAndCompute(g, None)
    xy = np.array([k.pt for k in kp], np.float32) if kp else np.zeros((0, 2), np.float32)
    return xy, des


def mutual_fraction(img4, img5, pa, pb):
    """Fraction of the STORED matches whose two endpoints are also mutual SIFT matches."""
    xy4, d4 = sift_feats(img4); xy5, d5 = sift_feats(img5)
    if d4 is None or d5 is None or len(xy4) < 8 or len(xy5) < 8:
        return dict(status='INSUFFICIENT_KEYPOINTS', mutual_frac=None, ratio=0)
    bf = cv2.BFMatcher()
    m45 = bf.knnMatch(d4, d5, k=2); m54 = bf.knnMatch(d5, d4, k=2)
    f45 = {m.queryIdx: m.trainIdx for m, n in m45 if m.distance < 0.75 * n.distance}
    f54 = {m.queryIdx: m.trainIdx for m, n in m54 if m.distance < 0.75 * n.distance}
    mutual = {(i, j) for i, j in f45.items() if f54.get(j) == i}
    if not mutual:
        return dict(status='NO_MUTUAL', mutual_frac=0.0, ratio=0)
    mi = np.array(list(mutual))
    p4, p5 = xy4[mi[:, 0]], xy5[mi[:, 1]]
    # stored endpoints -> nearest keypoint within 2 px, then mutual membership
    kd4 = xy4; kd5 = xy5
    ok = 0
    for a, b in zip(pa, pb):
        i = int(np.argmin(np.linalg.norm(kd4 - a, axis=1))); j = int(np.argmin(np.linalg.norm(kd5 - b, axis=1)))
        if np.linalg.norm(kd4[i] - a) <= 2 and np.linalg.norm(kd5[j] - b) <= 2 and (i, j) in mutual:
            ok += 1
    return dict(status='OK', mutual_frac=ok / max(len(pa), 1), ratio=len(mutual))


def main():
    M = np.load(C21/'runs/G03/MATCHES.npz')
    a = [str(x) for x in M['a']]; b = [str(x) for x in M['b']]; off = M['off']
    pa = M['pa']; pb = M['pb']
    r = json.loads((C21/'runs/G03/RESULTS.json').read_text()); H = np.array(r['H'])
    c4, c5, K = cams()
    rows = []
    for k in range(len(a)):
        lo, hi = int(off[k]), int(off[k+1])
        u, v = pa[lo:hi], pb[lo:hi]
        e_pose = official_sampson(u, v, H, c4[a[k]], c5[b[k]], K)
        Fimg, mask = cv2.findFundamentalMat(u.astype(np.float32), v.astype(np.float32),
                                            cv2.USAC_MAGSAC, 1.5, 0.999, 10000)
        if Fimg is None or Fimg.shape != (3, 3):
            e_img = np.full(len(u), np.nan)
        else:
            e_img = sampson_px_formula(Fimg / np.linalg.norm(Fimg), u, v)
        rows.append(dict(v004=a[k], v005=b[k], n=len(u),
                         pose_median=float(np.median(e_pose)), pose_p95=float(np.percentile(e_pose, 95)),
                         img_median=float(np.nanmedian(e_img)), img_p95=float(np.nanpercentile(e_img, 95)) if np.isfinite(e_img).any() else float('nan'),
                         frac_img_better=float(np.nanmean(e_img < e_pose)),
                         magsac_inliers=int(mask.sum()) if mask is not None else 0,
                         magsac_inlier_frac=float(mask.mean()) if mask is not None else float('nan')))
    df = pd.DataFrame(rows)
    df.to_csv(OUT/'F_pose_vs_F_img.csv', index=False)
    # mutual consistency for focus pairs only (re-extracting SIFT is the expensive part)
    mrows = []
    for (u, v) in FOCUS:
        k = next(i for i in range(len(a)) if a[i] == u and b[i] == v)
        lo, hi = int(off[k]), int(off[k+1])
        try:
            im4, im5 = load_rgb(u), load_rgb(v)
            res = mutual_fraction(im4, im5, pa[lo:hi], pb[lo:hi])
        except Exception as ex:
            res = dict(status=f'ERROR:{ex}', mutual_frac=None, ratio=0)
        mrows.append(dict(v004=u, v005=v, n_stored=hi-lo, **res))
    mdf = pd.DataFrame(mrows); mdf.to_csv(OUT/'mutual_consistency.csv', index=False)
    # per-frame normalised stats for 005
    pts = pd.read_csv(OUT/'point_residuals.csv')
    f5 = pts.groupby('v005').agg(n=('err_px', 'size'), pairs=('v004', 'nunique'),
                                 median=('err_px', 'median'), p95=('err_px', lambda s: np.percentile(s, 95)),
                                 frac_gt50=('err_px', lambda s: float((s > 50).mean()))).reset_index()
    f5['view_rank_by_frac'] = f5['frac_gt50'].rank(ascending=False).astype(int)
    f5.to_csv(OUT/'frame_residuals_normalised_005.csv', index=False)
    # W0 quality cross-check for the frames involved in focus pairs
    w0 = []
    for side, frames in (('004', sorted({u for u, _ in FOCUS})), ('005', sorted({v for _, v in FOCUS}))):
        adm = pd.read_csv(WS/'camera_mainline/G03'/f'video{side}'/'admission.csv')
        for f in frames:
            row = adm[adm['view'].astype(str) == f]
            if len(row):
                x = row.iloc[0]
                w0.append(dict(video=side, view=f, status=x['admission_status'],
                               held_n=x.get('held_n'), held_median=x.get('held_median'),
                               held_p95=x.get('held_p95'), ring_raw_mae=x.get('ring_raw_mae')))
    pd.DataFrame(w0).to_csv(OUT/'W0_quality_crosscheck.csv', index=False)
    # figure: F_pose vs F_img epipolar lines on real images for 4 focus pairs
    sel = FOCUS[:4]
    fig, axs = plt.subplots(len(sel), 2, figsize=(14, 3.4*len(sel)), squeeze=False, constrained_layout=True)
    for row, (u, v) in enumerate(sel):
        im4, im5 = load_rgb(u), load_rgb(v)
        k = next(i for i in range(len(a)) if a[i] == u and b[i] == v)
        lo, hi = int(off[k]), int(off[k+1])
        uu, vv = pa[lo:hi], pb[lo:hi]
        Fp, _ = __import__('shared_se3').fundamental(np.eye(4), c5[v], K, K) if False else (None, None)
        # F_pose from the official model
        T = np.linalg.inv(c5[v]) @ (H @ c4[u]); R, t = T[:3, :3], T[:3, 3]
        tx = np.array([[0, -t[2], t[1]], [t[2], 0, -t[0]], [-t[1], t[0], 0]])
        Fpose = np.linalg.inv(K).T @ (tx @ R) @ np.linalg.inv(K); Fpose /= np.linalg.norm(Fpose)
        Fimg, _ = cv2.findFundamentalMat(uu.astype(np.float32), vv.astype(np.float32), cv2.USAC_MAGSAC, 1.5, 0.999, 10000)
        for col, (im, linepts, F) in enumerate(((im4, uu, Fpose), (im5, vv, Fimg))):
            ax = axs[row, col]; ax.imshow(im); ax.axis('off')
            ax.set_title(f'{"004" if col==0 else "005"} {u if col==0 else v}  ({len(uu)} matches)', fontsize=9)
        # draw 6 sampled points: predicted line under F_pose (cyan) and F_img (magenta)
        order = np.argsort(-np.abs(uu[:, 0]-319.5))[:6]
        for j in order:
            for col, (im, pts, Fl, color) in enumerate(((im4, uu, Fpose, '#00d8ff'), (im5, vv, Fpose.T, '#00d8ff'))):
                l = Fl @ np.r_[uu[j] if col == 0 else vv[j], 1.0]
                x = np.array([0, im.shape[1]-1]); y = -(l[0]*x + l[2])/l[1] if abs(l[1]) > 1e-9 else None
                if y is not None: axs[row, col].plot(x, y, c=color, lw=.9, alpha=.8)
        if Fimg is not None and Fimg.shape == (3, 3):
            Fi = Fimg/np.linalg.norm(Fimg)
            for j in order:
                for col, (im, p, Fl) in enumerate(((im4, uu, Fi.T), (im5, vv, Fi))):
                    l = Fl @ np.r_[p[j], 1.0]
                    x = np.array([0, im.shape[1]-1]); y = -(l[0]*x + l[2])/l[1] if abs(l[1]) > 1e-9 else None
                    if y is not None: axs[row, col].plot(x, y, c='#ff2fb0', lw=.9, alpha=.55, ls='--')
        axs[row, 0].set_ylabel(f'{u}\n↔{v}', fontsize=8)
    fig.suptitle('Cyan = F_pose (W0 + 021 H); magenta dashed = F_img (MAGSAC on the same matches)\n'
                 'Diagnostic only: F_img is not ground truth and is not fed back', fontsize=10)
    fig.savefig(OUT/'05_Fpose_vs_Fimg_epipolar.png', dpi=165); plt.close(fig)
    summary = dict(n_pairs=len(df),
                   pose_median_median=float(df['pose_median'].median()),
                   img_median_median=float(df['img_median'].median()),
                   pairs_img_better_median=int((df['img_median'] < df['pose_median']).sum()),
                   magsac_inlier_frac_median=float(df['magsac_inlier_frac'].median()),
                   frac_img_better_median=float(df['frac_img_better'].median()))
    (OUT/'S3_summary.json').write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary, indent=1))
    print(mdf.to_string(index=False))
    print(f5.sort_values('frac_gt50', ascending=False).head(8).to_string(index=False))


if __name__ == '__main__':
    main()
