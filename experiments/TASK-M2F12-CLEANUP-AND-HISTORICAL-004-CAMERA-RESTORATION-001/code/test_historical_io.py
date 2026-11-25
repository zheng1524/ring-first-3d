import unittest,tempfile
from pathlib import Path
from historical_io import permitted, adapt_constants
import ast
class IsolationTests(unittest.TestCase):
 def test_new_result(self):self.assertTrue(permitted('/runs/new/predictions/C.npz','/runs/new',[],[]))
 def test_old_pose_denied(self):self.assertFalse(permitted('/old/predictions/C.npz','/runs/new',[],[]))
 def test_old_tracks_denied(self):self.assertFalse(permitted('/old/observations/tracks.npz','/runs/new',[],[]))
 def test_explicit_raw(self):self.assertTrue(permitted('/raw/a.mp4','/runs/new',['/raw/a.mp4'],[]))
 def test_old_bank_denied(self):self.assertFalse(permitted('/old/reference_banks/G01.npz','/runs/new',[],[]))
 def test_r10_identity(self):
  t=ast.parse('a=5.6; b=6.2; c=.6');self.assertEqual(ast.dump(adapt_constants(t,5.6)),ast.dump(ast.parse('a=5.6; b=6.2; c=.6')))
 def test_r5_physical(self):
  ns={};exec(compile(adapt_constants(ast.parse('a=5.6; b=6.2; c=.6'),3.1),'test','exec'),ns);self.assertAlmostEqual(ns['a'],3.1);self.assertAlmostEqual(ns['b'],3.7);self.assertEqual(ns['c'],.6)
if __name__=='__main__':unittest.main()
