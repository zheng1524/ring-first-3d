#!/usr/bin/env python3
"""P1: independent F_img check — estimate F on TRAIN points only, evaluate on held-out points.

Also: homography degeneracy test, epipole location, and per-pair mutual subsets.
Read-only; no change to 021 H, W0 or matches.
"""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd, cv2
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
WS = Path('/home/liu/ring_first_3d_workspace')
C21 = WS/'experiments/TASK-E4-W0-CROSSVIDEO-021-CORRECTIVE'
N = WS/'experiments/TASK-E4-W0-CROSSVIDEO-023-RESTORE-AND-VALIDATE'
OUT = N/'runs/G03'; OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(C21/'core')); sys.path.insert(0, str(N/'tools'))
import shared_se3 as S3
from forensic_epipolar_fixed import F_from_pose, K, load_rgb, cams


def sampson(F, a, b):
    x = np.c_[a, np.ones(len(a))]; y = np.c_[b, np.ones(len(b))]
    Fx = (F @ x.T).T; Fty = (F.T @ y.T).T
    return np.abs(np.einsum('ij,ij->i', y, Fx))/np.sqrt((Fx[:, :2]**2).sum(1)+(Fty[:, :2]**2).sum(1)+1e-12)


def epipole(F):
    _, _, Vt = np.linalg.svd(F); e5 = Vt[-1]; e5 = e5/e5[2] if abs(e5[2]) > 1e-12 else e5
    _, _, Vt2 = np.linalg.svd(F.T); e4 = Vt2[-1]; e4 = e4/e4[2] if abs(e4[2]) > 1e-12 else e4
    return e4, e5


def main():
    M = np.load(C21/'runs/G03/MATCHES.npz')
    a = [str(x) for x in M['a']]; b = [str(x) for x in M['b']]; off = M['off']
    pa, pb = M['pa'], M['pb']
    H = np.array(json.loads((C21/'runs/G03/RESULTS.json').read_text())['H'])
    c4, c5 = cams()
    hold_pose, hold_img, hold_hom, n_tr, n_ho, e4s, e5s, names = [], [], [], [], [], [], [], []
    for k in range(len(a)):
        lo, hi = int(off[k]), int(off[k+1])
        x4, x5 = pa[lo:hi].copy(), pb[lo:hi].copy()
        n = len(x4)
        if n < 24:
            continue
        # spatial split: train on the left half of image 4, hold out the right half
        med = float(np.median(x4[:, 0]))
        tr = x4[:, 0] <= med; ho = ~tr
        if tr.sum() < 12 or ho.sum() < 8:
            continue
        Fp = F_from_pose(H, c4[a[k]], c5[b[k]], K)
        d_pose = sampson(Fp, x4[ho], x5[ho])
        Fi, _ = cv2.findFundamentalMat(x4[tr].astype(np.float32), x5[tr].astype(np.float32),
                                       cv2.USAC_MAGSAC, 1.5, 0.999, 10000)
        if Fi is None or Fi.shape != (3, 3):
            Fi = None
        d_img = sampson(Fi/np.linalg.norm(Fi), x4[ho], x5[ho]) if Fi is not None else np.full(ho.sum(), np.nan)
        Hm, _ = cv2.findHomography(x4[tr], x5[tr], cv2.RANSAC, 3.0) if tr.sum() >= 12 else (None, None)
        if Hm is not None:
            proj = cv2.perspectiveTransform(x4[ho].reshape(-1, 1, 2).astype(np.float64), Hm).reshape(-1, 2)
            d_hom = np.linalg.norm(proj - x5[ho], axis=1)
        else:
            d_hom = np.full(ho.sum(), np.nan)
        name = f'{a[k]}__{b[k]}'; names.append(name)
        hold_pose.append(float(np.median(d_pose))); hold_img.append(float(np.nanmedian(d_img)))
        hold_hom.append(float(np.nanmedian(d_hom))); n_tr.append(int(tr.sum())); n_ho.append(int(ho.sum()))
        e4, e5 = epipole(Fp); e4s.append(e4); e5s.append(e5)
    df = pd.DataFrame(dict(pair=names, n_train=n_tr, n_holdout=n_ho,
                           pose_holdout_median=hold_pose, img_holdout_median=hold_img,
                           homography_holdout_median=hold_hom))
    df['img_better'] = df['img_holdout_median'] < df['pose_holdout_median']
    df.to_csv(OUT/'P1_F_holdout_comparison.csv', index=False)
    ep = pd.DataFrame(dict(pair=names,
                           e4_x=[float(x[0]) for x in e4s], e4_y=[float(x[1]) for x in e4s],
                           e5_x=[float(x[0]) for x in e5s], e5_y=[float(x[1]) for x in e5s]))
    ep.to_csv(OUT/'P1_epipoles.csv', index=False)
    summ = dict(n_pairs=len(df),
                pose_holdout_median=float(df.pose_holdout_median.median()),
                img_holdout_median=float(df.img_holdout_median.median()),
                homography_holdout_median=float(df.homography_holdout_median.median()),
                pairs_img_better=int(df.img_better.sum()),
                frac_img_better=float(df.img_better.mean()),
                note=('F_img is estimated on the train half only and evaluated on the held-out half, '
                      'so this is an out-of-sample comparison. Homography is the degeneracy probe: '
                      'if H_img explains the holdout as well as F_img, the scene/motion is near-planar or low-parallax.'))
    (OUT/'P1_summary.json').write_text(json.dumps(summ, indent=1))
    print(json.dumps(summ, indent=1))
    print(df[['pose_holdout_median','img_holdout_median','homography_holdout_median']].describe().round(3).to_string())
    fig, ax = plt.subplots(figsize=(8, 5), constrained_layout=True)
    ax.scatter(df.pose_holdout_median, df.img_holdout_median, s=14, alpha=.7, label='F_img vs F_pose (held-out points)')
    ax.plot([0.1, 200], [0.1, 200], 'k--', lw=.8, label='equal')
    ax.set_xscale('log'); ax.set_yscale('log')
    ax.set_xlabel('F_pose holdout median (px)'); ax.set_ylabel('F_img holdout median (px)')
    ax.set_title('P1: out-of-sample comparison (F_img fitted on the train half only)')
    ax.legend(fontsize=8); ax.grid(alpha=.2)
    fig.savefig(OUT/'06_P1_F_holdout.png', dpi=140); plt.close(fig)


if __name__ == '__main__':
    main()
