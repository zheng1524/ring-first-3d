import sys, unittest
from pathlib import Path
import numpy as np
R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R/'code'))
import shared_se3 as S3

K = np.array([[490., 0, 319.5], [0, 490., 179.5], [0, 0, 1.]])


class TestSharedSE3(unittest.TestCase):
    def test_exp_identity(self):
        self.assertTrue(np.allclose(S3.exp_se3(np.zeros(3)), np.eye(4)))

    def test_pose_from_q_zero_is_seed(self):
        seed = np.eye(4); seed[:3, 3] = [1., 2., 3.]
        self.assertTrue(np.allclose(S3.pose_from_q(np.zeros(6), seed), seed))

    def test_pose_valid_so3(self):
        seed = np.eye(4)
        H = S3.pose_from_q(np.array([0.5, -0.2, 0.1, 0.3, -0.1, 0.05]), seed)
        self.assertAlmostEqual(float(np.linalg.det(H[:3, :3])), 1.0, places=9)
        self.assertLess(float(np.abs(H[:3, :3] @ H[:3, :3].T - np.eye(3)).max()), 1e-9)

    def test_sampson_zero_at_true_pose(self):
        rng = np.random.default_rng(0)
        C4 = np.eye(4); C5 = np.eye(4); C5[:3, 3] = [30., 0., 0.]
        X = np.c_[rng.uniform(-5, 5, 8), rng.uniform(-5, 5, 8), rng.uniform(20, 30, 8)]
        u4, _ = S3_geom_project(X, C4); u5, _ = S3_geom_project(X, C5)
        d = S3.sampson_px(u4, u5, np.eye(4), C4, C5, K)
        self.assertLess(float(np.max(d)), 1e-6)

    def test_correction_bounds_respected(self):
        seed = np.eye(4)
        ring = {}
        pairs = []
        q, L, hist, acc = S3.optimize(seed, ring, pairs, K, iters=3)
        H = S3.pose_from_q(q, seed)
        self.assertLessEqual(float(np.linalg.norm(H[:3, 3] - seed[:3, 3])), S3.MAX_T_MM + 1e-9)


def S3_geom_project(X, C):
    q = (X - C[:3, 3]) @ C[:3, :3]
    p = q @ K.T
    return p[..., :2] / p[..., 2:], q[..., 2]


if __name__ == '__main__':
    unittest.main(verbosity=2)
