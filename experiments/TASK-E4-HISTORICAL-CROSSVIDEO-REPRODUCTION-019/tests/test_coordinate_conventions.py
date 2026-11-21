import sys, unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'adapters'))
import coordinate_adapter as CA


class TestConventions(unittest.TestCase):
    def test_SE3_inverse(self):
        T = np.eye(4); T[:3, :3] = CA.yaw_about_axis(47.0)[:3, :3]; T[:3, 3] = [3., -2., 1.]
        self.assertTrue(np.allclose(T @ CA.inverse(T), np.eye(4), atol=1e-9))

    def test_c2w_composition(self):
        H = CA.yaw_about_axis(30.0); T = np.eye(4); T[:3, 3] = [10., 0., 40.]
        self.assertTrue(np.allclose(CA.apply_to_points(H, CA.apply_to_points(CA.inverse(H), np.array([[1., 2., 3.]]))),
                                    np.array([[1., 2., 3.]]), atol=1e-9))

    def test_world_point_transform(self):
        H = CA.yaw_about_axis(90.0)
        X = np.array([[1., 0., 0.]])
        self.assertTrue(np.allclose(CA.apply_to_points(H, X), np.array([[0., 1., 0.]]), atol=1e-9))

    def test_scale_and_relative_motion_preservation(self):
        H = CA.yaw_about_axis(47.0); H[:3, 3] = [1., 2., 3.]
        C = np.array([[10., 0., 40.], [-20., 5., 42.]])
        d0 = np.linalg.norm(C[0] - C[1]); d1 = np.linalg.norm(CA.apply_to_points(H, C)[0] - CA.apply_to_points(H, C)[1])
        self.assertAlmostEqual(d0, d1, places=9)

    def test_ring_axis_rotation_preserves_radius(self):
        H = CA.yaw_about_axis(47.0); C = np.array([[30., 10., 40.]])
        self.assertAlmostEqual(np.linalg.norm(C[0]), np.linalg.norm(CA.apply_to_points(H, C)[0]), places=9)

    def test_normal_parity(self):
        H = CA.yaw_about_axis(47.0); n = np.array([[0., 0., 1.]])
        self.assertTrue(np.allclose(CA.apply_to_points(H, n), n, atol=1e-9))

    def test_pose_validity(self):
        self.assertTrue(CA.check_pose(np.eye(4))['valid'])
        bad = np.eye(4); bad[:3, :3] = np.diag([1., 1., -1.])
        self.assertFalse(CA.check_pose(bad)['valid'])


if __name__ == '__main__':
    unittest.main()
