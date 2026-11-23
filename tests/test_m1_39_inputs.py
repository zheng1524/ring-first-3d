"""M1 39-group input registry tests.

Ring counts are GROUP counts (22 R10 / 17 R5), not video-row counts.
"""
import sys
import unittest
from pathlib import Path

WS = Path('/home/liu/ring_first_3d_workspace')
sys.path.insert(0, str(WS / 'tools'))
import prepare_m1_inputs as P


class Registry39(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.groups, cls.rows, cls.photos = P.build_registry()

    def test_counts(self):
        self.assertEqual(len(self.groups), 39)
        self.assertEqual(len(self.rows), 79)
        self.assertEqual(sum(r['frames'] for r in self.rows), 790)
        self.assertEqual(len(self.photos), 39)
        self.assertEqual(sum(len(v) for v in self.photos.values()), 120)

    def test_ring_counts_are_groups(self):
        by_group = {}
        for r in self.rows:
            by_group.setdefault(r['group'], set()).add(r['ring_mm'])
        self.assertEqual(len(by_group), 39)
        self.assertEqual(sum(1 for v in by_group.values() if v == {10.0}), 22)
        self.assertEqual(sum(1 for v in by_group.values() if v == {5.0}), 17)
        self.assertEqual(sum(1 for v in by_group.values() if len(v) != 1), 0)

    def test_video_and_photo_identity(self):
        from collections import Counter
        per_group = Counter()
        seen = set()
        for r in self.rows:
            key = (r['group'], r['video_id'])
            self.assertNotIn(key, seen)
            seen.add(key)
            per_group[r['group']] += 1
        self.assertEqual(dict(Counter(per_group.values())), {2: 38, 3: 1})
        self.assertTrue(all(Path(r['raw_path']).exists() for r in self.rows))
        self.assertTrue(all(len(v) in (3, 4) for v in self.photos.values()))
        self.assertEqual(sum(1 for v in self.photos.values() if len(v) == 4), 3)


if __name__ == '__main__':
    unittest.main(verbosity=2)
