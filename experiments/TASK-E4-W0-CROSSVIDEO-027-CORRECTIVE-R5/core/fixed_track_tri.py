"""Fixed-track triangulation adapter (historical 019 loop, unchanged math).

0027 P0.2 requires experiment A (fixed tracks, identical 2D observations, only cameras change).
features019.landmarks couples track construction + quality gates, so we reuse ITS per-track code
verbatim on a FIXED track list. Equivalence with the historical output is asserted by a test.
"""
import itertools
import numpy as np, cv2
from scipy.optimize import least_squares
import features019 as F19


def project(X, v):
    T = np.asarray(v['T'], float); K = np.asarray(v['K'], float)
    p = (np.asarray(X, float) - T[:3, 3]) @ T[:3, :3]
    q = p @ K.T
    return q[:2]/q[2], q[2]


def triangulate_tracks(tracks, VIEWS):
    """tracks: list of [(view_id, feature_id), ...] (>=3 members, sorted)."""
    out = []
    for tr in tracks:
        vv = [VIEWS[v] for v, _ in tr]
        xy = np.array([F19.features(v)['xy'][j] for v, (_, j) in zip(vv, tr)])
        centers = np.array([np.asarray(v['T'])[:3, 3] for v in vv])
        i, j = max(itertools.combinations(range(len(tr)), 2),
                   key=lambda ij: np.linalg.norm(centers[ij[0]]-centers[ij[1]]))
        a, b = vv[i], vv[j]
        P1 = np.asarray(a['K']) @ np.linalg.inv(np.asarray(a['T']))[:3]
        P2 = np.asarray(b['K']) @ np.linalg.inv(np.asarray(b['T']))[:3]
        H = cv2.triangulatePoints(P1, P2, xy[i:i+1].T, xy[j:j+1].T)
        X = H[:3, 0]/H[3, 0]

        def res(x):
            return np.concatenate([project(x, v)[0]-p for v, p in zip(vv, xy)])
        X = least_squares(res, X, loss='soft_l1', f_scale=1.5, max_nfev=30).x
        err = np.linalg.norm(res(X).reshape(-1, 2), axis=1)
        z = np.array([project(X, v)[1] for v in vv])
        rays = X - centers; rays /= np.linalg.norm(rays, axis=1)[:, None]
        par = np.degrees(np.arccos(np.clip(rays @ rays.T, -1, 1))).max()
        out.append(dict(X=X, reproj=err, parallax=par, z=z))
    return out
