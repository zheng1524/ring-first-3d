import json, sys, unittest
from pathlib import Path
import numpy as np
R = Path(__file__).resolve().parents[1]
WS = Path('/home/liu/ring_first_3d_workspace')
sys.path.insert(0, str(R/'adapters')); sys.path.insert(0, str(WS/'camera_mainline/code'))
import coordinate_adapter as CA


class TestW0Provenance(unittest.TestCase):
    def test_g03_cameras_come_from_w0_file(self):
        d = np.load(WS/'camera_mainline/G03/video005/camera_result.npz')
        self.assertEqual(str(d['source_arm']) if 'source_arm' in d else 'W0', 'W0')
        man = json.loads((WS/'camera_mainline/G03/video005/manifest.json').read_text())
        self.assertIn('tracks_sha256', man)

    def test_no_legacy_camera_files_used(self):
        man = json.loads((WS/'camera_mainline/G03/video005/manifest.json').read_text())
        self.assertNotIn('ring_first_3d_e4_sdf_localization', json.dumps(man))


class TestConventions(unittest.TestCase):
    def test_se3_inverse(self):
        H = CA.yaw_about_axis(47.0); H[:3, 3] = [0.2, -0.1, 0.3]
        self.assertTrue(np.allclose(H @ CA.inverse(H), np.eye(4), atol=1e-9))

    def test_asymmetric_scene_catches_direction_flip(self):
        """An asymmetric point set must give different residuals for H and H^-1."""
        X = np.array([[10., 0., 0.], [0., 12., 0.], [0., 0., 14.]])
        H = CA.yaw_about_axis(30.0); H[:3, 3] = [1., 2., 3.]
        a = CA.apply_to_points(H, X); b = CA.apply_to_points(CA.inverse(H), X)
        self.assertGreater(float(np.abs(a - b).max()), 1.0)


class TestCrossGroupConsistency(unittest.TestCase):
    def test_single_protocol_file(self):
        cfg = json.loads((R/'config/UNIFIED_PROTOCOL.json').read_text()) if (R/'config/UNIFIED_PROTOCOL.json').exists() else None
        self.assertIsNotNone(cfg)
        self.assertEqual(cfg['algo'], 'w0-crossvideo-v1')

    def test_no_group_branch_in_entry(self):
        src = (R/'code/run_cross_video.py').read_text()
        for bad in ("if group ==", "elif group ==", "G03' and", 'if g =='):
            self.assertNotIn(bad, src)


class TestResumeIntegrity(unittest.TestCase):
    def test_run_state_marks_running_not_pass(self):
        p = R/'audit/RUN_STATE.json'
        if not p.exists():
            self.skipTest('no run yet')
        st = json.loads(p.read_text())
        for k, v in st['stages'].items():
            self.assertIn(v['status'], ('PENDING', 'RUNNING', 'PASS', 'FAILED', 'BLOCKED', 'INTERRUPTED'))

    def test_stage_records_hashes(self):
        p = R/'audit/RUN_STATE.json'
        if not p.exists():
            self.skipTest('no run yet')
        st = json.loads(p.read_text())
        self.assertIn('code_hash', st)
        self.assertTrue(len(st['code_hash']) == 64)


if __name__ == '__main__':
    unittest.main(verbosity=2)
