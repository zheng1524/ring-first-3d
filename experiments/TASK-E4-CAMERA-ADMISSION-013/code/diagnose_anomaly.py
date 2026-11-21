"""One-shot anomaly diagnosis: per-track held errors + triangulation geometry."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
WS = Path('/home/liu/ring_first_3d_workspace')
T = WS/'experiments/TASK-E4-CAMERA-ADMISSION-013'
T011 = WS/'experiments/TASK-E4-RING-RGB-JOINT-BA-011-REPAIR'
T012 = WS/'experiments/TASK-E4-RING-RGB-JOINT-BA-012'
sys.path.insert(0, '/home/liu/ring_first_3d_workspace/src')
from ring_first_3d.mainline.native.geometry import project
K = np.array([[490., 0, 319.5], [0, 490., 179.5], [0, 0, 1]])
T006 = WS/'experiments/TASK-E4-UNIFIED-RING-CONTOUR-REFINEMENT-005'
views = json.loads((T006/'runs/prepared/G03_005/PREPARED.json').read_text())['views']
ids = [v['view'] for v in views]
tr = dict(np.load(T011/'runs/G03_005/B0/observations/tracks005.npz'))
xy = tr['xy']; held = np.asarray(tr['held']).astype(bool)
TRACK_IDS = [str(s) for s in tr['ids']]


def triangulate(u1, u2, C1, C2):
    P1 = K @ np.c_[C1[:3, :3].T, -C1[:3, :3].T @ C1[:3, 3]]
    P2 = K @ np.c_[C2[:3, :3].T, -C2[:3, :3].T @ C2[:3, 3]]
    A = np.r_[u1[0]*P1[2]-P1[0], u1[1]*P1[2]-P1[1], u2[0]*P2[2]-P2[0], u2[1]*P2[2]-P2[1]].reshape(4, 4)
    _, _, Vt = np.linalg.svd(A)
    X = Vt[-1]
    return None if abs(X[3]) < 1e-12 else X[:3]/X[3]


def diagnose(cam_path, view_id, label):
    cams = np.load(cam_path)['c2w']
    i = ids.index(view_id)
    rows = []
    for t in np.flatnonzero(held):
        u = xy[t, i]
        if not np.isfinite(u[0]):
            continue
        others = [j for j in range(len(ids)) if j != i and np.isfinite(xy[t, j, 0])]
        if len(others) < 2:
            continue
        best, bd = None, -1
        for a in range(len(others)):
            for b in range(a+1, len(others)):
                j, k = others[a], others[b]
                d = np.linalg.norm(cams[j][:3, 3]-cams[k][:3, 3])
                if d > bd:
                    bd, best = d, (j, k)
        j, k = best
        X = triangulate(xy[t, j], xy[t, k], cams[j], cams[k])
        if X is None:
            continue
        uv, z = project(X[None], cams[i], K)
        if not np.isfinite(uv).all():
            continue
        e = float(np.linalg.norm(uv[0]-u))
        # viewing angle between the two triangulating rays
        r1 = (X - cams[j][:3, 3]); r2 = (X - cams[k][:3, 3])
        ang = float(np.degrees(np.arccos(np.clip(r1 @ r2/np.linalg.norm(r1)/np.linalg.norm(r2), -1, 1))))
        rows.append(dict(arm=label, view=view_id, track=int(t), track_id=int(t),
                         err=round(e, 3), tri_view_a=ids[j], tri_view_b=ids[k],
                         baseline_mm=round(float(bd), 2), angle_deg=round(ang, 2),
                         depth_a=round(float(z[0]), 2), obs_in_other_views=int(len(others))))
    df = pd.DataFrame(rows).sort_values('err', ascending=False)
    return df


if __name__ == '__main__':
    out = []
    out.append(diagnose(T012/'runs/G03_005'/'W0'/'cameras.npz', 'G03_v005_raw00229', 'W0'))
    out.append(diagnose(T011/'runs/G03_005'/'B0'/'cameras.npz', 'G03_v005_raw00229', 'B0'))
    out.append(diagnose(T012/'runs/G03_005'/'W3'/'cameras.npz', 'G03_v005_raw00186', 'W3'))
    out.append(diagnose(T012/'runs/G03_005'/'W0'/'cameras.npz', 'G03_v005_raw00186', 'W0'))
    df = pd.concat(out, ignore_index=True)
    df.to_csv(T/'metrics/ANOMALY_TRACK_ERRORS.csv', index=False)
    for (arm, view), g in df.groupby(['arm', 'view']):
        top = g.head(3)
        print(f'== {arm} {view}: n={len(g)} median={g.err.median():.2f} p95={np.percentile(g.err,95):.2f} max={g.err.max():.2f}')
        print(top[['track_id', 'err', 'baseline_mm', 'angle_deg', 'tri_view_a', 'tri_view_b']].to_string(index=False))
