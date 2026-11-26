import unittest
import numpy as np
try:
 from solver2 import solve_methods, mixed_loss, ring_residual
 from support2 import containing_faces
 READY=True
except ImportError:READY=False
from ring_first_3d.sim.geometry import se3,transform
class Contracts(unittest.TestCase):
 def setUp(self):self.assertTrue(READY,'M4/support adapters not implemented')
 def test_quadratic_ring_not_soft_l1(self):
  z=np.array([100.,100.]);r=mixed_loss(1,1)(z);self.assertAlmostEqual(r[0,0],2*(np.sqrt(101)-1));self.assertEqual(r[0,1],100);self.assertEqual(r[1,1],1);self.assertEqual(r[2,1],0)
 def test_exact_ring_M4_equals_M3(self):
  rng=np.random.default_rng(4);A=rng.normal(size=(30,3));D=se3([.1,-.05,.5,.3,.2,.1]);B=transform(A,D);R=dict(center=D[:3,3],normal=D[:3,2],covariance=np.zeros((5,5)),status='EXACT',radius_mm=5.6);out=solve_methods(A,B,R);np.testing.assert_allclose(out['M3']['T'],out['M4']['T'],atol=1e-10);self.assertLess(np.linalg.norm(out['M4']['T']@D-np.eye(4)),.00001)
 def test_ring_noise_is_not_exact(self):
  r=ring_residual(np.eye(4),np.array([.1,.2,.3]),np.array([0,0,1.]));np.testing.assert_allclose(r,[.1,.2,.3,0,0])
 def test_triangle_boundary_returns_all_faces(self):
  uv=np.array([[0.,0.],[1,0],[0,1],[1,1]]);F=np.array([[0,1,2],[1,3,2]]);self.assertEqual(containing_faces(np.array([.5,.5]),uv,F),[0,1]);self.assertEqual(containing_faces(np.array([.2,.2]),uv,F),[0]);self.assertEqual(containing_faces(np.array([2,2]),uv,F),[])
 def test_held_projection_is_cross_video(self):
  from ring_first_3d.contracts.coordinates import project
  K=np.eye(3);A=np.array([[1.,0.,4.]]);C=np.eye(4);D=se3([0,0,.4,.5,0,0]);local=transform(A,D);before=project(local,K,C)[0];after=project(transform(local,np.linalg.inv(D)),K,C)[0];np.testing.assert_allclose(after,project(A,K,C)[0],atol=1e-12);self.assertGreater(np.linalg.norm(before-after),.1)
if __name__=='__main__':unittest.main()
