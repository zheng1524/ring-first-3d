import unittest
import numpy as np
from ring_first_3d.v6_raw.trusted_restore import trusted_subset
class TrustedOnlyTests(unittest.TestCase):
 def test_excludes_all_three_nontrusted_states_and_preserves_ids(self):
  V=np.arange(18,dtype=float).reshape(6,3);F=np.array([[0,1,2],[1,2,3],[2,3,4],[3,4,5]]);state=np.array([0,1,2,3],np.uint8)
  out=trusted_subset(V,F,state)
  np.testing.assert_array_equal(out['V'],V);np.testing.assert_array_equal(out['F'],F[:1]);np.testing.assert_array_equal(out['original_face_id'],[0]);np.testing.assert_array_equal(out['excluded_original_face_id'],[1,2,3]);np.testing.assert_array_equal(out['original_vertex_id'],np.arange(6))
 def test_no_trusted_is_an_empty_surface_not_a_vertex_component(self):
  out=trusted_subset(np.zeros((3,3)),np.array([[0,1,2]]),np.array([3]))
  self.assertEqual(out['F'].shape,(0,3));self.assertEqual(len(out['V']),3)
 def test_unknown_encoding_or_misalignment_fails(self):
  with self.assertRaises(ValueError):trusted_subset(np.zeros((3,3)),np.array([[0,1,2]]),np.array([4]))
  with self.assertRaises(ValueError):trusted_subset(np.zeros((3,3)),np.array([[0,1,2]]),np.array([]))
