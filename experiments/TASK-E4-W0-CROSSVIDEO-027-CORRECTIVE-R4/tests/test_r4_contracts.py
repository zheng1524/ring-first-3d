"""R4 Gate A/B/C tests: loss switching, energy identity, ring counts, budget, perturbations, E-group retriangulation."""
import json, sys, unittest
from pathlib import Path
import numpy as np
WS = Path('/home/liu/ring_first_3d_workspace')
R4 = WS/'experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R4'
sys.path.insert(0, str(R4/'core'))
import r4_run as R
import ba_core_r4 as BA


class TestLossSwitch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        R.RUN_CACHE = {}
        sc, obs, ring_obs, rr = R.make_fixed()
        X0, ids = R.baseline_X(sc, obs)
        cv = R.camvar.CameraVariables(sc['cams'], R.S.C4[0], [])
        cams_world = {c: (sc['C_gt'][c] if sc['cams'][c][0] == '004' else sc['C_gt'][c]) for c in sc['cams']}
        cls.P = BA.BAProblemR4(sc['cams'], sc['K_of'], obs, ring_obs, X0, cv, R.geom_from(cams_world, rr))
        cls.H = sc['H']; cls.dx = {c: np.zeros(6) for c in sc['cams']}   # H_gt makes 004 cameras = GT
        cls.X = X0.copy()

    def test_joint_path_honours_rgb_mode(self):
        # a deliberately bad state with large residuals
        Xb = self.X + np.c_[np.zeros((len(self.X), 2)), np.full(len(self.X), 4.0)]
        eh, _ = self.P.energy_table(self.H, self.dx, Xb, 'huber')
        es, _ = self.P.energy_table(self.H, self.dx, Xb, 'squared')
        self.assertGreater(abs(eh['rgb']-es['rgb']), 1e-3, 'huber and squared must differ for large residuals')
        rh, _ = self.P.residual_vector(self.H, self.dx, Xb, 'huber')
        rs, _ = self.P.residual_vector(self.H, self.dx, Xb, 'squared')
        self.assertGreater(abs(0.5*(rh**2).sum()-0.5*(rs**2).sum()), 1e-3)
        # small residuals: both are ~quadratic and agree to 1e-6 relative
        Xs = self.X + 1e-4*np.random.default_rng(0).normal(size=self.X.shape)
        eh2, _ = self.P.energy_table(self.H, self.dx, Xs, 'huber')
        es2, _ = self.P.energy_table(self.H, self.dx, Xs, 'squared')
        self.assertLess(abs(eh2['rgb']-es2['rgb'])/max(es2['rgb'], 1e-30), 1e-6)

    def test_energy_identity(self):
        for mode in ('huber', 'squared', 'dir2d'):
            e, r = self.P.energy_table(self.H, self.dx, self.X, mode)
            self.assertLess(abs(e['total_terms']-e['half_r2']), 1e-9, mode)
            self.assertGreater(e['n_ring_I'], 0); self.assertGreater(e['n_ring_C'], 0); self.assertGreater(e['n_ring_O'], 0)
            self.assertGreater(e['rgb_n'], 0)


class TestPerturbations(unittest.TestCase):
    def test_camera_perturbation_is_recorded_and_relative(self):
        sc, obs, ring_obs, rr = R.make_fixed()
        cams, info = R.perturb_cams(sc, [R.S.C4[1], R.S.C4[2]], 0.5, 0.3, seed=1)
        self.assertEqual(len(info), 2)
        moved = [c for c in cams if not np.allclose(cams[c], np.asarray(sc['cams'][c][1], float))]
        self.assertEqual(sorted(moved), sorted([R.S.C4[1], R.S.C4[2]]))
        self.assertTrue(np.allclose(cams[R.S.C4[0]], np.asarray(sc['cams'][R.S.C4[0]][1], float)))

    def test_e_group_retriangulates_with_perturbed_cameras(self):
        sc, obs, ring_obs, rr = R.make_fixed()
        X0, _ = R.baseline_X(sc, obs)
        cams, _ = R.perturb_cams(sc, R.S.C5, 0.5, 0.0, seed=2, which=('005',))
        obs5 = [o for o in obs if sc['cams'][o[0]][0] == '005']
        Xe, _ = R.S.triangulate(obs5, {c: ('x', cams[c]) for c in R.S.C5}, sc['K_of'], 12)
        self.assertGreater(np.median(np.linalg.norm(Xe-X0, axis=1)), 1e-3, 'E1 retriangulation must differ')
        self.assertGreater(np.median(np.linalg.norm(Xe-sc['X'][:len(Xe)], axis=1)), 1e-4)


if __name__ == '__main__':
    unittest.main(verbosity=2)
