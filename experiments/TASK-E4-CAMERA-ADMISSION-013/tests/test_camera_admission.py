import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'code'))
import camera_admission as A

POL = A.load_policy()
BASE = dict(pose_valid=True, cad_valid=True, ring_raw_mae=0.9, held_n=100, held_median=2.4,
            held_p95=4.4, positive_depth=0.99, big_error_fraction=0.01, center_jump_mm=0.5,
            rotation_jump_deg=1.0)


class TestAdmission(unittest.TestCase):
    def test_accept_normal(self):
        s, why, hard = A.classify(BASE, POL); self.assertEqual(s, 'ACCEPT'); self.assertFalse(hard)
    def test_reject_nonrigid(self):
        s, _, hard = A.classify(dict(BASE, pose_valid=False), POL); self.assertEqual(s, 'REJECT'); self.assertTrue(hard)
    def test_insufficient(self):
        s, why, _ = A.classify(dict(BASE, held_n=5), POL); self.assertEqual(s, 'INSUFFICIENT_EVIDENCE')
    def test_ring_fail(self):
        s, why, _ = A.classify(dict(BASE, ring_raw_mae=3.5), POL); self.assertEqual(s, 'QUARANTINE')
    def test_isolated_track_artifact(self):
        m = dict(BASE, held_p95=9.0, big_error_fraction=0.02)
        s, why, _ = A.classify(m, POL); self.assertEqual(s, 'QUARANTINE')
        s2, _ = A.diagnose_once(m, POL, 'DEGENERATE_TRIANGULATION'); self.assertEqual(s2, 'ACCEPT')
    def test_bad_camera_rejects_after_diagnosis(self):
        m = dict(BASE, held_median=9.0, held_p95=20.0)
        s, _, _ = A.classify(m, POL); self.assertEqual(s, 'QUARANTINE')
        s2, _ = A.diagnose_once(m, POL, 'ISOLATED_TRACKS'); self.assertEqual(s2, 'REJECT')
    def test_reference_photo_without_evidence(self):
        s, why, _ = A.classify(dict(BASE, held_n=0, held_median=None, held_p95=None), POL)
        self.assertEqual(s, 'INSUFFICIENT_EVIDENCE')


if __name__ == '__main__':
    unittest.main(verbosity=2)
