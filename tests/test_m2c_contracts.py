import json,sys,unittest
from pathlib import Path
import numpy as np,pandas as pd
WS=Path('/home/liu/ring_first_3d_workspace'); OUT=WS/'runs/m2c_trajectory_admission'; A=OUT/'A_correctness'; B=OUT/'B_admission'
sys.path.insert(0,str(WS/'src')); sys.path.insert(0,str(WS/'tools'))
from ring_first_3d.mainline.native.ring_cad import params,project_contours

class M2CContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.w=pd.read_csv(A/'W0_79_VIDEO_RESULTS.csv'); cls.cc=pd.read_csv(A/'CAD_CONTRACT_VALIDATION.csv'); cls.clean=pd.read_csv(OUT/'MASK_CLEAN_PER_FRAME.csv'); cls.pos=pd.read_csv(A/'POSITIVE_DEPTH_DIAGNOSTICS.csv'); cls.v=json.loads((OUT/'VALIDATION_39.json').read_text())
    def test_cad_contract(self):
        self.assertEqual(params(5)['centerline_radius_mm'],3.1); self.assertEqual(params(10)['centerline_radius_mm'],5.6)
        self.assertEqual(params(5)['wire_radius_mm'],.6)
        self.assertTrue(self.cc.radius_ok.all()); self.assertTrue(self.cc.wire_ok.all()); self.assertEqual(len(self.cc),79)
        self.assertTrue(self.v['cad_contract_all_ok'])
    def test_projection_valid(self):
        # a real W0 camera from G03; R10 and R5 must both produce finite contours
        row=self.w[(self.w.group_id.str.contains('GP_Ip_20.0mm'))&(self.w.video_id==5)].iloc[0]
        z=np.load(row.w0_file); c=z['c2w'][0]
        for ring in [5,10]:
            cs=project_contours(c,np.array([[490,0,319.5],[0,490,179.5],[0,0,1.]]),ring)
            self.assertTrue(any(np.isfinite(np.asarray(x)).all() for x in cs))
    def test_clean_and_depth(self):
        self.assertEqual(len(self.clean),790); self.assertEqual(int(self.clean.clean_changed.sum()),29); self.assertEqual(int(self.clean.changed_pixels.sum()),1549)
        self.assertEqual(len(self.pos),766); self.assertTrue(self.pos.positive_depth.notna().all()); self.assertTrue(self.pos.positive_depth_held_fraction.notna().all())
        self.assertTrue((self.pos.positive_depth_held_fraction>=0).all())
    def test_a1_counts(self):
        self.assertEqual(len(self.w),79); self.assertEqual(len(pd.read_csv(A/'W0_39_GROUP_SUMMARY.csv')),39)
        self.assertEqual(int((self.w.new_w0_poses>0).sum()),79); self.assertEqual(self.v['w0_full'],67); self.assertEqual(self.v['w0_partial'],12)
        self.assertEqual(self.v['accept'],71); self.assertEqual(self.v['implementation_errors'],0)
        self.assertTrue(self.v['A_CORRECTNESS_PASS']); self.assertFalse(self.v['A_TRAJECTORY_REPAIR_COMPLETE'])
    def test_admission_and_downstream_status(self):
        s=pd.read_csv(B/'ADMISSION_SUMMARY.csv'); d=dict(zip(s.arm,s[['eligible_cameras','videos_with_any','targets_ready','supports_ready']].itertuples(index=False,name=None)))
        self.assertEqual(d['S0'],(71,25,30,16)); self.assertEqual(d['S1'],(348,63,137,129)); self.assertEqual(d['S2'],(348,63,137,129))
        h=pd.read_csv(B/'HERO_EXECUTION_RESULTS.csv'); self.assertTrue((h.status=='NOT_EXECUTED_RESOURCE').all())
        self.assertFalse(self.v['B_DOWNSTREAM_EVALUATION_COMPLETE']); self.assertTrue(self.v['HUMAN_REVIEW_PENDING'])

if __name__ == "__main__":
    unittest.main(verbosity=2)
