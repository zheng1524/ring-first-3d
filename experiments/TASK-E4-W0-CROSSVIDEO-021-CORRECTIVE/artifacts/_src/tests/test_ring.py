import sys, unittest
from pathlib import Path
import numpy as np
C = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(C/'core'))
sys.path.insert(0, '/home/liu/ring_first_3d_workspace/src')
import shared_se3 as S3
from ring_first_3d.mainline.native.camera import torus_contours
K = np.array([[490., 0, 319.5], [0, 490., 179.5], [0, 0, 1.]])


def cam(rot_deg=0.0, t=(30., 0., 40.)):
    C = np.eye(4); C[:3, :3] = np.diag([1., -1., -1.]); C[:3, 3] = t
    th = np.deg2rad(rot_deg); c, s = np.cos(th), np.sin(th)
    Rz = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
    C[:3, :3] = Rz @ C[:3, :3]
    return C


class TestRing(unittest.TestCase):
    def test_ring_term_zero_at_true_pose(self):
        C = cam()
        pts = np.asarray(torus_contours(C, K)[0], float)
        ring = {'v': dict(C=C, pts=pts)}
        L = S3.ring_term(np.eye(4), ring, K, stride=1)
        self.assertLess(L, 1e-6)

    def test_ring_has_translation_gradient(self):
        C = cam()
        pts = np.asarray(torus_contours(C, K)[0], float)
        ring = {'v': dict(C=C, pts=pts)}
        L0 = S3.ring_term(np.eye(4), ring, K)
        H = np.eye(4); H[:3, 3] = [0.3, 0., 0.]
        L1 = S3.ring_term(H, ring, K)
        self.assertGreater(abs(L1 - L0), 1e-6)

    def test_ring_yaw_symmetry(self):
        """Ring CAD alone must NOT determine the global yaw (rotational symmetry)."""
        C = cam()
        pts = np.asarray(torus_contours(C, K)[0], float)
        ring = {'v': dict(C=C, pts=pts)}
        L0 = S3.ring_term(np.eye(4), ring, K)
        th = np.deg2rad(40.0); c, s = np.cos(th), np.sin(th)
        Hy = np.eye(4); Hy[:3, :3] = [[c, -s, 0], [s, c, 0], [0, 0, 1]]
        # the CAD curve follows the camera, so a yaw of the whole rig is invisible to Ring alone
        ring2 = {'v': dict(C=Hy @ C, pts=np.asarray(torus_contours(Hy @ C, K)[0], float))}
        L1 = S3.ring_term(np.eye(4), ring2, K)
        self.assertLess(abs(L1 - L0), 1e-6)

    def test_ring_invalid_geometry_penalty(self):
        C = cam(t=(5.6, 0., 0.0))     # camera on the tube -> invalid apparent contour
        pts = np.asarray(torus_contours(cam(), K)[0], float)
        self.assertGreaterEqual(S3.ring_term(np.eye(4), {'v': dict(C=C, pts=pts)}, K), 50.0 - 1e-9)


if __name__ == '__main__':
    unittest.main(verbosity=2)
