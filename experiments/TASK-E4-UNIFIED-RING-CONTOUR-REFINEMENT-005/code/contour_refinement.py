"""B2: DXY ellipse -> normal-direction RGB edge search -> smooth periodic curve.

The curve is Gamma(s) = Gamma0(s) + delta(s) n(s), delta represented by a low-order
Fourier series (K harmonics) so the result is closed and smooth but NOT an ellipse.
"""
import numpy as np, cv2


def _resample(poly, n):
    poly = np.asarray(poly, float)
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(poly, axis=0), axis=1))]
    if d[-1] == 0:
        return np.repeat(poly[:1], n, axis=0)
    s = np.linspace(0, d[-1], n, endpoint=False)
    return np.c_[np.interp(s, d, poly[:, 0]), np.interp(s, d, poly[:, 1])]


def normals(curve):
    t = np.roll(curve, -1, axis=0) - np.roll(curve, 1, axis=0)
    t /= np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-9)
    n = np.c_[-t[:, 1], t[:, 0]]
    c = curve.mean(0)
    out = n.copy()
    for i in range(len(curve)):                    # orient outward
        if np.dot(curve[i] - c, n[i]) < 0:
            out[i] = -n[i]
    return out


def fourier_delta(coef, theta, K):
    d = np.zeros_like(theta)
    for k in range(1, K + 1):
        d += coef[2 * (k - 1)] * np.cos(k * theta) + coef[2 * (k - 1) + 1] * np.sin(k * theta)
    return d


def rgb_edge_cost(gray, base, nrm, delta, search, theta, K, scale=80.0):
    """Negative gradient magnitude along the normal, maximised at the true edge."""
    pts = base + nrm * fourier_delta(delta, theta, K)[:, None]
    h, w = gray.shape
    cost = 0.0
    for i, (x, y) in enumerate(pts):
        x0, y0 = int(round(x)), int(round(y))
        if x0 < 2 or y0 < 2 or x0 >= w - 2 or y0 >= h - 2:
            cost += 1.0
            continue
        patch = gray[y0 - 2:y0 + 3, x0 - 2:x0 + 3].astype(np.float32)
        gx = cv2.Sobel(patch, cv2.CV_32F, 1, 0, ksize=3); gy = cv2.Sobel(patch, cv2.CV_32F, 0, 1, ksize=3)
        mag = float(np.hypot(gx, gy).max())
        reward = min(mag / scale, 1.0)
        cost += 1.0 - reward
    return cost


def refine(rgb, ellipse, ring_labels, K=4, n=180, search_px=4.0, lam_smooth=2.0, lam_dev=0.15, lam_width=0.5):
    """Return refined curve and the normal displacement field delta(s)."""
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    base = _resample(np.asarray(_ellipse_poly(ellipse, 360)), n)
    nrm = normals(base)
    theta = np.linspace(0, 2 * np.pi, n, endpoint=False)
    # visibility support: samples whose base point is near real ring pixels
    from scipy.spatial import cKDTree
    ys, xs = np.nonzero(ring_labels == 2)
    vis = np.zeros(n, bool)
    if len(ys):
        d, _ = cKDTree(np.c_[xs, ys].astype(float)).query(base, k=1)
        vis = d <= 3.0
    delta = np.zeros(2 * K)
    try:
        from scipy.optimize import minimize
        def obj(c):
            e_edge = rgb_edge_cost(gray, base, nrm, c, search_px, theta, K)
            d = fourier_delta(c, theta, K)
            e_smooth = float(np.sum(np.diff(d, 2) ** 2))
            e_dev = float(np.sum(d ** 2))
            return e_edge + lam_smooth * e_smooth / n + lam_dev * e_dev / n
        res = minimize(obj, delta, method='Powell', options=dict(maxiter=400, xtol=1e-2, ftol=1e-3))
        delta = res.x
    except Exception:
        pass
    d = fourier_delta(delta, theta, K)
    d = np.where(vis, d, 0.0)          # inferred arcs keep the DXY prior (no strong forcing)
    d = np.clip(d, -search_px, search_px)
    return base + nrm * d[:, None], d, vis


def _ellipse_poly(e, n):
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    c, s = np.cos(np.deg2rad(e['angle_deg'])), np.sin(np.deg2rad(e['angle_deg']))
    x = e['major_radius'] * np.cos(t); y = e['minor_radius'] * np.sin(t)
    return np.c_[c * x - s * y + e['cx'], s * x + c * y + e['cy']]
