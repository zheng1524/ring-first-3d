import sys, unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, '/home/liu/ring_first_3d_workspace/camera_mainline/code')
import w0_adapter as A

R = Path(__file__).resolve().parents[1]


class TestFailClosed(unittest.TestCase):
    def test_missing_admission_blocks(self):
        with self.assertRaises(A.W0AdapterError):
            A.load_views('G99', '004')

    def test_unknown_status_not_accepted(self):
        views, acc = A.load_views('G03', '005')
        for v in acc:
            self.assertEqual(v['admission'], 'ACCEPT')
        self.assertTrue(all(v['admission'] != 'UNKNOWN' for v in acc))

    def test_k_matches_cache(self):
        views, _ = A.load_views('G03', '005')
        for v in views[:3]:
            K = np.load(v['RGB_cache'])['K']
            self.assertTrue(np.allclose(K, v['K']))

    def test_no_duplicate_view_ids(self):
        views, _ = A.load_views('G03', '004')
        self.assertEqual(len(views), len({v['view'] for v in views}))


if __name__ == '__main__':
    unittest.main(verbosity=2)
