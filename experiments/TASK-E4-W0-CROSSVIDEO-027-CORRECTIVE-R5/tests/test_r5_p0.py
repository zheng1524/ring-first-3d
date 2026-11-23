"""R5 P0 tests: exact perturbation magnitudes, M3b joint params, M4 params/offset, E-group perturbation applied."""
import sys, unittest
from pathlib import Path
import numpy as np
WS = Path('/home/liu/ring_first_3d_workspace')
R5 = WS/'experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R5'
sys.path.insert(0, str(R5/'core'))
import r5_core as C
from se3 import exp_se3


class TestPerturbation(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.F = C.build_fixed(sub=8)

    def test_magnitudes_exact(self):
        for deg, mm in ((0.25, 0.25), (0.5, 0.5)):
            cams, info = C.perturb_cams(self.F['sc'], [C.S.C4[1], C.S.C4[2]], np.deg2rad(deg), mm, seed=1)
            for r in info:
                self.assertAlmostEqual(r['rot_deg'], deg, places=6)
                self.assertAlmostEqual(r['trans_mm'], mm, places=6)

    def test_anchor_and_005_untouched(self):
        cams, info = C.perturb_cams(self.F['sc'], C.S.C4, np.deg2rad(0.5), 0.25, seed=2)
        moved = sorted(r['cam'] for r in info)
        self.assertEqual(moved, sorted([C.S.C4[1], C.S.C4[2]]))
        self.assertTrue(np.allclose(cams[C.S.C4[0]], np.asarray(self.F['sc']['cams'][C.S.C4[0]][1], float)))
        for c in C.S.C5:
            self.assertTrue(np.allclose(cams[c], np.asarray(self.F['sc']['cams'][c][1], float)))


class TestModes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.F = C.build_fixed(sub=8)
        cls.P = C.make_problem(cls.F, {c: np.asarray(cls.F['sc']['cams'][c][1], float) for c in cls.F['sc']['cams']})

    def test_M3b_joint_has_H_and_X(self):
        H0 = exp_se3(np.r_[np.zeros(3), np.deg2rad([0, 0, 3.0])])
        H, X, info = C.solve(self.P, self.F['X0'], 'M3b', H0=H0, budget=40)
        self.assertEqual(info['n_params'], 6 + 3*len(self.F['X0']))
        self.assertGreater(np.linalg.norm(H - H0), 0.0, 'H must move in the joint stage')

    def test_M4_parameter_layout(self):
        P = C.make_problem(self.F, {c: np.asarray(self.F['sc']['cams'][c][1], float) for c in self.F['sc']['cams']},
                           released=[C.S.C4[1], C.S.C4[2]])
        H0 = np.eye(4)
        H, X, info = C.solve(P, self.F['X0'], 'M4', H0=H0, budget=30)
        self.assertEqual(info['n_params'], 6 + 12 + 36)
        self.assertEqual(len(X), len(self.F['X0']))
        self.assertEqual(len(P._last_dx[C.S.C4[1]]), 6)

    def test_E_group_perturbation_changes_geometry(self):
        sc = self.F['sc']
        cams, info = C.perturb_cams(sc, C.S.C5, np.deg2rad(0.5), 0.0, seed=3, which=('005',))
        self.assertGreater(len(info), 0)
        obs5 = [o for o in self.F['obs'] if sc['cams'][o[0]][0] == '005']
        X0 = self.F['X0']
        Xe, ids = C.S.triangulate(obs5, {c: ('x', cams[c]) for c in C.S.C5}, sc['K_of'], 12)
        common = [i for i in ids if i < len(X0)]
        d = np.median([np.linalg.norm(Xe[list(ids).index(i)] - X0[i]) for i in common])
        self.assertGreater(d, 1e-3, 'E1 retriangulation must differ from baseline')


if __name__ == '__main__':
    unittest.main(verbosity=2)
