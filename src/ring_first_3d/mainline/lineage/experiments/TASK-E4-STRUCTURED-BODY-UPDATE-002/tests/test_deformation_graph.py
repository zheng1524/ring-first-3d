import unittest,numpy as np,torch,trimesh
from deformation_graph import DeformationGraph,so3
class GraphTests(unittest.TestCase):
 def setUp(self):
  self.m=trimesh.creation.icosphere(subdivisions=1);self.g=DeformationGraph(self.m.vertices,self.m.faces)
 def test_identity(self):
  z=torch.zeros((32,3),dtype=torch.float64);np.testing.assert_allclose(self.g.mesh(z,z),self.m.vertices,atol=1e-14);np.testing.assert_allclose(self.g.weights_np.sum(1),1)
 def test_rigid(self):
  w=torch.tensor([.2,-.1,.05],dtype=torch.float64).expand(32,3);R=so3(w)[0];t=self.g.g@R.T+torch.tensor([.3,.2,-.1])-self.g.g
  torch.testing.assert_close(self.g.mesh(w,t),self.g.V@R.T+torch.tensor([.3,.2,-.1]));self.assertLess(float(self.g.energy(w,t)),1e-25)
 def test_geodesic_and_so3(self):
  self.assertEqual(len(set(self.g.node_ids)),32);w=torch.randn(32,3,dtype=torch.float64);R=so3(w);torch.testing.assert_close(R@R.transpose(-1,-2),torch.eye(3,dtype=R.dtype).expand(32,3,3));torch.testing.assert_close(torch.linalg.det(R),torch.ones(32,dtype=R.dtype))
 def test_gradient(self):
  a=torch.tensor(.02,dtype=torch.float64,requires_grad=True);w=torch.ones(32,3,dtype=a.dtype)*a;t=torch.arange(96,dtype=a.dtype).reshape(32,3)*a*.01
  fn=lambda z:self.g.mesh(torch.ones_like(w)*z,torch.arange(96,dtype=a.dtype).reshape(32,3)*z*.01).square().sum()+self.g.energy(torch.ones_like(w)*z,torch.arange(96,dtype=a.dtype).reshape(32,3)*z*.01)
  self.assertTrue(torch.autograd.gradcheck(fn,(a,),eps=1e-6,atol=1e-5))
