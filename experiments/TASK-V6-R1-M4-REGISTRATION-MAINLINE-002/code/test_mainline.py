import unittest
import numpy as np
import importlib.util

class Contracts(unittest.TestCase):
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
