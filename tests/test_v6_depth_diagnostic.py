import unittest
import numpy as np
from ring_first_3d.v6_raw.evaluate import depth_diagnostic
class DepthDiagnosticTests(unittest.TestCase):
 def test_known_layers_and_invalid_pixels(self):
  a=np.array([[10.,12.],[20.,np.nan]]);b=np.array([[10.,10.],[10.,10.]])
  r=depth_diagnostic(a,b,np.ones((2,2),bool));self.assertEqual(r['common_pixels'],3);self.assertEqual(r['median_absolute_mm'],2.);self.assertAlmostEqual(r['P95_absolute_mm'],9.2);self.assertEqual(r['over_5mm_fraction'],1/3)
 def test_empty_is_not_zero_error(self):
  r=depth_diagnostic(np.ones((2,2)),np.ones((2,2)),np.zeros((2,2),bool));self.assertEqual(r['status'],'NOT_EVALUABLE');self.assertIsNone(r['MAE_mm'])
if __name__=='__main__':unittest.main()
