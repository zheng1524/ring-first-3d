import sys, unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'code'))
import yaw_solver as YS
K = np.array([[490., 0, 319.5], [0, 490., 179.5], [0, 0, 1]])


def cam(x, y, z, yaw=0.0):
    C = np.eye(4); C[:3, 3] = [x, y, z]
    f = -np.array([x, y, z]) / np.linalg.norm([x, y, z])
    xa = np.cross([0, 0, 1.], f); xa /= np.linalg.norm(xa)
    R = np.c_[xa, np.cross(f, xa), -f]
    C[:3, :3] = YS.Rz(yaw) @ R
    return C


def proj(X, C):
    q = (X - C[:3, 3]) @ C[:3, :3]; p = q @ K.T
    return p[..., :2] / p[..., 2:], q[..., 2]


class TestGeometry(unittest.TestCase):
    def test_F_uses_K(self):
        """F must equal K^-T E K^-1; using E directly on pixels is the 017 bug."""
        Ca, Cb = cam(20, 0, 40), cam(-20, 5, 42)
        E, _ = YS.essential(Ca, Cb)
        F, _ = YS.fundamental(Ca, Cb, K, K)
        F_ref = np.linalg.inv(K).T @ E @ np.linalg.inv(K)
        self.assertTrue(np.allclose(F, F_ref / np.linalg.norm(F_ref), atol=1e-9))

    def test_zero_sampson_at_true_pose(self):
        X = np.array([[5., 2, 3], [-3, 4, 1], [1, -5, 2], [6, 0, -2], [0, 3, 4], [2, 2, 5]])
        Ca, Cb = cam(20, 0, 40), cam(-20, 5, 42)
        ua, za = proj(X, Ca); ub, zb = proj(X, Cb)
        F, _ = YS.fundamental(Ca, Cb, K, K)
        d = YS.sampson(ua, ub, F)
        self.assertLess(float(np.max(d)), 1e-6)

    def test_rotation_about_ring_centre(self):
        C = cam(30, 0, 40)
        C2 = YS.rotate_pose(C, np.deg2rad(30))
        self.assertAlmostEqual(float(np.linalg.norm(C[:3, 3])), float(np.linalg.norm(C2[:3, 3])), places=9)
        self.assertAlmostEqual(float(np.degrees(np.arctan2(C2[1, 3], C2[0, 3]) -
                                               np.arctan2(C[1, 3], C[0, 3]))), 30.0, places=6)

    def test_wrong_pose_not_zero(self):
        X = np.array([[5., 2, 3], [-3, 4, 1], [1, -5, 2], [6, 0, -2], [0, 3, 4], [2, 2, 5]])
        Ca, Cb = cam(20, 0, 40), cam(-20, 5, 42)
        ua, za = proj(X, Ca); ub, zb = proj(X, Cb)
        F, _ = YS.fundamental(YS.rotate_pose(Ca, np.deg2rad(40)), Cb, K, K)
        self.assertGreater(float(np.median(YS.sampson(ua, ub, F))), 1.0)


if __name__ == '__main__':
    unittest.main()
