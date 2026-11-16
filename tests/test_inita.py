"""Exact source/initialization, view weights, GT-copy and Mesh-adapter contracts."""
import json,copy,tempfile,unittest,ast,hashlib
from pathlib import Path
import numpy as np,yaml
from ring_first_3d.policy.contracts import ROOT,load_task,PolicyError,stages_for
from ring_first_3d.policy.inita_contracts import TASK_ID,INIT_STAGES,permissions,verify
from ring_first_3d.inita.hero import mesh_ellipse,inherited_mesh_optimizer
from ring_first_3d.multisurface.registration import optimize
from ring_first_3d.inita.artifacts import validate
class InitAContracts(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.p=Path(self.tmp.name)/'TASK.yaml';self.raw=yaml.safe_load((ROOT/'experiments'/TASK_ID/'TASK.yaml').read_text())
 def task(self):self.p.write_text(yaml.safe_dump(self.raw));return load_task(self.p)
 def reject(self,code):
  with self.assertRaises(PolicyError)as e:self.task()
  self.assertEqual(e.exception.code,code)
 def test_stages_smoke_both_parts_before_expansion(self):self.assertEqual(stages_for(self.task()),INIT_STAGES)
 def test_no_ellipsoid_initialization_substitution(self):self.raw['inita']['initialization']='E1_ELLIPSOID';self.reject('INITIALIZATION_LINEAGE')
 def test_original_optimizer_budget_not_shortened(self):self.raw['inita']['training_budget']['max_accepted']=5;self.reject('FROZEN_PROTOCOL')
 def test_evaluator_transform_may_not_enter_HERO(self):self.raw['inita']['HERO_uses_GT_aligned_Body']=True;self.reject('GT_LEAK')
 def test_no_per_frame_camera_variables(self):self.raw['inita']['camera_parameters']='free_frame_cameras';self.reject('CAMERA_SCOPE')
 def test_all11_physical_groups_required(self):self.raw['inita']['cases'].pop();self.reject('DATA_ISOLATION')
 def test_cannot_skip_source_gate(self):self.raw['authorization']['stages'].remove('G0_sources');self.reject('AUTHORIZATION')
 def test_source_sha_cannot_drift(self):
  t=self.task();t['inita']['assets']['sources']['sha256']='0'*64
  with self.assertRaises(PolicyError)as e:verify(t)
  self.assertEqual(e.exception.code,'SOURCE_SHA')
 def test_GT_metadata_denied_predictor_allowed_evaluator(self):
  t=self.task();p=permissions(t,'G2_smoke_hero',self.p.parent);self.assertFalse(p['allow_GT']);self.assertIn(Path(t['inita']['assets']['GT_metadata']['path']),p['gt_paths']);self.assertTrue(permissions(t,'G3_all_evaluate',self.p.parent)['allow_GT'])
 def test_surface_optimizer_bytecode_is_unchanged(self):self.assertEqual(inherited_mesh_optimizer().__code__.co_code,optimize.__code__.co_code)
 def test_actual_mesh_projection_does_not_require_ellipsoid_parameters(self):
  import trimesh
  mesh=trimesh.creation.icosphere(subdivisions=1,radius=2.);V=np.asarray(mesh.vertices)+[0,0,20];K=np.array([[100.,0,50],[0,100.,50],[0,0,1.]]);c,M,a,curve=mesh_ellipse(V,np.asarray(mesh.faces),K,np.eye(4));np.testing.assert_allclose(c,[50,50],atol=1e-3);self.assertTrue((np.linalg.eigvalsh(M)>0).all());self.assertEqual(curve.shape,(128,2))
 def test_exact_013_lineage_and_G08_missing004_preserved(self):
  d=json.loads(Path(self.raw['inita']['assets']['sources']['path']).read_text());g=next(r for r in d['cases']if r['case']=='G08');self.assertTrue(g['status'].startswith('NOT_EVALUABLE'));self.assertFalse(any(v['meta']['video']=='004'for v in g['FIT']))
  for row in d['cases']:
   a=np.load(row['initial']['path']);b=np.load(row['resolved013_initial']['path']);np.testing.assert_array_equal(a['V'],b['V']);np.testing.assert_array_equal(a['F_solid'],b['F_solid'])
 def test_actual_GT_and_HERO_artifacts_required(self):
  with self.assertRaises(PolicyError)as e:validate(self.p.parent,dict(attempts=[dict(path='attempts/001-G4_visualize-test/result.json')]))
  self.assertEqual(e.exception.code,'ARTIFACT_MISSING')
