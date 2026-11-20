import sys, unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'code'))
import contour_geometry as CG, joint_residual_blocks as JB


class TestGeometry(unittest.TestCase):
    def setUp(self):
        t = np.linspace(0, 2*np.pi, 200, endpoint=False)
        self.poly = np.c_[60*np.cos(t), 45*np.sin(t)]

    def test_fixed_length(self):
        for m in (128, 256, 512):
            self.assertEqual(len(CG.resample_closed(self.poly, m)), m)

    def test_no_cache_pollution(self):
        """Repeated evaluations and object churn must not change distances."""
        pts = np.c_[10*np.ones(5), np.linspace(-5, 5, 5)]
        ref = CG.dist_to_polyline(pts, self.poly).copy()
        for _ in range(50):
            tmp = np.c_[60*np.cos(np.linspace(0, 6, 100)), 45*np.sin(np.linspace(0, 6, 100))]
            CG.dist_to_polyline(pts, tmp)
            np.testing.assert_allclose(CG.dist_to_polyline(pts, self.poly), ref, atol=1e-12)

    def test_arc_length_uniform(self):
        r = CG.resample_closed(self.poly, 64)
        d = np.linalg.norm(np.diff(np.r_[r, r[:1]], axis=0), axis=1)
        self.assertLess(d.std()/d.mean(), 0.02)

    def test_distance_matches_bruteforce(self):
        pts = np.c_[self.poly[10]+[0.5, 0.0], self.poly[100]+[0.0, 1.0]]
        d = CG.dist_to_polyline(pts, self.poly)
        brute = np.linalg.norm(pts[:, None, :] - self.poly[None, :, :], axis=2).min(1)
        # exact segment distance must never exceed nearest-vertex distance
        self.assertTrue(np.all(d <= brute + 1e-9))
        self.assertTrue(np.all(d >= 0))

    def test_degenerate_not_zero(self):
        import numpy as np
        M = np.eye(4); M[:3, 3] = [0, 0, 45]
        K = np.array([[490.,0,319.5],[0,490.,179.5],[0,0,1]])
        ob = dict(q_train=np.zeros((8, 2)), inner=None, outer=None)
        r, _ = JB.ring_residual('A1', lambda C, o, p, K0: np.zeros(8), M, ob, K)
        self.assertGreater(float(np.abs(r).max()), 1.0)   # explicit penalty, not zero


if __name__ == '__main__':
    unittest.main()
