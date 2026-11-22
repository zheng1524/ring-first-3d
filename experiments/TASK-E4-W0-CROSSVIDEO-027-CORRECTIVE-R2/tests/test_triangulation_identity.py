"""P0 tri identity tests T1-T5 (stable feature ids, never re-derived from track order)."""
import sys, unittest
from pathlib import Path
import numpy as np
WS = Path('/home/liu/ring_first_3d_workspace')
R = WS/'experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R2'
sys.path.insert(0, str(R/'core'))
import r2_synth as S


class TestTriangulationIdentity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sc = S.build_scene(seed=0, nlm=12)
        cls.obs = S.rgb_observations(cls.sc)
        cls.gt = {c: ('x', cls.sc['C_gt'][c]) for c in cls.sc['cams']}

    def test_T1_T3_noiseless_gt_cameras(self):
        X, ids = S.triangulate(self.obs, self.gt, self.sc['K_of'], 12)
        self.assertEqual(len(X), 12)
        self.assertTrue(np.array_equal(ids, np.arange(12)))
        err = np.linalg.norm(X - self.sc['X'], axis=1)
        self.assertLess(err.max(), 1e-6, f'max {err.max()}')

    def test_T2_no_landmark_swapping(self):
        X, ids = S.triangulate(self.obs, self.gt, self.sc['K_of'], 12)
        D_gt = np.linalg.norm(self.sc['X'][:, None, :] - self.sc['X'][None], axis=2)
        D_tr = np.linalg.norm(X[:, None, :] - X[None], axis=2)
        self.assertLess(np.abs(D_gt-D_tr).max(), 1e-6)

    def test_T4_shuffled_feature_order_with_updated_mapping(self):
        rng = np.random.default_rng(3); perm = rng.permutation(12)
        obs2 = [(c, int(perm[i]), uv) for c, i, uv in self.obs]
        X1, ids1 = S.triangulate(self.obs, self.gt, self.sc['K_of'], 12)
        X2, ids2 = S.triangulate(obs2, self.gt, self.sc['K_of'], 12)
        m2 = {int(i): k for k, i in enumerate(ids2)}
        for i in range(12):
            # feature id perm[i] now carries landmark i's observations
            self.assertLess(np.linalg.norm(X2[m2[int(perm[i])]]-X1[i]), 1e-9)

    def test_T5_missing_observations_do_not_shift_others(self):
        obs2 = [o for o in self.obs if not (o[0] == S.C4[0] and o[1] in (0, 1, 2))]
        X1, _ = S.triangulate(self.obs, self.gt, self.sc['K_of'], 12)
        X2, ids2 = S.triangulate(obs2, self.gt, self.sc['K_of'], 12)
        pos = {int(i): k for k, i in enumerate(ids2)}
        for i in range(3, 12):
            self.assertLess(np.linalg.norm(X2[pos[i]]-X1[i]), 1e-6)


if __name__ == '__main__':
    unittest.main(verbosity=2)
