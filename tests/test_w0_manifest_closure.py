import json
import unittest
from pathlib import Path
import numpy as np

WS = Path('/home/liu/ring_first_3d_workspace')
ROOT = WS / 'runs/m1_final_39'


def first_packet():
    for p in sorted(ROOT.glob('*/*/RUN_MANIFEST.json')):
        yield p.parent


class W0PackageContract(unittest.TestCase):
    def test_completed_packet_is_self_contained(self):
        d = next(iter(first_packet()), None)
        if d is None:
            self.skipTest('no completed W0 packet yet')
        man = json.loads((d / 'RUN_MANIFEST.json').read_text())
        for k in ('prepared', 'tracks', 'code', 'config', 'artifacts'):
            self.assertIn(k, man)
        self.assertEqual(len(man['prepared']['sha256']), 64)
        self.assertTrue((d / 'W0.npz').exists())
        self.assertTrue((d / 'camera_result.npz').exists())
        self.assertTrue((d / 'admission.csv').exists())
        self.assertTrue((d / 'quality_summary.json').exists())
        self.assertTrue((d / 'STATUS.json').exists())
        w = np.load(d / 'W0.npz')
        c = np.asarray(w['c2w'], float)
        self.assertTrue(np.isfinite(c).all())
        for T in c:
            R = T[:3, :3]
            self.assertTrue(np.allclose(R @ R.T, np.eye(3), atol=1e-8))
            self.assertAlmostEqual(abs(float(np.linalg.det(R))), 1.0, places=8)
        self.assertEqual(len(c), len([x for x in w['ids']]))


if __name__ == '__main__':
    unittest.main(verbosity=2)
