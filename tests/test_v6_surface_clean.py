import unittest
import numpy as np
from ring_first_3d.v6_raw.surface_clean import native_mapping,candidate_faces
class CleanTests(unittest.TestCase):
 def test_half_pixel_resize_mapping(self):
  uv=np.array([[0,0],[639,359],[10,180]])
  pix,lo,hi,w=native_mapping(uv,352,360)
  self.assertTrue(np.array_equal(pix[:2],[[0,0],[639,351]]));self.assertTrue(np.all((w>=0)&(w<=1)))
  np.testing.assert_allclose((lo*(1-w)+hi*w)[2],(180+.5)*352/360-.5)
 def test_sparse_or_boundary_alone_is_not_delete(self):
  f=dict(perspective_stretch=np.array([20.,2,20,20]),native_depth_jump_mm=np.array([.1,.1,.8,.8]),CAD_occluded=np.array([False,False,False,True]))
  got=candidate_faces(f,np.array([0,0,2,2]),np.array([0,0,0,0]),np.zeros(4,bool))
  np.testing.assert_array_equal(got,[False,False,True,False])
 def test_two_supports_keep_conflict_unknown(self):
  f=dict(perspective_stretch=np.array([20.]),native_depth_jump_mm=np.array([.8]),CAD_occluded=np.array([False]))
  self.assertFalse(candidate_faces(f,np.array([2]),np.array([2]),np.array([False]))[0])
