import unittest
import numpy as np
from ring_first_3d.sift_comparison.surfaces import zbuffer, paired_depth

class DepthTests(unittest.TestCase):
    def test_nearest_layer_wins_not_last_input(self):
        uv=np.array([[1.,1.],[1.,1.],[8.,8.],[0.,0.]])
        depth=zbuffer(uv,np.array([2.,9.,3.,-1.]),(3,3))
        self.assertEqual(depth[1,1],2.)
        self.assertEqual(np.isfinite(depth).sum(),1)

    def test_common_region_and_occlusion_denominators(self):
        rz=np.array([[4.,10.,np.nan]]);sz=np.array([[5.,5.,8.]])
        target=np.array([[5.,5.,5.]])
        out,masks=paired_depth(rz,target,sz,target,np.ones((1,3),bool))
        self.assertEqual(out['all_common']['pixels'],2)
        self.assertEqual(out['both_nonoccluded']['pixels'],1)
        self.assertEqual(out['target_polyp_pixels'],3)
        self.assertEqual(out['all_common']['R']['P95'],4.8)
        self.assertEqual(out['all_common']['S']['median'],0.)
        self.assertEqual(out['R_possible_occluded'],1)
        self.assertEqual(out['S_possible_occluded'],1)

    def test_empty_depth_is_not_zero_error(self):
        z=np.full((2,2),np.nan);out,_=paired_depth(z,z,z,z,np.ones((2,2),bool))
        self.assertIsNone(out['all_common']['R']['median'])
        self.assertEqual(out['all_common']['pixels'],0)

class GPUAndFreezeTests(unittest.TestCase):
    def test_own_cuda_context_is_not_another_job(self):
        from ring_first_3d.sift_comparison.surfaces import other_gpu_processes
        self.assertEqual(other_gpu_processes('123, python, 204 MiB\n456, python, 8000 MiB',123),['456, python, 8000 MiB'])
        self.assertEqual(other_gpu_processes('123, python, 204 MiB',123),[])

    def test_failed_or_changed_normalization_is_rejected(self):
        from ring_first_3d.sift_comparison.core import validate_frozen_similarity
        with self.assertRaises(ValueError):validate_frozen_similarity({'status':'NOT_EVALUABLE'},{},None,None)
        sim=dict(status='FROZEN',scale=1,rotation=np.eye(3).tolist(),translation=[0,0,0],camera_hashes={'R':'a','S':'b'})
        c=np.eye(4)[None]
        with self.assertRaises(ValueError):validate_frozen_similarity(sim,{'R':'a','S':'changed'},c,c)
        changed=c.copy();changed[0,0,3]=2
        with self.assertRaises(ValueError):validate_frozen_similarity(sim,sim['camera_hashes'],c,changed)
