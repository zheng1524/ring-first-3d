"""025 contracts: identity index mapping, H direction, split isolation, visuals read-only."""
import json, sys, unittest
from pathlib import Path
import numpy as np, pandas as pd
N = Path(__file__).resolve().parents[1]
RUN = N/'replay_019_020/runs'; OUT = N/'runs/G03'
sys.path.insert(0, str(N/'core'))


class TestIdentityMapping(unittest.TestCase):
    def test_csv_matches_npz_coordinates(self):
        ids = pd.read_csv(OUT/'IDENTITIES'/'HISTORICAL_020_IDENTITIES.csv')
        lm4 = np.load(RUN/'landmarks'/'CROSS_004.npz'); lm5 = np.load(RUN/'landmarks'/'INDEPENDENT_005.npz')
        for _, r in ids.iterrows():
            self.assertTrue(np.allclose(lm4['X'][int(r.landmark_004)], [r.X004_x, r.X004_y, r.X004_z], atol=1e-9))
            self.assertTrue(np.allclose(lm5['X'][int(r.landmark_005)], [r.X005_x, r.X005_y, r.X005_z], atol=1e-9))
        self.assertEqual(len(ids), len({(int(a), int(b)) for a, b in zip(ids.landmark_004, ids.landmark_005)}))


class TestDirections(unittest.TestCase):
    def test_holdout_uses_H_and_Hinv(self):
        ho = pd.read_csv(OUT/'EVALUATION'/'HOLDOUT_BIDIRECTIONAL.csv')
        self.assertIn('004->005', set(ho.side)); self.assertIn('005->004', set(ho.side))
        H = np.load(OUT/'CONSISTENCY'/'H_HYPOTHESIS.npz')['H']
        ids = pd.read_csv(OUT/'IDENTITIES'/'HISTORICAL_020_IDENTITIES.csv')
        lm4 = np.load(RUN/'landmarks'/'CROSS_004.npz')['X']; lm5 = np.load(RUN/'landmarks'/'INDEPENDENT_005.npz')['X']
        i = int(ids.landmark_004[0]); j = int(ids.landmark_005[0])
        fwd = H[:3, :3] @ lm4[i] + H[:3, 3]
        rev = np.linalg.inv(H)[:3, :3] @ lm5[j] + np.linalg.inv(H)[:3, 3]
        self.assertGreater(np.linalg.norm(fwd - lm5[j]), 0.0)
        self.assertGreater(np.linalg.norm(rev - lm4[i]), 0.0)


class TestSplitIsolation(unittest.TestCase):
    def test_holdout_views_not_in_identity_chain(self):
        sp = json.loads((OUT/'SPLIT.json').read_text())
        names = json.loads((RUN/'features'/'CROSS_NAMED_3D_TRACK_PAIRS.json').read_text())['matches']
        used = {e['a'] for m in names for e in m['evidence']} | {e['b'] for m in names for e in m['evidence']}
        self.assertFalse(used & set(sp['ho4']), 'a 004 HOLDOUT view leaked into identity votes')
        self.assertFalse(used & set(sp['ho5']), 'a 005 HOLDOUT view leaked into identity votes')


class TestVisualsReadOnly(unittest.TestCase):
    def test_visuals_do_not_write_status(self):
        src = (N/'core'/'p6_visuals.py').read_text()
        for bad in ('.to_csv(OUT/\'IDENTITIES\'', 'final_identity_status\'] =', 'assume'):
            self.assertNotIn(bad, src)


if __name__ == '__main__':
    unittest.main(verbosity=2)
