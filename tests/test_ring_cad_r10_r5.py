import sys
import unittest
from pathlib import Path
import numpy as np

WS = Path('/home/liu/ring_first_3d_workspace')
sys.path.insert(0, str(WS / 'src'))
from ring_first_3d.mainline.native.camera import torus_contours  # noqa: E402
from ring_first_3d.mainline.native import _kernels  # noqa: E402


def cam():
    C = np.eye(4); C[:3, 3] = [0., 0., 40.]
    K = np.array([[490., 0., 319.5], [0., 490., 179.5], [0., 0., 1.]])
    return C, K


class RingCadR10R5(unittest.TestCase):
    def test_r10_default_is_bitwise_kernel(self):
        C, K = cam()
        a = torus_contours(C, K)
        b = _kernels.torus_contours(C[:3, 3], C[:3, :3], K, R=5.6, r=.6, n=256)
        np.testing.assert_allclose(a, b, rtol=0, atol=0)

    def test_r5_g07_cad_dimensions(self):
        p = (WS / 'assets/retained_sources/ring_first_3d_e4_sdf_localization/experiments/'
             'TASK-E4-PYTORCH3D-RING-AWARE-001/runs/FREE_VERTEX_013/inputs/G07/RING.npz')
        V = np.load(p)['V']
        r = np.linalg.norm(V[:, :2], axis=1)
        self.assertAlmostEqual(float(r.min()), 2.5, places=6)
        self.assertAlmostEqual(float(r.max()), 3.7, places=6)
        self.assertAlmostEqual(5.0 / 2.0 + 0.6, 3.1, places=12)

    def test_r5_actually_changes_projection(self):
        C, K = cam()
        a = torus_contours(C, K, ring_radius=5.6, ring_wire=0.6)
        b = torus_contours(C, K, ring_radius=3.1, ring_wire=0.6)
        self.assertGreater(float(np.abs(a - b).max()), 1.0)
        self.assertTrue(np.isfinite(a).all() and np.isfinite(b).all())


if __name__ == '__main__':
    unittest.main(verbosity=2)
