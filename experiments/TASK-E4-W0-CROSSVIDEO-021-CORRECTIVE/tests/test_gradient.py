import sys, unittest
from pathlib import Path
import numpy as np
C = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(C/'core'))
import torch
import shared_se3 as S3
import torch_objective as TO
K = np.array([[490., 0, 319.5], [0, 490., 179.5], [0, 0, 1.]])


def make():
    rng = np.random.default_rng(0)
    C4 = np.eye(4); C4[:3, :3] = np.diag([1., -1., -1.]); C4[:3, 3] = [15., 0., 40.]
    C5 = np.eye(4); C5[:3, :3] = np.diag([1., -1., -1.]); C5[:3, 3] = [-15., 4., 41.]
    X = np.c_[rng.uniform(-4, 4, 60), rng.uniform(-4, 4, 60), rng.uniform(-3, 3, 60)]
    def proj(C):
        q = (X - C[:3, 3]) @ C[:3, :3]; p = q @ K.T; return p[:, :2] / p[:, 2:]
    return (C4, C5, proj(C4), proj(C5))


class TestGradient(unittest.TestCase):
    def test_autograd_matches_finite_difference_epi_prior(self):
        C4, C5, u4, u5 = make()
        t = lambda x: torch.tensor(x, dtype=torch.float64)
        pairs = [(t(C4), t(C5), t(u4), t(u5))]
        seed = t(np.eye(4)); Kt = t(K)
        q0 = np.array([0.05, 0.02, -0.01, 0.01, 0.02, -0.01])   # away from the minimum
        q = torch.tensor(q0, dtype=torch.float64, requires_grad=True)
        loss = TO.epi_prior_loss(q, seed, pairs, Kt)
        loss.backward()
        g_auto = q.grad.detach().numpy().copy()
        eps = 1e-7
        g_fd = np.zeros(6)
        for k in range(6):
            qp = q0.copy(); qp[k] += eps
            qm = q0.copy(); qm[k] -= eps
            lp = float(TO.epi_prior_loss(torch.tensor(qp), seed, pairs, Kt))
            lm = float(TO.epi_prior_loss(torch.tensor(qm), seed, pairs, Kt))
            g_fd[k] = (lp - lm) / (2 * eps)
        # relative agreement over all six parameters
        rel = np.abs(g_auto - g_fd) / (np.abs(g_fd) + 1e-9)
        self.assertLess(float(np.max(rel)), 0.05, f'auto={g_auto} fd={g_fd}')
        self.assertGreater(float(np.linalg.norm(g_auto)), 1e-9)

    def test_prior_gradient_only(self):
        t = lambda x: torch.tensor(x, dtype=torch.float64)
        q = torch.zeros(6, dtype=torch.float64, requires_grad=True)
        loss = TO.epi_prior_loss(q, t(np.eye(4)), [], t(K))
        loss.backward()
        np.testing.assert_allclose(q.grad.numpy(), 0.0, atol=1e-12)


if __name__ == '__main__':
    unittest.main(verbosity=2)
