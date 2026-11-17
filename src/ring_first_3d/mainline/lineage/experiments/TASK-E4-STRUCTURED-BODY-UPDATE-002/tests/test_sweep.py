import unittest,numpy as np,torch,trimesh
from bspline_sweep import BSplineSweep,basis,boundary_loop
class SweepTests(unittest.TestCase):
 def setUp(self):
  m=trimesh.creation.icosphere(subdivisions=1);self.body=dict(V=m.vertices.copy(),F=m.faces.copy(),F_solid=m.faces.copy(),inferred_base_faces=np.zeros(len(m.faces),bool),boundary_vertex=np.zeros(len(m.vertices),bool));patch=[0];direction=m.face_normals[0];self.s=BSplineSweep(self.body,patch,direction,length=1.5)
 def test_basis_partition(self):
  B,D=basis();np.testing.assert_allclose(B.sum(1),1,atol=1e-14);np.testing.assert_allclose(D.sum(1),0,atol=1e-14)
 def test_shared_root_and_connected_manifold(self):
  V=torch.as_tensor(self.body['V'],dtype=torch.float64);W,info=self.s.generate(V);body=self.s.body(W.detach().numpy(),self.body);m=trimesh.Trimesh(body['V'],body['F_solid'],process=False);self.assertTrue(m.is_watertight);self.assertTrue(m.is_winding_consistent);self.assertEqual(len(m.split()),1);np.testing.assert_allclose(W.detach().numpy()[self.s.loop],self.body['V'][self.s.loop]);self.assertEqual(len(self.s.loop),3)
 def test_independent_axes_gradient(self):
  V=torch.as_tensor(self.body['V'],dtype=torch.float64);W,info=self.s.generate(V);loss=W.square().sum()+sum(self.s.penalties(W,info));loss.backward();self.assertGreater(float(self.s.control.grad.norm()),0);self.assertGreater(float(self.s.radii.grad.norm()),0)

 def test_parameters_finite_difference(self):
  V=torch.as_tensor(self.body['V'],dtype=torch.float64)
  def fun():
   W,_=self.s.generate(V);return (W*torch.arange(W.numel(),dtype=W.dtype).reshape(W.shape)).sum()
  value=fun();value.backward()
  for parameter,index in [(self.s.control,(2,1)),(self.s.radii,(2,0)),(self.s.radii,(2,1))]:
   analytic=float(parameter.grad[index]);old=float(parameter[index]);eps=1e-6
   with torch.no_grad():parameter[index]=old+eps
   plus=float(fun())
   with torch.no_grad():parameter[index]=old-eps
   minus=float(fun())
   with torch.no_grad():parameter[index]=old
   self.assertAlmostEqual(analytic,(plus-minus)/(2*eps),delta=1e-4*max(1,abs(analytic)))
