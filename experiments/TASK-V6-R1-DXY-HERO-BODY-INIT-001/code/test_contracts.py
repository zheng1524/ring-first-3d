import unittest
import numpy as np
from geometry import ellipsoid_depth, clipped_depth, clip, body_mesh, corrected_points

class Contracts(unittest.TestCase):
 def setUp(self):
  self.p=np.r_[0.,0.,5.,0.,0.,0.,np.log([2.,2.,2.])]
  self.r=np.array([[0.,0.,0.,0.,0.,1.],[0.,0.,0.,.1,0.,1.]])
 def test_axial_bias(self):
  z=ellipsoid_depth(self.p,self.r)
  self.assertAlmostEqual(z[0],3.)
  X=corrected_points(self.r,z+.4,.4)
  self.assertTrue(np.allclose(X,self.r[:,:3]+self.r[:,3:]*z[:,None]))
 def test_cap_does_not_explain(self):
  z,hit,cap=clipped_depth(self.p,self.r,np.array([0.,0.,1.,-5.]))
  self.assertTrue(cap.all());self.assertFalse(hit.any())
  z,hit,cap=clipped_depth(self.p,self.r,np.array([0.,0.,-1.,5.]))
  self.assertTrue(hit.all());self.assertFalse(cap.any())
 def test_exact_clip_provenance(self):
  V,F=body_mesh(self.p);a=clip(V,F,np.array([0.,0.,1.,-5.]))
  ids=a['original_vertex_ID'];self.assertTrue(np.array_equal(a['V'][ids>=0],V[ids[ids>=0]]))
  self.assertLess(np.max(abs(a['V'][ids<0,2]-5.)),1e-9)
  self.assertTrue(a['inferred_base_faces'].any());self.assertTrue((a['original_face_ID'][a['inferred_base_faces']]==-1).all())
 def test_projection_invariance(self):
  from scipy.spatial.transform import Rotation
  R=Rotation.from_rotvec([.3,.1,-.2]).as_matrix();t=np.array([1.,2.,3.]);r=self.r.copy();r[:,:3]=r[:,:3]@R.T+t;r[:,3:]=r[:,3:]@R.T
  p=self.p.copy();p[:3]=R@p[:3]+t;p[3:6]=Rotation.from_matrix(R).as_rotvec()
  self.assertTrue(np.allclose(ellipsoid_depth(p,r),ellipsoid_depth(self.p,self.r)))
 def test_cut_boundary_not_full_ellipse(self):
  from fit import Problem
  from geometry import rays
  C=np.eye(4);K=np.eye(3);uv=np.array([[0.,0.]])
  f=dict(case='A',K=K,C=C,uv=uv,target=np.ones(1),grid_weight=np.ones(1),rays=rays(uv,K,C),boundary=uv,DXY=dict(available=False))
  original=Problem([f],[],self.p).pieces(self.p,np.zeros(0))['visible_boundary']
  clipped=Problem([f],[],self.p,np.array([1.,0.,0.,0.])).pieces(self.p,np.zeros(0))['visible_boundary']
  self.assertGreater(abs(original[0]),.01);self.assertLess(abs(clipped[0]),1e-9)

if __name__=='__main__':unittest.main()
