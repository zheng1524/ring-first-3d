"""Level-1 reproduction from bundled fixtures + saved H/split (no W0 files needed)."""
import json, sys
from pathlib import Path
import numpy as np
B = Path(__file__).resolve().parents[1]
sys.path.insert(0, '/home/liu/ring_first_3d_workspace/camera_mainline/code')
import shared_se3 as S3
K = np.array([[490., 0, 319.5], [0, 490., 179.5], [0, 0, 1.]])


def main():
    d4 = np.load(B/'fixtures/camera_004.npz'); d5 = np.load(B/'fixtures/camera_005.npz')
    c4 = {str(i): d4['c2w'][k] for k, i in enumerate(d4['ids'])}
    c5 = {str(i): d5['c2w'][k] for k, i in enumerate(d5['ids'])}
    ms = np.load(B/'runs/G03/MATCHES.npz')
    r = json.loads((B/'runs/G03/RESULTS.json').read_text())
    sp = json.loads((B/'runs/G03/SPLIT.json').read_text())
    H = np.array(r['B_se3']['H'])
    pairs = {}
    for k in range(len(ms['a'])):
        a, b = str(ms['a'][k]), str(ms['b'][k])
        lo, hi = int(ms['off'][k]), int(ms['off'][k+1])
        pairs.setdefault(b, []).append((c4[a], c5[b], ms['pa'][lo:hi], ms['pb'][lo:hi]))
    def med(views):
        d = np.concatenate([S3.sampson_px(u, v, H, A, Bv, K) for vb in views for (A, Bv, u, v) in pairs.get(vb, [])])
        return float(np.median(d)), int(len(d)), float(np.mean(d < 3))
    fit = med(sp['fit']); ho = med(sp['holdout'])
    out = dict(fit_median=fit[0], fit_n=fit[1], fit_inlier3=fit[2],
               holdout_median=ho[0], holdout_n=ho[1], holdout_inlier3=ho[2],
               expected=dict(fit_median=r['B_se3']['fit']['median'], holdout_median=r['B_se3']['holdout']['median']),
               match=bool(abs(fit[0]-r['B_se3']['fit']['median']) < 0.01 and abs(ho[0]-r['B_se3']['holdout']['median']) < 0.01))
    print(json.dumps(out, indent=1))
    (B/'metrics/OFFLINE_REPRODUCTION.json').write_text(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
