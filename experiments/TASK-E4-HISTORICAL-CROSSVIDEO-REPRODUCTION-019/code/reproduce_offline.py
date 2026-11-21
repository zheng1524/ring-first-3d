"""Level-1 offline reproduction from the bundled fixtures (no raw video, no legacy paths)."""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'adapters'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import coordinate_adapter as CA, yaw_solver_019 as YS, geometry_019 as G  # noqa

R = Path(__file__).resolve().parents[1]
FIX = R/'fixtures'


def main():
    c4 = np.load(FIX/'camera_004.npz'); c5 = np.load(FIX/'camera_005.npz')
    P4 = {str(i): c4['c2w'][k] for k, i in enumerate(c4['ids'])}
    P5 = {str(i): c5['c2w'][k] for k, i in enumerate(c5['ids'])}
    K = np.array([[490., 0, 319.5], [0, 490., 179.5], [0, 0, 1.]])
    d = np.load(FIX/'cross_video_B.npz')
    ms = [(str(d['a'][k]), str(d['b'][k]), d['pa'][int(d['off'][k]):int(d['off'][k+1])],
           d['pb'][int(d['off'][k]):int(d['off'][k+1])]) for k in range(len(d['a']))]
    pairs = [(P4[a], P5[b], pa, pb, K, K) for a, b, pa, pb in ms]
    o = YS.solve(pairs)
    print(json.dumps(dict(n_pairs=len(ms), theta=o['theta'], status=o['status'],
                          median_px=o['median_px'], inlier3=o['inlier3']), indent=1))
    H = CA.yaw_about_axis(47.24387768097719)
    a = CA.audit_transform(H, 'H_005<-004_yaw47')
    print(json.dumps(dict(det=a['det'], orth=a['orth'], valid=a['valid']), indent=1))


if __name__ == '__main__':
    main()
