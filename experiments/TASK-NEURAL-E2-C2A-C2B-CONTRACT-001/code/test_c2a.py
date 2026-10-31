"""C2a acceptance: analytic Sphere + actual frozen Ring CAD + synthetic BG."""
from context import *
from opacity import *
import traceback

def main():
    freeze('C2A_BEFORE_TEST.json',dict(stage='C2a only; C2b not started',official_density=asset(SDF/'code/model/density.py')))
    cfg=load(R/'config/C2_CONTRACT.json');checks=[]
    def check(name,ok,detail=None):
        checks.append(dict(test=name,pass_=bool(ok),detail=detail))
        if not ok:
            save('metrics/C2A_GATE.json',dict(mandatory_CPU_tests_passed=False,checks=checks,C2a='FAIL',C2b='NOT_STARTED',GPU='NOT_GRANTED'))
            raise AssertionError((name,detail))
    n=96;u,v=np.meshgrid(np.arange(n),np.arange(n));uv=np.c_[u.ravel(),v.ravel()]
    K=np.array([[100.,0,47.5],[0,100.,47.5],[0,0,1.]])
    T=np.eye(4);T[:3,3]=[0,0,-25]
    rays=vis.camera_rays(uv,K,T);factor=np.linalg.norm(rays[:,3:],axis=1);d=rays[:,3:]/factor[:,None];o=rays[:,:3]
    rs=SameCameraScene(ring('R10'),K,T,(n,n),str(VENDOR));ring_t=rs.cast(uv)['t_hit'].numpy()*factor
    # Two already-declared synthetic BG planes: left occluder z=1 and a rear
    # z=18 plane. This test geometry is never used as a real observation.
    vertices=np.array([[-7,-7,1],[-1,-7,1],[-1,7,1],[-7,7,1],[-20,-20,18],[20,-20,18],[20,20,18],[-20,20,18]],float)
    faces=np.array([[0,1,2],[0,2,3],[4,5,6],[4,6,7]])
    bgmesh=trimesh.Trimesh(vertices,faces,process=False);bg=SameCameraScene(bgmesh,K,T,(n,n),str(VENDOR))
    bg_hit=bg.cast(uv);bg_t=bg_hit['t_hit'].numpy()*factor;bg_primitive=bg_hit['primitive_ids'].numpy()
    center=np.array([1.,0.,5.]);radius=4.5
    sphere_entry,_=sphere_interval(o,d,center,radius);sphere_t=np.where(sphere_entry>0,sphere_entry,np.inf);sphere_t=np.nan_to_num(sphere_t,nan=np.inf)
    first=np.minimum(np.minimum(ring_t,bg_t),sphere_t)
    labels=np.zeros(len(o),int);labels[sphere_t==first]=1;labels[(ring_t==first)&np.isfinite(ring_t)]=2;labels[48*n+48]=255
    q=visibility_intervals(o,d,[0,0,5],9,ring_t,bg_t)
    sem=ray_semantics(labels,q,sphere_t,background_known=np.isfinite(bg_t))
    raw=lambda p:torch.linalg.vector_norm(p-torch.tensor(center),dim=-1)-radius
    out=integrate_visible(o,d,q,raw,beta_mm=.08,bins=cfg['quadrature_bins'],ray_z_cosine=1/factor)
    acc=out['opacity'].detach().numpy();classes=sem['class_id']
    check('five ray semantics present',set(classes)==set(range(5)),dict(zip(SEMANTICS,np.bincount(classes,minlength=5).tolist())))
    check('visible positive opacity responds to Sphere',float(np.median(acc[classes==0]))>.98,dict(N=int((classes==0).sum()),median=float(np.median(acc[classes==0]))))
    check('Ring/BG censored prefixes do not absorb hidden Sphere',float(np.quantile(acc[np.isin(classes,[2,3])],.95))<.02,dict(N=int(np.isin(classes,[2,3]).sum()),p95=float(np.quantile(acc[np.isin(classes,[2,3])],.95))))
    check('unknown has zero supervision weight',np.all(sem['mask_weight'][classes==4]==0))
    check('no hidden segment supervised',not sem['hidden_supervised'].any())
    sampled=out['t_mm'].detach().numpy();ids=out['active_ids']
    check('samples only inside finite ROI and before first occluder',np.all(sampled>=q['start_mm'][ids,None])and np.all(sampled<=q['end_mm'][ids,None])and np.all(sampled<q['cutoff_mm'][ids,None]))
    # A foreground annotation inconsistent with fixed CAD must be UNKNOWN,
    # never silently turned into a confident negative or camera adjustment.
    idx=int(np.flatnonzero((classes==2)&q['valid'])[0]);wrong_labels=np.array([1]);qq={k:np.asarray(val)[[idx]]for k,val in q.items()}
    conflict=ray_semantics(wrong_labels,qq,np.array([q['cutoff_mm'][idx]+1]),np.array([True]))
    check('positive mask/occluder contradiction retained as unknown',conflict['class_id'][0]==4 and conflict['mask_weight'][0]==0)
    # Old error: full ray terminator always absorbs, even with no Polyp.
    empty=integrate_visible(o[:32],d[:32],{k:np.asarray(val)[:32]for k,val in q.items()},lambda p:torch.ones(len(p),dtype=p.dtype)*5,.08)
    old=1-np.exp(-1e10*numpy_density(np.array([-1.]),.1001))[0]
    check('E0 saturated tail rejected for an empty Polyp field',old>.999999 and float(empty['opacity'].max())<1e-6,dict(old_opacity=old,new_max=float(empty['opacity'].max())))
    oe=np.array([[0.,0.,-20.]]);de=np.array([[0.,0.,1.]])
    qe=visibility_intervals(oe,de,[0,0,0],2,ring_t=np.array([4.]))
    def forbidden(p):raise AssertionError('empty/occluded interval queried SDF')
    ee=integrate_visible(oe,de,qe,forbidden)
    check('occluder before ROI evaluates zero SDF samples',ee['sample_N']==0 and float(ee['opacity'][0])==0)
    # Continuous moving BG cutoff, with Sphere fixed and central ray in Ring hole.
    stops=np.linspace(21.,29.,2001);oo=np.tile(oe,(len(stops),1));dd=np.tile(de,(len(stops),1))
    qc=visibility_intervals(oo,dd,[0,0,5],6,background_t=stops)
    sphere=lambda p:torch.linalg.vector_norm(p-torch.tensor([0.,0.,5.]),dim=-1)-2.
    sweep=integrate_visible(oo,dd,qc,sphere,.08)['opacity'].detach().numpy();jump=np.max(abs(np.diff(sweep)))
    check('opacity continuous as background crosses Sphere',jump<cfg['continuity_max_step']and sweep[-1]>.98 and sweep[0]<1e-6,dict(max_adjacent_change=jump,step_mm=float(stops[1]-stops[0]),start=sweep[0],end=sweep[-1]))
    table('metrics/C2A_OPACITY_CONTINUITY.csv',[dict(background_t_mm=t,opacity=a)for t,a in zip(stops,sweep)])
    # Known analytic integral for a constant interior density: independent target.
    edges=np.linspace(2.,3.,129);sdf=torch.full((128,),-1.,dtype=torch.float64);weights=finite_cell_weights(sdf,edges,.08)
    expected=-np.expm1(-float(numpy_density(np.array([-1.]),.08)[0]))
    check('finite opacity matches closed-form Beer-Lambert integral',abs(float(weights.sum())-expected)<cfg['analytic_abs_tol'])
    clipped=clip_sampler_edges(np.array([0.,1.,2.,2.5,3.,4.,1e10]),2.1,2.9)
    check('adaptive sampler bridge inserts ROI bounds and excludes terminator',np.array_equal(clipped,np.array([2.1,2.5,2.9])))
    check('source rays use axial Z to ray length conversion',np.max(abs(unproject(np.full(len(uv),30.),T,uv,K)-(o+d*(30*factor)[:,None])))<1e-6)
    x=torch.tensor([[2.,3.,4.],[6.,-4.,9.]],dtype=torch.float64);origin=[1.,-2.,3.];scale=23.
    norm=world_to_network(x,origin,scale);check('world/network units close in mm',float(abs(norm*scale+torch.tensor(origin)-x).max())<cfg['unit_roundtrip_mm'])
    # Unit-normalized density and interval lengths preserve optical depth.
    netweights=finite_cell_weights(sdf/scale,edges/scale,.08/scale)
    check('opacity invariant to mm/network gauge',float(abs(netweights-weights).max())<cfg['analytic_abs_tol'])
    # Differentiable analytic geometry only; never optimize/update any parameter.
    theta=torch.tensor(2.,dtype=torch.float64,requires_grad=True);og=np.array([[2.1,0.,-8.]]);dg=np.array([[0.,0.,1.]])
    qg=visibility_intervals(og,dg,[0,0,0],5)
    def predict(r):return integrate_visible(og,dg,qg,lambda p:torch.linalg.vector_norm(p,dim=-1)-r,.08)['opacity'][0]
    ag=predict(theta);deriv=torch.autograd.grad(ag,theta,retain_graph=True)[0];eps=1e-5;fd=(predict(theta.detach()+eps)-predict(theta.detach()-eps))/(2*eps)
    check('geometry gradient agrees with independent finite differences',abs(float(deriv-fd))<cfg['gradient_abs_tol']and float(deriv)>0,dict(autograd=float(deriv),finite_difference=float(fd)))
    pos=-ag.clamp(1e-8,1-1e-8).log();neg=-torch.log1p(-ag.clamp(1e-8,1-1e-8))
    gp=torch.autograd.grad(pos,theta,retain_graph=True)[0];gn=torch.autograd.grad(neg,theta)[0]
    check('positive/negative Mask losses have opposite nonzero geometry gradients',float(gp)<0 and float(gn)>0,dict(positive=float(gp),negative=float(gn)))
    unknown_loss=masked_opacity_loss(dict(opacity=ag[None]),dict(mask_weight=[0.],mask_target=[1.]))
    check('unknown contributes zero Mask loss',float(unknown_loss)==0)
    # Ring-first rays and true BG geometry are independently raycast by the
    # reused SameCameraScene; constant z rear plane has known exact intersections.
    rear=(bg_primitive>=2)&(bg_primitive<4);expected_t=(18-T[2,3])*factor[rear]
    check('background mesh first-hit coordinates are axial/ray consistent',np.max(abs(bg_t[rear]-expected_t))<.002,dict(rear_triangle_hit_N=int(rear.sum()),max_error_mm=float(np.max(abs(bg_t[rear]-expected_t))),selection='actual primitive_id 2/3; no ray-length heuristic'))
    counts=[dict(class_name=s,N=int((classes==i).sum()),active_prefix_N=int(((classes==i)&q['valid']).sum()),median_opacity=float(np.median(acc[classes==i])),mask_weight_sum=float(sem['mask_weight'][classes==i].sum()))for i,s in enumerate(SEMANTICS)]
    table('metrics/C2A_SYNTHETIC_CLASSES.csv',counts)
    table('metrics/C2A_TESTS.csv',checks)
    np.savez_compressed(R/'local_results/C2A_synthetic.npz',opacity=acc.reshape(n,n),class_id=classes.reshape(n,n),sphere_t=sphere_t.reshape(n,n),ring_t=ring_t.reshape(n,n),background_t=bg_t.reshape(n,n),cutoff=q['end_mm'].reshape(n,n),labels=labels.reshape(n,n),K=K,c2w=T,plane_vertices=vertices,plane_faces=faces)
    save('metrics/C2A_SYNTHETIC_GATE.json',dict(C2a='SYNTHETIC_CPU_PASS',mandatory_CPU_tests_passed=True,check_N=len(checks),checks=checks,
        official_network_forward_N=0,model_weight_update_N=0,GPU='NOT_GRANTED',official_integration='CALLABLE_RAW_SDF_PROTOCOL_IMPLEMENTED; no official neural execution',
        five_semantics=SEMANTICS,background='synthetic mesh proof; real background use separately gated by cached source quality',
        permitted_next_stage='C2a real camera/CAD/background link validation',formal_GPU_science='NOT_READY_OFFICIAL_INTEGRATION_AND_AUTHORIZATION_PENDING'))
    save('metrics/C2A_GATE.json',dict(C2a='SYNTHETIC_PASS_REAL_LINK_PENDING',mandatory_CPU_tests_passed=False,C2b='NOT_STARTED',GPU='NOT_GRANTED'))
    save('provenance/C2A_EXECUTED_REUSE.json',REUSE)
    print('C2A_SYNTHETIC_COMPLETE',len(checks),'CPU acceptance checks; validate real links before C2b',flush=True)

if __name__=='__main__':main()
