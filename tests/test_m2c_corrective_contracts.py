import json,sys,unittest
from pathlib import Path
import numpy as np,pandas as pd
WS=Path('/home/liu/ring_first_3d_workspace'); R=WS/'runs/m2c_corrective_completion'
sys.path[:0]=[str(WS/'src'),str(WS/'tools')]
from ring_first_3d.mainline.native.ring_cad import params
from ring_first_3d.mainline.native.camera import torus_contours
class CorrectiveContracts(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.pos=pd.read_csv(R/'POSITIVE_DEPTH_VALIDATION.csv'); cls.traj=pd.read_csv(R/'TRAJECTORY_PER_FRAME.csv'); cls.sup=pd.read_csv(R/'HERO_SUPPORT_SELECTION.csv'); cls.val=json.loads((R/'VALIDATION_39.json').read_text())
 def test_cad(self):
  self.assertEqual(params(5)['centerline_radius_mm'],3.1); self.assertEqual(params(10)['centerline_radius_mm'],5.6)
  C=np.eye(4);C[2,3]=30;K=np.array([[490,0,319.5],[0,490,179.5],[0,0,1.]])
  cs=torus_contours(C,K,ring_radius=3.1,ring_wire=.6); self.assertEqual(len(cs),2)
 def test_depth_actual_observations(self):
  self.assertEqual(len(self.pos),766); self.assertTrue(self.pos.observed_point_count.notna().all()); self.assertTrue((self.pos.observed_point_count<=self.pos.total_points).all()); self.assertTrue((self.pos.observed_point_count>0).all())
 def test_trajectory_endpoint_detection(self):
  vc=self.traj.groupby(['group_id','video_id']).trajectory_class.first(); self.assertEqual(int((vc=='T2_ISOLATED_BRANCH').sum()),7); self.assertEqual(int((vc=='T3_CONSECUTIVE_BRANCH').sum()),3)
 def test_s1_s2_different(self):
  s1=self.sup[self.sup.arm=='S1'].set_index(['group_id','video_id','target_view']);s2=self.sup[self.sup.arm=='S2'].set_index(['group_id','video_id','target_view']);common=s1.index.intersection(s2.index);diff=sum(s1.loc[i,'support_views']!=s2.loc[i,'support_views'] for i in common); self.assertEqual(len(common),316); self.assertEqual(diff,284)
 def test_hero_smoke_and_body_status(self):
  h=json.loads((R/'hero_smoke/SMOKE_RESULT.json').read_text()); self.assertTrue(h.get('inference_executed')); self.assertEqual(h.get('native_shape'),[352,640]); self.assertLess(h.get('peak_GPU_bytes'),6*1024**3)
  self.assertTrue(self.val['HERO_ACTUALLY_EXECUTED']); self.assertFalse(self.val['BODY_ACTUALLY_EXECUTED']); self.assertFalse(self.val['A2_UNIFIED_EXECUTION_COMPLETE'])
if __name__=='__main__': unittest.main(verbosity=2)
