"""Analytic contract tests are unit fixtures, never substitute G01 science data."""
import copy,json,tempfile,unittest,subprocess,sys
from pathlib import Path
import numpy as np
import yaml
from scipy.spatial.transform import Rotation
from ring_first_3d.policy.contracts import ROOT,PolicyError,load_task
from ring_first_3d.policy.sim_contracts import TASK_ID,SIM_STAGES,permissions,verify
from ring_first_3d.sim.geometry import error_transform,transform,rigid_fit,pose_error
from ring_first_3d.sim.registration import ring_only
from ring_first_3d.sim.mapping import candidates
from ring_first_3d.sim.legacy import namespace
from ring_first_3d.sim.artifacts import validate


class SimProtocolTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.path=self.root/'TASK.yaml'
        self.raw=yaml.safe_load((ROOT/'experiments'/TASK_ID/'TASK.yaml').read_text())

    def task(self):self.path.write_text(yaml.safe_dump(self.raw));return load_task(self.path)

    def denied(self,code):
        with self.assertRaises(PolicyError)as e:self.task()
        self.assertEqual(e.exception.code,code)

    def test_explicit_review_revision_and_full_handlers_authorized(self):
        t=self.task();self.assertFalse(t['sim']['realism_is_blocking']);self.assertTrue(t['sim']['internal_geometry_is_blocking']);self.assertEqual(t['authorization']['stages'],list(SIM_STAGES))

    def test_latest_world_condition_matrix_is_not_old_protocol(self):
        t=self.task();self.assertEqual(t['sim']['conditions']['S1'],{'004':'I','005':'A'});self.assertEqual(t['sim']['conditions']['S4'],{'004':'A','005':'A'})

    def test_axis_change_is_rejected(self):
        self.raw['sim']['error_axis']=[1.,0.,0.];self.denied('INJECTION_PROTOCOL')

    def test_matrix_change_is_rejected(self):
        self.raw['sim']['conditions']['S2']['004']='B';self.denied('INJECTION_PROTOCOL')

    def test_wrong_units_rejected(self):
        self.raw['variables']['geometry_unit']='m';self.denied('COORDINATES')

    def test_GT_body_and_unfrozen_body_rejected(self):
        self.raw['sim']['body_frozen_during_registration']=False;self.denied('GT_LEAK')

    def test_cannot_skip_Smoke(self):
        self.raw['authorization']['stages'].remove('G3_smoke_evaluate');self.denied('AUTHORIZATION')

    def test_public_source_SHA_mismatch_rejected_before_GT(self):
        t=self.task();t['sim']['assets']['source_manifest']['sha256']='0'*64
        with self.assertRaises(PolicyError)as e:verify(t)
        self.assertEqual(e.exception.code,'SOURCE_SHA')

    def test_GT_roles_and_clean_pose_denial(self):
        t=self.task();self.assertFalse(permissions(t,'G1_initialize',self.root)['allow_GT']);self.assertTrue(permissions(t,'G1_evaluate',self.root)['allow_GT'])
        (self.root/'attempts/0001-G0_simulate-unit/public/initialization').mkdir(parents=True)
        self.assertTrue(permissions(t,'G3_matrix_predict',self.root)['denied_read_prefixes'])

    def test_missing_full_mesh_visualization_rejected(self):
        with self.assertRaises(PolicyError)as e:validate(self.root,dict(attempts=[dict(path='attempts/001-G4_visualize-unit/result.json')],sim_files={}))
        self.assertEqual(e.exception.code,'ARTIFACT_MISSING')

    def test_reused_nine_parameter_model_and_original_solver(self):
        ns=namespace(self.task());p=np.r_[0.,0.,10.,0.,0.,0.,np.log([2.,2.,3.])];V,F=ns['mesh'](p,np.eye(3),False)
        self.assertEqual(len(p),9);self.assertTrue(np.isfinite(V).all());self.assertEqual(F.shape[1],3)
        self.assertTrue(any(r['name']=='Problem.solve'and r['mathematics_modified']is False for r in ns['reuse_receipts']))

    def test_mediated_mapping_changes_query_and_retains_barycentric_point(self):
        ns=namespace(self.task());p=np.r_[0.,0.,10.,0.,0.,0.,np.log([2.,2.,3.])];V,F=ns['mesh'](p,np.eye(3),False)
        K=np.array([[100.,0,32],[0,100,32],[0,0,1.]]);body=dict(V=V,F=F,p=p,R0=np.eye(3));fit=dict(center_px=[40.,32.],basis_px=np.diag([22.,22.]))
        uv=np.array([[40.,32.],[50.,32.]])
        m=candidates(uv,fit,body,K,np.eye(4),ns)
        self.assertTrue(m['valid'].all());self.assertGreater(m['displacement_px'].mean(),1.)
        np.testing.assert_allclose(np.einsum('ni,nij->nj',m['bary'],V[F[m['face']]]),m['points'])

    def test_predictor_IO_guard_denies_GT_and_clean_pose(self):
        attempt=self.root/'output';attempt.mkdir();clean=self.root/'clean';clean.mkdir();(clean/'camera.json').write_text('{}')
        code='''import sys,json
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from _policy_worker import install_io_guard
from ring_first_3d.policy.contracts import PolicyError
r=Path(sys.argv[2]);install_io_guard(r/'output',dict(role='predictor',allow_GT=False,gt_paths=[],run_root=r,denied_read_prefixes=[r/'clean']))
try:(r/'clean/camera.json').read_text()
except PolicyError as e:print(e.code)
'''
        p=subprocess.run([sys.executable,'-c',code,str(ROOT/'tools/research'),str(self.root)],capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(p.stdout.strip(),'CLEAN_POSE_LEAK')


class RigidGeometryTests(unittest.TestCase):
    def test_world_error_preserves_camera_to_Ring_and_pairwise_poses(self):
        D=error_transform(2,.5);C=np.eye(4);C[:3,3]=[2,3,30];B=C.copy();B[0,3]+=4
        np.testing.assert_allclose(np.linalg.inv(D)@(D@C),C,atol=1e-12)
        np.testing.assert_allclose(np.linalg.inv(D@C)@(D@B),np.linalg.inv(C)@B,atol=1e-12)
        self.assertAlmostEqual(pose_error(D)['rotation_deg'],2.);self.assertAlmostEqual(pose_error(D)['translation_mm'],.5)

    def test_shared_world_gauge_S4_has_zero_relative_error(self):
        D=error_transform(2,.5);e=pose_error(np.linalg.inv(D)@D);self.assertLess(e['rotation_deg'],1e-12);self.assertLess(e['translation_mm'],1e-12)

    def test_full_mesh_rigid_transform_preserves_topology_and_edges(self):
        V=np.array([[0.,0,0],[1,0,0],[0,1,0],[0,0,1]]);F=np.array([[0,1,2],[1,2,3]]);T=error_transform(3,.3);W=transform(V,T)
        np.testing.assert_allclose(np.linalg.norm(V[F[:,1]]-V[F[:,0]],axis=1),np.linalg.norm(W[F[:,1]]-W[F[:,0]],axis=1))
        np.testing.assert_allclose(transform(W,rigid_fit(W,V)),V,atol=1e-12)

    def test_ring_control_recovers_tilt_without_body_or_GT(self):
        theta=np.linspace(0,2*np.pi,300,endpoint=False);V=np.c_[5.6*np.cos(theta),5.6*np.sin(theta),np.zeros(len(theta))];D=error_transform(2,.5)
        X=ring_only(transform(V,D));np.testing.assert_allclose(X@D,np.eye(4),atol=1e-12)
