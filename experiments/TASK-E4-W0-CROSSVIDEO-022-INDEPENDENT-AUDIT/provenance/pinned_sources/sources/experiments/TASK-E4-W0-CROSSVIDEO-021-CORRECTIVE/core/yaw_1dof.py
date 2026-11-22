"""Ring-constrained 1-DoF yaw solver with periodic, cluster-based identifiability.

A 'pair' is a tuple (C_a, C_b, pa, pb, K_a, K_b): c2w poses, pixel correspondences, per-side K.
"""
import numpy as np
from geometry_1dof import rot_about_ring, fundamental, sampson, metrics

MERGE_DEG = 12.0
SEP_DEG = 20.0
RATIO = 1.25


def wrap180(a):
    return ((np.asarray(a, float) + 180.0) % 360.0) - 180.0


def _loss_at(pairs, theta, clip=5.0):
    vals = []
    for (Ca, Cb, pa, pb, Ka, Kb) in pairs:
        if len(pa) < 6:
            continue
        F, base = fundamental(rot_about_ring(Ca, np.deg2rad(theta)), Cb, Ka, Kb)
        if base < 1e-6 or not np.isfinite(F).all() or np.abs(F).max() < 1e-12:
            continue
        vals.append(metrics(sampson(pa, pb, F), clip)['loss'])
    return float(np.mean(vals)) if vals else np.nan


def _curve(pairs, grid, clip=5.0):
    return np.array([_loss_at(pairs, float(t), clip) for t in grid])


def find_minima(grid, curve, merge_deg=MERGE_DEG):
    ok = np.isfinite(curve)
    if ok.sum() < 5:
        return []
    g, c = grid[ok], curve[ok]
    step = abs(float(g[1] - g[0])) if len(g) > 1 else 1.0
    w = max(1, int(round(merge_deg / max(step, 1e-9))))
    if w > 1:                                  # circular moving average removes plateaus/ties
        k = np.ones(w) / w
        c = np.convolve(np.r_[c[-w:], c, c[:w]], k, mode='same')[w:w + len(c)]
    tol = 1e-12 * max(1.0, float(np.nanmax(np.abs(c))))
    idx = [i for i in range(len(c)) if c[i] < c[(i - 1) % len(c)] - tol and c[i] <= c[(i + 1) % len(c)] + tol]
    mins = sorted([(float(c[i]), float(g[i])) for i in idx])
    cl = []
    for loss, ang in mins:
        for k in cl:
            if abs(wrap180(ang - k['angle'])) < merge_deg:
                if loss < k['loss']:
                    k['loss'], k['angle'] = loss, ang
                k['n'] += 1
                break
        else:
            cl.append(dict(loss=loss, angle=ang, n=1))
    return cl


def solve(pairs, coarse=2.0, fine=0.1, clip=5.0):
    pairs = [p for p in pairs if len(p[2]) >= 6]
    if not pairs:
        return dict(theta=None, status='INSUFFICIENT_EVIDENCE', curve=[], fine_curve=[])
    grid = np.arange(-180.0, 180.0, coarse)
    curve = _curve(pairs, grid, clip)
    if not np.isfinite(curve).any():
        return dict(theta=None, status='INSUFFICIENT_EVIDENCE', curve=[], fine_curve=[])
    best = float(grid[int(np.nanargmin(curve))])
    from scipy.optimize import minimize_scalar
    r = minimize_scalar(lambda t: _loss_at(pairs, float(t), clip),
                        bounds=(best - coarse, best + coarse), method='bounded',
                        options=dict(xatol=1e-4))
    theta = float(r.x)
    ff = np.arange(-180.0, 180.0, fine)
    fcurve = _curve(pairs, ff, clip)
    clusters = sorted(find_minima(ff, fcurve), key=lambda k: k['loss'])
    d = np.concatenate([sampson(p[2], p[3], fundamental(rot_about_ring(p[0], np.deg2rad(theta)),
                                                       p[1], p[4], p[5])[0]) for p in pairs])
    m = metrics(d, clip)
    m['theta'] = theta
    m['clusters'] = [(round(k['angle'], 2), round(k['loss'], 4), k['n']) for k in clusters[:5]]
    far = [k for k in clusters[1:] if abs(wrap180(k['angle'] - theta)) > SEP_DEG]
    ok = np.isfinite(fcurve)
    away = np.array([l for a, l in zip(ff[ok], fcurve[ok]) if abs(wrap180(a - theta)) > 30.0])
    rise = float(np.median(away)) if len(away) else 0.0
    spread = float(np.nanmax(fcurve) - np.nanmin(fcurve)) if ok.any() else 0.0
    m['rise_away'] = rise
    m['loss_spread'] = spread
    if m['n'] == 0:
        m['status'] = 'LOW_MATCH_SUPPORT'
    elif m['inlier3'] < 0.25 or m['median_px'] is None:
        m['status'] = 'LOW_MATCH_SUPPORT'
    elif spread < 0.05:
        m['status'] = 'FLAT_OBJECTIVE'
    elif far and far[0]['loss'] < RATIO * max(clusters[0]['loss'], 1e-9) + 0.05:
        m['status'] = 'AMBIGUOUS_MULTIMODAL'
    elif rise < max(4.0 * (clusters[0]['loss'] if clusters else 1e9), 0.20):
        m['status'] = 'FLAT_OBJECTIVE'
    else:
        m['status'] = 'UNIQUE_MINIMUM'
    m['curve'] = list(zip(grid.tolist(), curve.tolist()))
    m['fine_curve'] = list(zip(ff.tolist(), fcurve.tolist()))
    return m
