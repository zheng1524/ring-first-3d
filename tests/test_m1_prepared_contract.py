import json
import sys
import unittest
from pathlib import Path
import numpy as np

WS = Path('/home/liu/ring_first_3d_workspace')
PREP = WS / 'runs/m1_final_39/prepared'
sys.path.insert(0, str(WS / 'tools'))
import prepare_m1_inputs as P


class PreparedContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.groups, cls.rows, cls.photos = P.build_registry()

    def test_all_39_groups_79_videos_790_frames(self):
        dirs = sorted(p for p in PREP.iterdir() if p.is_dir())
        self.assertEqual(len(dirs), 79)
        n_views = 0
        for p in dirs:
            d = json.loads((p / 'PREPARED.json').read_text())
            self.assertIn(d['group'], self.groups)
            self.assertIn(d['ring_mm'], (5.0, 10.0))
            self.assertTrue(np.allclose(np.asarray(d['K'], float), np.asarray(P.K, float)))
            n_views += len(d['views'])
        self.assertEqual(n_views, 790)

    def test_every_registered_frame_has_cache_labels_and_k(self):
        for r in self.rows:
            d = json.loads((PREP / f"{r['group']}_{r['video_id']}" / 'PREPARED.json').read_text())
            sub = [v for v in d['views']]
            self.assertEqual(len(sub), r['frames'])
            for q in sub:
                z = np.load(q['cache'])
                self.assertEqual(z['labels'].shape, (360, 640))
                self.assertTrue(np.isin(z['labels'], [0, 1, 2]).all(), q['cache'])
                self.assertTrue(np.allclose(np.asarray(z['K'], float), np.asarray(P.K, float)))


if __name__ == '__main__':
    unittest.main(verbosity=2)
