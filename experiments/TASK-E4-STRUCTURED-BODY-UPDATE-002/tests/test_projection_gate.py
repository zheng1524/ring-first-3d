import unittest,numpy as np,trimesh
from projection_gate import ProjectionGate,DEFAULT
from ring_first_3d.contour_guided.correspondence import explicit_pairs
from ring_first_3d.synthetic.raster import ray_map
class ProjectionTests(unittest.TestCase):
 def test_far_pair_rejected(self):
  a=np.array([[0.,0.],[1.,0.]]);n=np.tile([1.,0.],(2,1));p=explicit_pairs(a,n,a+100,n,np.ones(2,bool),DEFAULT);self.assertFalse(p['accepted'].any())
 def test_normal_tangent_unknown_rejected(self):
  p=explicit_pairs(np.array([[0.,0.]]),np.array([[1.,0.]]),np.array([[0.,10.]]),np.array([[0.,1.]]),np.array([False]),DEFAULT);self.assertFalse(p['accepted'].any())
 def test_fresh_candidate_rerender_and_protection(self):
  m=trimesh.creation.icosphere(subdivisions=1);V=m.vertices+np.array([0,0,5.]);b=dict(V=V,F=m.faces);K=np.array([[60,0,32],[0,60,32],[0,0,1.]]);C=np.eye(4);lab=ray_map(V,m.faces,K,C,(64,64))['valid'].astype(int);ring=dict(V=m.vertices+np.array([20,20,30]),F=m.faces);v=dict(id='x',video='004',role='FIT',K=K,C=C,labels=lab)
  g=ProjectionGate([v],ring,{'x':1.});old=g.rebuild(b,True);g.initial=old;new=g.rebuild(dict(b,V=V+np.array([1.,0,0])),True);self.assertEqual(g.generation,2);self.assertFalse(np.array_equal(old['x']['predicted'],new['x']['predicted']));self.assertTrue(g.protect(new));a=old['x']['pairs'];self.assertTrue(np.allclose(a['bary'][a['accepted']].sum(1),1))

 def test_strict_mutual_both_directions(self):
  from projection_gate import strict_mutual
  source=np.array([[0.,0.],[10.,0.]]);target=np.array([[0.,0.],[1.,0.]])
  ok=strict_mutual(source,target,np.array([0,0]),np.array([0,1]));self.assertEqual(ok.tolist(),[True,False])
