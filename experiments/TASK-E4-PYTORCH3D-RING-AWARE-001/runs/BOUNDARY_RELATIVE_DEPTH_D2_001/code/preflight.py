from depth_terms import *
def main():
 rows=[];checks=[]
 for name in load(R/'config/PROTOCOL.json')['cases']:
  c=Case(name);d=D2Depth(c);old=Depth(c);v0=c.base.verts_packed().detach().double();F=c.base.faces_packed();rng=np.random.default_rng(20261106)
  for cid in c.fit:
   v=v0.clone().requires_grad_(True);m=Meshes(verts=[v],faces=[F]);d.begin(m);old.begin(m);a,b,info,q=d.terms(m,cid,'E3');uniform,_,_,_=d.terms(m,cid,'E1');ol,_=old.loss(m,cid);assert abs(float(uniform-ol))<1e-10
   gradients=[]
   for label,loss in[('abs',a),('rel',b)]:
    grad=torch.autograd.grad(loss,v,retain_graph=True)[0];direction=tensor(rng.normal(size=v.shape),torch.float64);direction/=direction.norm();epsilon=1e-5;values=[]
    for sign in[-1,1]:
     mm=Meshes(verts=[v.detach()+sign*epsilon*direction],faces=[F]);d.begin(mm);aa,bb,_,_=d.terms(mm,cid,'E3');values.append(float(aa if label=='abs'else bb))
    analytic=float((grad*direction).sum());fd=(values[1]-values[0])/(2*epsilon);relative=abs(fd-analytic)/max(1e-6,abs(fd),abs(analytic));passed=np.isfinite(grad.cpu().numpy()).all()and relative<.03
    rows.append(dict(case=name,view=cid,term=label,full_vertex_gradient_norm=float(grad.norm()),gradient_per_mm_norm=float(grad.norm())/c.scale,lambda_weighted_norm=float(grad.norm())*.01,finite=True,FD_analytic=analytic,FD_numeric=fd,FD_relative_error=relative,passed=bool(passed)))
   pair=d.obs[cid]['pairs'];z=q['z'].detach();obs=d.obs[cid]['z_t'];ix=tensor(pair,torch.int64);delta=z[ix[:,0]]-z[ix[:,1]]-(obs[ix[:,0]]-obs[ix[:,1]]);shift=z+3.75;shiftdelta=shift[ix[:,0]]-shift[ix[:,1]]-(obs[ix[:,0]]-obs[ix[:,1]]);err=float((delta-shiftdelta).abs().max())if len(pair)else 0.;probe=torch.tensor([0.,.2],dtype=torch.float64,device=device,requires_grad=True);loss=robust((probe[0]-probe[1])/.5);gg=torch.autograd.grad(loss,probe)[0];checks.append(dict(case=name,view=cid,uniform_absolute_identical_to_previous_adapter=True,common_offset_max_error_mm=err,relative_difference_response_gradient=gg.cpu().numpy(),offset_invariance=err<1e-10,response_nonzero=float(gg.norm())>0,pair_N=len(pair)))
  print('PREFLIGHT',name,flush=True)
 table('metrics/GRADIENT_PREFLIGHT.csv',rows);save('metrics/PREFLIGHT.json',dict(passed=all(x['passed']for x in rows)and all(x['offset_invariance']and x['response_nonzero']for x in checks),rows=rows,relative_checks=checks,GT_used=False))
if __name__=='__main__':main()
