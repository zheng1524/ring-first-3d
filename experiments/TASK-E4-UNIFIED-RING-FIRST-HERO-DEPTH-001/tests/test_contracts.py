import importlib.util
from pathlib import Path
import tempfile
import unittest
import numpy as np
P=Path(__file__).resolve().parents[1]/'code/pipeline.py'
s=importlib.util.spec_from_file_location('task_pipeline',P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

class TaskContracts(unittest.TestCase):
    def result(self,source): return dict(candidate_source=source,c2w_mm=np.eye(4))
    def test_original_RF_admitted(self): self.assertEqual(m.camera_gate(self.result('originalRF5DoF_RGB_yaw'),1.,'PASS')['status'],'PASS')
    def test_PnP_rejected(self): self.assertEqual(m.camera_gate(self.result('REAL_RGB_PNP_LM'),1.,'PASS')['status'],'FAIL')
    def test_historical_rejected(self): self.assertEqual(m.camera_gate(self.result('HISTORICAL_FROZEN'),1.,'PASS')['status'],'FAIL')
    def test_yaw_unresolved_rejected(self): self.assertEqual(m.camera_gate(self.result('RING_ONLY_YAW_UNRESOLVED'),1.,'PASS')['status'],'FAIL')
    def test_bad_Ring_rejected(self): self.assertEqual(m.camera_gate(self.result('originalRF5DoF_RGB_yaw'),3.01,'PASS')['status'],'FAIL')
    def test_missing_ancestry_rejected(self): self.assertEqual(m.camera_gate(self.result('originalRF5DoF_RGB_yaw'),1.,'FAIL')['status'],'FAIL')
    def test_nonrigid_rejected(self):
        r=self.result('originalRF5DoF_RGB_yaw');r['c2w_mm'][0,0]=2
        self.assertIn('INVALID_SE3',m.camera_gate(r,1.,'PASS')['reasons'])
    def test_original_winner_not_mutated(self):
        r=self.result('REAL_RGB_PNP_LM');r['candidates']=[self.result('originalRF5DoF_RGB_yaw')]
        m.camera_gate(r,1.,'PASS');self.assertEqual(r['candidate_source'],'REAL_RGB_PNP_LM')
    def test_axial_Z_not_euclidean(self):
        from ring_first_3d.mainline.native.geometry import unproject
        p=unproject(np.array([10.]),np.eye(4),np.array([[1.,0.]]),np.eye(3))
        np.testing.assert_allclose(p,[[10.,0.,10.]])
        self.assertNotEqual(float(np.linalg.norm(p)),10.)
    def test_all_groups_and_videos_present(self):
        rows=m.read(m.TASK/'audit/SELECTED_VIEWS.json')
        self.assertEqual({r['meta']['case'] for r in rows},set(m.GROUPS))
        self.assertEqual(len({(r['meta']['case'],r['meta']['video']) for r in rows}),10)
    def test_FIT_HOLDOUT_disjoint(self):
        rows=m.read(m.TASK/'audit/SELECTED_VIEWS.json')
        f={r['meta']['id'] for r in rows if r['meta']['role']=='FIT'}
        h={r['meta']['id'] for r in rows if r['meta']['role']!='FIT'}
        self.assertFalse(f&h);self.assertEqual(len(f),80);self.assertEqual(len(h),25)
    def test_all_inputs_immutable(self):
        for r in m.read(m.TASK/'audit/SELECTED_VIEWS.json'):m.check_input(r)

if __name__=='__main__':unittest.main()
