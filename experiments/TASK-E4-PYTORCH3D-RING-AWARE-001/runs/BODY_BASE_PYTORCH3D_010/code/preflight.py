"""Required sign-equivalence, exact clipping and real-network gradient checks, no optimizer steps."""
from depth_terms import *
from planes import normalize,align,compare,orient_retained
from clip_mesh import clip

def main():
 tests=[];grads=[]
 def check(name,ok,**x):tests.append(dict(test=name,passed=bool(ok),**x))
 p=np.array([.2,.3,.9,-2.]);anchor=np.array([100.,-3.,20.]);q,a,d=compare(-7*p,3*p,anchor);check('scaled_opposite_plane_equivalence',a<1e-6 and d<1e-10,angle=a,anchor_offset_mm=d)
 p2=normalize(p);p2[3]+=.4;_,a,d=compare(-p2,p,anchor);check('offset_flip_synchronous',a<1e-6 and abs(d-.4)<1e-10,offset_mm=d)
 cube=trimesh.creation.box(extents=[2,2,2]);cl=clip(cube.vertices,cube.faces,[.2,.3,.9,0]);mm=trimesh.Trimesh(cl['V'],cl['F_solid'],process=False);check('exact_half_cube_volume_and_manifold',abs(mm.volume-4)<1e-9 and mm.is_watertight and mm.is_winding_consistent,volume_mm3=float(mm.volume));check('retained_original_vertices_unchanged',np.array_equal(cl['V'][cl['original_vertex_ID']>=0],cube.vertices[cl['original_vertex_ID'][cl['original_vertex_ID']>=0]]));check('cap_excluded_and_outward',len(cl['F'])+int(cl['inferred_base_faces'].sum())==len(cl['F_solid'])and(np.asarray(mm.face_normals)[cl['inferred_base_faces']]@normalize([.2,.3,.9,0])[:3]<-.999).all())
 reg=load(R/'metrics/BASE_SIGN_REGRESSION.json');g=next(x for x in reg if x['case']=='G09');check('G09_176_to_3_96deg',abs(g['old_max_angle']+g['sign_equivalent_max_angle']-180)<1e-7 and 3.8<g['sign_equivalent_max_angle']<4.1 and g['new_status']=='RELIABLE',old=g['old_max_angle'],new=g['sign_equivalent_max_angle']);check('G05_uncertainty_retained',next(x for x in reg if x['case']=='G05')['new_status']=='WEAK');check('all_broad_cases_clipped',all(x['clipped']for x in reg if x['contact']=='BROAD'))
 for case in load(R/'config/PROTOCOL.json')['cases']:
  for route in['P','S']:
   c=Case(case,route);c.name=case+'_'+route+'_PREFLIGHT';prior=RelativePrior(c);depth=D2Depth(c);v=c.base.verts_packed().detach().requires_grad_();m=Meshes(verts=[v],faces=[c.base.faces_packed()]);cid=next(k for k in c.fit if k in depth.obs);sil=c.loss(m,cid,'RingAware');pr=relative_total(prior(m));depth.begin(m);ab,rel,info,query=depth.terms(m,cid,'E3');vals={}
   for key,L in[('silhouette',sil),('prior',pr),('absolute',.01*ab),('relative',.01*rel)]:
    grad=torch.autograd.grad(L,v,retain_graph=True,allow_unused=True)[0];norm=0. if grad is None else float(grad.norm());finite=True if grad is None else bool(torch.isfinite(grad).all());vals[key]=dict(loss=float(L.detach()),gradient_norm=norm,finite=finite);check(case+'_'+route+'_'+key+'_finite',finite and bool(torch.isfinite(L)))
   check(case+'_'+route+'_initial_mesh',np.isfinite(c.V).all()and len(c.F)>0);grads.append(dict(case=case,route=route,source=cid,loss_gradient=vals,depth_info=info,zero_gradients=[k for k,x in vals.items()if x['gradient_norm']==0]))
   check(case+'_'+route+'_cap_never_in_observation_faces',len(c.F)+int(c.inferred.sum())==len(c.F_solid))
 # Same-view relative term must ignore common depth shift, respond to relative variation.
 z=torch.tensor([1.,2.4,3.1],device=device,dtype=torch.float64,requires_grad=True);hero=tensor([1.2,2.,2.7],torch.float64);pairs=tensor([[0,1],[1,2]],torch.int64)
 def rel_loss(q):return robust(((q[pairs[:,0]]-q[pairs[:,1]])-(hero[pairs[:,0]]-hero[pairs[:,1]]))/.5).mean()
 value=rel_loss(z);grad=torch.autograd.grad(value,z)[0];num=[]
 for j in range(3):
  delta=torch.zeros_like(z);delta[j]=1e-6;num.append(float((rel_loss(z.detach()+delta)-rel_loss(z.detach()-delta))/(2e-6)))
 check('relative_depth_common_shift_invariant',abs(float(value-rel_loss(z+4.7)))<1e-10);err=float(np.max(abs(grad.detach().cpu().numpy()-num)));check('relative_gradient_central_difference',err<1e-7 and float(grad.norm())>0,error=err)
 out=dict(passed=all(x['passed']for x in tests),tests=tests,optimizer_steps=0,real_GT_read=False);save('metrics/PREFLIGHT.json',out);save('metrics/INITIAL_LOSS_GRADIENTS.json',grads);print('PREFLIGHT',out['passed'],'tests',len(tests),flush=True);assert out['passed']
if __name__=='__main__':main()
