from components import *

def main():
    guard_optimizer();rows=[];passed=True
    for name in['virtual','real']:
        c=Case(name);prior=RelativePrior(c);dep=Depth(c)
        p=prior(c.base);zero=max(float(p[k])for k in['edge','laplacian','unsupported']);assert zero<1e-12
        # Model zero + six individual affine probes, independent of GT.
        V0=c.base.verts_packed();q=torch.zeros(6,device=device,requires_grad=True);vg=V0*q[3:].exp()+q[:3];assert torch.equal(vg,V0)
        for k in range(6):
            t=torch.zeros(6,device=device);t[k]=.01;vv=V0*t[3:].exp()+t[:3]
            expected=V0.clone()
            if k<3:expected[:,k]+=.01
            else:expected[:,k-3]*=float(np.exp(.01))
            assert torch.allclose(vv,expected,atol=1e-6)
        for cid in c.fit:
            off=torch.zeros_like(V0,requires_grad=True);m=c.base.offset_verts(off);dep.begin(m);loss,info=dep.loss(m,cid);g=torch.autograd.grad(loss,off)[0];norm=float(g.norm());ix=int(g.abs().argmax());vi,ax=divmod(ix,3);checks=[]
            for h in[1e-4,1e-5]:
                vals=[]
                for sg in[-1,1]:
                    delta=torch.zeros_like(V0);delta[vi,ax]=h*sg;mm=Meshes(verts=[V0.double()+delta.double()],faces=[c.base.faces_packed()]);dep.begin(mm)
                    with torch.no_grad():ll,_=dep.loss(mm,cid);vals.append(float(ll))
                fd=(vals[1]-vals[0])/(2*h);ad=float(g[vi,ax]);checks.append(dict(h=h,vertex=vi,axis=ax,analytic=ad,finite_difference=fd,relative_error=abs(fd-ad)/max(1e-7,abs(fd),abs(ad))))
            # One dense, deterministic direction checks the entire actual parameter field.
            rng=np.random.default_rng(20261106);direction=tensor(rng.normal(size=tuple(V0.shape)),torch.float64);direction/=direction.norm();h=1e-5;vals=[]
            for sg in[-1,1]:
                mm=Meshes(verts=[V0.double()+direction*(sg*h)],faces=[c.base.faces_packed()]);dep.begin(mm)
                with torch.no_grad():ll,_=dep.loss(mm,cid);vals.append(float(ll))
            fd=(vals[1]-vals[0])/(2*h);ad=float((g*direction).sum());dense=dict(analytic=ad,finite_difference=fd,absolute_error=abs(fd-ad),relative_error=abs(fd-ad)/max(1e-7,abs(fd),abs(ad)))
            ok=bool(torch.isfinite(g).all())and 0<norm<100 and info['active_N']>0 and info['O3D_axial_agreement_max_mm']<.001 and min(t['relative_error']for t in checks)<.15 and (dense['relative_error']<.2 or dense['absolute_error']<1e-5)
            passed&=ok;rows.append(dict(case=name,view=cid,passed=ok,relative_prior_zero=zero,depth_gradient_norm=norm,info=info,maximum_component_checks=checks,full_dense_direction=dense));print(rows[-1],flush=True)
    save('metrics/PREFLIGHT.json',dict(passed=bool(passed),rows=rows,optimizer_steps=0,full_vertex_gradients=True,depth_gradient_source='FP64 analytic ray/selected-face intersection; no zbuf backward',finite_difference_precision='FP64 vertices avoid sub-ULP all-vertex perturbation; actual training gradients FP32. Original FP32 diagnostic failure retained.'))
if __name__=='__main__':main()
