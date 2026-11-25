import unittest
import numpy as np
from ring_first_3d.v6_raw.policy import frame_indices, admit_camera, choose_sources, tuple_identity

class PolicyTests(unittest.TestCase):
 def test_original_sixteen(self):
  self.assertEqual(frame_indices(861),[0,57,115,172,229,287,344,401,459,516,573,631,688,745,803,860])
 def test_reject_short(self):
  with self.assertRaises(ValueError):frame_indices(8)
 def test_only_spread_relaxed(self):
  r=dict(held_observations=9,held_reprojection={'MAE':2.,'p95':4.},held_positive_fraction=1.,ring_held_self_contour_px={'MAE':1.,'p95':2.},initialization_center_spread_mm=7.)
  old,new,reasons=admit_camera(r);self.assertFalse(old);self.assertTrue(new);self.assertEqual(reasons,['初始化中心分散 7.000 mm > 2 mm'])
  r['held_reprojection']['MAE']=4.;self.assertFalse(admit_camera(r)[1])
 def test_nan_not_admitted(self):
  r=dict(held_observations=9,held_reprojection={'MAE':float('nan'),'p95':4.},held_positive_fraction=1.,ring_held_self_contour_px={'MAE':1.,'p95':2.},initialization_center_spread_mm=0.)
  self.assertFalse(admit_camera(r)[1])
 def test_original_tuple_preserved(self):
  ranked=[{'i':4,'overlap':30,'angle':20},{'i':1,'overlap':30,'angle':10},{'i':2,'overlap':30,'angle':9},{'i':3,'overlap':30,'angle':8}]
  src,old=choose_sources(ranked,{1,2,3},{1,2,3,4});self.assertEqual(src,[1,2,3]);self.assertTrue(old)
 def test_new_tuple_only_if_original_absent(self):
  ranked=[{'i':4,'overlap':30,'angle':20},{'i':1,'overlap':30,'angle':10},{'i':2,'overlap':30,'angle':9}]
  src,old=choose_sources(ranked,{1,2},{1,2,4});self.assertEqual(src,[4,1,2]);self.assertFalse(old)
 def test_identity_detects_camera_change(self):
  fs=[dict(RGB=np.zeros((2,2,3),np.uint8),labels=np.zeros((2,2),np.uint8),K=np.eye(3),c2w_mm=np.eye(4),raw_frame=i)for i in range(4)]
  k=tuple_identity(fs,'raw','model');fs[1]['c2w_mm'][0,3]=1.;self.assertNotEqual(k,tuple_identity(fs,'raw','model'))
if __name__=='__main__':unittest.main()
