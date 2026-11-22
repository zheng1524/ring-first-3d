"""Level-1 reproduction: recompute the G03 FIT/HOLDOUT Sampson medians from saved inputs."""
import json, sys
from pathlib import Path
import numpy as np
C = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(C/'core'))
import shared_se3 as S3
K = np.array([[490., 0, 319.5], [0, 490., 179.5], [0, 0, 1.]])


def main():
    r = json.loads((C/'runs/G03/RESULTS.json').read_text())
    sp = json.loads((C/'runs/G03/SPLIT.json').read_text())
    ms = np.load(C/'runs/G03/MATCHES.npz')
    H = np.array(r['H'])
    seed = np.eye(4); th = np.deg2rad(r['init']['theta']); c, s = np.cos(th), np.sin(th)
    seed[:3, :3] = [[c, -s, 0], [s, c, 0], [0, 0, 1]]
    # the cameras are recovered from the W0 files (real inputs, not from the saved statistics)
    d4 = np.load(Path('/home/liu/ring_first_3d_workspace/camera_mainline/G03/video004/camera_result.npz'))
    d5 = np.load(Path('/home/liu/ring_first_3d_workspace/camera_mainline/G03/video005/camera_result.npz'))
    c4 = {str(i): d4['c2w'][k] for k, i in enumerate(d4['ids'])}
    c5 = {str(i): d5['c2w'][k] for k, i in enumerate(d5['ids'])}
    per = {}
    for k in range(len(ms['a'])):
        a, b = str(ms['a'][k]), str(ms['b'][k])
        lo, hi = int(ms['off'][k]), int(ms['off'][k+1])
        per.setdefault(b, []).append((c4[a], c5[b], ms['pa'][lo:hi], ms['pb'][lo:hi]))
    def med(views, M):
        d = np.concatenate([S3.sampson_px(u, v, M, A, B, K) for vb in views for (A, B, u, v) in per.get(vb, [])])
        return float(np.median(d)), int(len(d)), float(np.mean(d < 3))
    fit_seed = med(sp['fit'], seed); ho_seed = med(sp['holdout'], seed)
    fit = med(sp['fit'], H); ho = med(sp['holdout'], H)
    out = dict(seed=dict(fit_median=fit_seed[0], holdout_median=ho_seed[0]),
               final=dict(fit_median=fit[0], fit_n=fit[1], fit_inlier3=fit[2],
                          holdout_median=ho[0], holdout_n=ho[1], holdout_inlier3=ho[2]),
               expected=dict(seed_fit=r['seed']['fit']['median'], seed_holdout=r['seed']['holdout']['median'],
                             fit=r['final']['fit']['median'], holdout=r['final']['holdout']['median']),
               match=bool(abs(fit[0] - r['final']['fit']['median']) < 1e-6 and
                          abs(ho[0] - r['final']['holdout']['median']) < 1e-6 and
                          abs(fit_seed[0] - r['seed']['fit']['median']) < 1e-6))
    print(json.dumps(out, indent=1))
    (C/'metrics/OFFLINE_REPRODUCTION.json').write_text(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
