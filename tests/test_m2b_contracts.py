import json,sys,unittest
from pathlib import Path
import pandas as pd
WS=Path('/home/liu/ring_first_3d_workspace'); OUT=WS/'runs/m2b_ring_global_branch'
sys.path.insert(0,str(WS/'tools'))
from validate_m1_all_groups import w0_numeric

class M2BContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=pd.read_csv(OUT/'W0_79_VIDEO_RESULTS.csv'); cls.g=pd.read_csv(OUT/'W0_39_GROUP_SUMMARY.csv')
        cls.v=json.loads((OUT/'VALIDATION_39.json').read_text()); cls.ring=pd.read_csv(OUT/'RING_OBSERVATION_PER_FRAME.csv')
        cls.g03=pd.read_csv(OUT/'G03_BRANCH_METRICS.csv')
    def test_counts(self):
        self.assertEqual(len(self.d),79); self.assertEqual(len(self.g),39)
        self.assertEqual((self.d.new_w0_poses>0).sum(),79); self.assertEqual((self.d.partial_or_full_recovery=='FULL').sum(),69)
        self.assertEqual((self.d.partial_or_full_recovery=='PARTIAL').sum(),10); self.assertEqual((self.d.partial_or_full_recovery=='NOT_COMPUTABLE').sum(),0)
        self.assertEqual(int(self.d.new_accept.fillna(0).sum()),72); self.assertEqual(self.v['implementation_errors'],0)
    def test_ring_all(self):
        self.assertEqual(len(self.ring),40); self.assertTrue((self.ring.q_train_corrected==128).all())
        s=self.ring.groupby(['group_id','video_id']).q_train_corrected.min(); self.assertTrue((s==128).all())
        self.assertEqual(self.ring[self.ring.group_id.str.contains('GP_Is_18')].q_train_original.max(),0)
    def test_g03(self):
        a0=self.g03[(self.g03.method=='A0_M2A')&(self.g03.video_id==4)].iloc[0]; a1=self.g03[(self.g03.method=='A1_RING')&(self.g03.video_id==4)].iloc[0]; a2=self.g03[(self.g03.method=='A2_GLOBAL')&(self.g03.video_id==4)].iloc[0]
        self.assertGreater(a0.max_adjacent_rotation_deg,100); self.assertLess(a1.max_adjacent_rotation_deg,5); self.assertLess(a2.max_adjacent_rotation_deg,10)
        self.assertLess(a1.held_median,a2.held_median)
    def test_all_w0_numeric(self):
        bad=[]
        for _,r in self.d.iterrows():
            p=Path(r.w0_file); ring=10.0 if r.ring_type=='R10' else 5.0
            ok,_,why=w0_numeric(p,int(r.new_w0_poses),ring)
            if not ok: bad.append((r.group_id,r.video_id,why))
        self.assertEqual(bad,[])
    def test_visual_index(self):
        self.assertTrue((OUT/'visualization/NONACCEPT_INDEX.html').exists())
        self.assertEqual(len(list((OUT/'visualization/C_nonaccept_w0/per_video_contact_sheets').glob('*.jpg'))),79)
        self.assertEqual(len(list((OUT/'visualization/D_camera_ring_3d/per_video').glob('*.jpg'))),79)
        self.assertTrue((OUT/'visualization/E_summary/failure_gallery.png').exists())
        nc=pd.read_csv(OUT/'NONACCEPT_DIAGNOSTIC_CLASS.csv'); self.assertEqual(len(nc),694); self.assertEqual(len(nc[nc.human_review_status=='HUMAN_REVIEW_PENDING']),694)
    def test_m2a_rebuild_log(self):
        log=(OUT/'logs/m2a_merge_rebuild.log').read_text(); self.assertIn('new_w0_generated',log)

if __name__=='__main__': unittest.main(verbosity=2)
