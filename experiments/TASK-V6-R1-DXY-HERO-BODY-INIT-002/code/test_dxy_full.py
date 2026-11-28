import unittest, importlib.util, sys
from pathlib import Path
import numpy as np
class PixelContract(unittest.TestCase):
 def test_pixel_branch_solves_real_boundary_without_claiming_ring_measurement(self):
  spec=importlib.util.find_spec('dxy_full');self.assertIsNotNone(spec,'Task pixel outlet is missing')
  from dxy_full import pixel_only
  import cv2
  lab=np.zeros((180,240),np.uint8);cv2.ellipse(lab,(120,90),(55,34),27,0,360,1,-1)
  r=pixel_only(np.zeros((180,240,3),np.uint8),lab,'test:ellipse')
  self.assertIsNotNone(r['selected']);self.assertFalse(r['official_measurement_valid']);self.assertEqual(r['status'],'PIXEL_ONLY')
  self.assertGreater(len(r['P']),100);self.assertEqual(len(r['Q']),0)
  c=r['selected'];self.assertLess(np.linalg.norm(np.array(c['center_px'])-[120,90]),2)
  self.assertNotIn('D_frame_mm',c);self.assertTrue(any(x['selected'] for x in r['candidates']))
 def test_pixel_branch_does_not_invent_curve_for_empty_input(self):
  spec=importlib.util.find_spec('dxy_full');self.assertIsNotNone(spec,'Task pixel outlet is missing')
  from dxy_full import pixel_only
  r=pixel_only(np.zeros((80,100,3),np.uint8),np.zeros((80,100),np.uint8),'test:empty')
  self.assertIsNone(r['selected']);self.assertEqual(r['status'],'NO_CURVE')
if __name__=='__main__':unittest.main()
