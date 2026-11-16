"""Analytic geometry tests are unit cases only, never substituted for real G01."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import numpy as np
import yaml
from scipy.spatial.transform import Rotation
from ring_first_3d.policy.contracts import ROOT,PolicyError,load_task,stages_for
from ring_first_3d.policy.science_contracts import SCIENCE_STAGES,permissions,verify
from ring_first_3d.synthetic.correspondence import inject,correspond
from ring_first_3d.synthetic.raster import rasterize,closest,independent_rays
from ring_first_3d.contracts.coordinates import unproject

TASK=ROOT/'experiments/TASK-E4-SYNTHETIC-BODY-PIXEL-CORRESPONDENCE-001/TASK.yaml'


class ScienceProtocolTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'TASK.yaml';self.raw=yaml.safe_load(TASK.read_text())

    def save(self):
        self.path.write_text(yaml.safe_dump(self.raw));return load_task(self.path)

    def assert_rejected(self,code):
        with self.assertRaises(PolicyError)as error:self.save()
        self.assertEqual(error.exception.code,code)

    def test_scientific_schema_role_and_stages(self):
        task=self.save();self.assertEqual(stages_for(task),SCIENCE_STAGES)
        self.assertFalse(permissions(task,'C1_predict',Path(self.tmp.name))['allow_GT'])
        self.assertTrue(permissions(task,'C1_evaluate',Path(self.tmp.name))['allow_GT'])

    def test_no_G2_authorization(self):
        self.raw['authorization']['stages'].append('G2_optimize')
        self.assert_rejected('AUTHORIZATION')

    def test_no_extra_conditions_or_retuning(self):
        self.raw['science']['conditions']['C1']['depth_bias_mm']=2.
        self.assert_rejected('INJECTION_PROTOCOL')

    def test_no_invented_G01_initialization(self):
        self.raw['science']['body_initialization']='temporary_ellipsoid'
        self.assert_rejected('SCIENCE_SCOPE')

    def test_public_corruption_has_no_clean_pose_or_depth(self):
        from ring_first_3d.synthetic.scene import observation
        data=observation(np.array([[32.,31]]),np.array([5.]),np.array([[100.,0,31.5],[0,100,31.5],[0,0,1.]]),np.eye(4),dict(depth_bias_mm=1.,rotation_y_deg=2.,translation_x_mm=.5),'FIT',np.ones((64,64),bool))
        self.assertFalse({'T','z','z_true','P_true','face','bary'}&set(data))
        np.testing.assert_array_equal(data['z_observed'],[6.])
        self.assertIn('T_estimated',data)

    def test_atomic_science_publish_uses_new_attempt_before_pointer_advance(self):
        from ring_first_3d.synthetic.artifacts import enhance
        from ring_first_3d.contracts.identities import sha256
        import shutil
        root=Path(self.tmp.name);pending=root/'snapshot_pending';(pending/'visualization').mkdir(parents=True)
        (root/'RUN_MANIFEST.json').write_text('{"attempts":[]}')
        (pending/'metrics.json').write_text('{}');(pending/'RESULT_CARD.md').write_text('UNIT ONLY');(pending/'TECHNICAL_REPORT.md').write_text('UNIT ONLY')
        (pending/'visualization/index.html').write_text('<html><svg></svg><h2>Registered real regression evidence</h2>')
        folder=root/'attempts/unit-G1_visualize';(folder/'figures').mkdir(parents=True)
        image=Path(self.raw['inputs']['evidence']['path']);shutil.copyfile(image,folder/'figures/01_scene.png')
        shutil.copyfile(image,pending/'evidence.png');(folder/'PIXEL_FACE_AUDIT.csv').write_text('unit_only\n')
        files={name:dict(sha256=sha256(folder/name),bytes=(folder/name).stat().st_size)for name in ['figures/01_scene.png','PIXEL_FACE_AUDIT.csv']}
        latest={'G1_visualize':dict(status='PASS',attempt_id='unit-G1_visualize',payload=dict(figures={'01_scene.png':'unit-only atomic publication'},rows=[],files=files))}
        state={};enhance(root,self.save(),state,latest,pending)
        self.assertIn('01_scene.png',state['scientific_figures'])
        self.assertTrue((pending/'visualization/01_scene.png').is_file())

    def test_missing_real_asset_NOT_EVALUABLE(self):
        task=self.save();task['science']['assets']['blend']['path']='/missing-real-G01.blend'
        with self.assertRaises(PolicyError)as e:verify(task)
        self.assertEqual(e.exception.code,'NOT_EVALUABLE')

    def test_prediction_cannot_read_private_or_prior_evaluation(self):
        root=Path(self.tmp.name);attempt=root/'attempt';attempt.mkdir();private=root/'private';private.mkdir();(private/'truth.npz').write_bytes(b'unit-role-denial-only')
        # The enclosing verification worker must not resolve shutil's fd-relative
        # directory-open "private" against its cwd during unit fixture cleanup.
        # Rename only our disposable unit fixture before TemporaryDirectory cleanup.
        self.addCleanup(lambda:private.rename(root/'unit_role_fixture_complete'))
        evaldir=root/'0008-C0_evaluate-unit';evaldir.mkdir();(evaldir/'metrics.json').write_text('{}')
        code='''import sys,json
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from _policy_worker import install_io_guard
from ring_first_3d.policy.contracts import PolicyError
root=Path(sys.argv[2]);install_io_guard(root/'attempt',dict(role='predictor',gt_paths=[],run_root=root,allow_GT=False))
codes=[]
for p in [root/'private/truth.npz',root/'0008-C0_evaluate-unit/metrics.json']:
 try:p.read_bytes()
 except PolicyError as e:codes.append(e.code)
print(json.dumps(codes))
'''
        p=subprocess.run([sys.executable,'-c',code,str(ROOT/'tools/research'),str(root)],capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(json.loads(p.stdout),['GT_LEAK','GT_LEAK'])


class InjectionGeometryTests(unittest.TestCase):
    def setUp(self):
        self.K=np.array([[100.,0,32],[0,100,32],[0,0,1.]])
        self.T=np.eye(4);self.T[:3,:3]=Rotation.from_euler('x',23,degrees=True).as_matrix();self.T[:3,3]=[4,5,6]
        self.uv=np.array([[10.,20],[32,32],[50,40]]);self.z=np.array([10.,15.,20.])

    def test_C0_roundtrip(self):
        p,t,r=inject(self.uv,self.z,self.K,self.T,dict(depth_bias_mm=0.,rotation_y_deg=0.,translation_x_mm=0.))
        np.testing.assert_allclose(p,unproject(self.uv,self.z,self.K,self.T));np.testing.assert_allclose(t,self.T)

    def test_C1_actual_axial_not_range(self):
        p,_,_=inject(self.uv,self.z,self.K,self.T,dict(depth_bias_mm=1.,rotation_y_deg=0.,translation_x_mm=0.))
        delta=(p-unproject(self.uv,self.z,self.K,self.T))@self.T[:3,:3]
        np.testing.assert_allclose(delta[:,2],1.,atol=1e-12)
        self.assertGreater(np.linalg.norm(delta[0]),1.)

    def test_C3_right_local_pose(self):
        old=self.T.copy();z=self.z.copy()
        p,t,r=inject(self.uv,self.z,self.K,self.T,dict(depth_bias_mm=0.,rotation_y_deg=2.,translation_x_mm=.5))
        relative=np.linalg.inv(self.T)@t
        np.testing.assert_allclose(relative[:3,3],[.5,0,0],atol=1e-12)
        self.assertAlmostEqual(np.degrees(Rotation.from_matrix(relative[:3,:3]).magnitude()),2.)
        np.testing.assert_array_equal(self.T,old);np.testing.assert_array_equal(self.z,z)


class PixelSurfaceTests(unittest.TestCase):
    def setUp(self):
        self.V=np.array([[-2.,-2,5],[2,-2,5],[2,2,5],[-2,2,5]])
        self.F=np.array([[0,1,2],[0,2,3]])
        self.K=np.array([[100.,0,31.5],[0,100,31.5],[0,0,1.]])
        self.T=np.eye(4)

    def test_metric_pixel_barycentric_and_independent_engine(self):
        r=rasterize(self.V,self.F,self.K,self.T,(64,64));q=r['points'][31,32]
        np.testing.assert_allclose(q,[.025,-.025,5.],atol=1e-5)
        self.assertAlmostEqual(float(r['bary'][31,32].sum()),1.,places=5)
        z=independent_rays(self.V,self.F,np.array([[32,31]]),self.K,self.T)
        np.testing.assert_allclose(z,[5.],atol=1e-5)

    def test_closest_surface_is_not_closest_vertex(self):
        q=closest(self.V,self.F,np.array([[.31,.22,6.]]))
        np.testing.assert_allclose(q['points'],[[.31,.22,5]],atol=1e-6)
        self.assertGreater(np.linalg.norm(self.V-q['points'][0],axis=1).min(),1.)

    def test_Ring_occlusion_retains_NaN(self):
        ring=self.V.copy();ring[:,2]=4.
        uv=np.array([[32,31]]);P=unproject(uv,np.array([6.]),self.K,self.T)
        out,_=correspond(self.V,self.F,ring,self.F,uv,P,self.K,self.T,(64,64))
        self.assertTrue(out['pixel_face']['valid'][0]);self.assertFalse(out['pixel_face_ring']['valid'][0])
        self.assertTrue(np.isnan(out['pixel_face_ring']['points']).all());self.assertEqual(out['pixel_face_ring']['face'][0],-1)

    def test_shared_edge_missing_pixels_are_not_hidden(self):
        from ring_first_3d.synthetic.raster import ray_map
        gt=ray_map(self.V,self.F,self.K,self.T,(64,64));r=rasterize(self.V,self.F,self.K,self.T,(64,64))
        missing=gt['valid']&~r['valid']
        self.assertEqual(int(gt['valid'].sum()),4096)
        self.assertTrue(np.isnan(r['points'][missing]).all())


if __name__=='__main__':unittest.main()
