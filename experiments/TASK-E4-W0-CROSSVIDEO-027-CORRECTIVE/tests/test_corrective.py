"""Before/after tests for the 027 defects (non-trivial numeric assertions)."""
import json, os, sys, unittest
from pathlib import Path
import numpy as np, torch
WS = Path('/home/liu/ring_first_3d_workspace')
C = WS/'experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE'
B = WS/'experiments/TASK-E4-W0-CROSSVIDEO-027-RING-ANCHORED-BA-PILOT'
sys.path.insert(0, str(C/'core')); sys.path.insert(0, str(C/'replay')); sys.path.insert(0, str(B/'core')); sys.path.insert(0, str(B/'replay')); sys.path.insert(0, str(WS/'src'))
os.environ.update(E4_RUN_DIR=str(C/'replay'),
    RING_CAD=str(WS/'assets/retained_sources/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-HERO-BODY-ADAPT-018/inputs/G03/RING.npz'),
    RING_NORM=str(WS/'assets/retained_sources/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/FREE_VERTEX_013/inputs/G03/NORMALIZATION.json'))
import camvar, ring_adapter, ring_energy
from se3 import exp_se3
from ring020_026 import RingRenderer, tensor, canonical
views = {v['id']: v for v in json.loads((C/'replay'/'config'/'VIEWS.json').read_text())}
split = json.loads((C/'runs/G03/SPLIT.json').read_text())
CAMS = {**{c: ('004', np.asarray(views[c]['T'], float)) for c in split['fit4']},
        **{c: ('005', np.asarray(views[c]['T'], float)) for c in split['fit5']}}


class TestVariableManagement(unittest.TestCase):
    def test_old_anchor_never_matches_any_camera(self):
        import ba_core as OLD
        P = OLD.Problem(CAMS, {c: np.asarray(views[c]['K'], float) for c in CAMS}, [], {}, np.zeros((12, 3)), None,
                        dict(sig_rot=.1, sig_trans=.1, sig_geo=50.), anchor=('005', 0))
        self.assertEqual(len(P.order), len(CAMS))       # D1: nothing was frozen
        self.assertNotIn('005', P.order)                 # sanity on the type
        self.assertTrue(all(isinstance(c, str) for c in P.order))

    def test_new_variable_sets(self):
        cv = camvar.CameraVariables(CAMS, split['fit4'][0], split['fit4'][1:])
        self.assertEqual(len(cv.released), 2)
        self.assertEqual(len(cv.frozen), len(CAMS)-2)
        self.assertIn(split['fit4'][0], cv.frozen)
        for c in split['fit5']:
            self.assertIn(c, cv.frozen)
            self.assertNotIn(c, cv.released)
        self.assertEqual(cv.dim(12), 6 + 12 + 36)

    def test_frozen_cameras_never_change(self):
        cv = camvar.CameraVariables(CAMS, split['fit4'][0], split['fit4'][1:])
        rng = np.random.default_rng(0)
        th0 = np.zeros(cv.dim(12))
        for _ in range(5):
            th = th0 + rng.normal(0, .05, cv.dim(12))
            H, dx, X = cv.unpack(th, np.eye(4), 12)
            for c in cv.frozen: self.assertFalse(np.any(dx[c] != 0.0))
            self.assertTrue(np.all(dx[split['fit4'][0]] == 0.0))


class TestRingOrder(unittest.TestCase):
    def test_increment_recovers_the_actual_camera(self):
        cid = split['fit5'][0]; T0 = np.asarray(views[cid]['T'], float)
        Cact = exp_se3(np.r_[[0.4, -0.2, 0.1], np.deg2rad([0.7, 0.3, 1.1])]) @ T0
        inc = ring_adapter.ring_increment_from_camera(Cact, T0)
        good = canonical(tensor(inc @ T0, torch.float64)).detach().cpu().numpy()
        ref = canonical(tensor(Cact, torch.float64)).detach().cpu().numpy()
        self.assertLess(np.abs(good-ref).max(), 1e-12)
        bad = canonical(tensor(np.linalg.inv(T0) @ Cact, torch.float64)).detach().cpu().numpy()
        self.assertGreater(np.abs(bad-ref).max(), 1e-3)   # the 027 order is detectably wrong

    def test_evaluation_matches_historical_renderer(self):
        rr = RingRenderer(sorted(CAMS)); cid = sorted(CAMS)[0]; T0 = np.asarray(views[cid]['T'], float)
        Cact = exp_se3(np.r_[[0.2, 0.1, -0.1], np.deg2rad([0.2, -0.1, 0.5])]) @ T0
        a = ring_adapter.evaluate_ring_at_camera(rr, Cact, T0, cid)
        L, _, _ = rr.losses(tensor(ring_adapter.ring_increment_from_camera(Cact, T0), torch.float64), cid)
        for k in ('M', 'I', 'C', 'O'):
            self.assertAlmostEqual(a[k], float(L[k]), places=12)


class TestRingEnergy(unittest.TestCase):
    def test_lambda_is_an_energy_weight(self):
        d = np.array([0.5, 2.0, 6.0, 1.0])
        e1 = float(0.5*(ring_energy.ring_residuals(d, 1.0, 0.35)**2).sum())
        e4 = float(0.5*(ring_energy.ring_residuals(d, 4.0, 0.35)**2).sum())
        self.assertAlmostEqual(e4/e1, 4.0, places=12)      # 4x, not 16x
        hist = 0.35*np.mean(np.where(d/3 < 1, 0.5*(d/3)**2, np.abs(d/3)-0.5))
        self.assertAlmostEqual(e1, hist, places=12)

    def test_zero_observations_are_finite(self):
        self.assertEqual(len(ring_energy.ring_residuals(np.zeros(0), 1.0, .35)), 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
