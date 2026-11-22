"""P0 tests: resume==uninterrupted, forced-reject rollback, gradient consistency, epipolar with different K."""
import sys, unittest
from pathlib import Path
import numpy as np
C = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(C/'core')); sys.path.insert(0, '/home/liu/ring_first_3d_workspace/src')
import controlled_gt as CG
import optimize as O
from geometry import project, fundamental, sampson, line_dist
from se3 import exp_se3

K = np.array([[490., 0, 319.5], [0, 490., 179.5], [0, 0, 1.]])
K2 = np.array([[560., 0, 300.0], [0, 560., 170.0], [0, 0, 1.]])


def loss_loop(q, obs, H_seed=np.eye(4)):
    H = exp_se3(q*O.SCALE) @ H_seed
    tot, n = 0.0, 0
    for o in obs:
        for X, u, Cc, use_H in ((o['X'], o['u4'], o['C4'], False), (o['X'], o['u5'], o['C5'], True)):
            Xc = (H[:3, :3] @ X.T).T + H[:3, 3] if use_H else X
            qv = (Xc - Cc[:3, 3]) @ Cc[:3, :3]
            p = qv @ K.T
            m = p[:, 2] > 0
            uv = p[m, :2]/p[m, 2:3]
            e = np.linalg.norm(uv - u[m], axis=1)/3.0
            tot += float(np.sum(np.where(e < 1, 0.5*e*e, e-0.5))); n += int(m.sum())
    return tot/max(n, 1)


class TestResume(unittest.TestCase):
    def test_resume_equals_uninterrupted(self):
        H_true = CG.H_of(6.0, (0.5, 0.2, -0.1)); obs = CG.observations(H_true, seed=3)
        f = lambda q: CG.loss_bidir(q, obs)
        st = O.empty_state(); st['best'] = f(st['q'])
        for _ in range(40):
            st = O.step_once(f, st)
        q_full = st['q'].copy()
        st2 = O.empty_state(); st2['best'] = f(st2['q'])
        for _ in range(20):
            st2 = O.step_once(f, st2)
        O.state_to_npz('/tmp/ck024.npz', st2)
        st3 = O.state_from_npz('/tmp/ck024.npz')
        for _ in range(20):
            st3 = O.step_once(f, st3)
        np.testing.assert_array_equal(q_full, st3['q'])
        self.assertEqual(st['step'], st3['step'])

    def test_forced_rejection_rolls_back(self):
        H_true = CG.H_of(6.0, (0.5, 0.2, -0.1)); obs = CG.observations(H_true, seed=3)
        f = lambda q: CG.loss_bidir(q, obs)
        st = O.empty_state(); st['best'] = f(st['q'])
        for _ in range(5):
            st = O.step_once(f, st)
        q0, m0, v0, b0 = st['q'].copy(), st['m'].copy(), st['v'].copy(), st['best']
        st = O.step_once(f, st, allowed=False)
        np.testing.assert_array_equal(st['q'], q0)
        np.testing.assert_array_equal(st['m'], m0)
        np.testing.assert_array_equal(st['v'], v0)
        self.assertEqual(st['best'], b0)
        self.assertEqual(st['reject_reason'], 'NONFINITE_OR_FORCED')


class TestGradient(unittest.TestCase):
    def test_fd_of_formal_loss_matches_independent_implementation(self):
        obs = CG.observations(CG.H_of(6.0, (0.5, 0.2, -0.1)), seed=3)
        q = np.array([0.03, -0.02, 0.01, 0.02, -0.01, 0.03])
        g1, g2 = np.zeros(6), np.zeros(6)
        h = 1e-5
        for k in range(6):
            qp = q.copy(); qp[k] += h; qm = q.copy(); qm[k] -= h
            g1[k] = (CG.loss_bidir(qp, obs)-CG.loss_bidir(qm, obs))/(2*h)
            g2[k] = (loss_loop(qp, obs)-loss_loop(qm, obs))/(2*h)
        self.assertLess(float(np.abs(g1-g2).max()), 1e-9, f'{g1} vs {g2}')
        # the loss value itself must agree
        self.assertAlmostEqual(CG.loss_bidir(q, obs), loss_loop(q, obs), places=10)


class TestEpipolarDifferentK(unittest.TestCase):
    def test_direction_and_distances(self):
        C4 = CG.look_at([20., 0., 40.]); C5 = CG.look_at([-20., 4., 41.])
        F, base = fundamental(C4, C5, K, K2)
        self.assertGreater(base, 1.0)
        rng = np.random.default_rng(0)
        X = np.c_[rng.uniform(-4, 4, 30), rng.uniform(-4, 4, 30), rng.uniform(-3, 3, 30)]
        u4, _ = project(X, C4, K); u5, _ = project(X, C5, K2)
        # true correspondences: Sampson ~ 0
        self.assertLess(float(np.max(sampson(u4, u5, F))), 1e-9)
        # a shifted point must produce a line at that distance on the 005 image
        u5s = u5 + np.array([5.0, 0.0])
        d5 = np.array([line_dist(F @ np.r_[a, 1.], b) for a, b in zip(u4, u5s)])
        s = sampson(u4, u5s, F)
        self.assertTrue(np.all(s <= d5 + 1e-9))
        self.assertGreater(float(np.median(d5)), 0.1)
        # F^T x5 must be the line on the 004 image (asymmetric test: K differ)
        d4 = np.array([line_dist(F.T @ np.r_[b, 1.], a) for a, b in zip(u4, u5s)])
        self.assertGreater(float(np.median(d4)), 0.1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
