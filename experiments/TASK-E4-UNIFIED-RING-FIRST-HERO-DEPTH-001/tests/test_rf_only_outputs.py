from pathlib import Path
import importlib.util,json,unittest
import numpy as np
T=Path(__file__).resolve().parents[1];O=T/'runs/RF_ONLY_V1'
def read(p):return json.loads(Path(p).read_text())
class RFOnlyContracts(unittest.TestCase):
    def test_all_105_have_admission_record(self):self.assertEqual(len(list(O.glob('G*/0*/camera/*/ADMISSION.json'))),105)
    def test_RF_only_selects_original_candidates_exactly(self):
        for p in O.glob('G*/0*/camera/*/CAMERA_RESULT.json'):
            r=read(p);original=read(r['original_result']);q=original['candidates'][r['selected_candidate_index']]
            self.assertEqual(q['source'],'originalRF5DoF_RGB_yaw');np.testing.assert_array_equal(q['C'],r['c2w_mm'])
            allowed=[c for c in original['candidates'] if c['source']=='originalRF5DoF_RGB_yaw']
            self.assertEqual(q['FIT_objective'],min(c['FIT_objective'] for c in allowed))
    def test_no_current_HOLDOUT_map_overlap(self):
        held={v['meta']['RGB_content_sha'] for v in read(T/'audit/SELECTED_VIEWS.json') if v['meta']['role']!='FIT'}
        for b in read(O/'BANK_ADMISSION.json'):
            if b['status']!='PASS':continue
            for ref in b['calibration_FIT_ancestry']:
                self.assertEqual(ref['role'],'FIT');self.assertEqual(ref['video'],b['video']);self.assertTrue(ref['RGB_array_SHA256']);self.assertNotIn(ref['RGB_array_SHA256'],held)
    def test_missing_video_maps_cannot_fall_back_to_004(self):
        for g in ['G02','G03','G05','G06']:
            for p in (O/g/'005/camera').glob('*/ADMISSION.json'):self.assertEqual(read(p)['status'],'FAIL')
    def test_G01_005_unverified_gauge_rejected(self):
        for p in (O/'G01/005/camera').glob('*/ADMISSION.json'):self.assertEqual(read(p)['status'],'FAIL')
    def test_fresh_HERO_exactly_32(self):
        files=list(O.glob('G*/004/hero/*/INFERENCE.json'));self.assertEqual(len(files),32)
        for p in files:
            r=read(p);self.assertTrue(r['inference_executed']);self.assertFalse(r['reused_historical_depth']);self.assertEqual(r['depth_definition'],'axialZ')
    def test_HERO_target_supports_all_FIT_same_video(self):
        roles={v['meta']['id']:(v['meta']['role'],v['meta']['video']) for v in read(T/'audit/SELECTED_VIEWS.json')}
        for p in O.glob('G*/004/hero/*/SOURCE.json'):
            r=read(p);self.assertEqual(len(r['frames']),4)
            for cid in r['frames']:self.assertEqual(roles[cid],('FIT','004'))
    def test_gradient_contract_nonzero_and_finite_difference(self):
        r=read(O/'G01/004/body/CONTRACT_B2/FINITE_DIFFERENCE_METRIC_TRANSLATION.json');self.assertEqual(r['status'],'PASS');self.assertGreater(abs(r['autograd']),1e-4);self.assertLess(r['relative_error'],.03)

if __name__=='__main__':unittest.main()
