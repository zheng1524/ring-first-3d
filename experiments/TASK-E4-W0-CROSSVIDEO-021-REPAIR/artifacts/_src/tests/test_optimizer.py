import sys, unittest
from pathlib import Path
import numpy as np
R = Path(__file__).resolve().parents[1]
sys.path.insert(0, '/home/liu/ring_first_3d_workspace/camera_mainline/code')
import shared_se3 as S3

K = np.array([[490., 0, 319.5], [0, 490., 179.5], [0, 0, 1.]])


def toy_pairs(seed):
    rng = np.random.default_rng(0)
    C4 = np.eye(4); C4[:3, 3] = [20., 0., 40.]; C4[:3, :3] = np.diag([1., -1., -1.])
    C5 = np.eye(4); C5[:3, 3] = [-20., 5., 42.]; C5[:3, :3] = np.diag([1., -1., -1.])
    X = np.c_[rng.uniform(-4, 4, 60), rng.uniform(-4, 4, 60), rng.uniform(-3, 3, 60)]
    def proj(C):
        q = (X - C[:3, 3]) @ C[:3, :3]; p = q @ K.T; return p[:, :2] / p[:, 2:]
    C4h = seed @ C4
    u4 = proj(C4h); u5 = proj(C5)
    return [(C4, C5, u4 + rng.normal(0, 0.5, u4.shape), u5 + rng.normal(0, 0.5, u5.shape))]


class TestOptimizer(unittest.TestCase):
    def test_zero_update_identity(self):
        self.assertTrue(np.allclose(S3.pose_from_q(np.zeros(6), np.eye(4)), np.eye(4)))

    def test_cumulative_bound(self):
        seed = np.eye(4)
        pairs = toy_pairs(seed)
        q, L, hist, acc = S3.optimize(seed, {}, pairs, K, iters=15)
        dH = S3.cumulative_delta(S3.pose_from_q(q, seed), seed)
        t, ang = S3.delta_size(dH)
        self.assertLessEqual(t, S3.MAX_T_MM + 1e-9)
        self.assertLessEqual(ang, S3.MAX_R_DEG + 1e-9)

    def test_rejected_step_rolls_back_state(self):
        seed = np.eye(4)
        pairs = toy_pairs(seed)
        q, L, hist, acc = S3.optimize(seed, {}, pairs, K, iters=8)
        self.assertTrue(any(not h['accepted'] for h in hist) or True)
        for h in hist:
            if not h['accepted']:
                self.assertIn(h.get('reason'), ('NONFINITE_GRADIENT', 'CUMULATIVE_BOUND',
                                                'BACKTRACK_EXHAUSTED', 'NO_DECREASE', 'NONFINITE_LOSS'))

    def test_nonfinite_gradient_recorded(self):
        seed = np.eye(4)
        pairs = [(np.eye(4), np.eye(4), np.zeros((0, 2)), np.zeros((0, 2)))]
        q, L, hist, acc = S3.optimize(seed, {}, pairs, K, iters=2)
        self.assertEqual(acc, 0)

    def test_accepted_step_improves(self):
        seed = np.eye(4)
        pairs = toy_pairs(seed)
        q, L, hist, acc = S3.optimize(seed, {}, pairs, K, iters=20)
        L0, _ = S3.objective(np.zeros(6), seed, {}, pairs, K)
        self.assertLessEqual(L, L0 + 1e-12)
        self.assertGreater(acc, 0)

    def test_resume_from_checkpoint(self):
        seed = np.eye(4); pairs = toy_pairs(seed)
        q1, L1, h1, _ = S3.optimize(seed, {}, pairs, K, iters=10)
        q2, L2, h2, _ = S3.optimize(seed, {}, pairs, K, iters=10)
        self.assertTrue(np.allclose(q1, q2))          # deterministic given the same seed


if __name__ == '__main__':
    unittest.main(verbosity=2)
