import sys, unittest
from pathlib import Path
import numpy as np
from scipy.linalg import expm
R = Path(__file__).resolve().parents[1]
sys.path.insert(0, '/home/liu/ring_first_3d_workspace/camera_mainline/code')
import se3, shared_se3 as S3

K = np.array([[490., 0, 319.5], [0, 490., 179.5], [0, 0, 1.]])
SEED = np.eye(4)


class TestSE3SixDof(unittest.TestCase):
    def test_zero_update_identity(self):
        self.assertTrue(np.allclose(S3.pose_from_q(np.zeros(6), SEED), SEED, atol=1e-12))

    def test_translation_only(self):
        H = S3.pose_from_q(np.array([0.1, 0., 0., 0., 0., 0.]), SEED)
        self.assertTrue(np.allclose(H[:3, :3], np.eye(3), atol=1e-12))
        np.testing.assert_allclose(H[:3, 3], [0.06, 0., 0.], atol=1e-12)

    def test_rotation_only(self):
        H = S3.pose_from_q(np.array([0., 0., 0., 0.1, 0., 0.]), SEED)
        np.testing.assert_allclose(H[:3, 3], [0., 0., 0.], atol=1e-12)
        self.assertGreater(np.linalg.norm(H[:3, :3] - np.eye(3)), 1e-3)

    def test_all_six_parameters_active(self):
        base = S3.pose_from_q(np.zeros(6), SEED)
        for k in range(6):
            q = np.zeros(6); q[k] = 0.1
            self.assertGreater(np.linalg.norm(S3.pose_from_q(q, SEED) - base), 1e-9, f'param {k} inert')

    def test_translation_rotation_independent(self):
        a = S3.pose_from_q(np.array([0.1, 0., 0., 0., 0., 0.]), SEED)
        b = S3.pose_from_q(np.array([0., 0., 0., 0.1, 0., 0.]), SEED)
        self.assertGreater(np.linalg.norm(a[:3, 3] - b[:3, 3]), 1e-6)
        self.assertGreater(np.linalg.norm(a[:3, :3] - b[:3, :3]), 1e-6)

    def test_se3_against_scipy_expm(self):
        rng = np.random.default_rng(0)
        for _ in range(20):
            xi = rng.normal(0, 0.3, 6)
            self.assertTrue(np.allclose(se3.exp_se3(xi), expm(se3.hat(xi)), atol=1e-12))

    def test_se3_inverse(self):
        rng = np.random.default_rng(1)
        for _ in range(10):
            H = se3.exp_se3(rng.normal(0, 0.2, 6))
            self.assertTrue(np.allclose(H @ np.linalg.inv(H), np.eye(4), atol=1e-12))
            self.assertAlmostEqual(float(np.linalg.det(H[:3, :3])), 1.0, places=12)
        # pure translation/rotation: exp(-xi) is the exact inverse
        for xi in (np.array([0.3, -0.2, 0.1, 0., 0., 0.]), np.array([0., 0., 0., 0.2, -0.1, 0.05])):
            self.assertTrue(np.allclose(se3.exp_se3(xi) @ se3.exp_se3(-xi), np.eye(4), atol=1e-12))

    def test_se3_composition(self):
        a = se3.exp_se3(np.array([0.1, 0., 0., 0., 0., 0.]))
        b = se3.exp_se3(np.array([0., 0.2, 0., 0., 0., 0.]))
        self.assertTrue(np.allclose(a @ b, se3.exp_se3(np.array([0.1, 0.2, 0., 0., 0., 0.])), atol=1e-12))
        r1 = se3.exp_se3(np.array([0., 0., 0., 0.05, 0., 0.]))
        r2 = se3.exp_se3(np.array([0., 0., 0., 0.07, 0., 0.]))
        self.assertTrue(np.allclose(r1 @ r2, se3.exp_se3(np.array([0., 0., 0., 0.12, 0., 0.])), atol=1e-12))

    def test_against_pytorch3d_if_available(self):
        try:
            import torch
            from pytorch3d.transforms import se3_exp_map
        except Exception:
            self.skipTest('pytorch3d not importable')
        rng = np.random.default_rng(2)
        for _ in range(5):
            xi = rng.normal(0, 0.2, 6)
            # verified convention: pytorch3d takes (v, omega) and returns the row-vector transpose
            p3d = se3_exp_map(torch.tensor([xi], dtype=torch.float64))[0].numpy().T
            self.assertTrue(np.allclose(se3.exp_se3(xi), p3d, atol=1e-5))

    def test_camera_projection_and_depth(self):
        C = np.eye(4); C[:3, 3] = [0, 0, 40.]
        C[:3, :3] = np.diag([1., -1., -1.])          # camera +z points at the Ring origin
        X = np.array([[0., 0., 0.], [5., 5., 0.]])
        q = (X - C[:3, 3]) @ C[:3, :3]
        uv = q @ K.T; uv = uv[:, :2] / uv[:, 2:]
        self.assertTrue((q[:, 2] > 0).all())
        np.testing.assert_allclose(uv[0], [319.5, 179.5], atol=1e-9)


class TestSampson(unittest.TestCase):
    def _F(self):
        C1 = np.eye(4); C2 = np.eye(4); C2[:3, 3] = [30., 0., 0.]
        T = np.linalg.inv(C2) @ C1
        R, t = T[:3, :3], T[:3, 3]
        tx = np.array([[0, -t[2], t[1]], [t[2], 0, -t[0]], [-t[1], t[0], 0]])
        F = np.linalg.inv(K).T @ (tx @ R) @ np.linalg.inv(K)
        return F / np.linalg.norm(F)

    def test_zero_at_true_correspondence(self):
        rng = np.random.default_rng(3)
        C1 = np.eye(4); C2 = np.eye(4); C2[:3, 3] = [30., 0., 0.]
        X = np.c_[rng.uniform(-3, 3, 6), rng.uniform(-3, 3, 6), rng.uniform(35, 45, 6)]
        def proj(C):
            q = (X - C[:3, 3]) @ C[:3, :3]; p = q @ K.T; return p[:, :2] / p[:, 2:]
        F = self._F()
        u1, u2 = proj(C1), proj(C2)
        a = np.c_[u1, np.ones(len(u1))]; b = np.c_[u2, np.ones(len(u2))]
        Fa = (F @ a.T).T; Ftb = (F.T @ b.T).T
        d = np.abs(np.einsum('ij,ij->i', b, Fa)) / np.sqrt(Fa[:, 0]**2 + Fa[:, 1]**2 + Ftb[:, 0]**2 + Ftb[:, 1]**2)
        self.assertLess(float(np.max(d)), 1e-6)

    def test_standard_formula_matches_point_to_line(self):
        """Our denominator must equal sqrt(|Fx1|^2 + |F^T x2|^2), not the sum of two norms."""
        F = self._F()
        u1 = np.array([[100., 120.]]); u2 = np.array([[300., 90.]])
        a = np.c_[u1, np.ones(1)]; b = np.c_[u2, np.ones(1)]
        Fa = (F @ a.T).T; Ftb = (F.T @ b.T).T
        num = np.abs(np.einsum('ij,ij->i', b, Fa))
        d_std = num / np.sqrt(Fa[:, 0]**2 + Fa[:, 1]**2 + Ftb[:, 0]**2 + Ftb[:, 1]**2)
        d_old = num / (np.hypot(Fa[:, 0], Fa[:, 1]) + np.hypot(Ftb[:, 0], Ftb[:, 1]))
        self.assertGreater(abs(float(d_std[0] - d_old[0])), 1e-6)

    def test_shared_se3_uses_standard_sampson(self):
        rng = np.random.default_rng(4)
        F = self._F()
        u1 = rng.uniform(0, 640, (5, 2)); u2 = rng.uniform(0, 360, (5, 2))
        C1 = np.eye(4); C2 = np.eye(4); C2[:3, 3] = [30., 0., 0.]
        d = S3.sampson_px(u1, u2, np.eye(4), C1, C2, K)
        a = np.c_[u1, np.ones(5)]; b = np.c_[u2, np.ones(5)]
        Fa = (F @ a.T).T; Ftb = (F.T @ b.T).T
        ref = np.abs(np.einsum('ij,ij->i', b, Fa)) / np.sqrt(Fa[:, 0]**2 + Fa[:, 1]**2 + Ftb[:, 0]**2 + Ftb[:, 1]**2)
        self.assertTrue(np.allclose(d, ref, atol=1e-6))


if __name__ == '__main__':
    unittest.main(verbosity=2)
