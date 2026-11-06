from stable import *
from pmgr_self import self_intersections
from scipy.optimize import LinearConstraint

def main():
 checks=[];initial=[];gradients=[]
 def test(name,ok,**extra):checks.append(dict(test=name,passed=bool(ok),**extra))
 # Independent numerical sign equivalence remains distinct from directed clipping side.
 from planes import compare,normalize
 p=np.array([.1,.2,.9,3.]);_,angle,dist=compare(-3*p,p,[1.,2.,3.]);test('unoriented_plane_sign_equivalence',angle<1e-8 and dist<1e-10);test('directed_halfspaces_are_opposite',np.sign(np.array([0,0,0,1])@normalize(p))!=np.sign(np.array([0,0,0,1])@normalize(-p)))
 # Proper and coplanar intersections must be found, separated triangles must not.
 A=np.array([[0.,0,0],[2,0,0],[0,2,0]]);B=np.array([[.4,.4,-1],[.4,.4,1],[1.2,1.2,.5]]);V=np.r_[A,B];F=np.array([[0,1,2],[3,4,5]]);test('proper_triangle_intersection_detected',self_intersections(V,F)['intersections']>0)
 B=np.array([[.2,.2,0],[1.2,.2,0],[.2,1.2,0]]);test('coplanar_overlap_detected',self_intersections(np.r_[A,B],F)['intersections']>0);test('separated_coplanar_not_crossing',self_intersections(np.r_[A,B+[4,0,0]],F)['intersections']==0)
 # Mature Adam state rollback, including initialized moment buffers and step counter.
 x=torch.tensor([1.,2.],device=device,dtype=torch.float64,requires_grad=True);opt=torch.optim.Adam([x],lr=.02);(x*x).sum().backward();opt.step();opt.zero_grad();x0=x.detach().clone();st=copy.deepcopy(opt.state_dict());(x*x).sum().backward();opt.step()
 with torch.no_grad():x.copy_(x0)
 opt.load_state_dict(st);test('rejected_Adam_parameters_moments_step_exact_restore',torch.equal(x,x0)and state_equal(opt.state_dict(),st))
 qp=minimize(lambda v:((v-np.array([-1.,2.]))**2).sum(),[0.,0.],jac=lambda v:2*(v-np.array([-1.,2.])),constraints=[LinearConstraint([[1.,0]],[0.],[np.inf])],method='SLSQP');test('contact_tangent_QP_control',qp.success and abs(qp.x[0])<1e-6 and abs(qp.x[1]-2)<1e-6)
 for n in load(R/'config/PROTOCOL.json')['cases']:
  c=Case(n);ch=Chart(c);guard=GeometryGuard(c,ch);q=torch.zeros(54,device=device,dtype=torch.float64,requires_grad=True);v=ch.vertices(q);zeroerror=float(abs(v.detach().cpu().numpy()-c.V).max());test(n+'_chart_zero_reproduces_C',zeroerror<1e-12,error=zeroerror);test(n+'_initial_mesh_closed_consistent',guard.topology.is_watertight and guard.topology.is_winding_consistent);test(n+'_initial_no_nonadjacent_self',guard.initial_self['intersections']==0)
  m=load(R/'inputs'/n/'C_INITIAL_MODEL.json');old=R.parent/'BODY_BASE_INIT_009';base=load(old/'inputs'/n/'BASE.json');plane=normalize(base['plane']);test(n+'_plane_directed009_unchanged',np.allclose(ch.plane,plane,rtol=0,atol=1e-14))
  if m['inheritance']['action']=='EXACT_FROZEN_C_REUSED':test(n+'_frozen_C_exact',np.array_equal(np.load(old/'local_results'/n/'C_SELECTED.npz')['V'],c.V))
  if ch.cap:
   hh=c.V@plane[:3]+plane[3];test(n+'_initial_above_plane',hh.min()>-1e-10);test(n+'_cover_has48_inferred_faces',int(c.inferred.sum())==48 and len(c.F)+48==len(c.F_solid));rng=np.random.default_rng(20261107);r=rng.normal(0,.005,54);V=ch.vertices(tensor(r,torch.float64)).detach().cpu().numpy();h=V@plane[:3]+plane[3];test(n+'_nonzero_chart_cannot_go_underground',h.min()>-1e-10 and abs(h[np.unique(c.F_solid[c.inferred])]).max()<1e-10)
  L=Objective(c,ch);loss,parts=L(q);g=torch.autograd.grad(loss,q)[0];test(n+'_complete_chart_gradient_finite',torch.isfinite(loss)and torch.isfinite(g).all()and float(g.norm())>0);gradients.append(dict(case=n,loss=parts,gradient_norm=float(g.norm()),global_gradient_norm=float(g[:6].norm()),low_gradient_norm=float(g[6:22].norm()),high_gradient_norm=float(g[22:].norm())))
  why,info,geo=guard.inspect(c.V,c.V);test(n+'_initial_guard_feasible',not why,reasons=why);initial.append(dict(case=n,**info,initial_Ring_collision=guard.col0,initial_reverse_min=float(guard.reverse0.min()),initial_self=guard.initial_self,tau_mm=ch.tau))
 save('metrics/INITIAL_GEOMETRY.json',initial);table('metrics/INITIAL_GEOMETRY.csv',initial);save('metrics/INITIAL_GRADIENTS.json',gradients);save('metrics/PREFLIGHT.json',dict(passed=all(x['passed']for x in checks),tests=checks,formal_optimizer_steps=0,synthetic_Adam_test_updates=2,GT_read=False));print('PREFLIGHT',len(checks),[x for x in checks if not x['passed']],flush=True);assert all(x['passed']for x in checks)
if __name__=='__main__':main()
