"""Explicit A0 / A1 / A2 ring blocks with separated lambda_C / lambda_P / lambda_B.

The frozen BA multiplies each view's ring residual by sqrt(counts[i]/rglen[i]),
so the total ring influence is ~counts[i] * mean(r^2) whatever rglen is.
We keep that mechanism untouched and only change what the boundary block is.
"""
import numpy as np
import contour_geometry as CG

TAU = 1.0      # px geometric tolerance
SIGMA = 1.0    # px observation noise
W_INVISIBLE = 0.25
M = 256


def contour_block(pose, K, obs, tau=TAU, sigma=SIGMA, m=M, lam_C=1.0):
    """Per-sample normalised residual (optimizer applies the robust loss)."""
    from ring_first_3d.mainline.native.camera import torus_contours
    ci, co = CG.split_by_area(torus_contours(np.asarray(pose), np.asarray(K)))
    blocks, status = [], []
    for curve, poly, vis in ((ci, obs.get('inner'), obs.get('inner_vis')),
                             (co, obs.get('outer'), obs.get('outer_vis'))):
        if curve is None or poly is None or len(np.asarray(poly)) == 0:
            blocks.append(np.full(m, 10.0))      # degenerate => explicit penalty, not zero
            status.append('MISSING_CAD_OR_DXY')
            continue
        pts = CG.resample_closed(curve, m)
        d = CG.dist_to_polyline(pts, poly)
        w = np.where(np.asarray(vis, bool)[:len(d)] if vis is not None else True, 1.0, W_INVISIBLE)
        w = w / max(w.sum(), 1e-9)
        blocks.append(lam_C * np.maximum(0.0, d - tau) / sigma * np.sqrt(w))
        status.append('ok')
    return np.concatenate(blocks), status


def ring_residual(arm, base, pose, ob, K, lam_C=1.0):
    """Return the full ring residual for the requested arm.

    A0 : frozen block (no DXY)                      -> unchanged
    A1 : boundary block replaced by DXY contours    -> same nominal weight, no tau
    A2 : A1 + tau>0 flexible band, lam_C configurable
    """
    b = np.asarray(base(pose, ob, 'train', K), float)
    if arm == 'A0':
        return b, dict(mode='A0', n=len(b))
    nq = len(ob['q_train'])
    tau = 0.0 if arm == 'A1' else TAU
    cb, st = contour_block(pose, K, ob, tau=tau, lam_C=lam_C)
    out = np.r_[cb, b[nq:]]          # material (p) and background (b) blocks untouched
    return out, dict(mode=arm, n=len(out), contour_n=len(cb), tail_n=len(b) - nq,
                     tau=tau, lam_C=lam_C, status=st)
