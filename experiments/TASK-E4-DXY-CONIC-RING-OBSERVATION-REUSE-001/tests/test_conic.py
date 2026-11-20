"""Unit/synthetic tests for the conic Ring observation (Step 4).

Run: PYTHONPATH=<ws>/src:<task>/code python -m unittest discover -s tests -v
No frozen artifact is modified.
"""
import unittest
import numpy as np
import cv2
from scipy.spatial.transform import Rotation as Rot

from ring_first_3d.mainline.native.camera import torus_contours
import conic as C

K = np.array([[490., 0, 319.5], [0, 490., 179.5], [0, 0, 1]])


def pose(dist=45.0, tilt_deg=0.0, azimuth_deg=0.0, yaw_deg=0.0):
    R = Rot.from_euler('z', yaw_deg, degrees=True).as_matrix()
    R = R @ Rot.from_euler('x', tilt_deg, degrees=True).as_matrix()
    R = Rot.from_euler('z', azimuth_deg, degrees=True).as_matrix() @ R
    M = np.eye(4); M[:3, :3] = R; M[:3, 3] = [0, 0, dist]
    return M


def ellipse_from_projected_contour(curve):
    e = cv2.fitEllipse(np.asarray(curve, np.float32).reshape(-1, 1, 2))
    (cx, cy), (d1, d2), ang = e
    return dict(cx=float(cx), cy=float(cy), major_radius=float(max(d1, d2) / 2),
                minor_radius=float(min(d1, d2) / 2),
                angle_deg=float(ang + (90 if d1 < d2 else 0)))


def obs_from_pose(M, n=96, occlude=None):
    curves = torus_contours(M, K)
    inner, outer = C.split_curves(curves)
    ei = ellipse_from_projected_contour(inner)
    eo = ellipse_from_projected_contour(outer)
    q = np.asarray(curves[0], float)
    ob = dict(dxy_inner_conic=C.conic_from_ellipse(ei), dxy_inner_weight=1.0,
              dxy_outer_conic=C.conic_from_ellipse(eo), dxy_outer_weight=1.0,
              q_train=q[:n])
    return ob, ei, eo


class TestResidual(unittest.TestCase):
    def test_front_facing_ring_near_zero(self):
        M = pose(dist=45.0)
        ob, _, _ = obs_from_pose(M)
        r = C.conic_residual(M, ob, K, mode='A1')
        self.assertLess(float(np.mean(r)), 1.0, f'front-facing residual too high: {np.mean(r)}')

    def test_tilted_ring_near_zero(self):
        for tilt in (20, 35):
            M = pose(dist=45.0, tilt_deg=tilt)
            ob, _, _ = obs_from_pose(M)
            r = C.conic_residual(M, ob, K, mode='A1')
            self.assertLess(float(np.mean(r)), 2.0, f'tilt {tilt} residual {np.mean(r)}')

    def test_distance_sweep(self):
        for d in (30.0, 45.0, 70.0, 100.0):
            M = pose(dist=d)
            ob, _, _ = obs_from_pose(M)
            r = C.conic_residual(M, ob, K, mode='A1')
            self.assertLess(float(np.mean(r)), 1.5, f'dist {d} residual {np.mean(r)}')

    def test_perturbation_increases_residual(self):
        M = pose(dist=45.0, tilt_deg=20)
        ob, _, _ = obs_from_pose(M)
        good = float(np.mean(C.conic_residual(M, ob, K)))
        Mbad = M.copy(); Mbad[:3, 3] += [4.0, 0, 0]
        bad = float(np.mean(C.conic_residual(Mbad, ob, K)))
        self.assertGreater(bad, good + 1.0, f'perturbation not detected: {good} vs {bad}')

    def test_partial_occlusion(self):
        M = pose(dist=45.0, tilt_deg=15)
        ob, _, _ = obs_from_pose(M)
        # keep only 60% of the inner boundary; the conic is unchanged
        ob['q_train'] = ob['q_train'][: int(0.6 * len(ob['q_train']))]
        r = C.conic_residual(M, ob, K, mode='A1')
        self.assertLess(float(np.mean(r)), 1.5)

    def test_incomplete_inner_boundary_falls_back(self):
        M = pose(dist=45.0)
        ob, _, _ = obs_from_pose(M)
        ob.pop('dxy_inner_conic')
        r = C.conic_residual(M, ob, K, mode='A1')
        self.assertEqual(len(r), 64, 'outer-only residual must still be produced')

    def test_ellipse_fit_error_is_monotone(self):
        M = pose(dist=45.0, tilt_deg=25)
        ob, ei, _ = obs_from_pose(M)
        base = float(np.mean(C.conic_residual(M, ob, K)))
        worse = dict(ei); worse['major_radius'] *= 1.05
        ob2 = dict(ob); ob2['dxy_inner_conic'] = C.conic_from_ellipse(worse)
        self.assertGreater(float(np.mean(C.conic_residual(M, ob2, K))), base)

    def test_quality_weight_bounds(self):
        rec = dict(branch='visible_inner_arc_RANSAC',
                   diagnostics=dict(inner_arc_coverage=1.0, inner_normalized_residual=0.0,
                                    inner_sector_instability=0.0))
        self.assertAlmostEqual(C.quality_weight(rec), 1.0, places=6)
        rec2 = dict(branch='centerline_symmetry_min', diagnostics=dict(
            inner_arc_coverage=0.5, inner_normalized_residual=0.05, inner_sector_instability=0.2))
        w = C.quality_weight(rec2)
        self.assertTrue(0.05 <= w <= 1.0)
        self.assertLess(w, 1.0)

    def test_curve_split_by_area(self):
        M = pose(dist=45.0)
        inner, outer = C.split_curves(torus_contours(M, K))
        ai = abs(cv2.contourArea(np.asarray(inner, np.float32).reshape(-1, 1, 2)))
        ao = abs(cv2.contourArea(np.asarray(outer, np.float32).reshape(-1, 1, 2)))
        self.assertLess(ai, ao)


if __name__ == '__main__':
    unittest.main(verbosity=2)
