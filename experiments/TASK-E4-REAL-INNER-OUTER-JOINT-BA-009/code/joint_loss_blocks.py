"""Separate Inner / Outer contour blocks (C1/C2/C3) for the inner-outer ablation."""
import numpy as np
import contour_geometry as CG

TAU = {"C1": 0.0, "C2": 0.0, "C3": 0.0, "A2": 1.0}
SIGMA = 1.0
M = 256


def contour_block(pose, K, ob, which='both', tau=0.0, sigma=SIGMA, m=M):
    """Return (residual_vector, status). `which` selects the DXY curve(s) used."""
    from ring_first_3d.mainline.native.camera import torus_contours
    ci, co = CG.split_by_area(torus_contours(np.asarray(pose), np.asarray(K)))
    parts, status = [], []
    spec = [('inner', ci, ob.get('inner'), ob.get('inner_vis'))] if which == 'inner' else \
           [('outer', co, ob.get('outer'), ob.get('outer_vis'))] if which == 'outer' else \
           [('inner', ci, ob.get('inner'), ob.get('inner_vis')),
            ('outer', co, ob.get('outer'), ob.get('outer_vis'))]
    for name, curve, poly, vis in spec:
        if curve is None or poly is None or len(np.asarray(poly)) == 0:
            parts.append(np.full(m, 10.0)); status.append(name + ':MISSING'); continue
        pts = CG.resample_closed(curve, m)
        d = CG.dist_to_polyline(pts, poly)
        w = np.ones(m) if vis is None else np.where(np.asarray(vis, bool)[:m], 1.0, 0.0)
        if w.sum() < 8:                       # no trustworthy evidence -> explicit UNOBSERVED
            parts.append(np.full(m, 10.0)); status.append(name + ':UNOBSERVED'); continue
        w = w / w.sum()
        parts.append(np.maximum(0.0, d - tau) / sigma * np.sqrt(w))
        status.append(name + ':ok(vis=%d)' % int((np.asarray(vis, bool)[:m]).sum() if vis is not None else m))
    return np.concatenate(parts), status


def ring_residual(arm, base, pose, ob, K):
    """B0 = frozen boundary; C1/C2/C3/A2 = DXY contour blocks + frozen material/background."""
    b = np.asarray(base(pose, ob, 'train', K), float)
    if arm == 'B0':
        return b, dict(mode='B0', n=len(b))
    which = {'C1': 'inner', 'C2': 'outer', 'C3': 'both', 'A2': 'both'}[arm]
    tau = TAU.get(arm, 0.0)
    cb, st = contour_block(pose, K, ob, which=which, tau=tau)
    nq = len(ob['q_train'])
    return np.r_[cb, b[nq:]], dict(mode=arm, contour_n=len(cb), tail_n=len(b) - nq, tau=tau, status=st)
