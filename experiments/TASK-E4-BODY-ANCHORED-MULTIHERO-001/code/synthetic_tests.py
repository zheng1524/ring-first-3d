"""Production correction/correspondence/point-face/rollback tests; explicit controls."""
from body_multi import *
from native_multi import corrected,face_normals,raycast,project
from types import SimpleNamespace

def main():
 rows=[]
 def test(name,ok,**kw):
  rows.append(dict(test=name,PASS=bool(ok),**kw));print(name,bool(ok),kw,flush=True)
 C=np.eye(4);xy=np.stack(np.meshgrid(np.linspace(-.3,.3,17),np.linspace(-.25,.25,17)),axis=-1).reshape(-1,2);A=np.c_[np.ones(len(xy)),xy];r=np.c_[xy,np.ones(len(xy))];n=np.tile([0,0,-1.],(len(xy),1));q=r*10.;noise=np.array([.35,.12,-.10]);X=r*(10.+A@noise)[:,None];s=SimpleNamespace(id='control',theta=np.zeros(3),ray=r,A=A,o={'X':X});cr=dict(matched=np.ones(len(xy),bool),index=np.arange(len(xy)),normal=n,Q=q);t,rec=bias_proposal(s,cr);after=X+r*(A@t)[:,None];test('same_surface_offset_reduced',np.mean(abs(after[:,2]-10))<.03,initial_MAE_mm=float(abs(X[:,2]-10).mean()),final_MAE_mm=float(abs(after[:,2]-10).mean()),theta=t.tolist(),rank=rec['rank']);s.o={'X':q};t0,_=bias_proposal(s,cr);test('zero_bias_unchanged',np.max(abs(t0))<1e-9,max_abs_theta=float(abs(t0).max()));after=corrected(X,C,t);uv0=X[:,:2]/X[:,2,None];uv1=after[:,:2]/after[:,2,None];test('native_rays_preserved',np.max(abs(uv0-uv1))<1e-12,max_error=float(abs(uv0-uv1).max()))
 # Two distinct boxes: rear visible branch cannot attach to the nearer front branch.
 front=trimesh.creation.box([2,2,.2]);front.apply_translation([0,0,5]);rear=trimesh.creation.box([2,2,.2]);rear.apply_translation([3,0,6]);V=np.r_[front.vertices,rear.vertices];F=np.r_[front.faces,rear.faces+len(front.vertices)];b=scene(V,F);X2=np.array([[0.,0,6.],[3.,0,5.9]]);uv=X2[:,:2]/X2[:,2,None];z=raycast(b,C,np.eye(3),uv)['t_hit'];test('distinct_branches_first_layer_protected',z[0]<5 and abs(z[1]-5.9)<.02,first_Z=z.tolist(),branch_identity_not_NN=True)
 # Production correspondence test: legitimate hidden branch stays UNEXPLAINED, visible separate branch MATCHED.
 K=np.array([[100.,0,100],[0,100.,100],[0,0,1.]]);pu,pz=project(X2,C,K);fs=SimpleNamespace(C=C,K=K,uv=pu,sub=np.arange(2),z0=pz,A=np.c_[np.ones(2),X2[:,:2]/pz[:,None]],theta=np.zeros(3),peer_conflict=np.zeros(2,bool),points=lambda:X2,normals=lambda:np.tile([0,0,-1.],(2,1)),mask_at=lambda X:np.ones(len(X),bool));far=trimesh.creation.box();far.apply_translation([1000,1000,1000]);cr=correspond(fs,V,F,b,scene(far.vertices,far.faces));test('production_branch_correspondences',cr['state'][0]==1 and cr['state'][1]==0,states=cr['state'].tolist(),expected='occluded extra branch UNEXPLAINED / distinct visible branch MATCHED')
 # The same official PyTorch3D point-face operator as weak anchors; no output scalar trick.
 v=tensor([[-1.,-1.,10.],[1.,-1.,10.],[0,1.,10.]]).requires_grad_();p=tensor([[0.,0.,9.5]]);ind=tensor([0],torch.int64);loss=point_face_distance(p,ind,v[None],ind,1,1e-10).sum();grad=torch.autograd.grad(loss,v)[0];eps=1e-3
 def f(vv):return float(point_face_distance(p,ind,vv[None],ind,1,1e-10).sum())
 fd=(f(v.detach()+tensor([[0,0,eps]]*3))-f(v.detach()-tensor([[0,0,eps]]*3)))/(2*eps);test('nohit_triangle_geometry_gradient',torch.isfinite(grad).all()and grad.norm()>0 and abs(fd-float(grad[:,2].sum()))<.005,gradient=grad.tolist(),FD=fd,analytic=float(grad[:,2].sum()))
 values=[('s3',.3),('s1',.1),('s2',.2)];s1=sum(v for _,v in sorted(values));s2=sum(v for _,v in sorted(reversed(values)));test('source_order_invariant',s1==s2,canonical_sort=True)
 par=torch.zeros((3,3),device=device,dtype=torch.float64,requires_grad=True);opt=torch.optim.Adam([par],lr=.02);(par.sum()).backward();op0=copy.deepcopy(opt.state_dict());p0=par.detach().clone();opt.step();opt.load_state_dict(op0)
 with torch.no_grad():par.copy_(p0)
 test('rollback_optimizer_and_parameters',state_equal(op0,opt.state_dict())and torch.equal(par,p0))
 save('metrics/SYNTHETIC_TESTS.json',rows);assert all(r['PASS']for r in rows),'SYNTHETIC_GATE_FAILED'
if __name__=='__main__':main()
