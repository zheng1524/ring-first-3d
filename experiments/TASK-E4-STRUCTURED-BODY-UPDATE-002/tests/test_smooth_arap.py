import unittest,numpy as np,torch,trimesh
from smooth_arap import SmoothARAP
from deformation_graph import so3
class ARAPTests(unittest.TestCase):
 def setUp(self):
  m=trimesh.creation.icosphere(subdivisions=1);self.s=SmoothARAP(m.vertices,m.faces)
 def test_rigid_invariance(self):
  R=so3(torch.tensor([[.4,.1,-.2]],dtype=torch.float64))[0];V=self.s.V@R.T+torch.tensor([1.,2.,3.]);r=self.s.rotations(V);a,b,e=self.s.energies(V,r);self.assertLess(float(abs(e)),1e-23)
 def test_exact_higher_order_definition(self):
  V=self.s.V.clone();V[:,2]+=.03*V[:,0]**2;r=self.s.rotations(V);a,b,e=self.s.energies(V,r);manual=(self.s.mass*((self.s.L@V/self.s.mass[:,None]-torch.einsum('nij,nj->ni',r,self.s.ref_lap))**2).sum(1)).sum();torch.testing.assert_close(b,manual);torch.testing.assert_close(e,.3*a+.7*b);self.assertGreater(float(b),0)
 def test_mass_and_laplacian(self):
  self.assertTrue(bool((self.s.mass>0).all()));torch.testing.assert_close(self.s.L,self.s.L.T);torch.testing.assert_close(self.s.L.sum(1),torch.zeros(len(self.s.V),dtype=torch.float64),atol=1e-14,rtol=0)
 def test_gradient_fixed_rotations(self):
  r=self.s.rotations(self.s.V);a=torch.tensor(.03,dtype=torch.float64,requires_grad=True)
  self.assertTrue(torch.autograd.gradcheck(lambda x:self.s.energies(self.s.V+torch.sin(self.s.V)*x,r)[2],(a,),eps=1e-6,atol=1e-5))
 def test_smooth_deformation_finite(self):
  V=self.s.V+torch.sin(self.s.V)*.02;r=self.s.rotations(V);a,b,e=self.s.energies(V,r);self.assertTrue(torch.isfinite(e));self.assertLess(float(e),1.)
