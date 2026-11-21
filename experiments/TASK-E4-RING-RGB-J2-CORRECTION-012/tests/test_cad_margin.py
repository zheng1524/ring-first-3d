import sys, unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'code'))
import j2_obs_correct as J


def pose(x, y, z):
    M = np.eye(4); M[:3, 3] = [x, y, z]; return M


class TestMargin(unittest.TestCase):
    def test_analytic_matches_dense(self):
        rng = np.random.default_rng(0)
        for _ in range(60):
            p = pose(rng.uniform(-9, 9), rng.uniform(-9, 9), rng.uniform(-9, 9))
            a, n = J.cad_margin_analytic(p), J.cad_margin_numeric(p)
            self.assertLess(abs(a-n), 1e-3, f'{a} vs {n} at {p[:3,3]}')
    def test_regimes(self):
        self.assertGreater(J.cad_margin_analytic(pose(0, 0, 0)), 0)       # at centre: silhouette exists
        self.assertLess(J.cad_margin_analytic(pose(5.6, 0, 0.1)), 0)      # near the tube: invalid
        self.assertGreater(J.cad_margin_analytic(pose(0, 0, 45)), 0)      # far: valid
        for d in (2.0, 5.6, 9.0):
            for z in (0.0, 0.5, 3.0):
                p = pose(d, 0, z)
                self.assertLess(abs(J.cad_margin_analytic(p)-J.cad_margin_numeric(p)), 1e-3)
    def test_barrier_gradient_direction(self):
        # moving the camera away from the ring must reduce the barrier
        p_near = pose(5.6, 0, 0.2); p_far = pose(5.6, 0, 3.0)
        b_near = float(np.sum(J.barrier_block(p_near)**2))
        b_far = float(np.sum(J.barrier_block(p_far)**2))
        self.assertGreater(b_near, b_far)
        self.assertGreater(b_near, 0.0); self.assertEqual(b_far, 0.0)
    def test_invalid_fallback_has_gradient(self):
        a = J._penalty_from_margin(pose(5.6, 0, 0.1))
        b = J._penalty_from_margin(pose(5.6, 0, 0.4))
        self.assertNotAlmostEqual(a, b, places=3)

if __name__ == '__main__':
    unittest.main()
