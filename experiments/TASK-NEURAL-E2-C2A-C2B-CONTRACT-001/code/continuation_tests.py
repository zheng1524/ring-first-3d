"""New CPU wiring checks only; no E1/E2 stage-suite repetition or model forward."""
from continuation_context import *
from finite_joint_adapter import *
from opacity import integrate_visible
import copy


class AnalyticImplicit:
    """Official raw-head signature, explicitly not a neural model."""
    def __init__(self,theta,scale):self.theta=theta;self.scale=scale;self.calls=0;self.clamp_calls=0
    def forward(self,x):
        self.calls+=1
        radius=self.theta[0]/self.scale;shift=torch.stack([self.theta[1]*0,self.theta[1]*0,self.theta[1]/self.scale])
        sdf=self.theta[2]*(torch.linalg.vector_norm(x-shift,dim=-1)-radius)
        # Raw features share analytic geometry to exercise RGB-to-geometry paths.
        return torch.cat([sdf[:,None],x,sdf[:,None]],dim=1)
    def get_outputs(self,*args):self.clamp_calls+=1;raise AssertionError('CLAMPED_HEAD_FORBIDDEN')
    def get_sdf_vals(self,*args):self.clamp_calls+=1;raise AssertionError('CLAMPED_HEAD_FORBIDDEN')


class AnalyticRadiance:
    def __init__(self,color):self.color=color;self.indices=[]
    def forward(self,points,normals,view_dirs,feature_vectors,indices):
        self.indices.append(indices)
        return torch.sigmoid(self.color[None,:]+.12*points+.07*normals+.03*view_dirs+feature_vectors[:,-1:])


def proposals(packet,scale,bins=256):
    a=np.asarray(packet['start']);b=np.asarray(packet['end']);u=np.linspace(0,1,bins+1)
    interior=a[:,None]+(b-a)[:,None]*u
    return np.c_[np.zeros(len(a)),interior,np.full(len(a),1e10)]/scale


def main():
    cfg=dict(test_only=True,loss_coefficients=dict(rgb=1.,mask=.1,depth=.1,eikonal=.1),
        physical_depth_normalization_mm=1.,rgb_huber_delta=.05,synthetic_beta_mm=.08,
        proposal_bins=256,gradient_nonzero_threshold=1e-10,FD_epsilon_mm=1e-5,FD_abs_tol=2e-4,
        source_selection='exact frozen E2 batch; no resampling/parameter search',
        scientific_training_coefficients='UNSET; test coefficients are not approved scientific budgets',
        official_runtime='NOT_EXECUTED; API/source static binding plus analytic callables',GPU='NOT_GRANTED')
    csave('config/JOINT_WIRING_CPU.json',cfg);freeze_continuation();checks=[];responses=[];artifacts=[]
    def check(name,ok,detail=None):
        row=dict(test=name,pass_=bool(ok),detail=detail);checks.append(row)
        if not ok:
            csave('metrics/JOINT_WIRING_GATE.json',dict(status='FAIL',checks=checks,GPU='NOT_GRANTED'))
            raise AssertionError((name,detail))
    official=[]
    for cls,name,file in [('ImplicitNetwork','forward','network.py'),('ImplicitNetwork','get_outputs','network.py'),
        ('ImplicitNetwork','get_sdf_vals','network.py'),('RenderingNetwork','forward','network.py'),
        ('UniformSampler','get_z_vals','ray_sampler.py'),('ErrorBoundSampler','get_z_vals','ray_sampler.py'),
        ('MonoSDFLoss','get_eikonal_loss','loss.py'),('MonoSDFLoss','get_depth_loss','loss.py')]:
        f,info=official_method(SDF/'code/model'/file,cls,name);official.append(info)
        if cls=='RenderingNetwork':check('official radiance signature bound',info['args']==['self','points','normals','view_dirs','feature_vectors','indices'])
        if name in ['get_outputs','get_sdf_vals']:check('official clamped method identified '+name,'torch.minimum' in ast.unparse(f))
        if name=='get_depth_loss':check('official legacy affine/scale-shift depth loss not reused','50' in ast.unparse(f))
        if name=='get_z_vals':check('official sampler device assumptions recorded '+cls,'.cuda()' in ast.unparse(f))
    csave('provenance/OFFICIAL_API_BINDING.json',dict(methods=official,executed_method='MonoSDFLoss.get_eikonal_loss exact AST only',
        neural_forward_N=0,official_sampler_execution_N=0,reason='official sampler has CUDA-specific allocations and calls clamped head; requires separately authorized runtime port/binding'))
    domains=load(BASE/'config/SDF_INITIALIZATION_CANDIDATE.json')['scenes'];state=[]
    for scene,refs in selected().items():
        domain=domains[scene];scale=domain['mm_per_unit'];packets=[source_packet(x) for x in refs]
        theta=torch.tensor([domain['proposed_init_radius_mm'],0.,1.1],dtype=torch.float64,requires_grad=True)
        color=torch.tensor([.1,-.2,.3],dtype=torch.float64,requires_grad=True)
        beta=torch.tensor(cfg['synthetic_beta_mm']/scale,dtype=torch.float64,requires_grad=True)
        original=[p.detach().clone() for p in [theta,color,beta]]
        implicit=AnalyticImplicit(theta,scale);radiance=AnalyticRadiance(color)
        adapter=FiniteJointAdapter(implicit,radiance,domain['world_origin_mm'],scale,beta)
        preds=[adapter.render(b,proposals(b,scale,cfg['proposal_bins']),i) for i,b in enumerate(packets)]
        points=np.concatenate([b['origin'][:32]+b['direction'][:32]*((b['start'][:32]+b['end'][:32])/2)[:,None] for b in packets])
        eik=adapter.eikonal(points)
        terms,counts=joint_losses(preds,packets,[scene]*3,dict.fromkeys(refs,1/3),eik,cfg['loss_coefficients'])
        check('three frozen source RGB/ray packets '+scene,len(packets)==3 and all(len(x['RGB'])==320 for x in packets))
        check('raw head bypasses both clamped helpers '+scene,implicit.calls>0 and implicit.clamp_calls==0)
        check('official per-reference radiance index supplied '+scene,set(radiance.indices)=={0,1,2})
        check('official Eikonal expression gives analytic amplitude result '+scene,abs(float(eik.detach())-.01)<1e-12)
        for b,p in zip(packets,preds):
            check('finite sampler contract '+b['source'],all(z['min_t_mm']>=b['start'][z['ray']]-1e-9 and z['max_t_mm']<=b['end'][z['ray']]+1e-9 for z in p['query_limits']))
            check('missed depths remain NaN '+b['source'],bool(torch.isnan(p['axial_depth_mm'][~p['render_hit']]).all()))
            check('RGB restricted to interior/front hits '+b['source'],counts[b['source']]['RGB_N']<=int((b['sampling_class']==0).sum()) and counts[b['source']]['RGB_N']>0)
            check('all source losses retain denominators '+b['source'],counts[b['source']]['observed_N']==counts[b['source']]['valid_N']+counts[b['source']]['miss_N'])
        for name,value in terms.items():
            grads=torch.autograd.grad(value,[theta,color,beta],retain_graph=True,allow_unused=True)
            norms=[0. if g is None else float(torch.linalg.vector_norm(g.detach())) for g in grads]
            check('finite geometry gradient '+scene+' '+name,bool(torch.isfinite(value)) and all(g is None or bool(torch.isfinite(g).all()) for g in grads) and norms[0]>cfg['gradient_nonzero_threshold'],norms)
            if name in ['rgb','total']:check('RGB radiance-parameter gradient '+scene+' '+name,norms[1]>cfg['gradient_nonzero_threshold'],norms)
            if name in ['mask','depth','total']:check('physical beta gradient '+scene+' '+name,norms[2]>cfg['gradient_nonzero_threshold'],norms)
            responses.append(dict(scene=scene,loss=name,value=float(value.detach()),geometry_gradient_norm=norms[0],radiance_gradient_norm=norms[1],beta_network_gradient_norm=norms[2],
                per_source_counts=counts,official_model_prediction=False,parameters_updated=False))
        # Deliberately remove every hit from one source. The old reducer by
        # itself permits partial means; the new three-reference entry rejects it.
        failed=[dict(p) for p in preds];failed[0]['render_hit']=np.zeros_like(preds[0]['render_hit'])
        failed[0]['axial_depth_mm']=torch.full_like(preds[0]['axial_depth_mm'],float('nan'))
        try:joint_losses(failed,packets,[scene]*3,dict.fromkeys(refs,1/3),eik,cfg['loss_coefficients']);denied=False
        except IncompleteReferenceError as exc:denied=exc.counts[refs[0]]['valid_N']==0
        check('all-miss reference cannot be dropped from joint mean '+scene,denied)
        try:joint_losses(preds,packets,[scene,scene,'OTHER'],dict.fromkeys(refs,1/3),eik,cfg['loss_coefficients']);denied=False
        except ValueError:denied=True
        check('cross-video joint loss rejected '+scene,denied)
        check('analytic parameters unchanged '+scene,all(torch.equal(p.detach(),q) for p,q in zip([theta,color,beta],original)))
        folder=R/'local_results/continuation_cpu';folder.mkdir(exist_ok=True)
        for ref,p in zip(refs,preds):
            path=folder/(ref+'_joint_response.npz');np.savez_compressed(path,opacity=p['opacity'].detach().numpy(),rgb=p['rgb_values'].detach().numpy(),axial_Z_mm=p['axial_depth_mm'].detach().numpy(),render_hit=p['render_hit'])
            artifacts.append(asset(path))
        state.append(dict(scene=scene,counts=counts,model_identity=scene+'_SHARED_POLYP_SDF',
            source_ROI_rule=domain['rule'] if 'rule'in domain else'radius=0.5*fixed source ROI',analytic_beta_mm=cfg['synthetic_beta_mm'],
            official_beta='UNSET',no_updates=True))
    # Independent scalar finite difference of Mask->raw geometry on a grazing ray.
    radius=torch.tensor([2.,0.,1.],dtype=torch.float64,requires_grad=True);cp=torch.tensor([.1,.1,.1],dtype=torch.float64,requires_grad=True)
    pp=dict(origin=np.array([[2.1,0.,-8.]]),direction=np.array([[0.,0.,1.]]),cosine=np.array([1.]),start=np.array([3.]),end=np.array([13.]),valid=np.array([True]))
    def prediction(rad):
        ad=FiniteJointAdapter(AnalyticImplicit(rad,1.),AnalyticRadiance(cp),[0,0,0],1.,torch.tensor(.08,dtype=torch.float64))
        return ad.render(pp,proposals(pp,1.,512),0)['opacity'][0]
    out=prediction(radius);g=torch.autograd.grad(out,radius)[0][0];eps=cfg['FD_epsilon_mm']
    offset=torch.tensor([eps,0,0]);fd=(prediction(radius.detach()+offset)-prediction(radius.detach()-offset))/(2*eps)
    check('new raw/radiance bridge gradient matches finite differences',abs(float(g-fd))<cfg['FD_abs_tol'] and float(g)>0,dict(autograd=float(g),finite_difference=float(fd)))
    # Independent RGB path derivative, on an actual front-hit analytic ray.
    pp_rgb=dict(pp,origin=np.array([[.4,0.,-8.]]))
    def rgb_value(rad):
        ad=FiniteJointAdapter(AnalyticImplicit(rad,1.),AnalyticRadiance(cp),[0,0,0],1.,torch.tensor(.08,dtype=torch.float64))
        return ad.render(pp_rgb,proposals(pp_rgb,1.,512),0)['rgb_values'][0].sum()
    rg=torch.autograd.grad(rgb_value(radius),radius)[0][0]
    rfd=(rgb_value(radius.detach()+offset)-rgb_value(radius.detach()-offset))/(2*eps)
    check('RGB-to-geometry derivative matches independent finite difference',abs(float(rg-rfd))<cfg['FD_abs_tol'] and abs(float(rg))>1e-6,dict(autograd=float(rg),finite_difference=float(rfd)))
    # An empty interval must not query either callable, including its boundary.
    class NoQuery:
        def forward(self,*a):raise AssertionError('EMPTY_INTERVAL_QUERIED')
    empty=FiniteJointAdapter(NoQuery(),NoQuery(),[0,0,0],1.,torch.tensor(.08))
    ep=empty.render(dict(pp,valid=np.array([False])),proposals(pp,1.),0)
    check('empty finite intervals perform zero raw/radiance calls',ep['raw_query_N']==0 and float(ep['opacity'][0])==0 and bool(torch.isnan(ep['axial_depth_mm'][0])))
    # Optical depth must be invariant to physical network gauge.
    gauge=FiniteJointAdapter(AnalyticImplicit(radius,23.),AnalyticRadiance(cp),[0,0,0],23.,torch.tensor(.08/23.,dtype=torch.float64))
    scaled=gauge.render(pp,proposals(pp,23.,512),0)['opacity'][0]
    check('new bridge opacity invariant under mm/network gauge',abs(float(scaled-out))<1e-10,dict(abs_difference=float(abs(scaled-out).detach())))
    try:empty.render(pp,np.array([0.,float('inf')]),0);denied=False
    except ValueError:denied=True
    check('nonfinite sampler proposals fail explicitly',denied)
    try:FiniteJointAdapter(NoQuery(),NoQuery(),[0,0,0],1.,torch.tensor(-.08));denied=False
    except ValueError:denied=True
    check('negative physical density beta rejected',denied)
    # Reject non-CPU official module injection without ever importing/running it.
    Fake=type('BlockedOfficial',(),{'__module__':'model.network'})
    try:FiniteJointAdapter(Fake(),AnalyticRadiance(cp),[0,0,0],1.,torch.tensor(.08));denied=False
    except PermissionError:denied=True
    check('official neural execution remains blocked',denied)
    check('new adapter did not import official neural module',not any(n=='model.network' or n.startswith('mapanything.models') for n in sys.modules))
    ctable('metrics/JOINT_LOSS_GRADIENTS.csv',responses);ctable('metrics/JOINT_WIRING_TESTS.csv',checks)
    csave('metrics/JOINT_WIRING_GATE.json',dict(status='PASS_ANALYTIC_CPU_WIRING_ONLY',check_N=len(checks),checks=checks,scenes=state,
        GPU='NOT_GRANTED',official_neural_forward_N=0,official_sampler_execution_N=0,weights_loaded_N=0,weight_update_N=0,
        official_runtime_verified=False,formal_GPU_ready=False))
    csave('provenance/ANALYTIC_RESPONSE_ARTIFACTS.json',artifacts)
    print('CONTINUATION_CPU_WIRING_COMPLETE',len(checks),'checks; official neural/sampler execution0; updates0')


if __name__=='__main__':main()
