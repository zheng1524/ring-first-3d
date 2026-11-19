import unittest,numpy as np,trimesh
from ring_collision_gate import RingCollisionGate
class RingTests(unittest.TestCase):
 def setUp(self):
  r=trimesh.creation.icosphere(subdivisions=2,radius=1);b=trimesh.creation.icosphere(subdivisions=1,radius=.4);b.vertices+=np.array([1.1,0,0]);self.ring=dict(V=r.vertices,F=r.faces);self.body=dict(V=b.vertices.copy(),F=b.faces,F_solid=b.faces);self.gate=RingCollisionGate(self.body,self.ring)
 def shifted(self,d):return dict(self.body,V=self.body['V']+np.array([d,0,0]))
 def test_original_collision_unchanged_accept(self):self.assertTrue(self.gate.check(self.body,self.body)[0])
 def test_reduced_collision_accept(self):self.assertTrue(self.gate.check(self.shifted(.1),self.body)[0])
 def test_unrelated_update_accept(self):
  b=dict(self.body,V=self.body['V'].copy());q=b['V'][:,0]>1.35;b['V'][q,0]+=.03;self.assertTrue(self.gate.check(b,self.body)[0])
 def test_worsened_collision_reject(self):self.assertFalse(self.gate.check(self.shifted(-.1),self.body)[0])
 def test_new_collision_reject(self):
  initial=self.shifted(1);g=RingCollisionGate(initial,self.ring);self.assertFalse(g.check(self.body,initial)[0])
