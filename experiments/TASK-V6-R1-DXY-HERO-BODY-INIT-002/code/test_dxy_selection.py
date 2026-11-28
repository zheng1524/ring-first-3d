"""Actual frozen frame regression: close numerical candidates are not one ID."""
import unittest,json
from pathlib import Path
import numpy as np
import dxy_full
F=Path(__file__).resolve().parents[1]/'evidence/DXY_SELECTION_REGRESSION.json'
class SelectionIdentity(unittest.TestCase):
 def test_old_allclose_reproduces_wrong_real_pool_id(self):
  f=json.loads(F.read_text());s=f['selected'];matches=[r for r in f['pool'] if np.allclose(r['center_px'],s['center_px']) and np.allclose(r['basis_px'],s['basis_px'])]
  self.assertEqual(matches[0]['record_id'],f['wrong_approximate_id'])
  self.assertNotEqual(matches[0]['record_id'],f['expected_exact_id'])
 def test_exact_resolution_uses_actual_geometry_identity(self):
  f=json.loads(F.read_text());self.assertTrue(hasattr(dxy_full,'resolve_selected_record'),'Exact identity resolver missing')
  chosen,equivalent=dxy_full.resolve_selected_record(f['pool'],f['selected'],f['body'],f['shape'],f['origin'])
  self.assertEqual(chosen['record_id'],f['expected_exact_id']);self.assertEqual(equivalent,[f['expected_exact_id']])
 def test_equal_geometry_requires_observed_identity(self):
  f=json.loads(F.read_text());good=next(r for r in f['pool'] if r['record_id']==f['expected_exact_id']);other=dict(good,record_id=good['record_id']+':duplicate')
  with self.assertRaises(ValueError):dxy_full.resolve_selected_record([good,other],f['selected'],f['body'],f['shape'],f['origin'])
  chosen,ids=dxy_full.resolve_selected_record([good,other],f['selected'],f['body'],f['shape'],f['origin'],other['record_id'])
  self.assertEqual(chosen['record_id'],other['record_id']);self.assertEqual(len(ids),2)
if __name__=='__main__':unittest.main()
