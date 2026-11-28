"""Scientific contract checks for the revised fixed-domain objective."""
import unittest
from fit_revision import *

def source(i,depth,x=0):
 r=np.tile([x,0,0,0,0,1.],(12,1));D=np.full(12,depth)
 return dict(rays=r,D=D,raw_X=corrected_points(r,D,0),C=np.eye(4),meta=dict(source_id=str(i),case=str(i),raw_target=i,support=[],reference=i))
class RevisedContracts(unittest.TestCase):
 def test_same_bias_subproblem_even_when_miss_and_plane_conflict(self):
  p=np.r_[0.,0,3,np.zeros(3),np.zeros(3)];s=[source(0,2,x=1.5),source(1,2)]
  problem=Problem([],s,p,plane=np.array([0,0,1.,-2.3]));b=np.array([.1,-.1]);q=b.copy();q[0]=-.2
  full=sum(problem.values(p,q).values())-sum(problem.values(p,b).values())
  part=problem.bias_coordinate_value(p,b,0,-.2)-problem.bias_coordinate_value(p,b,0,.1)
  self.assertAlmostEqual(full,part,places=10)
 def test_fixed_geometry_recovers_opposite_quarter_mm_through_optimizer(self):
  p=np.r_[0.,0,3,np.zeros(3),np.zeros(3)];problem=Problem([],[source(0,2.25),source(1,1.75)],p);b=np.zeros(2)
  for _ in range(15):b,log=problem.solve_bias(p,b)
  self.assertLess(np.max(abs(b-[.25,-.25])),.05)
  self.assertTrue(all(x['accepted']for x in log))
 def test_common_absolute_bias_remains_constrained(self):
  p=np.r_[0.,0,3,np.zeros(3),np.zeros(3)];problem=Problem([],[source(0,2.25),source(1,2.25)],p);b=np.zeros(2)
  for _ in range(15):b,_=problem.solve_bias(p,b)
  self.assertLess(float(b.mean()),.1)
 def test_cad_occludes_without_shrinking_depth_denominator(self):
  p=np.r_[0.,0,3,np.zeros(3),np.zeros(3)];s=[source(0,2.25)];s[0]['cad_z']=np.ones(12)
  problem=Problem([],s,p);z,hit,cap=problem.model_depth(p,s[0]);self.assertFalse(hit.any())
  self.assertEqual(len(problem.source_parts(p,0,0)['depth']),12)
 def test_ring_inside_cost_has_contact_tolerance(self):
  m=trimesh.creation.box(extents=[1,1,1]);m.apply_translation([0,0,3]);p=np.r_[0.,0,3,np.zeros(3),np.log([.2,.2,.2])]
  problem=Problem([],[],p,cad=dict(V=m.vertices,F=m.faces));self.assertGreater(problem.values(p,[])['CAD_penetration'],0)
 def test_seeds_do_not_change_regularization_reference(self):
  p=np.r_[0.,0,3,np.zeros(3),np.zeros(3)];problem=Problem([],[],p);reference=problem.p0.copy()
  _,_,_,record=problem.solve_multistart([('original',p),('other',p+[.1,0,0,0,0,0,0,0,0])],np.empty(0),1,'TEST')
  np.testing.assert_array_equal(problem.p0,reference);np.testing.assert_array_equal(record['fixed_prior_reference'],reference)
 def test_stable_plane_cannot_force_conflicting_trusted_surface(self):
  import base_revision
  rng=np.random.default_rng(4);bg=np.c_[rng.uniform(-2,2,(192,2)),np.zeros(192)]
  ss=[]
  for i in range(2):
   x=np.c_[rng.uniform(-1,1,(64,2)),np.r_[np.full(16,-.6),np.full(32,.3),np.full(16,.05)]]
   c=np.eye(4);c[2,3]=5
   ss.append(dict(raw_X=x,bg_X=bg,bg_distance_px=np.full(192,10),C=c,meta=dict(source_id=str(i),case=str(i),reference=i)))
  result=base_revision.estimate(ss)
  self.assertEqual(result['status'],'WEAK');self.assertFalse(result['apply']);self.assertTrue(result['downgraded_for_conflict'])
if __name__=='__main__':unittest.main()
