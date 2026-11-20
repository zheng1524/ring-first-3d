import sys, unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'code'))
import joint_loss as JL, cad_contour_correspondence as CC

K = np.array([[490.,0,319.5],[0,490.,179.5],[0,0,1]])
def pose(d=45., tilt=0.):
    M = np.eye(4); c,s = np.cos(np.deg2rad(tilt)), np.sin(np.deg2rad(tilt))
    M[:3,:3] = [[1,0,0],[0,c,-s],[0,s,c]]; M[:3,3] = [0,0,d]; return M

def synth_obs(M, n=360):
    from ring_first_3d.mainline.native.camera import torus_contours
    ci, co = CC.split(torus_contours(M, K))
    return dict(inner=np.asarray(ci), outer=np.asarray(co),
                inner_vis=np.ones(n,bool), outer_vis=np.ones(n,bool), quality={})

class TestJointLoss(unittest.TestCase):
    def test_zero_inside_tolerance(self):
        M = pose(); ob = synth_obs(M)
        v = JL.ring_block(M, K, ob)
        self.assertTrue(np.all(v < 1e-6), v)

    def test_grows_with_perturbation(self):
        M = pose(); ob = synth_obs(M)
        M2 = M.copy(); M2[:3,3] += [4.,0,0]
        self.assertGreater(float(np.sum(JL.ring_block(M2,K,ob))), float(np.sum(JL.ring_block(M,K,ob)))+1e-3)

    def test_sample_count_invariance(self):
        M = pose(); ob = synth_obs(M)
        a = float(np.sum(JL.ring_block(M,K,ob,m=128)))
        b = float(np.sum(JL.ring_block(M,K,ob,m=512)))
        self.assertLess(abs(a-b), 1e-9)

    def test_ring_vector_density_invariance(self):
        from synth_v2 import make_pose, ring_obs
        M = make_pose(45., 15.)
        ob = ring_obs(M)
        a = float(np.sum(JL.ring_vector(M, K, ob, m=128)**2))
        b = float(np.sum(JL.ring_vector(M, K, ob, m=512)**2))
        self.assertLess(abs(a-b), 1e-9)

    def test_compose_length_fixed(self):
        M = pose(); ob = synth_obs(M)
        r = JL.compose(M,K,ob,np.zeros(10))
        self.assertEqual(len(r), 12)

if __name__=='__main__': unittest.main()
