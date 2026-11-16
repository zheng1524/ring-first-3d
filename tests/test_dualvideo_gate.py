"""Denial tests and analytic projection fixtures; never used as G01 assets."""
import copy,json,tempfile,unittest,subprocess,sys
from pathlib import Path
import numpy as np
import yaml
from ring_first_3d.policy.contracts import ROOT,PolicyError,load_task
from ring_first_3d.policy.dualvideo_contracts import permissions,verify,DUAL_STAGES
from ring_first_3d.dualvideo.audit import projection_metrics,passes,fixed_pose_certificate,check_sources
from ring_first_3d.dualvideo.artifacts import validate_artifacts

TASK=ROOT/'experiments/TASK-E4-G01-DUALVIDEO-BODY-ANCHORED-REGISTRATION-001/TASK.yaml'


class DualvideoGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.path=self.root/'TASK.yaml';self.raw=yaml.safe_load(TASK.read_text())

    def task(self):
        self.path.write_text(yaml.safe_dump(self.raw));return load_task(self.path)

    def reject(self,code):
        with self.assertRaises(PolicyError)as e:self.task()
        self.assertEqual(e.exception.code,code)

    def test_user_clarified_004_world_004_005_local_conditions(self):
        t=self.task();self.assertEqual(t['dualvideo']['conditions']['S1']['video'],'004')
        self.assertEqual(t['dualvideo']['conditions']['S4']['video'],'005')
        self.assertEqual(t['authorization']['stages'],list(DUAL_STAGES))

    def test_wrong_unit_denied(self):
        self.raw['variables']['geometry_unit']='m';self.reject('COORDINATES')

    def test_redirecting_world_error_to005_denied(self):
        self.raw['dualvideo']['conditions']['S1']['video']='005';self.reject('INJECTION_PROTOCOL')

    def test_extra_condition_denied(self):
        self.raw['dualvideo']['conditions']['S5']=dict(self.raw['dualvideo']['conditions']['S1']);self.reject('INJECTION_PROTOCOL')

    def test_gate_bypass_denied(self):
        self.raw['authorization']['stages'].remove('G0_scene_audit');self.reject('AUTHORIZATION')

    def test_weak_projection_tolerance_denied(self):
        self.raw['dualvideo']['gates']['observed_to_full_CAD_boundary_p95_px_max']=999;self.reject('SCENE_GATE')

    def test_gt_body_substitution_denied(self):
        self.raw['dualvideo']['body_initialization']='Original Blender mesh';self.reject('GT_LEAK')

    def test_asset_SHA_mismatch_denied(self):
        t=self.task();t['dualvideo']['assets']['source_manifest']['sha256']='0'*64
        with self.assertRaises(PolicyError)as e:verify(t)
        self.assertEqual(e.exception.code,'SOURCE_SHA')

    def test_predictor_has_no_scene_GT_permission(self):
        t=self.task();self.assertFalse(permissions(t,'G1_initialize',self.root)['allow_GT'])
        self.assertTrue(permissions(t,'G0_scene_audit',self.root)['allow_GT'])

    def test_shape_identity_and_shared_ring_bytes_cannot_certify_pose(self):
        result=fixed_pose_certificate(dict(objects=[dict(name='球体',type='MESH')]),dict(shared_world_certified=False))
        self.assertEqual(result['status'],'NOT_EVALUABLE');self.assertIsNone(result['transform'])

    def test_projection_matched_and_unmatched_regions(self):
        mask=np.zeros((30,30),bool);mask[10:20,10:20]=True
        m=projection_metrics(mask,mask);self.assertEqual(m['support_within2px'],1.);self.assertEqual(m['observed_to_CAD_boundary_p95_px'],0.)
        other=np.roll(mask,10,axis=0);m=projection_metrics(mask,other)
        self.assertGreater(m['unmatched_observed_pixels'],0);self.assertLess(m['support_within2px'],.95)
        self.assertFalse(passes(m,self.raw['dualvideo']['gates']))

    def test_no_observed_or_projected_ring_denied(self):
        mask=np.zeros((30,30),bool);m=projection_metrics(mask,mask)
        self.assertIsNone(m['support_within2px']);self.assertFalse(passes(m,self.raw['dualvideo']['gates']))

    def test_missing_scene_visualization_denied(self):
        with self.assertRaises(PolicyError)as e:validate_artifacts(self.root,dict(attempts=[],dualvideo_files={'scene.html':dict(sha256='0'*64,bytes=10)}))
        self.assertEqual(e.exception.code,'ARTIFACT_MISSING')

    def test_bound_original_native_camera_not_corrected_cache(self):
        m=json.loads(Path(self.raw['dualvideo']['assets']['source_manifest']['path']).read_text())
        # Source provenance is independently checked, not accepted from YAML alone.
        r=copy.deepcopy(m['rows'][0]);r['Camera_to_Ring'][0][3]+=.1
        with self.assertRaises(PolicyError)as e:check_sources(r)
        self.assertEqual(e.exception.code,'CAMERA_BINDING')

    def test_initialization_worker_denies_GT_read(self):
        t=self.task();p=permissions(t,'G1_initialize',self.root)
        p['gt_paths']=[str(x)for x in p['gt_paths']];p['run_root']=str(p['run_root'])
        code='''import sys,json
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from _policy_worker import install_io_guard
from ring_first_3d.policy.contracts import PolicyError
p=json.loads(sys.argv[2]);p['gt_paths']=[Path(x)for x in p['gt_paths']];p['run_root']=Path(p['run_root'])
install_io_guard(Path(sys.argv[3]),p)
try:Path(p['gt_paths'][0]).read_bytes()
except PolicyError as e:print(e.code)
'''
        r=subprocess.run([sys.executable,'-c',code,str(ROOT/'tools/research'),json.dumps(p),str(self.root)],capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(r.stdout.strip(),'GT_LEAK')
