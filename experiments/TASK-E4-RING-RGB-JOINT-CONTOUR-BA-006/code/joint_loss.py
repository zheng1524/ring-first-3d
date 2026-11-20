"""Flexible Ring contour residual (A1) composed with the frozen BA residual blocks.

Residual vector = [ring_block(2,) , frozen_tail(...)] where the frozen tail is the
material/background + RGB-side residual produced by the frozen implementation.
Normalisation makes the Ring block independent of the number of samples.
"""
import numpy as np
from scipy.optimize import least_squares
import cad_contour_correspondence as CC
import ring_contour_observation as RO

TAU = 1.0        # px, pre-registered tolerance
SIGMA = 1.0      # px
HUBER = 2.0
W_INVISIBLE = 0.25
M_SAMPLES = 256


def huber(r, d=HUBER):
    a = np.abs(r)
    return np.where(a <= d, 0.5*r*r, d*(a-0.5*d))


def ring_block(pose, K, obs, tau=TAU, sigma=SIGMA, m=M_SAMPLES, weights=(0.5, 0.5)):
    from ring_first_3d.mainline.native.camera import torus_contours
    ci, co = CC.split(torus_contours(np.asarray(pose), np.asarray(K)))
    vals = []
    for curve, poly, vis, wk in ((ci, obs['inner'], obs['inner_vis'], weights[0]),
                                 (co, obs['outer'], obs['outer_vis'], weights[1])):
        if curve is None:
            vals.append(0.0); continue
        pts = CC.sampled(curve, m)
        d = CC.dist_to_polyline(pts, poly)
        res = np.maximum(0.0, d - tau) / sigma
        w = np.where(vis[:len(res)], 1.0, W_INVISIBLE)
        vals.append(wk * float(np.sum(w*huber(res))/max(w.sum(), 1e-9)))
    return np.array(vals)


def compose(pose, K, obs, base_tail, tau=TAU):
    """A1 residual: normalized 2-value Ring block + the frozen material/RGB tail."""
    return np.r_[ring_block(pose, K, obs, tau=tau), np.asarray(base_tail, float)]
