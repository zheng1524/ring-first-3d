import context
import unittest,numpy as np
from scipy.spatial.transform import Rotation
from ring_first_3d.sim.geometry import se3,transform
from registration import pair_residuals,pack_pairs,solve_m5,pair_loss

def fixture():
 rng=np.random.default_rng(42);C=[];frames=[]
 for side in ['A','B']:
  for i in range(4):
   c=np.eye(4);c[:3,3]=[i*.6+(.15 if side=='B'else 0),.3*i if side=='B'else-.2*i,0];C.append(c);frames.append(dict(side=side,K=[[490,0,319.5],[0,490,179.5],[0,0,1]]))
 C=np.array(C);X=rng.uniform([-2,-2,12],[2,2,18],(40,3));xy=[]
 for c in C:
  P=X-c[:3,3];q=P@np.array(frames[0]['K']).T;xy.append(q[:,:2]/q[:,2:])
 xy=np.stack(xy,1);D=se3([.04,-.03,.4,.3,-.1,.2]);C[4:]=D@C[4:];tr=dict(xy=xy,held=np.arange(40)%5==0,category=np.zeros(40,int));return frames,C,tr,D
class Test(unittest.TestCase):
 def test_known_coordinate_transform(self):
  f,C,tr,D=fixture();p=pack_pairs(f,C,tr,~tr['held']);r=pair_residuals(np.linalg.inv(D),p);self.assertLess(max(abs(r)),1e-8);self.assertGreater(np.median(abs(pair_residuals(np.eye(4),p))),2)
 def test_held_excluded_by_pack(self):
  f,C,tr,D=fixture();p=pack_pairs(f,C,tr,~tr['held']);self.assertFalse(set(p['track_ids'])&set(np.flatnonzero(tr['held'])));self.assertEqual(len(p['track_ids']),32*16)
 def test_quadratic_prior_and_track_normalization(self):
  loss=pair_loss(np.array([.25,.75]));r=loss(np.array([100.,100.,100.]));self.assertAlmostEqual(r[0,0]/r[0,1],1/3);self.assertEqual(r[0,-1],100)
 def test_six_dof_solver_recovers_transform(self):
  f,C,tr,D=fixture();p=pack_pairs(f,C,tr,~tr['held']);ring=dict(center=D[:3,3],normal=D[:3,2],covariance=np.diag([.01]*3+[.0001]*2),status='ESTIMATED');r=solve_m5(p,ring,None);self.assertLess(np.linalg.norm(np.array(r['T'])@D-np.eye(4)),1e-4)
 def test_zero_baseline_not_zero_error(self):
  f,C,tr,D=fixture();C[:]=np.eye(4);p=pack_pairs(f,C,tr,~tr['held']);self.assertTrue((abs(pair_residuals(np.eye(4),p))>=30).all())
 def test_zero_baseline_solver_inconclusive(self):
  f,C,tr,D=fixture();C[:]=np.eye(4);p=pack_pairs(f,C,tr,~tr['held']);ring=dict(center=[0,0,0],normal=[0,0,1],covariance=np.eye(5)*.01,status='ESTIMATED');r=solve_m5(p,ring,None);self.assertEqual(r['quality'],'DEGENERATE_EPIPOLAR')
if __name__=='__main__':unittest.main()
