import ast,json,sys,tempfile,unittest
from pathlib import Path
import numpy as np
import torch,trimesh
TD=Path(__file__).resolve().parents[1];sys.path.insert(0,str(TD/'code'))
from io_utils import source_folder
from recover import restore
from embedded_sweep import EmbeddedSweep
from lengths import measure
from union_mesh import union,lifted_vertices,provenance
from ring_gate import CurrentRingGate,metrics_accept
from geometry_gate import namespace

def mesh(m):
    return dict(V=np.asarray(m.vertices),F=np.asarray(m.faces),F_solid=np.asarray(m.faces),inferred_base_faces=np.zeros(len(m.faces),bool),boundary_vertex=np.zeros(len(m.vertices),bool))
def config():
    return dict(control=[[0,0,.3],[0,0,.6],[0,0,1.],[0,0,1.5],[0,0,2.]],radii_logits=np.full((5,2),float(np.log(np.expm1(.2)))).tolist(),
        initial_axis=[1,0,0],exit_reference=[0,0,1],proximal=[0,0,.3],attachment_region_radius_mm=.8,overlap_transition_mm=.2,direction=[0,0,1])

class RecoveryTests(unittest.TestCase):
    def test_all_modules_parse(self):
        for p in (TD/'code').glob('*.py'):ast.parse(p.read_text(),filename=str(p))
    def test_exact_saved_G01(self):
        *_,r=restore('G01');self.assertLess(r['errors']['BODY_vertex_max_mm'],1e-5);self.assertTrue(r['topology_identical']);self.assertEqual(r['seed'],54)
    def test_exact_saved_G03(self):
        *_,r=restore('G03');self.assertLess(r['errors']['BODY_vertex_max_mm'],1e-5);self.assertTrue(r['topology_identical']);self.assertEqual(r['seed'],544)
    def test_no_other_case(self):
        with self.assertRaises(AssertionError):source_folder('G05')
    def test_embedded_not_counted_as_stalk(self):
        sw=EmbeddedSweep(config());b=mesh(trimesh.creation.icosphere(subdivisions=2,radius=1));r=measure(sw.controls().detach().numpy(),b)
        self.assertAlmostEqual(r['total_centerline_length_mm'],1.7,places=7);self.assertAlmostEqual(r['embedded_length_mm'],.7,places=5);self.assertAlmostEqual(r['exposed_stalk_length_mm'],1.,places=5)
    def test_arclength_not_chord(self):
        sw=EmbeddedSweep(config());C=sw.controls().detach().numpy();C[2,0]=.5;b=mesh(trimesh.creation.icosphere(subdivisions=2));r=measure(C,b)
        self.assertGreater(r['total_centerline_length_mm'],np.linalg.norm(C[-1]-C[0])+.01)
    def test_exterior_reentry_rejected(self):
        C=np.array([[0,0,0],[0,0,5],[0,0,-5],[0,0,5],[0,0,0.]])
        with self.assertRaises(ValueError):measure(C,mesh(trimesh.creation.icosphere(subdivisions=2)))
    def test_closed_sweep_no_internal_duplicates(self):
        sw=EmbeddedSweep(config());V,_=sw.generate();m=trimesh.Trimesh(V.detach().numpy(),sw.F,process=False)
        self.assertTrue(m.is_watertight);self.assertTrue(m.is_winding_consistent);self.assertGreater(m.volume,0)
        self.assertEqual(len(sw.F),len(np.unique(np.sort(sw.F,axis=1),axis=0)))
    def test_spline_gradient_finite_difference(self):
        sw=EmbeddedSweep(config());V,_=sw.generate();loss=(V[:,0]*V[:,2]).sum();loss.backward();actual=float(sw.control_tail.grad[1,0]);eps=1e-6
        with torch.no_grad():
            sw.control_tail[1,0]+=eps;vp,_=sw.generate();a=float((vp[:,0]*vp[:,2]).sum());sw.control_tail[1,0]-=2*eps;vm,_=sw.generate();b=float((vm[:,0]*vm[:,2]).sum())
        self.assertAlmostEqual(actual,(a-b)/(2*eps),places=5)
    def test_proximal_fixed(self):
        sw=EmbeddedSweep(config());self.assertFalse(sw.proximal.requires_grad);self.assertEqual(tuple(sw.control_tail.shape),(4,3));self.assertEqual(tuple(sw.radii.shape),(5,2))
    def test_expected_overlap_union_connected(self):
        b=mesh(trimesh.creation.icosphere(subdivisions=2));sw=EmbeddedSweep(config());V,_=sw.generate()
        with tempfile.TemporaryDirectory()as tmp:
            result=union(b,V.detach().numpy(),sw.F,Path(tmp)/'boolean');m=trimesh.Trimesh(result['V'],result['F_solid'],process=False)
            self.assertTrue(m.is_watertight);self.assertTrue(m.is_winding_consistent);self.assertEqual(len(m.split()),1)
            self.assertEqual(namespace()['self_intersections'](result['V'],result['F_solid'])['intersections'],0)
            self.assertEqual(len(result['F_solid']),len(np.unique(np.sort(result['F_solid'],axis=1),axis=0)))
            from ring_first_3d.multisurface.geometry import scene,closest
            P=np.array([[0,0,-1],[-1,0,0],[0,-1,0.]])
            Q,_,_=closest(scene(result['V'],result['F_solid']),P);self.assertLess(np.linalg.norm(P-Q,axis=1).max(),1e-5)
            p=provenance(result,V.detach().numpy(),sw.F);lifted=lifted_vertices(result,V,sw.F,p)
            self.assertTrue(np.array_equal(lifted.detach().numpy(),result['V']));lifted.square().sum().backward();self.assertTrue(torch.isfinite(sw.control_tail.grad).all())
    def test_sweep_self_intersection_detection(self):
        ns=namespace();V=np.array([[-1,-1,0],[1,-1,0],[0,1,0],[0,-.5,-1],[0,-.5,1],[0,.5,.5]])
        self.assertGreater(ns['self_intersections'](V,np.array([[0,1,2],[3,4,5]]))['intersections'],0)
    def test_FIT_HOLDOUT_isolation(self):
        from projection import RecoveryProjection
        with self.assertRaises(AssertionError):RecoveryProjection([dict(role='HOLDOUT')],{}, {},{})

class RingTests(unittest.TestCase):
    def setUp(self):
        self.tol=dict(depth_mm=1e-5,area_mm2=1e-4,energy_mm4=1e-6)
        self.zero={a+'_'+b:0. for a in ['body','ring']for b in ['max_mm','area_mm2','energy_mm4']}
    def test_no_contact_accept(self):self.assertEqual(metrics_accept(self.zero,self.zero,self.tol),[])
    def test_unchanged_existing_accept(self):
        a={k:1. for k in self.zero};self.assertEqual(metrics_accept(a,a,self.tol),[])
    def test_reduced_accept(self):self.assertEqual(metrics_accept({k:1. for k in self.zero},self.zero,self.tol),[])
    def test_body_worsens_reject(self):
        b=dict(self.zero,body_max_mm=.1);self.assertTrue(metrics_accept(self.zero,b,self.tol))
    def test_ring_worsens_reject(self):
        b=dict(self.zero,ring_max_mm=.1);self.assertTrue(metrics_accept(self.zero,b,self.tol))
    def test_numerical_variation_accept(self):
        b={k:1e-8 for k in self.zero};self.assertEqual(metrics_accept(self.zero,b,self.tol),[])
    def test_actual_bidirectional_SDF(self):
        b=mesh(trimesh.creation.icosphere(subdivisions=1));r=mesh(trimesh.creation.box(extents=[1,1,1],transform=trimesh.transformations.translation_matrix([4,0,0])))
        gate=CurrentRingGate(b,r);self.assertTrue(gate.check(b)[0]);moved=dict(b,V=b['V']+[4,0,0]);self.assertFalse(gate.check(moved)[0])
    def test_initial_not_a_hard_ceiling(self):
        source=(TD/'code/ring_gate.py').read_text();self.assertNotIn('minimum(self.initial',source);self.assertIn('current',source)

if __name__=='__main__':unittest.main()
