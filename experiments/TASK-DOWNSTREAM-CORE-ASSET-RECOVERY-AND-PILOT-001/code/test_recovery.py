import unittest
from ring_first_3d.mainline.paths import activate
activate('TASK-E4-STRUCTURED-BODY-UPDATE-002')
from optimizer import train

class BudgetBoundaryTests(unittest.TestCase):
    def test_invalid_budget_rejected_before_data_or_output_access(self):
        for n in [0, -1, 37, 1.5, True]:
            with self.subTest(n=n), self.assertRaises(ValueError):
                train(None, None, None, None, None, {'iterations':n}, '/should-not-be-written', 'DEFORM_ONLY')

class CoordinateBoundaryTests(unittest.TestCase):
    def test_rigid_transport_keeps_projection_and_camera_baseline(self):
        import numpy as np
        from snapshot import move_video
        from ring_first_3d.sim.geometry import se3,transform
        from ring_first_3d.contracts.coordinates import project
        H=se3([.2,-.1,.3,4.,-2.,1.]);C=np.stack([np.eye(4),se3([0,.05,0,1.,0,0])]);P=np.array([[0,0,8.],[1,2,9.],[-1,1,7.]])
        K=np.array([[490,0,319.5],[0,490,179.5],[0,0,1.]])
        s=dict(cameras=C,landmarks=P,hero=P+1,ring=P-1)
        b=move_video(s,H)
        for i in range(2):
            np.testing.assert_allclose(project(P,K,C[i])[0],project(b['landmarks'],K,b['cameras'][i])[0],atol=1e-10)
        np.testing.assert_allclose(np.linalg.inv(C[0])@C[1],np.linalg.inv(b['cameras'][0])@b['cameras'][1],atol=1e-12)
        np.testing.assert_allclose(b['hero'],transform(s['hero'],H))
    def test_scale_and_reflection_rejected(self):
        import numpy as np
        from snapshot import move_video
        for q in [2.,-1.]:
            H=np.eye(4);H[0,0]=q
            with self.assertRaises(ValueError):move_video({},H)

class FrozenSnapshotTests(unittest.TestCase):
    def test_transport_all_pose_expressions_and_depth_consistency(self):
        import numpy as np
        from snapshot import load_snapshot,move_video
        from ring_first_3d.sim.geometry import se3
        from ring_first_3d.contracts.coordinates import unproject
        a=load_snapshot();H=se3([.1,.2,-.1,2.,-1.,3.]);b=move_video(a,H)
        for i,f in enumerate(b['frames']):np.testing.assert_allclose(f['c2w_mm'],b['cameras'][i])
        h=b['hero_observation'];np.testing.assert_allclose(h['reference_pose_mm'],b['cameras'][0]);np.testing.assert_allclose(h['source_poses_mm'],b['cameras'][1:])
        np.testing.assert_array_equal(a['hero_observation']['depth_mm'],h['depth_mm'])
        np.testing.assert_array_equal(a['frames'][0]['RGB'],b['frames'][0]['RGB'])
