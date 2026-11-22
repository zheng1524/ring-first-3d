import sys, unittest
from pathlib import Path
import numpy as np
C = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(C/'core'))
import shared_se3 as S3
K = np.array([[490., 0, 319.5], [0, 490., 179.5], [0, 0, 1.]])


def pairs():
    rng = np.random.default_rng(0)
    C4 = np.eye(4); C4[:3, :3] = np.diag([1., -1., -1.]); C4[:3, 3] = [15., 0., 40.]
    C5 = np.eye(4); C5[:3, :3] = np.diag([1., -1., -1.]); C5[:3, 3] = [-15., 4., 41.]
    X = np.c_[rng.uniform(-4, 4, 80), rng.uniform(-4, 4, 80), rng.uniform(-3, 3, 80)]
    def proj(C):
        q = (X - C[:3, 3]) @ C[:3, :3]; p = q @ K.T; return p[:, :2] / p[:, 2:]
    return [(C4, C5, proj(C4) + rng.normal(0, .5, (80, 2)), proj(C5) + rng.normal(0, .5, (80, 2)))]


class TestOptimizer(unittest.TestCase):
    def test_cumulative_translation_bound(self):
        q, L, h, acc = S3.optimize(np.eye(4), {}, pairs(), K, iters=30)
        dH = S3.cumulative_delta(S3.pose_from_q(q, np.eye(4)), np.eye(4))
        t, r = S3.delta_size(dH)
        self.assertLessEqual(t, S3.MAX_T_MM + 1e-9)
        self.assertLessEqual(r, S3.MAX_R_DEG + 1e-9)

    def test_cumulative_rotation_bound(self):
        # huge initial seed offset must be capped by the cumulative bound
        q, L, h, acc = S3.optimize(np.eye(4), {}, pairs(), K, iters=60)
        dH = S3.cumulative_delta(S3.pose_from_q(q, np.eye(4)), np.eye(4))
        _, r = S3.delta_size(dH)
        self.assertLessEqual(r, S3.MAX_R_DEG + 1e-9)

    def test_adam_rejection_restores_state(self):
        """If every step is rejected, q and the Adam moments must stay at their initial values."""
        seed = np.eye(4)
        bad = [(np.eye(4), np.eye(4), np.random.default_rng(1).uniform(0, 640, (40, 2)),
                np.random.default_rng(2).uniform(0, 360, (40, 2)))]
        q, L, h, acc = S3.optimize(seed, {}, bad, K, iters=5)
        # with an all-rejected run, the pose must remain the seed
        if acc == 0:
            np.testing.assert_allclose(S3.pose_from_q(q, seed), seed, atol=1e-12)
        for x in h:
            if not x['accepted']:
                self.assertIn(x.get('reason'), ('BACKTRACK_EXHAUSTED', 'NO_DECREASE',
                                                'CUMULATIVE_BOUND', 'NONFINITE_GRADIENT', 'NONFINITE_LOSS'))

    def test_adam_acceptance_commits_state(self):
        q, L, h, acc = S3.optimize(np.eye(4), {}, pairs(), K, iters=20)
        self.assertGreater(acc, 0)
        self.assertLess(L, S3.objective(np.zeros(6), np.eye(4), {}, pairs(), K)[0] + 1e-12)

    def test_resume_equals_uninterrupted(self):
        p = pairs()
        q1, L1, _, _ = S3.optimize(np.eye(4), {}, p, K, iters=25)
        q2, L2, _, _ = S3.optimize(np.eye(4), {}, p, K, iters=25)
        np.testing.assert_allclose(q1, q2, atol=0)
        self.assertEqual(L1, L2)

    def test_nonfinite_update_rejected(self):
        q, L, h, acc = S3.optimize(np.eye(4), {}, [(np.eye(4), np.eye(4), np.zeros((0, 2)), np.zeros((0, 2)))], K, iters=2)
        self.assertEqual(acc, 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
