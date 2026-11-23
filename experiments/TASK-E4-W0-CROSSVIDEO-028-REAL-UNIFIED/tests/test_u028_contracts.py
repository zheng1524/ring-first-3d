"""028 contract tests: no group branching, freeze table not used for admission, H applied once."""
import sys, re, unittest
from pathlib import Path
WS = Path('/home/liu/ring_first_3d_workspace')
U = WS/'experiments/TASK-E4-W0-CROSSVIDEO-028-REAL-UNIFIED'
sys.path.insert(0, str(U/'core'))
sys.path.insert(0, str(WS/'experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R6/core'))


class TestNoGroupBranch(unittest.TestCase):
    def test_source_has_no_group_specific_algorithm(self):
        src = (U/'core'/'u028.py').read_text()
        for pat in (r"if\s+group\s*==", r"elif\s+group\s*==", r"if\s+a\.group\s*=="):
            self.assertIsNone(re.search(pat, src), f'group branch found: {pat}')
        self.assertNotIn("BLOCKED_BY_W0_ADMISSION", src)

    def test_discover_uses_assets_only(self):
        import u028
        d = u028.discover('G03', max_views=2)
        self.assertTrue(all(v in d for v in d))
        for v, x in d.items():
            self.assertIn(x['status'], ('OK', 'BLOCKED_MISSING_W0'))


class TestHOnce(unittest.TestCase):
    def test_h_applied_once(self):
        import r6_core as C
        from se3 import exp_se3
        import numpy as np
        T0 = np.eye(4); T0[:3, 3] = [10., 0., 0.]
        H = exp_se3(np.r_[[0.2, 0., 0.], np.deg2rad([0, 0, 5.])])
        self.assertTrue(np.allclose(C.cam_world(T0, '004', H), H @ T0))
        self.assertFalse(np.allclose(C.cam_world(T0, '004', H), H @ H @ T0))


if __name__ == '__main__':
    unittest.main(verbosity=2)
