"""Analytic fixtures verify contracts; never stand in for real G01 assets."""
import copy,json,tempfile,subprocess,sys,unittest
from pathlib import Path
import numpy as np
import yaml
from scipy.spatial.transform import Rotation
from ring_first_3d.policy.contracts import ROOT,load_task,PolicyError
from ring_first_3d.policy.fusion_contracts import TASK_ID,FUSION_STAGES,verify,permissions
from ring_first_3d.multisurface.geometry import depth_grid_mesh,transform,se3,mesh_sections,distribution
from ring_first_3d.multisurface.scene import noise_vectors
from ring_first_3d.multisurface.registration import body_residual
from ring_first_3d.multisurface.fusion import body_chart,owned_model
from ring_first_3d.multisurface.evaluate import fixed_stats
from ring_first_3d.multisurface.artifacts import validate


class MultisurfaceContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.path=self.root/'TASK.yaml';self.raw=yaml.safe_load((ROOT/'experiments'/TASK_ID/'TASK.yaml').read_text())
    def task(self):self.path.write_text(yaml.safe_dump(self.raw));return load_task(self.path)
    def reject(self,code):
        with self.assertRaises(PolicyError)as e:self.task()
        self.assertEqual(e.exception.code,code)
    def test_new_task_has_full_stages_and_both_bodies(self):
        t=self.task();self.assertEqual(t['authorization']['stages'],list(FUSION_STAGES));self.assertEqual(t['fusion']['body_arms'],['E1','E2'])
    def test_no_GT_triangle_union_as_independent_observations(self):
        self.raw['fusion']['mesh_builder']='GT_face_union';self.reject('MESH_SOURCE')
    def test_no_camera_optimization(self):
        self.raw['fusion']['camera_optimization']=True;self.reject('GT_LEAK')
    def test_wrong_units(self):
        self.raw['variables']['geometry_unit']='m';self.reject('COORDINATES')
    def test_cannot_skip_smoke_evaluation(self):
        self.raw['authorization']['stages'].remove('G3_smoke_evaluate');self.reject('AUTHORIZATION')
    def test_noise_variance_not_retuned(self):
        self.raw['fusion']['conditions']['C4']['sigma']['005']=[1.,.3];self.reject('INJECTION_PROTOCOL')
    def test_tolerance_ablation_and_main_tolerance_frozen(self):
        self.raw['fusion']['tolerance_mm']=.1;self.reject('FROZEN_PROTOCOL')
    def test_fixed_four_actual_section_planes(self):
        self.raw['fusion']['sections'][2]['offset_mm']=-3.;self.reject('FROZEN_PROTOCOL')
    def test_source_sha_rejected_before_private_asset_access(self):
        t=self.task();t['fusion']['assets']['source_manifest']['sha256']='0'*64
        with self.assertRaises(PolicyError)as e:verify(t)
        self.assertEqual(e.exception.code,'SOURCE_SHA')
    def test_predictor_does_not_receive_parent_clean_pose_or_GT(self):
        t=self.task();p=permissions(t,'G3_all_predict',self.root);self.assertFalse(p['allow_GT']);self.assertIn(Path(t['fusion']['parent_run']).resolve(),p['denied_read_prefixes']);self.assertTrue(permissions(t,'G4_evaluate',self.root)['allow_GT'])
    def test_first_figure_and_owned_full_mesh_artifacts_required(self):
        with self.assertRaises(PolicyError)as e:validate(self.root,dict(attempts=[dict(path='attempts/001-G4_visualize-unit/result.json')],multisurface_files={}))
        self.assertEqual(e.exception.code,'ARTIFACT_MISSING')
    def test_IO_guard_blocks_GT_inverse_and_source_manifest(self):
        target=self.root/'latent_error.txt';target.write_text('unit-only');clean=self.root/'cleanposes';clean.mkdir();(clean/'pose.json').write_text('{}');(self.root/'output').mkdir()
        code='''import sys,json
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from _policy_worker import install_io_guard
from ring_first_3d.policy.contracts import PolicyError
r=Path(sys.argv[2]);install_io_guard(r/'output',dict(role='predictor',allow_GT=False,gt_paths=[r/'latent_error.txt'],run_root=r,denied_read_prefixes=[r/'cleanposes']))
for p in [r/'latent_error.txt',r/'cleanposes/pose.json']:
 try:p.read_text()
 except PolicyError as e:print(e.code)
'''
        r=subprocess.run([sys.executable,'-c',code,str(ROOT/'tools/research'),str(self.root)],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(r.stdout.splitlines(),['GT_LEAK','CLEAN_POSE_LEAK'])


class IndependentGeometryTests(unittest.TestCase):
    def test_depth_grid_mesh_from_pixels_has_no_GT_face_identity(self):
        K=np.array([[10.,0,4],[0,10,4],[0,0,1.]]);z=np.full((10,10),10.);labels=np.ones((10,10),np.uint8);m,a=depth_grid_mesh(z,labels,K,2,5.)
        self.assertEqual(set(m),{'V','F','uv'});self.assertEqual(len(m['V']),25);self.assertEqual(len(m['F']),32);np.testing.assert_allclose(m['V'][:,2],10.)
        np.testing.assert_allclose(m['V'][:,:2],m['uv']-4);self.assertNotIn('gt_face',m)
    def test_depth_discontinuities_do_not_bridge_foreground_surfaces(self):
        K=np.eye(3);K[0,0]=K[1,1]=100;z=np.full((8,8),10.);z[:,4:]=30.;labels=np.ones((8,8),np.uint8);m,a=depth_grid_mesh(z,labels,K,1,1.)
        self.assertGreater(a['depth_discontinuity_triangles_rejected'],0);self.assertTrue((np.ptp(m['V'][m['F']][:,:,2],axis=1)<1.).all())
    def test_pose_error_action_has_both_left_bias_and_right_frame_noise(self):
        C=se3([.1,-.2,.3,4,5,30]);D=se3([0,np.deg2rad(2),0,.5,0,0]);N=se3([.01,.02,-.01,.1,-.2,.1]);P=np.array([[1.,2.,12.],[0,0,20.]])
        expected=transform(transform(transform(P,N),C),D);np.testing.assert_allclose(transform(P,D@C@N),expected)
        self.assertGreater(np.linalg.norm(expected-transform(P,D@C)),.1)
    def test_centered_noise_covariance_and_common_random_numbers(self):
        views=[dict(video=v)for v in ['004','005']for _ in range(8)];c={'L':dict(sigma={'004':[.3,.1],'005':[.3,.1]}),'H':dict(sigma={'004':[.7,.2],'005':[.7,.2]})};noise=noise_vectors(c,views,20261117)
        for v in ['004','005']:
            np.testing.assert_allclose(noise['L'][v].mean(0),0,atol=1e-16);np.testing.assert_allclose(noise['H'][v][:,:3],noise['L'][v][:,:3]*(.7/.3));np.testing.assert_allclose(noise['H'][v][:,3:],noise['L'][v][:,3:]*2)
            stats=distribution(noise['L'][v]);np.testing.assert_allclose(stats['empirical_covariance_ddof1'],np.cov(noise['L'][v],rowvar=False))
    def test_body_region_tolerance_does_not_force_observed_points_to_ellipsoid(self):
        delta=np.array([[.3,0,0],[.8,0,0],[0,0,0]]);r=body_residual(delta,.5);np.testing.assert_allclose(r,[[0,0,0],[.3,0,0],[0,0,0]])
    def test_exact_triangle_plane_intersection(self):
        V=np.array([[-1.,0,0],[1,0,0],[1,2,0]]);F=np.array([[0,1,2]]);s=mesh_sections(V,F,0,0.)
        self.assertEqual(s.shape,(1,2,3));np.testing.assert_allclose(s[:,:,0],0.);self.assertAlmostEqual(np.linalg.norm(s[0,1]-s[0,0]),1.)
        self.assertEqual(len(mesh_sections(V,F,0,20.)),0)
    def test_failed_targets_are_kept_in_denominator(self):
        s=fixed_stats([1.,np.nan,2.]);self.assertEqual(s['target_N'],3);self.assertEqual(s['numeric_N'],2);self.assertEqual(s['failed_N'],1)


class OwnershipTests(unittest.TestCase):
    def setUp(self):
        self.body=dict(p=np.zeros(9),R0=np.eye(3));V,F=body_chart(self.body,16,12);self.body.update(V=V,F=F)
        self.cfg=dict(fusion_min_incidence=.15,fusion_consensus_mm=.25,fusion_min_support=2,fusion_max_seam_jump_mm=8.)
    def test_measured_owner_equals_one_source_triangle_not_average_or_Body(self):
        V,F=self.body['V'],self.body['F'];meshes=[dict(V=V*1.1,F=F),dict(V=V*1.15,F=F)];old=[m['V'].copy()for m in meshes]
        model,own,stats=owned_model(self.body,meshes,['004','005'],self.cfg);valid=own['owner']>=0;self.assertTrue(valid.any());ix=np.where(valid)[0];winner=own['owner'][valid]
        np.testing.assert_allclose(model['V'][valid],own['candidate_points'][winner,ix],atol=1e-12)
        self.assertEqual(len(np.unique(own['base_face_ids'])),len(model['F']));self.assertTrue(stats['no_average_coordinates'])
        for before,m in zip(old,meshes):np.testing.assert_array_equal(before,m['V'])
    def test_overlap_conflicts_remain_explicit_with_original_candidates(self):
        V,F=self.body['V'],self.body['F'];meshes=[dict(V=V*r,F=F)for r in [1.1,1.11,1.7,1.71]];model,own,stats=owned_model(self.body,meshes,['004','004','005','005'],self.cfg)
        self.assertGreater(stats['overlap_conflict_vertices'],0);self.assertTrue(own['conflict'].any());self.assertGreater(own['spread_mm'].max(),.5);self.assertEqual(own['candidate_points'].shape[0],4)
    def test_chart_does_not_optimize_frozen_body_parameters(self):
        p=self.body['p'].copy();R=self.body['R0'].copy();V,F=body_chart(self.body);np.testing.assert_array_equal(p,self.body['p']);np.testing.assert_array_equal(R,self.body['R0']);np.testing.assert_allclose(np.linalg.norm(V,axis=1),1.,atol=1e-12)
