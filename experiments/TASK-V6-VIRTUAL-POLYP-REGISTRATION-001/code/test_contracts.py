import unittest
import numpy as np
from ring_first_3d.sim.geometry import se3,transform
from ring_first_3d.contracts.coordinates import project,validate_c2w
try:
 from registration import ring_only,solve
 from generate import texture
 AVAILABLE=True
except ImportError: AVAILABLE=False

class Contracts(unittest.TestCase):
 def setUp(self):self.assertTrue(AVAILABLE,'Registration/texture adapter not implemented')
 def test_ring_yaw_unobservable(self):
  T=se3([0,0,.5,2,-1,3]);c=transform(np.zeros((1,3)),T)[0];n=T[:3,2]
  M=ring_only(c,n);np.testing.assert_allclose(M[:3,:3],np.eye(3),atol=1e-12);np.testing.assert_allclose(transform(c[None],M),0,atol=1e-12)
 def test_joint_coordinates(self):
  K=np.array([[490,0,319.5],[0,490,179.5],[0,0,1.]]);C=se3([.1,.2,-.3,1,2,-20]);P=np.array([[0.,0.,0.],[1.,2.,1.]]);D=se3([.12,-.23,.51,3,-2,.4]);q,z=project(P,K,C);u,d=project(transform(P,D),K,D@C);np.testing.assert_allclose(q,u,atol=1e-10);np.testing.assert_allclose(z,d,atol=1e-10)
 def test_six_dof_and_outliers(self):
  rng=np.random.default_rng(4);A=rng.normal(size=(80,3))*3;D=se3([.1,-.2,.5,.3,-.4,.2]);B=transform(A,D);B[-4:]+=20
  T,rec=solve(A,B,D[:3,3],D[:3,2]);self.assertEqual(rec['status'],'ACCEPT');self.assertLess(np.linalg.norm(T@D-np.eye(4)),.03)
 def test_no_matches_rejected(self):
  T,r=solve(np.empty((0,3)),np.empty((0,3)),np.zeros(3),np.array([0.,0.,1.]));self.assertEqual(r['status'],'REJECT_INSUFFICIENT_TRACKS');self.assertIsNone(T)
 def test_scale_rejected(self):
  T=np.eye(4);T[0,0]=1.1
  with self.assertRaises(ValueError):validate_c2w(T)
 def test_texture_world_lock(self):
  P=np.array([[1.,2.,3.],[.1,-.3,2.]])
  np.testing.assert_array_equal(texture(P),texture(P[::-1])[::-1]);self.assertGreater(np.std(texture(np.random.default_rng(0).normal(size=(100,3)))),20)
if __name__=='__main__':unittest.main()
