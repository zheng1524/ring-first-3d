"""Meaningful geometry/gradient/role tests for the shared structural updater."""
import copy,json,sys,tempfile,unittest
from pathlib import Path
import numpy as np
import torch
import trimesh
from ring_first_3d.policy.contracts import ROOT,PolicyError,stages_for
from ring_first_3d.policy.structural_contracts import STRUCTURAL_STAGES,permissions
TD=ROOT/'experiments/TASK-E4-MULTIVIEW-STRUCTURAL-UPDATE-001'
sys.path.insert(0,str(TD/'code'))
import body_update as bu
from hero_relocation import relocate


def cube():
    a=trimesh.creation.icosphere(subdivisions=1,radius=1.)
    return dict(V=np.array(a.vertices),F=np.array(a.faces),F_solid=np.array(a.faces),inferred_base_faces=np.zeros(len(a.faces),bool),boundary_vertex=np.zeros(len(a.vertices),bool))


class StructuralTests(unittest.TestCase):
    def test_original_groups_keep_balanced_weights(self):
        views=[dict(id='a',video='004',direction_block=0),dict(id='b',video='004',direction_block=0),dict(id='c',video='005',direction_block=0)]
        self.assertEqual(bu.balanced_weights(views),dict(a=.25,b=.25,c=.5))
    def test_direction_bins_not_frame_counts(self):
        v=[dict(id=str(i),video='004',direction_block=i//2) for i in range(4)];w=bu.balanced_weights(v);self.assertAlmostEqual(sum(w.values()),1.);self.assertTrue(all(x==.25 for x in w.values()))
    def test_exact_initializer_no_shape_fit(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'initial.npz';a=cube();np.savez(p,**a);r=dict(V=np.array([[0.,0.,0.]]),F=np.array([[0,0,0]]));b=bu.initialize(p,r,r)
            for k in a:np.testing.assert_array_equal(a[k],b[k])
    def test_CAD_mismatch_rejected(self):
        with self.assertRaisesRegex(PolicyError,'CAD_FRAME'):bu.initialize('never_read',dict(V=np.zeros((1,3)),F=np.zeros((1,3))),dict(V=np.ones((1,3)),F=np.zeros((1,3))))
    def test_holdout_rejected_before_optimization(self):
        with self.assertRaisesRegex(PolicyError,'HOLDOUT_LEAK'):bu.update({},[dict(role='HOLDOUT')],{},{},{},{},Path('/tmp/never-write'),'unused')
    def test_depth_in_updater_rejected(self):
        with self.assertRaisesRegex(PolicyError,'DEPTH_LEAK'):bu.update({},[dict(role='FIT',depth=np.ones(1))],{},{},{},{},Path('/tmp/never-write'),'unused')
    def test_world_projection_jacobian_finite_difference(self):
        from scipy.spatial.transform import Rotation
        C=np.eye(4);C[:3,:3]=Rotation.from_rotvec([.1,.2,-.1]).as_matrix();C[:3,3]=[.3,-.2,-4]
        K=np.array([[480.,0,319.5],[0,490,179.5],[0,0,1.]])
        P=np.array([.2,.1,1.]);J=bu.projection_jacobian(P,K,C);h=1e-6;fd=np.column_stack([(bu.project((P+np.eye(3)[j]*h)[None],K,C)[0][0]-bu.project((P-np.eye(3)[j]*h)[None],K,C)[0][0])/(2*h) for j in range(3)])
        np.testing.assert_allclose(J,fd,atol=1e-7,rtol=1e-7)
    def test_torch_projection_matches_metric(self):
        C=np.eye(4);C[2,3]=-5;K=np.array([[200.,0,50],[0,200,40],[0,0,1.]])
        V=np.array([[.2,-.3,1.]])
        np.testing.assert_allclose(bu.project_torch(torch.tensor(V),K,C).numpy(),bu.project(V,K,C)[0],atol=1e-10)
    def test_actual_barycentric_gradient_finite_difference(self):
        V=torch.tensor([[0.,0.,4.],[1.,0.,4.],[0.,1.,5.]],dtype=torch.float64,requires_grad=True);b=torch.tensor([.2,.3,.5]);K=np.array([[300.,0,200],[0,300,100],[0,0,1.]]);C=np.eye(4)
        def f(W):return ((bu.project_torch((W*b[:,None]).sum(0)[None],K,C)-torch.tensor([[210.,110.]]))**2).sum()
        g=torch.autograd.grad(f(V),V)[0].numpy();A=V.detach().numpy();fd=np.empty_like(A);h=1e-6
        for i in range(3):
            for j in range(3):
                x=A.copy();y=A.copy();x[i,j]+=h;y[i,j]-=h;fd[i,j]=(float(f(torch.tensor(x)))-float(f(torch.tensor(y))))/(2*h)
        np.testing.assert_allclose(g,fd,rtol=1e-6,atol=1e-4)
    def test_extrusion_generates_connected_real_faces(self):
        a=cube();f=a['F'][0];normal=np.cross(a['V'][f[1]]-a['V'][f[0]],a['V'][f[2]]-a['V'][f[0]]);normal/=np.linalg.norm(normal)
        b,p=bu.extrude_patch(a,[0],normal*.2);m=trimesh.Trimesh(b['V'],b['F'],process=False)
        self.assertTrue(m.is_watertight);self.assertTrue(m.is_winding_consistent);self.assertEqual(len(m.split()),1);self.assertEqual(len(b['V']),len(a['V'])+3);self.assertEqual(len(p['new_wall_face_ids']),6)
    def test_extrusion_preserves_original_vertices(self):
        a=cube();b,p=bu.extrude_patch(a,[0],np.array([0.,0.,.1]));np.testing.assert_array_equal(b['V'][:len(a['V'])],a['V']);np.testing.assert_array_equal(p['parent_vertex_ids'],np.unique(a['F'][[0]]))
    def test_disconnected_patch_refused(self):
        a=cube()
        i=next(i for i in range(len(a['F'])) if set(a['F'][0]).isdisjoint(a['F'][i]))
        with self.assertRaisesRegex(PolicyError,'GROWTH_TOPOLOGY'):bu.extrude_patch(a,[0,i],np.array([0,0,.2]))
    def test_single_view_cannot_grow(self):
        a=cube();v=[dict(id='a',video='004',K=np.eye(3),C=np.eye(4))];p=dict(accepted=np.ones(1,bool),missing_support=np.ones(1,bool),face=np.array([0]),bary=np.array([[1/3]*3]),projected_uv=np.array([[0.,0.]]),target_uv=np.array([[10.,0.]]));cfg=dict(growth_patch_rings=1,growth_max_patch_faces=80,growth_min_views=3,growth_min_videos=2,growth_min_singular_ratio=.02,growth_max_inconsistency=.5,growth_min_mm=.1,growth_max_mm=.8,growth_candidates=3)
        candidates,_=bu.growth_candidates(a,v,dict(a=p),cfg);self.assertEqual(candidates,[])
    def test_consistent_three_view_two_video_support_can_grow(self):
        a=cube();face=0;point=a['V'][a['F'][face][0]];normal=point/np.linalg.norm(point);shift=.4*normal;v=[];pairs={}
        for i,pos in enumerate(([-2,0,-5],[2,0,-5],[0,2,-5])):
            C=np.eye(4);C[:3,3]=pos;K=np.array([[100.,0,50],[0,100,50],[0,0,1.]])
            view=dict(id=str(i),video='004' if i<2 else '005',K=K,C=C);v.append(view);uv=bu.project(point[None],K,C)[0][0];res=bu.projection_jacobian(point,K,C)@shift
            pairs[str(i)]=dict(accepted=np.ones(1,bool),missing_support=np.ones(1,bool),face=np.array([face]),bary=np.array([[1.,0.,0.]]),projected_uv=uv[None],target_uv=(uv+res)[None])
        cfg=dict(growth_patch_rings=1,growth_max_patch_faces=80,growth_min_views=3,growth_min_videos=2,growth_min_singular_ratio=.02,growth_max_inconsistency=.5,growth_min_mm=.1,growth_max_mm=.8,growth_candidates=3)
        candidates,audit=bu.growth_candidates(a,v,pairs,cfg);self.assertTrue(candidates);np.testing.assert_allclose(candidates[0]['delta'],shift,atol=1e-10);self.assertEqual(len(candidates[0]['support_views']),3)
    def test_real_simulation_adapter_accepts_RGB_cache_without_T(self):
        import yaml
        from data_adapter import simulation_data
        task=yaml.safe_load((TD/'TASK.yaml').read_text());body,views,ring,base,chart=simulation_data(task)
        self.assertEqual(len(views),24);self.assertEqual(sum(v['role']=='FIT' for v in views),16)
        self.assertEqual(body['V'].shape,(642,3));self.assertTrue(all(set(v)<=set(('id','video','role','direction_block','K','C','labels','RGB')) for v in views))
    def test_complete_objective_double_precision_laplacian_backward(self):
        a=cube();a['V'][:,2]+=5.;V=torch.tensor(a['V'],dtype=torch.float64,requires_grad=True);C=np.eye(4);K=np.array([[100.,0,50],[0,100,50],[0,0,1.]])
        faces=np.arange(12);bary=np.tile([.2,.3,.5],(12,1));P=np.einsum('ni,nij->nj',bary,a['V'][a['F'][faces]]);target=bu.project(P,K,C)[0]+np.array([1.,-.5]);pairs=dict(v=dict(accepted=np.ones(12,bool),face=faces,bary=bary,target_uv=target,direction=np.arange(12)%3));views=[dict(id='v',K=K,C=C)];cfg=dict(pixel_loss_scale=20.,lambda_lap=.03,lambda_edge=.02,lambda_prior=.002)
        value,per,parts=bu.objective(V,a,V.detach(),views,pairs,dict(v=1.),cfg,True);value.backward();self.assertTrue(torch.isfinite(V.grad).all());self.assertGreater(float(V.grad.norm()),0);self.assertGreater(float(value),0);np.testing.assert_allclose(per['v'],V.grad.detach().numpy(),atol=1e-12)
    def test_stage_order_requires_scientific_gate(self):
        self.assertLess(STRUCTURAL_STAGES.index('G4_C0_gate'),STRUCTURAL_STAGES.index('G5_real_update'));self.assertEqual(stages_for(dict(schema=9)),STRUCTURAL_STAGES)
    def test_gate_all_endpoints_not_only_2D(self):
        import inspect,experiment
        s=inspect.getsource(experiment.c0_evaluate)
        for x in ('GT_Chamfer_improvement','HOLDOUT_IoU_nonworsening','accepted_growth','growth_over_deform_GT_gain','no_geometry_worsening'):self.assertIn(x,s)
    def test_hero_does_not_change_camera_or_body(self):
        import inspect
        source=inspect.getsource(relocate)
        self.assertNotIn('body[\'V\']=',source);self.assertIn("source_pixel_error_max_px",source);self.assertIn("local_shape_replaced=False",source)
    def test_silhouette_unknown_ring_pixels_saved(self):
        a=cube();a['V'][:,2]+=5;K=np.array([[50.,0,30],[0,50,30],[0,0,1.]]);lab=np.zeros((60,60),int);lab[18:42,18:42]=1;lab[:,29:32]=2;v=dict(id='x',K=K,C=np.eye(4),labels=lab,video='004')
        cfg=dict(ring_unknown_px=3,samples_per_direction=80,negative_samples=40,capture_px=100,growth_min_gap_px=4)
        with tempfile.TemporaryDirectory() as d:
            pairs,rows=bu.assignments(a,[v],dict(x=np.full(lab.shape,np.inf)),cfg,Path(d));p=np.load(Path(d)/'x.npz');self.assertFalse(p['R_plus'][:,29:32].any());self.assertFalse(p['R_minus'][:,29:32].any());self.assertTrue(np.isin(p['face'],np.arange(len(a['F']))).all());self.assertGreater(rows[0]['candidate_N'],0)
    def test_saved_bary_points_reproject_to_native_pixel(self):
        a=cube();a['V'][:,2]+=5;K=np.array([[50.,0,30],[0,50,30],[0,0,1.]])
        r=bu.ray_map(a['V'],a['F'],K,np.eye(4),(60,60));ok=r['valid'];y,x=np.nonzero(ok);P=r['points'][ok];uv,_=bu.project(P,K,np.eye(4));self.assertLess(np.max(np.linalg.norm(uv-np.c_[x,y],axis=1)),1e-4);np.testing.assert_allclose(r['bary'][ok].sum(1),1,atol=1e-6)
    def test_final_report_plain_local_index_profile(self):
        from ring_first_3d.policy.artifacts import check_page_profile
        check_page_profile(TD.name,'<a href="x.png">actual PNG</a>')
        with self.assertRaises(PolicyError):check_page_profile(TD.name,'<script>bad()</script><a href="x">x</a>')
    def test_updater_one_shared_tensor_no_view_bodies(self):
        import inspect
        s=inspect.getsource(bu.update);self.assertIn('per[v[\'id\']]',s);self.assertIn('actual_shared_vertex_delta',s);self.assertIn("all(v['role']=='FIT'",s)


if __name__=='__main__':unittest.main()
