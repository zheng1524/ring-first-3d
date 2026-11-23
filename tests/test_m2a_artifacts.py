import json, sys, unittest
from pathlib import Path
import pandas as pd
WS = Path('/home/liu/ring_first_3d_workspace')
OUT = WS / 'runs/m2a_w0_recovery'
sys.path.insert(0, str(WS / 'tools'))
from validate_m1_all_groups import w0_numeric

class M2AEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.v = pd.read_csv(OUT / 'W0_79_VIDEO_RESULTS.csv')
        cls.g = pd.read_csv(OUT / 'W0_39_GROUP_SUMMARY.csv')
        cls.val = json.loads((OUT / 'VALIDATION_39.json').read_text())

    def test_counts(self):
        self.assertEqual(len(self.v), 79)
        self.assertEqual(len(self.g), 39)
        self.assertEqual(self.val['baseline_w0_generated'], 64)
        self.assertEqual(self.val['new_w0_generated'], 78)
        self.assertEqual((self.v.partial_or_full_recovery == 'FULL').sum(), 67)
        self.assertEqual((self.v.partial_or_full_recovery == 'PARTIAL').sum(), 11)
        self.assertEqual((self.v.partial_or_full_recovery == 'NOT_COMPUTABLE').sum(), 1)
        self.assertEqual(self.val['implementation_errors'], 0)
        self.assertEqual(self.val['cross_group_contamination'], 0)

    def test_required_fields(self):
        need = {'group_id','video_id','baseline_w0_poses','new_w0_poses','original_frames',
                'replacement_frames','bridge_frames','ring_valid_frames','original_components',
                'new_components','partial_or_full_recovery','baseline_accept','new_accept',
                'baseline_ring_mae','new_ring_mae','baseline_held_median','new_held_median',
                'baseline_held_p95','new_held_p95','trajectory_jump_count','j2_used',
                'j2_applicability','j2_result','geometry_diagnostic_status','human_review_status'}
        self.assertTrue(need <= set(self.v.columns), need - set(self.v.columns))

    def test_all_w0_numeric(self):
        bad = []
        for _, r in self.v.iterrows():
            p = r.get('w0_file')
            if not isinstance(p, str) or not Path(p).exists():
                continue
            ring = 10.0 if r.ring_type == 'R10' else 5.0
            n = int(r.original_frames) if r.recovery_method == 'BASELINE' else int(r.new_w0_poses)
            ok, _, why = w0_numeric(Path(p), n, ring)
            if not ok: bad.append((r.group_id, r.video_id, why))
        self.assertEqual(bad, [])

    def test_j2_and_visuals(self):
        j = json.loads((OUT / 'J2_REUSE_RECORD.json').read_text())
        self.assertFalse(j['j2_used'])
        self.assertEqual(j['j2_result'], 'NOT_RUN')
        self.assertTrue((OUT / 'visualization/F_summary/representative_contact_sheet.png').exists())
        self.assertTrue((OUT / 'visualization/C_pose_graph/C1/GP_Is_10.5mm_closed_R5_single_refY__005.png').exists())
        self.assertTrue((OUT / 'METHOD_COMPARISON.csv').exists())

if __name__ == '__main__':
    unittest.main(verbosity=2)
