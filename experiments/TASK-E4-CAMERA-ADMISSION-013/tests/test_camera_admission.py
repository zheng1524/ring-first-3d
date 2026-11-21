import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'code'))
import camera_admission as A, camera_rotation_metrics as RM

POL = A.load_policy()
BASE = dict(pose_valid=True, cad_valid=True, ring_raw_mae=0.9, held_n=100, held_median=2.4,
            held_p95=4.4, positive_depth=0.99, big_error_fraction=0.01,
            rotation_to_previous_deg=1.0, center_to_previous_mm=0.5)


class TestGate(unittest.TestCase):
    def test_accept_normal(self):
        self.assertEqual(A.decide(BASE, POL)['status'], 'ACCEPT')
    def test_reject_nonrigid(self):
        self.assertEqual(A.decide(dict(BASE, pose_valid=False), POL)['status'], 'REJECT')
    def test_missing_pose_field_not_accepted(self):
        m = dict(BASE); m.pop('pose_valid')
        self.assertNotEqual(A.decide(m, POL)['status'], 'ACCEPT')
    def test_missing_held_stats_insufficient(self):
        m = dict(BASE, held_median=None)
        self.assertEqual(A.decide(m, POL)['status'], 'INSUFFICIENT_EVIDENCE')
    def test_real_179_rotation_not_accepted(self):
        self.assertNotEqual(A.decide(dict(BASE, rotation_to_previous_deg=179.0), POL)['status'], 'ACCEPT')
    def test_diagnostic_does_not_bypass_ring(self):
        m = dict(BASE, held_p95=9.0, held_p95_valid=4.0, held_median_valid=2.4, ring_raw_mae=3.5)
        r = A.decide(m, POL, artefact='DEGENERATE_TRIANGULATION')
        self.assertNotEqual(r['status'], 'ACCEPT')
    def test_diagnostic_does_not_bypass_rotation(self):
        m = dict(BASE, held_p95=9.0, held_p95_valid=4.0, held_median_valid=2.4, rotation_to_previous_deg=179.0)
        self.assertNotEqual(A.decide(m, POL, artefact='DEGENERATE_TRIANGULATION')['status'], 'ACCEPT')
    def test_diagnostic_does_not_bypass_center_jump(self):
        m = dict(BASE, held_p95=9.0, held_p95_valid=4.0, held_median_valid=2.4, center_to_previous_mm=50.0)
        self.assertNotEqual(A.decide(m, POL, artefact='DEGENERATE_TRIANGULATION')['status'], 'ACCEPT')
    def test_diagnostic_can_clear_only_p95(self):
        m = dict(BASE, held_p95=9.0, held_p95_valid=4.0, held_median_valid=2.4)
        self.assertEqual(A.decide(m, POL, artefact='DEGENERATE_TRIANGULATION')['status'], 'ACCEPT')


class TestRotation(unittest.TestCase):
    def test_identity_and_small(self):
        I = RM.as_c2w(__import__('numpy').eye(4))
        self.assertAlmostEqual(RM.relative_deg(I, I), 0.0, places=6)
        for deg in (1, 5):
            M = I.copy(); M[:3, :3] = __import__('scipy.spatial.transform', fromlist=['Rotation']).Rotation.from_euler('y', deg, degrees=True).as_matrix()
            self.assertAlmostEqual(RM.relative_deg(I, M), deg, places=4)
    def test_179_kept(self):
        import numpy as np
        from scipy.spatial.transform import Rotation as Rot
        I = np.eye(4); M = np.eye(4); M[:3, :3] = Rot.from_euler('y', 179, degrees=True).as_matrix()
        self.assertGreater(RM.relative_deg(I, M), 178.0)
    def test_w2c_conversion(self):
        import numpy as np
        from scipy.spatial.transform import Rotation as Rot
        T = np.eye(4); T[:3, :3] = Rot.from_euler('y', 30, degrees=True).as_matrix(); T[:3, 3] = [1, 2, 3]
        back = RM.as_c2w(T, 'w2c')
        self.assertTrue(np.allclose(back @ T, np.eye(4), atol=1e-9))
    def test_q_minus_q(self):
        import numpy as np
        from scipy.spatial.transform import Rotation as Rot
        R = Rot.from_euler('z', 40, degrees=True).as_matrix()
        self.assertAlmostEqual(RM.angle_deg(R.T @ R), 0.0, places=6)

    def test_invalid_rotation(self):
        import numpy as np
        ok, why = RM.check_so3(np.ones((3, 3)))
        self.assertFalse(ok)


if __name__ == '__main__':
    unittest.main(verbosity=2)
