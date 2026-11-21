"""Level-1 reproduction: recompute the G03 forward residual before/after from saved inputs."""
import json, sys
from pathlib import Path
import numpy as np
T = Path(__file__).resolve().parents[1]
sys.path.insert(0, '/home/liu/ring_first_3d_workspace/camera_mainline/code')
import shared_se3 as S3
K = np.array([[490., 0, 319.5], [0, 490., 179.5], [0, 0, 1.]])


def main():
    d4 = np.load(T/'fixtures/camera_004.npz'); d5 = np.load(T/'fixtures/camera_005.npz')
    c4 = {str(i): d4['c2w'][k] for k, i in enumerate(d4['ids'])}
    c5 = {str(i): d5['c2w'][k] for k, i in enumerate(d5['ids'])}
    ms = np.load(T/'fixtures/CROSS_VIDEO_B_ACCEPT_matches.npz')
    res = json.loads((T/'runs/G03/SE3_RESULT.json').read_text())
    seed = np.eye(4); th = np.deg2rad(res['seed_yaw_deg']); c, s = np.cos(th), np.sin(th)
    seed[:3, :3] = [[c, -s, 0], [s, c, 0], [0, 0, 1]]
    H = np.array(res['H'])
    pairs = []
    for k in range(len(ms['a'])):
        a, b = str(ms['a'][k]), str(ms['b'][k])
        lo, hi = int(ms['off'][k]), int(ms['off'][k+1])
        pairs.append((c4[a], c5[b], ms['pa'][lo:hi], ms['pb'][lo:hi]))
    d0 = np.concatenate([S3.sampson_px(u, v, seed, A, B, K) for (A, B, u, v) in pairs])
    d1 = np.concatenate([S3.sampson_px(u, v, H, A, B, K) for (A, B, u, v) in pairs])
    out = dict(n_pairs=len(pairs), n_matches=len(d0),
               before_median=float(np.median(d0)), after_median=float(np.median(d1)),
               before_inlier3=float(np.mean(d0 < 3)), after_inlier3=float(np.mean(d1 < 3)),
               expected=dict(before_median=5.323, after_median=4.248),
               match=bool(abs(np.median(d0)-5.323) < 0.01 and abs(np.median(d1)-4.248) < 0.01))
    print(json.dumps(out, indent=1))
    (T/'metrics/OFFLINE_REPRODUCTION.json').write_text(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
