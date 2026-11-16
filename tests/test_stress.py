"""Stress scope, inherited-source, isolation and pixel adapter regressions."""
import copy,json,tempfile,unittest
from pathlib import Path
import numpy as np
import yaml
from ring_first_3d.policy.contracts import ROOT,load_task,PolicyError,stages_for
from ring_first_3d.policy.stress_contracts import TASK_ID,CONDITIONS,STRESS_STAGES,permissions,verify
from ring_first_3d.multisurface.scene import noise_vectors
from ring_first_3d.stress.handlers import ctf_eligible
from ring_first_3d.stress.real import native_pixels,safe_project,validate_view
from ring_first_3d.stress.artifacts import validate
class StressContractTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.path=Path(self.tmp.name)/'TASK.yaml';self.raw=yaml.safe_load((ROOT/'experiments'/TASK_ID/'TASK.yaml').read_text())
 def task(self):self.path.write_text(yaml.safe_dump(self.raw));return load_task(self.path)
 def reject(self,code):
  with self.assertRaises(PolicyError)as e:self.task()
  self.assertEqual(e.exception.code,code)
 def test_schema6_retains_order_and_original35_before_science(self):self.assertEqual(stages_for(self.task()),STRESS_STAGES)
 def test_cannot_increase_threshold_in_main_method(self):self.raw['fusion']['candidate_reject_distance_mm']=5.;self.reject('FROZEN_PROTOCOL')
 def test_noise_sigma_cannot_silently_change(self):self.raw['fusion']['conditions']['C7']['sigma']['004'][0]=3.;self.reject('INJECTION_PROTOCOL')
 def test_cannot_skip_real_audit_or_smoke(self):self.raw['authorization']['stages'].remove('G0_real_audit');self.reject('AUTHORIZATION')
 def test_real_GT_not_available_to_predictor(self):
  t=self.task();p=permissions(t,'real_predict',self.path.parent);self.assertFalse(p['allow_GT']);self.assertIn(Path(t['stress']['parent_multisurface_run']),p['denied_read_prefixes']);self.assertTrue(permissions(t,'G4_evaluate',self.path.parent)['allow_GT'])
 def test_wrong_units_rejected(self):self.raw['variables']['geometry_unit']='m';self.reject('COORDINATES')
 def test_GT_selecting_model_rejected(self):self.raw['fusion']['GT_selects_predictor']=True;self.reject('GT_LEAK')
 def test_source_sha_fails_before_any_scientific_run(self):
  t=self.task();t['stress']['assets']['algorithm_lock']['sha256']='0'*64
  with self.assertRaises(PolicyError)as e:verify(t)
  self.assertEqual(e.exception.code,'SOURCE_SHA')
 def test_CTF_trigger_uses_only_prediction_correspondences(self):
  t=self.task();self.assertFalse(ctf_eligible(t,dict(body=[dict(accepted_N=75,target_N=100)],pair_rate=.7)));self.assertTrue(ctf_eligible(t,dict(body=[dict(accepted_N=20,target_N=100)],pair_rate=.7)));self.assertTrue(ctf_eligible(t,dict(body=[dict(accepted_N=75,target_N=100)],pair_rate=.4)))
 def test_real_and_simulation_visual_evidence_mandatory(self):
  with self.assertRaises(PolicyError)as e:validate(self.path.parent,dict(attempts=[dict(path='attempts/001-G4_visualize-unit/result.json')]))
  self.assertEqual(e.exception.code,'ARTIFACT_MISSING')
 def test_high_variance_preserves_seed_direction_and_zero_mean(self):
  views=[dict(video=v)for v in ['004','005']for _ in range(8)];noise=noise_vectors(CONDITIONS,views,20261117)
  for v in ['004','005']:
   np.testing.assert_allclose(noise['C7'][v].mean(0),0,atol=1e-15);np.testing.assert_allclose(noise['C6'][v][:,:3],noise['C4'][v][:,:3]*(1.2/.7));np.testing.assert_allclose(noise['C7'][v][:,3:],noise['C4'][v][:,3:]*3)
 def test_native_pixel_center_resampling_is_not_naive_resize(self):
  K=np.array([[490.,0,319.5],[0,490.,179.5],[0,0,1.]]);A=np.diag([1.,352/360,1.]);A[1,2]=.5*352/360-.5;uv=np.array([[0,0],[319,175],[639,351]]);full=native_pixels(uv,A@K,K);np.testing.assert_array_equal(full,[[0,0],[319,179],[639,359]])
 def test_behind_camera_kept_as_anomaly_not_projected_as_valid(self):
  uv,z=safe_project(np.array([[1.,2.,-2.],[1,2,2.]]),np.eye(3),np.eye(4));self.assertFalse((z>0)[0]);self.assertTrue((z>0)[1]);self.assertTrue(np.isfinite(uv).all())
