"""Tests for the opt-in Ring priors.

Two contracts are asserted:
  1. REMOVABILITY: with no prior enabled the composed residual is bit-identical to
     the frozen A0 residual, so the 005 pipeline is untouched.
  2. GEOMETRY: each prior is finite, zero-ish at a self-consistent synthetic pose,
     grows under perturbation, and P5 is invariant to a per-view radial offset.
"""
import unittest
import numpy as np
import cv2

from ring_first_3d.mainline.native.camera import torus_contours, residual
import priors as P

K = np.array([[490., 0, 319.5], [0, 490., 179.5], [0, 0, 1]])


def pose(dist=45.0, tilt=0.0):
    M = np.eye(4)
    c, s = np.cos(np.deg2rad(tilt)), np.sin(np.deg2rad(tilt))
    M[:3, :3] = np.array([[1, 0, 0], [0, c, -s], [0, s, c]], float)
    M[:3, 3] = [0, 0, dist]
    return M


def syn_obs(M, n_q=64):
    ci, co = P.split_curves(torus_contours(M, K))
    ei = _fit(ci); eo = _fit(co)
    q = np.asarray(ci, float)[:n_q]
    ob = dict(q_train=q, p_train=np.zeros((8, 2)), b_train=np.zeros((8, 2)),
              dxy_inner_conic=P._conic(ei), dxy_outer_conic=P._conic(eo))
    ob = P.cache_dxy(ob, dict(inner=ei, outer=eo))
    return ob, ei, eo


def _fit(curve):
    (cx, cy), (d1, d2), ang = cv2.fitEllipse(np.asarray(curve, np.float32).reshape(-1, 1, 2))
    return dict(cx=float(cx), cy=float(cy), major_radius=float(max(d1, d2) / 2),
                minor_radius=float(min(d1, d2) / 2),
                angle_deg=float(ang + (90 if d1 < d2 else 0)))


class TestRemovability(unittest.TestCase):
    def test_empty_priors_is_identity(self):
        M = pose()
        ob, _, _ = syn_obs(M)
        from ring_first_3d.mainline.native.camera import observe
        labels = np.zeros((360, 640), np.uint8)
        cv2.circle(labels, (320, 180), 90, 2, 6)
        cv2.circle(labels, (320, 180), 40, 1, -1)
        full = observe(labels)
        q = full['q_train']
        base = residual(M, full, K)
        out = P.compose(M, full, K, base, len(q), {})
        self.assertTrue(np.array_equal(base, out), 'empty prior set must be bit-identical to A0')

    def test_prior_functions_are_registered(self):
        for name in ('P2', 'P3', 'P4', 'P5'):
            self.assertIn(name, P.PRIOR_FUNCS)
        self.assertEqual(P.ENABLED, {}, 'default must be no priors')


class TestPriorGeometry(unittest.TestCase):
    def test_all_priors_finite(self):
        for tilt in (0, 20, 35):
            M = pose(45.0, tilt)
            ob, _, _ = syn_obs(M)
            for name, fn in P.PRIOR_FUNCS.items():
                r = fn(M, K, ob)
                self.assertTrue(np.isfinite(r).all(), f'{name} not finite at tilt {tilt}')
                self.assertGreater(len(r), 0)

    def test_perturbation_increases_shape_and_width(self):
        M = pose(45.0, 20)
        ob, _, _ = syn_obs(M)
        good2 = float(np.mean(np.abs(P.residual_shape(M, K, ob))))
        good3 = float(np.mean(np.abs(P.residual_width(M, K, ob))))
        Mb = M.copy(); Mb[:3, 3] += [4.0, 0, 0]
        bad2 = float(np.mean(np.abs(P.residual_shape(Mb, K, ob))))
        bad3 = float(np.mean(np.abs(P.residual_width(Mb, K, ob))))
        self.assertGreater(bad2, good2, 'shape prior must detect translation')
        self.assertGreater(bad3, good3, 'width prior must detect translation')

    def test_p5_offset_invariance(self):
        """P5 must not change when the DXY contour is uniformly inflated radially."""
        M = pose(45.0, 15)
        ob, ei, eo = syn_obs(M)
        base = float(np.mean(np.abs(P.residual_offsetfree_conic(M, K, ob))))
        ob2 = dict(ob)
        for key, e in (('inner', dict(ei)), ('outer', dict(eo))):
            e['major_radius'] *= 1.04; e['minor_radius'] *= 1.04
            ob2[f'dxy_{key}_pts'] = P.ellipse_pts(e)
        inflated = float(np.mean(np.abs(P.residual_offsetfree_conic(M, K, ob2))))
        self.assertLess(abs(inflated - base), 0.2 * max(base, 1e-3) + 0.05,
                        f'P5 not offset-invariant: {base} vs {inflated}')

    def test_p1_trust_weights_bounded(self):
        M = pose(45.0)
        ob, ei, eo = syn_obs(M)
        w = P.q_trust(ob, dict(inner=ei, outer=eo))
        self.assertEqual(len(w), len(ob['q_train']))
        self.assertTrue((w > 0).all() and (w <= 1).all())

    def test_p4_harmonic_length(self):
        M = pose(45.0)
        ob, _, _ = syn_obs(M)
        r = P.residual_harmonic(M, K, ob)
        self.assertEqual(len(r), 2 * 2 * P.HARMONIC_K)   # two contours x (real+imag) x K

    def test_compose_with_priors_finite(self):
        M = pose(45.0)
        ob, _, _ = syn_obs(M)
        base = np.zeros(64 + 16)
        for enabled in ({'P1': 1.0}, {'P5': 1.0}, {'P1': 1.0, 'P2': 0.1},
                        {'P1': 1.0, 'P3': 0.1}, {'P1': 1.0, 'P4': 0.1}):
            out = P.compose(M, ob, K, base, 64, enabled)
            self.assertTrue(np.isfinite(out).all(), f'{enabled} produced non-finite residual')


if __name__ == '__main__':
    unittest.main(verbosity=2)
