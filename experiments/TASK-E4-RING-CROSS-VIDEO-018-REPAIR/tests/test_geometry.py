import sys, unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'code'))
import geometry as G, yaw_solver as YS
K = np.array([[490., 0, 319.5], [0, 490., 179.5], [0, 0, 1.]])


class TestCameraValidity(unittest.TestCase):
    def test_camera_rotation_validity(self):
        rng = np.random.default_rng(0)
        for _ in range(20):
            C = G.look_at(rng.uniform(-60, 60, 3))
            ok, why = G.check_so3(C[:3, :3])
            self.assertTrue(ok, why)

    def test_camera_positive_depth(self):
        C = G.look_at([30, 0, 40]); X = np.array([[0., 0, 0], [5, 2, 3], [-4, 1, 2]])
        _, z = G.project(X, C, K)
        self.assertTrue((z > 0).all(), z)

    def test_world_to_camera_conversion(self):
        C = G.look_at([30, 0, 40]); X = np.array([[0., 0, 0]])
        q = (X - C[:3, 3]) @ C[:3, :3]
        uv, z = G.project(X, C, K)
        self.assertAlmostEqual(float(z[0]), float(q[0, 2]), places=9)
        self.assertTrue(np.allclose(uv[0], (q[0, :2] / q[0, 2]) @ K[:2, :2].T + K[:2, 2]))

    def test_mirrored_camera_rejection(self):
        C = G.look_at([30, 0, 40]); C[:3, :3] = C[:3, :3] @ np.diag([1., 1., -1.])
        ok, why = G.check_so3(C[:3, :3])
        self.assertFalse(ok); self.assertIn('DET', why)

    def test_F_uses_K(self):
        Ca, Cb = G.look_at([30, 0, 40]), G.look_at([-20, 5, 42])
        E, _ = G.essential(Ca, Cb); F, _ = G.fundamental(Ca, Cb, K, K)
        R = np.linalg.inv(K).T @ E @ np.linalg.inv(K)
        self.assertTrue(np.allclose(F, R / np.linalg.norm(R), atol=1e-9))

    def test_zero_sampson_at_true_pose(self):
        X = np.array([[5., 2, 3], [-3, 4, 1], [1, -5, 2], [6, 0, -2], [0, 3, 4], [2, 2, 5]])
        Ca, Cb = G.look_at([30, 0, 40]), G.look_at([-20, 5, 42])
        ua, _ = G.project(X, Ca, K); ub, _ = G.project(X, Cb, K)
        F, _ = G.fundamental(Ca, Cb, K, K)
        self.assertLess(float(np.max(G.sampson(ua, ub, F))), 1e-6)


class TestAmbiguity(unittest.TestCase):
    def _curve(self, f, grid):
        return np.array([f(t) for t in grid])

    def test_single_minimum_not_ambiguous(self):
        g = np.arange(-180, 180, 0.1)
        c = 1 - np.exp(-((YS.wrap180(g - 17.0)) ** 2) / 50.0)
        cl = YS.find_minima(g, c)
        self.assertEqual(len(cl), 1)

    def test_two_separated_minima(self):
        g = np.arange(-180, 180, 0.1)
        c = 1 - np.maximum(np.exp(-((YS.wrap180(g - 17.0)) ** 2) / 50.0),
                           np.exp(-((YS.wrap180(g + 60.0)) ** 2) / 50.0))
        self.assertEqual(len(YS.find_minima(g, c)), 2)

    def test_periodic_boundary(self):
        g = np.arange(-180, 180, 0.1)
        c = 1 - np.exp(-((YS.wrap180(g - 179.5)) ** 2) / 20.0)
        self.assertEqual(len(YS.find_minima(g, c)), 1)

    def test_flat_loss_curve(self):
        g = np.arange(-180, 180, 0.1)
        cl = YS.find_minima(g, np.zeros_like(g))
        self.assertLessEqual(len(cl), 2)

    def test_loss_bounds(self):
        d = np.array([0.0, 1.0, 5.0, 100.0])
        L, sat = G.robust_loss(d, clip=5.0, eps=1.0)
        self.assertLessEqual(L, 5.0)
        self.assertAlmostEqual(sat, 0.25)


if __name__ == '__main__':
    unittest.main(verbosity=2)
