import json, sys, unittest
from pathlib import Path
import numpy as np
R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R/'code'))
import historical_ransac as HR


class TestHistoricalRepair(unittest.TestCase):
    def test_symlink_restored(self):
        p = R/'historical/replay_G01/experiments/TASK-E4-RING-SIFT-SYMMETRIC-REGISTRATION-020/landmarks/CROSS_004.npz'
        q = R/'historical/replay_G01/experiments/TASK-E4-RING-POLYP-REGISTRATION-019/landmarks/CROSS_004.npz'
        if not q.exists():
            self.skipTest('full replay tree not shipped in the audit package')
        self.assertTrue(p.exists())
        self.assertEqual(p.resolve(), q.resolve())

    def test_landmark_count_153(self):
        p = R/'historical/replay_G01/experiments/TASK-E4-RING-POLYP-REGISTRATION-019/landmarks/CROSS_004.npz'
        if not p.exists():
            p = R/'fixtures/CROSS_004.npz'
        d = np.load(p, allow_pickle=True)
        self.assertEqual(len(d['X']), 153)
        self.assertEqual(d['des'].shape, (153, 128))

    def test_named_pairs_18(self):
        nm = json.loads((R/'fixtures/CROSS_NAMED_3D_TRACK_PAIRS.json').read_text())['matches']
        self.assertEqual(len(nm), 18)

    def test_ransac_reproduces_5_of_18(self):
        nm = json.loads((R/'fixtures/CROSS_NAMED_3D_TRACK_PAIRS.json').read_text())['matches']
        X4 = np.array([x['X004'] for x in nm]); X5 = np.array([x['X005'] for x in nm])
        out = HR.run(X4, X5)
        self.assertEqual(out['within_075mm'], 5)
        self.assertAlmostEqual(out['center_mm'], 2.160167553193399, places=9)
        self.assertAlmostEqual(out['tilt_deg'], 4.852245376490619, places=9)

    def test_frozen_R0_R3_give_2(self):
        nm = json.loads((R/'fixtures/CROSS_NAMED_3D_TRACK_PAIRS.json').read_text())['matches']
        X4 = np.array([x['X004'] for x in nm]); X5 = np.array([x['X005'] for x in nm])
        for f in ('R0.json', 'R3.json'):
            H = np.array(json.loads((R/'fixtures'/f).read_text())['T'])
            d = np.linalg.norm(X4 - (X5 @ H[:3, :3].T + H[:3, 3]), axis=1)
            self.assertEqual(int((d <= 0.75).sum()), 2, f)


if __name__ == '__main__':
    unittest.main(verbosity=2)
