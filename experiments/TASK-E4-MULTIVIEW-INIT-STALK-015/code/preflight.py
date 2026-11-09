"""Initialization identity and physical-coordinate checks; zero optimizer steps."""
from initialize import Initializer
from p3d import *
from multiview import MultiObjective
from free_model import FreeVertices
import gc
def main():
    guard_optimizer();rows=[]
    for c in load(R/'config/CASE_LOCK.json'):
        n=c['name'];a=Initializer(n,'Init-B');V,*_=a.shape(a.p0);err=float(abs(V-a.V0).max());assert err<1e-10
        p=a.p0.copy();p[0]=.02;W,*_=a.shape(p)
        if a.cap:
            h=W@a.plane[:3]+a.plane[3];assert h.min()>-1e-7;expected=.02*a.Q[:,0]
        else:expected=np.array([.02,0,0])
        assert np.max(abs((W-V)-expected))<1e-10
        b=Initializer(n,'Init-C');CV,CF,CS,flag=b.shape(b.p0);tm=trimesh.Trimesh(CV,CS,process=False);assert np.isfinite(CV).all()and tm.is_watertight and tm.is_winding_consistent
        if flag.any():assert np.min(CV@b.plane[:3]+b.plane[3])>-1e-7
        rows.append(dict(case=n,affine_identity_max_mm=err,translation_response_correct=True,C_family=b.model['meta']['family'],C_parameters=len(b.p0),C_watertight=True,C_vertices=len(CV),current_vertices=len(V),GT_read=False))
        print('IDENTITY_CHECK',n,err,b.model['meta']['family'],flush=True)
        del a,b;gc.collect();torch.cuda.empty_cache()
    c=Case('G01');ch=FreeVertices(c);ch.total_trust_D=1.;q=torch.zeros((ch.N,3),device=device,dtype=torch.float64,requires_grad=True);o=MultiObjective(c,ch,'D0_013');o.attempt=40;L,p=o.compute(q,True);assert np.isfinite(L)and torch.isfinite(q.grad).all()and q.grad.norm()>0
    save('provenance/INITIALIZATION_PREFLIGHT.json',dict(epoch=time.time(),checks=rows,full_multiview_objective=L,gradient_norm=float(q.grad.norm()),finite=True,optimizer_steps=0,official_PyTorch3D_render=True,GT_read=False));table('metrics/INITIALIZATION_PREFLIGHT.csv',rows);print('INIT_IDENTITY_AND_FULL_GRADIENT_PASS',len(rows),L,flush=True)
if __name__=='__main__':main()
