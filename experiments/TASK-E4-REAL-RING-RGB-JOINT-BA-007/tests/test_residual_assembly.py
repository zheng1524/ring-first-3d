import sys, unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path('/home/liu/ring_first_3d_workspace/experiments/TASK-E4-REAL-RING-RGB-JOINT-BA-007/code')))
import joint_loss as JL


class TestAssembly(unittest.TestCase):
    def test_ring_vector_fixed_length(self):
        from synth_helpers import make_obs
        ob = make_obs()
        self.assertEqual(len(JL.ring_vector(np.eye(4), np.eye(3)*490, ob, m=64)), 128)

    def test_density_invariance(self):
        from synth_helpers import make_obs
        ob = make_obs()
        K = np.array([[490.,0,319.5],[0,490.,179.5],[0,0,1]])
        M = np.eye(4); M[:3,3] = [0,0,45]
        # mismatched curves: invariance holds up to sampling phase, relative tolerance
        a = float(np.sum(JL.ring_vector(M,K,ob,m=128)**2))
        b = float(np.sum(JL.ring_vector(M,K,ob,m=512)**2))
        self.assertLess(abs(a-b), 0.02*max(a,b,1e-9))
        # matched curves (DXY built from the CAD projection): exact zero for both densities
        from ring_first_3d.mainline.native.camera import torus_contours
        import cad_contour_correspondence as CC
        ci, co = CC.split(torus_contours(M,K))
        ob2 = dict(inner=np.asarray(ci), outer=np.asarray(co),
                   inner_vis=np.ones(len(ci),bool), outer_vis=np.ones(len(co),bool))
        self.assertLess(float(np.sum(JL.ring_vector(M,K,ob2,m=128)**2)), 1e-9)
        self.assertLess(float(np.sum(JL.ring_vector(M,K,ob2,m=512)**2)), 1e-9)

    def test_fallback_without_dxy(self):
        ob = dict(inner=np.zeros((0,2)), outer=np.zeros((0,2)),
                  inner_vis=np.zeros(4,bool), outer_vis=np.zeros(4,bool))
        r = JL.ring_vector(np.eye(4), np.eye(3)*490, ob, m=16)
        self.assertTrue(np.isfinite(r).all())


if __name__ == '__main__':
    unittest.main()
