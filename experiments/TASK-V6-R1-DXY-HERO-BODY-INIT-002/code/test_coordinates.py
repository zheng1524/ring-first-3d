import unittest,numpy as np
class CoordinateRouting(unittest.TestCase):
 def test_rejected_common_transform_removed_from_all_geometry(self):
  from observations_revision import transform_samples
  from scipy.spatial.transform import Rotation
  T=np.eye(4);T[:3,:3]=Rotation.from_euler('xyz',[.2,.1,.5]).as_matrix();T[:3,3]=[1,2,3]
  C=np.eye(4);C[:3,3]=[0,0,-20]
  r=np.array([[0,0,-20,.1,.2,1.]])
  src=dict(C=C,rays=r,raw_X=np.array([[1,2,-10.]]),bg_X=np.array([[2,3,0.]]),D=np.array([10.]))
  common=transform_samples(src,T);back=transform_samples(common,np.linalg.inv(T))
  for key in src:np.testing.assert_allclose(src[key],back[key],atol=1e-12)
  np.testing.assert_allclose((common['raw_X']-common['C'][:3,3])@common['C'][:3,:3],(src['raw_X']-C[:3,3])@C[:3,:3],atol=1e-12)
if __name__=='__main__':unittest.main()
