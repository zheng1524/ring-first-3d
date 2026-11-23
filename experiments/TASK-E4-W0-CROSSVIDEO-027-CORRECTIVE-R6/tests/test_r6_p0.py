"""R6 Tests 1-10 (key subset): Ring residual vector, candidate final H, H applied once,
M2/M3b separation, reference-camera awareness, HOLDOUT isolation, M4 local camera, no GT."""
import sys, unittest
from pathlib import Path
import numpy as np
WS = Path('/home/liu/ring_first_3d_workspace')
R6 = WS/'experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R6'
sys.path.insert(0, str(R6/'core'))
import r6_core as C
import ba_core_r4 as BA
from se3 import exp_se3


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.F = C.build_fixed(sub=8)
        cls.sc = cls.F['sc']
        cls.cams = {c: np.asarray(cls.sc['cams'][c][1], float) for c in cls.sc['cams']}
        cls.geom0 = C.geom_from(cls.F, np.eye(4), cls.cams)


class TestRingVector(Base):
    def test_vector_matches_energy_and_length(self):
        H = exp_se3(np.r_[[0.3, -0.2, 0.1], np.deg2rad([0.5, -0.3, 3.0])])
        P = C.make_problem(self.F, H)
        P.ring_obs = {c: self.F['ring_obs'][c] for c in C.S.C4}   # compare 004 ring block only
        r = C.ring_vector_for_H(self.F, H, P.geom)
        e_vec = 0.5*(r**2).sum()
        # independent energy computation via the BA problem at the same cameras
        blk = P.blocks(H, {c: np.zeros(6) for c in P.cams}, self.F['X0'])
        e_ring = 0.5*sum((np.concatenate(blk[k])**2).sum() for k in ('I', 'C', 'O') if blk[k])
        self.assertLess(abs(e_vec-e_ring)/max(e_ring, 1e-12), 1e-12)
        n_obs = sum(len(self.F['ring_obs'][c].get(k, [])) for c in C.S.C4 for k in ('inner', 'outer', 'mid'))
        self.assertGreater(len(r), 0)
        self.assertLessEqual(len(r), n_obs)


class TestCandidatePose(Base):
    def test_candidate_records_final_H(self):
        cands = C.ring_candidates(self.F, list(range(8)), self.cams, yaw_step=60)
        self.assertGreater(len(cands), 3)
        for c in cands:
            H = np.asarray(c['H'])
            self.assertEqual(H.shape, (4, 4))
            Hi = np.asarray(c['H_initial'])
            self.assertGreaterEqual(c['refine_rot_deg'], 0.0)
            if abs(c['yaw_initial'] - 60.0) < 1e-9:
                self.assertTrue(np.allclose(Hi[:3, 3], 0.0))


class TestHOnce(Base):
    def test_H_applied_once(self):
        H = exp_se3(np.r_[[0.4, -0.3, 0.2], np.deg2rad([0.7, -0.4, 12.0])])
        P = C.make_problem(self.F, H)         # cameras passed are W0; H is inside
        Cw = P.cameras_from(H, {c: np.zeros(6) for c in P.cams})
        for c in P.cams:
            v = self.sc['cams'][c][0]
            expect = H @ self.cams[c] if v == '004' else self.cams[c]
            self.assertLess(np.abs(Cw[c]-expect).max(), 1e-12)
            # and NOT H@H@T0
            if v == '004':
                self.assertGreater(np.abs(Cw[c] - (H @ H @ self.cams[c])).max(), 1e-6)


class TestStageSeparation(Base):
    def test_M2_and_M3b_recorded_separately(self):
        H0 = np.eye(4)
        P = C.make_problem(self.F, H0)
        H2v, X2, i2 = C.solve(P, self.F['X0'], 'M2', H0=H0, budget=40)
        H3v, X3, i3 = C.solve(P, X2, 'M3b', H0=H2v, budget=40)
        self.assertFalse(np.allclose(H2v, H3v))
        self.assertEqual(i3['n_params'], 6+3*len(X2))
        self.assertTrue(hasattr(P, 'stage1'))


class TestReferenceCameras(Base):
    def test_epipolar_uses_given_reference_cameras(self):
        H = self.sc['H']
        e_gt = C.epipolar_energy(self.F, H, [0, 1], self.cams)
        cams_p, info = C.perturb_cams(self.sc, C.S.C5, np.deg2rad(0.5), 0.0, seed=4, which=('005',))
        e_p = C.epipolar_energy(self.F, H, [0, 1], cams_p)
        self.assertGreater(len(info), 0)
        self.assertGreater(abs(e_gt[0]-e_p[0]), 1e-6, 'epipolar scoring must follow the passed 005 cameras')


class TestHoldoutIsolation(Base):
    def test_holdout_does_not_change_selection(self):
        ids_fit = list(range(8))
        cands_a = C.ring_candidates(self.F, ids_fit, self.cams, yaw_step=90)
        F2 = dict(self.F); obs2 = []
        for c, i, uv in self.F['obs']:
            obs2.append((c, i, np.asarray(uv, float) + (np.array([500., 500.]) if i >= 8 else 0)))
        F2['obs'] = obs2
        cands_b = C.ring_candidates(F2, ids_fit, self.cams, yaw_step=90)
        self.assertAlmostEqual(cands_a[0]['epi'], cands_b[0]['epi'], places=9)


class TestM4Local(Base):
    def test_M4_updates_released_camera(self):
        H = self.sc['H']
        cams_p, info = C.perturb_cams(self.sc, C.S.C4, np.deg2rad(0.5), 0.0, seed=7)
        self.assertGreater(len(info), 0)
        P = C.make_problem(self.F, H, released=[C.S.C4[1], C.S.C4[2]], cams=cams_p)
        Hm, X, info = C.solve(P, self.F['X0'], 'M4', H0=H, budget=25)
        self.assertEqual(info['n_params'], 6+12+36)
        self.assertTrue(any(np.abs(P.dx_final[c]).max() > 0 for c in P.cv.released))
        for c in P.cv.frozen:
            self.assertTrue(np.all(P.dx_final[c] == 0))


if __name__ == '__main__':
    unittest.main(verbosity=2)
