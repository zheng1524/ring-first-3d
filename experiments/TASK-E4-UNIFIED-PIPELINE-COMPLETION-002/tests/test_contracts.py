import unittest,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'code'))
import pipeline as p
from banks import restore_native
from inputs import calibration_admission
from ring_first_3d.mainline.native.camera import RF_CONFIG

class Contracts(unittest.TestCase):
    def test_restore_identity(self):
        x=np.arange(12).reshape(4,3);np.testing.assert_array_equal(restore_native(x,np.eye(4)),x)
    def test_restore_explicit_rigid(self):
        from scipy.spatial.transform import Rotation
        h=np.eye(4);h[:3,:3]=Rotation.from_euler('xyz',[.1,.2,.3]).as_matrix();h[:3,3]=[1,2,3];x=np.arange(12).reshape(4,3);np.testing.assert_allclose(restore_native(x@h[:3,:3].T+h[:3,3],h),x,atol=1e-12)
    def test_restore_rejects_scale(self):
        h=np.eye(4);h[0,0]=2
        with self.assertRaises(AssertionError):restore_native(np.zeros((3,3)),h)
    def test_PnP_rejected(self):
        r=dict(candidate_source='REAL_RGB_PNP_LM',c2w_mm=np.eye(4));self.assertEqual(p.camera_gate(r,0,'PASS')['status'],'FAIL')
    def test_bad_bank_rejected(self):
        r=dict(candidate_source='originalRF5DoF_RGB_yaw',c2w_mm=np.eye(4));self.assertEqual(p.camera_gate(r,0,'FAIL')['status'],'FAIL')
    def test_unchanged_three_pixel_gate(self):
        r=dict(candidate_source='originalRF5DoF_RGB_yaw',c2w_mm=np.eye(4));self.assertEqual(p.camera_gate(r,3,'PASS')['status'],'PASS');self.assertEqual(p.camera_gate(r,3.0001,'PASS')['status'],'FAIL')
    def test_HOLDOUT_rejected_before_read(self):
        bad,_=calibration_admission(dict(role='HOLDOUT',video='004',case='G01'),'G01','004',set());self.assertIn('NOT_ARCHIVED_FIT',bad)
    def test_other_video_rejected(self):
        bad,_=calibration_admission(dict(role='FIT',video='005',case='G01'),'G01','004',set());self.assertIn('WRONG_VIDEO_OR_GROUP',bad)
    def test_RF_config_is_unchanged(self):
        self.assertEqual(RF_CONFIG['max_nfev'],35);self.assertEqual(RF_CONFIG['seed_retain'],2);self.assertEqual(RF_CONFIG['numerical_success_max_training_px'],3.)
    def test_selection_denominators(self):
        vv=p.views();self.assertEqual(len(vv),105);self.assertEqual(sum(v['meta']['role']=='FIT' for v in vv),80)
    def test_inherited_reference_not_retrained(self):
        self.assertTrue(p.inherited('G01','004'));self.assertFalse(p.inherited('G01','005'));self.assertFalse(p.inherited('G02','004'))
    def test_HOLDOUT_pixel_identity_excluded(self):
        from PIL import Image
        v=p.views()[0];m=v['meta'];bad,_=calibration_admission(dict(m,T=m['T']),'G01','004',{m['RGB_content_sha']});self.assertIn('CURRENT_HOLDOUT_PIXEL_OVERLAP',bad)
    def test_body_adapter_video_is_configuration(self):
        import adapters
        ns=adapters.load('body_stage','G02','005');self.assertIn('VIDEO',ns['setup'].__code__.co_names);self.assertEqual(ns['VIDEO'],'005');self.assertEqual(ns['T'],p.TASK)
    def test_evaluator_routes_same_instance(self):
        import adapters
        ns=adapters.load('evaluate_stage','G02','005');self.assertEqual([c['case'] for c in ns['p'].cases()],['G02']);self.assertEqual(ns['VIDEO'],'005');self.assertEqual(ns['OUT'],p.OUT)
    def test_HERO_same_native_inference_function(self):
        import adapters
        ns=adapters.load('hero_stage');self.assertEqual(ns['OUT'],p.OUT)

if __name__=='__main__':unittest.main()
