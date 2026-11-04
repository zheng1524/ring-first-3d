"""Deterministic geometry/unknown/gradient tests, before formal fits."""
from losses import *
from trust_region import *
from mesh_basis import *
from observability import decompose
import time
def main():
    tests=[]
    def check(name,p,**details):tests.append(dict(name=name,passed=bool(p),**details));assert p,name
    p=Problem('G01_004','E1');V=p.V0.clone().requires_grad_(True);o=p.o[0];z,ok,_=exact_depth(V,p.F,o['uv'],o['Kn'],o['T']);cpu=cast(mesh_scene(p.b['V'],p.F),o['uv'],o['Kn'],o['T'])[0]
    check('EXACT_NATIVE_TRIANGLE_FIRST_Z',np.max(abs(z.detach().cpu().numpy()[ok]-cpu[ok]))<.0001,max_error_mm=float(np.max(abs(z.detach().cpu().numpy()[ok]-cpu[ok]))))
    zi=int(np.flatnonzero(ok)[100]);g=torch.autograd.grad(z[zi],V)[0];d=tensor(np.array([.2,-.3,.7]))[None].expand_as(V);analytic=float((g*d).sum());h=.001
    with torch.no_grad():za=exact_depth(V+d*h,p.F,o['uv'][zi:zi+1],o['Kn'],o['T'])[0];zb=exact_depth(V-d*h,p.F,o['uv'][zi:zi+1],o['Kn'],o['T'])[0]
    fd=float((za-zb)/(2*h));check('REAL_NATIVE_FULL_VERTEX_DEPTH_GRADIENT',abs(analytic-fd)<.02,autograd=analytic,finite_difference=fd)
    for scene in protocol()['scenes']:
        for initial in ['E1','E2']:
            b=dict(np.load(R/'inputs'/f'{scene}_{initial}_basis.npz'));u=np.random.default_rng(42).normal(0,.01,128);before=shape(b,u);u2=u.copy();u2[44:]=0
            check(scene+initial+'_M_ORTHOGONAL',float(b['raw_orth'])<1e-7 and float(b['tangent_overlap'])<1e-7)
            check(scene+initial+'_ZERO_AND_STAGE_TRANSFER',np.array_equal(shape(b,np.zeros(128)),b['V'])and np.array_equal(shape(b,u2),b['V']+b['n']*(b['phi']@u2)[:,None]))
    # Unknown Ring cells retain their known-pixel conditional proportion.
    check('ALL_FULL_MASK_MASS_PRESERVED',all(abs((obs(c)['target']*obs(c)['known_mass']).sum()*4-(source(c)['labels']==1).sum())<1e-8 for c in p.ids))
    A=np.array([[1.,0,1],[0,1,1],[0,0,0],[0,0,0]]);Q,s,rank=decompose(A);check('SVD_RANK_AND_COMPACT_PROJECTOR',rank==2 and np.linalg.norm(A-Q@(Q.T@A))<1e-10)
    si=self_intersections(p.b['V'],p.F);check('P0_NO_NONADJACENT_SELF_INTERSECTION',si['intersections']==0,**si)
    # Actual triangle/triangle crossing, not just a normal-flip surrogate.
    vv=np.array([[-1,0,0],[1,0,0],[0,2,0],[0,.5,-1],[0,.5,1],[0,1.5,.2]],float);ff=np.array([[0,1,2],[3,4,5]])
    check('TRIANGLE_CROSSING_DETECTED',self_intersections(vv,ff)['intersections']>0)
    a=torch.zeros(128,device='cuda',requires_grad=True);samples=[]
    for k in range(5):
        t=time.monotonic();loss,parts,_=p.objective(a,p.schedule(0,k));grad=torch.autograd.grad(loss,a)[0];torch.cuda.synchronize();samples.append(time.monotonic()-t)
        check('FINITE_REAL_NETWORK_FREE_GEOMETRY_GRADIENT_'+str(k),bool(torch.isfinite(grad).all())and float(grad.norm())>0)
    save('metrics/CONTRACT_TESTS.json',tests);save('metrics/PERFORMANCE.json',dict(gradient_seconds=samples,steady_gradient_seconds=float(np.median(samples[1:])),GPU_peak_bytes=torch.cuda.max_memory_allocated(),planned_primary_runs=48,planned_count_matched_runs=32,gradient_budget_per_run=120,notes='native exact triangle ray selection CPU; GPU silhouette and all geometry parameter gradients; P0 J shared across arms/seeds'))
    print('CONTRACTS',len(tests),'PASS','BENCH',samples,flush=True)
if __name__=='__main__':main()
