"""Calibrated gradients, detached assignments, visibility, protocol and no depth leakage."""
import copy,json,tempfile,unittest,inspect
from pathlib import Path
import numpy as np,yaml
from ring_first_3d.policy.contracts import ROOT,load_task,PolicyError,stages_for
from ring_first_3d.policy.contour_contracts import TASK_ID,CONTOUR_STAGES,permissions,verify
from ring_first_3d.contour_guided.correspondence import project,project_torch,explicit_pairs,target_boundary
from ring_first_3d.contour_guided.hero import optimizer,mesh_candidates,CONFIG
from ring_first_3d.multisurface.registration import optimize
from ring_first_3d.contour_guided.artifacts import validate

class ContourContracts(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.path=Path(self.tmp.name)/'TASK.yaml';self.raw=yaml.safe_load((ROOT/'experiments'/TASK_ID/'TASK.yaml').read_text())
 def task(self):self.path.write_text(yaml.safe_dump(self.raw));return load_task(self.path)
 def reject(self,code):
  with self.assertRaises(PolicyError)as e:self.task()
  self.assertEqual(e.exception.code,code)
 def test_stages_before_all_groups(self):self.assertEqual(stages_for(self.task()),CONTOUR_STAGES)
 def test_no_new_camera_parameters(self):self.raw['contour']['camera_parameters']='SHARED_005';self.reject('CAMERA_SCOPE')
 def test_no_HERO_depth_loss(self):self.raw['contour']['A3_depth_loss']=True;self.reject('CAMERA_SCOPE')
 def test_no_Body_update_after_freeze(self):self.raw['contour']['HERO_updates_Body']=True;self.reject('CAMERA_SCOPE')
 def test_no_changed_budget(self):self.raw['inita']['training_budget']['max_proposals']=81;self.reject('FROZEN_PROTOCOL')
 def test_no_new_initial_body(self):self.raw['inita']['initialization']='TRAINED_A2';self.reject('INITIALIZATION_LINEAGE')
 def test_no_captured_range_tuning(self):self.raw['contour']['pairing']['max_distance_px']=80.;self.reject('FROZEN_PROTOCOL')
 def test_all11_retained(self):self.raw['inita']['cases'].pop();self.reject('DATA_ISOLATION')
 def test_GT_copy_excluded(self):self.raw['inita']['HERO_uses_GT_aligned_Body']=True;self.reject('GT_LEAK')
 def test_source_SHA_rejection(self):
  t=self.task();t['inita']['assets']['sources']['sha256']='0'*64
  with self.assertRaises(PolicyError)as e:verify(t)
  self.assertEqual(e.exception.code,'SOURCE_SHA')
 def test_training_denies_depth_and_GT(self):
  t=self.task();p=permissions(t,'G1_all_train',self.path.parent);s=json.loads(Path(t['inita']['assets']['sources']['path']).read_text());depth=[Path(r['path'])for c in s['cases']for r in c['depth'].values()];self.assertFalse(p['allow_GT']);self.assertTrue(set(depth)<=set(p['denied_read_prefixes']));self.assertTrue(permissions(t,'G3_all_evaluate',self.path.parent)['allow_GT'])
 def test_all_four_body_mapping_controls(self):self.assertEqual(self.task()['contour']['HERO_methods'],['M0','H1','H2','H3','H4','ICP'])
 def test_HERO_optimizer_bytecode_identical(self):self.assertEqual(optimizer().__code__,optimize.__code__)
 def test_projection_gradient_has_calibrated_pixel_per_mm_units(self):
  import torch
  V=np.array([[1.,2.,10.],[2.,-1.,12.]]);K=np.array([[300.,0,100.],[0,310.,80.],[0,0,1.]]);C=np.eye(4);q=torch.tensor(V,dtype=torch.float64,requires_grad=True);uv=project_torch(q,K,C);uv[0,0].backward();self.assertAlmostEqual(q.grad[0,0],30.);self.assertAlmostEqual(q.grad[0,2],-3.);eps=1e-5
  for a in range(3):
   plus=V.copy();minus=V.copy();plus[0,a]+=eps;minus[0,a]-=eps;fd=(project(plus,K,C)[0][0,0]-project(minus,K,C)[0][0,0])/(2*eps);self.assertAlmostEqual(float(q.grad[0,a]),fd,places=7)
 def test_rotation_and_translation_coordinate_convention(self):
  C=np.eye(4);C[:3,:3]=np.array([[0.,-1.,0],[1.,0,0],[0,0,1]]);C[:3,3]=[3.,4.,5.];local=np.array([[1.,2.,10.]]);world=local@C[:3,:3].T+C[:3,3];K=np.array([[100.,0,0],[0,100.,0],[0,0,1.]]);np.testing.assert_allclose(project(world,K,C)[0],[[10,20]])
 def test_bidirectional_mutual_normal_correspondence(self):
  B=np.array([[10.,10.],[10.,20.],[10.,30.]]);T=B+[2.,0];N=np.tile([1.,0.],(3,1));p=explicit_pairs(B,N,T,N,np.ones(3,bool),CONFIG);self.assertEqual(p['accepted'].sum(),6);self.assertEqual(set(p['direction']),{0,1})
 def test_wrong_normals_and_contact_rejected(self):
  B=np.array([[10.,10.],[10.,20.]]);N=np.tile([1.,0.],(2,1));bad=np.tile([0.,1.],(2,1));p=explicit_pairs(B,N,B,bad,np.ones(2,bool),CONFIG);self.assertFalse(p['accepted'].any());p=explicit_pairs(B,N,B,N,np.zeros(2,bool),CONFIG);self.assertTrue((p['reasons']=='RING_BOUNDARY_UNKNOWN').all())
 def test_no_silent_capture_expansion(self):
  B=np.array([[10.,10.]]);N=np.array([[1.,0.]]);p=explicit_pairs(B,N,B+[80,0],N,np.ones(1,bool),CONFIG);self.assertFalse(p['accepted'].any())
 def test_Mesh_region_hits_actual_triangle_and_barycentric_point(self):
  import trimesh
  m=trimesh.creation.icosphere(subdivisions=2,radius=2.);V=np.asarray(m.vertices)+[0,0,20];F=np.asarray(m.faces);K=np.array([[100.,0,50],[0,100.,50],[0,0,1.]]);C=np.eye(4);y,x=np.mgrid[:100,:100];lab=np.where((x-50)**2+(y-50)**2<100,1,0);ring=dict(V=np.asarray(m.vertices)*.1+[0,0,40],F=F);body=dict(V=V,F=F);r=mesh_candidates(np.array([[50.,50.],[51.,50.]]),body,K,C,lab,ring);self.assertTrue(r['valid'].any());ok=r['valid'];np.testing.assert_allclose(r['bary'][ok].sum(1),1.,atol=1e-6);np.testing.assert_allclose(r['points'][ok],np.einsum('ni,nij->nj',r['bary'][ok],V[F[r['face'][ok]]]))
 def test_required_scientific_images_not_skippable(self):
  with self.assertRaises(PolicyError):validate(self.path.parent,dict(attempts=[dict(path='attempts/001-G4_visualize-xx/result.json')]))
 def test_target_Ring_contact_unknown(self):
  lab=np.zeros((30,30),int);lab[10:20,10:20]=1;lab[20:25,8:22]=2;uv,n,known=target_boundary(lab);self.assertTrue((~known).any());self.assertTrue(known.any())
if __name__=='__main__':unittest.main()
