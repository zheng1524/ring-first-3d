"""Level-1 offline reproduction: no raw video needed, only the fixtures in this package."""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import geometry as G, yaw_solver as YS

R = Path(__file__).resolve().parents[1]


def load_cams(name):
    d = np.load(R/'fixtures'/name)
    return {str(i): d['c2w'][k] for k, i in enumerate(d['ids'])}, d


def load_matches(name):
    d = np.load(R/'fixtures'/name)
    out = []
    for k in range(len(d['a'])):
        lo, hi = int(d['off'][k]), int(d['off'][k+1])
        out.append((str(d['a'][k]), str(d['b'][k]), d['pa'][lo:hi], d['pb'][lo:hi]))
    return out


def main():
    c4, d4 = load_cams('camera_004.npz')
    c5, _ = load_cams('camera_005.npz')
    K = np.array([[490., 0, 319.5], [0, 490., 179.5], [0, 0, 1.]])
    res = {}
    for tag in ('CROSS_VIDEO_B_ACCEPT', 'CROSS_VIDEO_A_QUARANTINE'):
        ms = load_matches(f'{tag}_matches.npz')
        o = YS.solve([(c4[a], c5[b], pa, pb, K, K) for a, b, pa, pb in ms])
        thetas = np.array([p for p in (YS.solve([(c4[a], c5[b], pa, pb, K, K)])['theta']
                                       for a, b, pa, pb in ms) if p is not None])
        med = float(np.median(thetas)); mad = float(np.median(np.abs(thetas - med)))
        res[tag] = dict(theta_joint=o['theta'], status=o['status'], median_px=o['median_px'],
                        inlier3=o['inlier3'], n_pairs=len(ms), yaw_median=med, yaw_mad=mad,
                        frac_within_5deg=float(np.mean(np.abs(YS.wrap180(thetas - med)) < 5.0)))
    print(json.dumps(res, indent=1))
    out = R/'metrics'
    if not out.exists():
        out = R/'results'
    out.mkdir(parents=True, exist_ok=True)
    (out/'OFFLINE_REPRODUCTION.json').write_text(json.dumps(res, indent=1))


if __name__ == '__main__':
    main()
