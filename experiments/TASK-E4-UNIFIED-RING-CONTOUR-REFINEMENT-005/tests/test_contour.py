import numpy as np, unittest, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'code'))
import contour_refinement as CR, dxy_adapter as D


class TestContour(unittest.TestCase):
    def test_fourier_delta_zero(self):
        self.assertTrue(np.allclose(CR.fourier_delta(np.zeros(8), np.linspace(0, 6, 50), 4), 0))

    def test_normals_outward(self):
        t = np.linspace(0, 2 * np.pi, 64, endpoint=False)
        c = np.c_[100 + 30 * np.cos(t), 100 + 20 * np.sin(t)]
        n = CR.normals(c)
        dots = [np.dot(n[i], c[i] - c.mean(0)) for i in range(len(c))]
        self.assertGreater(min(dots), 0)

    def test_ellipse_poly_closed(self):
        e = dict(cx=100, cy=50, major_radius=30, minor_radius=20, angle_deg=10)
        p = CR._ellipse_poly(e, 100)
        self.assertEqual(p.shape, (100, 2))
        self.assertLess(np.linalg.norm(p[0] - p[-1]), 3.0)

    def test_conic_sampling(self):
        e = dict(cx=10, cy=20, major_radius=5, minor_radius=3, angle_deg=0)
        self.assertEqual(D.sample(e, 50).shape, (50, 2))
        M = D.conic(e)
        self.assertEqual(M.shape, (3, 3))


if __name__ == '__main__':
    unittest.main()
