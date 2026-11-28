import unittest
import numpy as np
import importlib.util

class Contracts(unittest.TestCase):
 def test_interrupted_stage_is_preserved_and_can_restart(self):
  import tempfile
  from pathlib import Path
  import context
  self.assertTrue(hasattr(context,'isolate_incomplete'),'missing interrupted stage recovery')
  with tempfile.TemporaryDirectory(dir=context.T/'runtime')as tmp:
   stage=Path(tmp)/'stage';stage.mkdir();(stage/'partial').write_text('evidence')
   archived=context.isolate_incomplete(stage)
   self.assertFalse(stage.exists());self.assertEqual((archived/'partial').read_text(),'evidence')
   stage.mkdir();self.assertTrue(stage.exists())
 def test_output_guard_rejects_input_and_transform_drift(self):
  import tempfile,json
  from pathlib import Path
  import context
  self.assertTrue(hasattr(context,'verify_registration'),'missing output frozen-input guard')
  with tempfile.TemporaryDirectory(dir=context.T/'runtime')as tmp:
   p=Path(tmp);inp=p/'CAD';inp.write_text('original');a=p/'ASSETS.json';a.write_text(json.dumps(dict(files=[dict(path=str(inp),sha256=context.sha(inp))])));r=p/'REGISTRATION.json';r.write_text('{}')
   f=p/'TRANSFORM_FREEZE.json';f.write_text(json.dumps(dict(registration_sha256=context.sha(r),inputs=[dict(path=str(a),sha256=context.sha(a))])))
   context.verify_registration(p);inp.write_text('changed')
   with self.assertRaises(AssertionError):context.verify_registration(p)
   inp.write_text('original');r.write_text('{"T":"modified"}')
   with self.assertRaises(AssertionError):context.verify_registration(p)
 def test_multivideo_connection_and_unconnected(self):
  self.assertIsNotNone(importlib.util.find_spec('connections'), 'missing group connection adapter')
  from connections import connect
  t=np.eye(4);t[0,3]=2
  edges={('004','006'):t,('006','009'):t}
  out=connect(['004','006','009','010'],'004',edges)
  np.testing.assert_allclose(out['009']['T'][:3,3],[4,0,0])
  self.assertIsNone(out['010']['T'])
  self.assertEqual(out['009']['path'],['009','006','004'])
 def test_pair_slice_preserves_global_held(self):
  self.assertIsNotNone(importlib.util.find_spec('connections'), 'missing pair view adapter')
  from connections import pair_view
  frames=[dict(side=x,case=x,id=x+'__frame0',K=np.eye(3).tolist()) for x in ['004','006','009']]
  tr=dict(xy=np.arange(18.).reshape(3,3,2),held=np.array([True,False,True]),category=np.zeros(3,int))
  f,c,t=pair_view(frames,np.tile(np.eye(4),(3,1,1)),tr,'006','009')
  np.testing.assert_array_equal(t['held'],tr['held'])
  np.testing.assert_array_equal(t['xy'],tr['xy'][:,[1,2]])
  self.assertEqual([x['side'] for x in f],['A','B'])
 def test_consumer_transform_once_and_original_faces(self):
  self.assertIsNotNone(importlib.util.find_spec('consume'), 'missing common-coordinate consumer')
  from consume import apply_source
  V=np.array([[0.,0,0],[1,0,0],[0,1,0],[0,0,1]])
  F=np.array([[0,1,2],[0,2,3]]);T=np.eye(4);T[:3,3]=[2,3,4]
  v,f=apply_source(V,F,[1],T,'LOCAL')
  np.testing.assert_allclose(v,V+[2,3,4]);np.testing.assert_array_equal(f,F[[1]])
  with self.assertRaises(ValueError):apply_source(v,F,[1],T,'COMMON')
if __name__=='__main__':unittest.main()
