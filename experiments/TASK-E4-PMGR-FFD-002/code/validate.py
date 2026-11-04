from inputs import *
from shape import *
from objective import Objective
from physical import blender_check
from collision import fcl_object
from renderer import tensor,clips
import fcl,time

def main():
    rows=[]
    def check(name,passed,**kw):
        rows.append(dict(name=name,passed=bool(passed),**kw));save('metrics/PRE_RUN_VALIDATION.json',rows);print(name,passed,flush=True);assert passed,name
    P=torch.tensor([[0.,0.,0.],[.2,.4,.7],[1.,1.,1.]],dtype=torch.float64);d=torch.zeros((2,2,2,3),dtype=P.dtype,requires_grad=True);out=free_form_deform_points(P,d,torch.zeros(3),torch.ones(3));check('FFD_ZERO_IDENTITY',torch.equal(P,out));d2=d.detach().clone();d2[1,1,1]=torch.tensor([2.,0.,.8]);expected=P+torch.prod(P,dim=1)[:,None]*torch.tensor([2.,0.,.8]);check('PYGEM_CORNER_DISPLACEMENT_REFERENCE',torch.max(abs(free_form_deform_points(P,d2,torch.zeros(3),torch.ones(3))-expected))<1e-12)
    out.square().sum().backward();h=1e-5;plus=d.detach().clone();minus=d.detach().clone();plus[1,1,1,0]+=h;minus[1,1,1,0]-=h;fd=float((free_form_deform_points(P,plus,torch.zeros(3),torch.ones(3)).square().sum()-free_form_deform_points(P,minus,torch.zeros(3),torch.ones(3)).square().sum())/(2*h));check('FFD_CONTROL_AUTOGRAD',abs(fd-float(d.grad[1,1,1,0]))<1e-8,FD=fd,gradient=float(d.grad[1,1,1,0]))
    scene='G01_004';cp=dict(np.load(R1/'local_results/G01_004/P0.npz'));m=Body(p0(scene,'E2'),cp['q'][:9]);b=dict(np.load(R/'inputs/G01_004_FFD_PREFLIGHT.npz'));m.fields=b['fields'];q=np.r_[m.p,np.zeros(12)];check('FROZEN_SAFE_P0_EXACT_IDENTITY',abs(m.vertices(q)-cp['V']).max()<1e-10,max_mm=float(abs(m.vertices(q)-cp['V']).max()),P0_sha256=sha(R1/'local_results/G01_004/P0.npz'))
    q48=np.r_[q,np.zeros(36)];check('P1_P2_ZERO_RESIDUAL_TRANSFER',abs(m.vertices(q)-m.vertices(q48)).max()<1e-12)
    ob=Objective(scene,m);a=ob.evaluate(q,mask_only=True);noaa=ob.evaluate(q,mask_only=True,aa=False);check('MASK_AUTOGRAD_BOTH_PARAMETER_BLOCKS',np.isfinite(a['g']).all()and np.linalg.norm(a['g'][:9])>1e-6 and np.linalg.norm(a['g'][9:])>1e-6,live9_norm=float(np.linalg.norm(a['g'][:9])),FFD_norm=float(np.linalg.norm(a['g'][9:])),no_AA_gradient_norm=float(np.linalg.norm(noaa['g'])))
    directions=[np.r_[np.array([.2,-.1,.3,.02,-.03,.01,.01,.02,-.02]),np.zeros(12)],np.r_[np.zeros(9),np.random.default_rng(217).normal(size=12)*.2]]
    for name,direction in zip(['LIVE9_REAL_MASK_FD','FFD_REAL_MASK_FD'],directions):
        for h in [.0001,.0003]:
            fd=(ob.evaluate(q+h*direction,gradient=False,mask_only=True)['E']-ob.evaluate(q-h*direction,gradient=False,mask_only=True)['E'])/(2*h);analytic=float(a['g']@direction);rel=abs(fd-analytic)/max(abs(fd),abs(analytic),1e-4);check(name+'_LOCAL_'+str(h),rel<.15,FD=fd,gradient=analytic,relative_difference=rel,h=h,maximum_vertex_movement_mm=float(np.linalg.norm(m.vertices(q+h*direction)-m.vertices(q),axis=1).max()),scope='local antialias derivative only; larger raster-event failures retained separately')
    V=tensor(m.vertices(q));cid='G01_004_growth_r06';d=ob.data.views[cid];s=d['s'];out=ob.renderer.render(V,m.F,d['K'],s['T']);plain=ob.renderer.render(V,m.F,d['K'],s['T'],cad=False);behind=plain['hard'].cpu().numpy()&np.isfinite(d['cad'])&(plain['z'].cpu().numpy()>d['cad']+.05);behind=cv2.erode(behind.astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool);maximum=float(out['alpha'].detach().cpu().numpy()[behind].max())if behind.any()else None;check('REAL_RING_FIRST_OCCLUSION',behind.sum()>10 and maximum<1e-5,occluded_pixel_N=int(behind.sum()),maximum_opacity=maximum)
    # UNKNOWN invariance of the very same pixel objective, not a replacement.
    y=d['target'];known=d['known'];w=d['weight'];sdf=d['sdf']
    def cost(x):
        pr=.001+.998*x;return (-(y*torch.log(pr)+(1-y)*torch.log1p(-pr))*w).sum()+.5*(1-(2*(x*y*known).sum()+1)/((x*known).sum()+(y*known).sum()+1))+.1*((x-y)*sdf*w).sum()
    x=out['alpha'].detach();u=1-known;e0=cost(x*known);e1=cost(x*known+u);check('SYMMETRIC_FIXED_UNKNOWN_INVARIANCE',abs(float(e0-e1))<1e-7,unknown_pixel_N=int(u.sum()),difference=float(e0-e1))
    X=obs('G01_004_ref08')['X'];expected,z=vis.project_camera(X,s['K'],s['T']);clip,_=clips(tensor(X),s['K'],s['T'],(640,360));cl=clip.detach().cpu().numpy();actual=np.c_[(cl[:,0]/cl[:,3]+1)*640/2-.5,(1-cl[:,1]/cl[:,3])*360/2-.5];check('A_TO_B_CAMERA_PIXEL_CENTER',abs(actual-expected).max()<.001,max_pixel_error=float(abs(actual-expected).max()),world_points_from='ref08',projected_camera=cid)
    vv,uu=np.meshgrid(np.arange(180),np.arange(320),indexing='ij');xy=np.c_[uu.ravel(),vv.ravel()];z=cast(mesh_scene(m.vertices(q),m.F),xy,d['K'],s['T'])[0];cz=d['cad'].ravel();oracle=(np.isfinite(z)&(z<=cz)).reshape(180,320);hard=out['hard'].cpu().numpy();iou=float((hard&oracle).sum()/max(1,(hard|oracle).sum()));check('CUDA_RASTER_VS_FROZEN_CPU_CAMERA',iou>.98,IoU=iou,CPU='same actual triangles; not GT')
    for gap in [.05,-.05]:
        body=trimesh.creation.box([2,2,2]);cad=trimesh.creation.box([2,2,2]);cad.apply_translation([2+gap,0,0]);res=fcl.CollisionResult();n=fcl.collide(fcl_object(body.vertices,body.faces),fcl_object(cad.vertices,cad.faces),fcl.CollisionRequest(),res);b=blender_check('CONTROL_GAP_'+('POS'if gap>0 else'NEG'),scene,body.vertices,body.faces,cad);check('FCL_BLENDER_GAP_'+str(gap),(n==0 and b['EXACT_intersection_volume_mm3']==0)if gap>0 else(n>0 and b['EXACT_intersection_volume_mm3']>.19),FCL_collisions=n,Blender=b)
    start=time.perf_counter()
    for _ in range(3):ob.evaluate(q)
    elapsed=(time.perf_counter()-start)/3;save('metrics/PERFORMANCE.json',dict(seconds_full_objective_and_backward=elapsed,GPU_peak_allocated_MiB=torch.cuda.max_memory_allocated()/2**20,nominal_iterations_per_arm=sum(protocol()['iterations']),estimated_six_arm_seconds=elapsed*sum(protocol()['iterations'])*2*6,extra_physical_checks_not_included=True,full_plan_not_reduced=True));print('VALIDATION_ALL_PASS',len(rows),'seconds/objective',elapsed,flush=True)

if __name__=='__main__':
    from renderer import clips
    main()
