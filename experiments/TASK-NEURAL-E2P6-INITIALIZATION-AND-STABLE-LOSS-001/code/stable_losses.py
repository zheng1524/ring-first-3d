"""Finite-opacity BCE in log optical depth, and conditional weak HERO anchor."""
from common import *

def log_density(f,beta):
    positive=-torch.log(2*beta)-f/beta
    negative=-torch.log(beta)+torch.log1p(-.5*torch.exp(torch.clamp_max(f/beta,0)))
    return torch.where(f>=0,positive,negative)

def stable_density(self,f,beta):
    return torch.exp(log_density(f,beta))

_fn,_info=official_method(E2C/'code/finite_joint_adapter.py','FiniteJointAdapter','render')
_ns=dict(e25.legacy.__dict__)
_celltree=ast.parse((E2C/'code/opacity.py').read_text());_cell=next(n for n in _celltree.body if isinstance(n,ast.FunctionDef)and n.name=='finite_cell_weights')
_cellns=dict(opacity.__dict__,official_density_func=stable_density)
exec(compile(ast.Module(body=[_cell],type_ignores=[]),str(E2C/'code/opacity.py'),'exec'),_cellns)
_ns['finite_cell_weights']=_cellns['finite_cell_weights']
exec(compile(ast.Module(body=[_fn],type_ignores=[]),str(E2C/'code/finite_joint_adapter.py'),'exec'),_ns)

class FiniteCPU(e25.AuthorizedFiniteCPU):
    # EXACT prior renderer AST; only equivalent, tail-stable density binding.
    render=_ns['render']

def proposal(b,scale):
    # Interior boundaries only; the reused clipper inserts exact ROI endpoints.
    u=np.arange(1,cfg()['sample_cells'])/cfg()['sample_cells']
    return (b['start'][:,None]+(b['end']-b['start'])[:,None]*u)/scale

def packet(ref,split):
    with np.load(R/f'local_results/packets/{ref}_{split}.npz')as z:
        b={k:z[k] for k in z.files}
    b['source']=str(b['source']);return b

def mask_bundle(model,domain,b,dtype=torch.float64,subset=None):
    valid=b['valid']&(b['mask_weight']>0)
    if subset is not None:valid&=subset
    ix=np.flatnonzero(valid)
    o=torch.tensor(b['origin'][ix],dtype=dtype);d=torch.tensor(b['direction'][ix],dtype=dtype)
    a=torch.tensor(b['start'][ix],dtype=dtype);end=torch.tensor(b['end'][ix],dtype=dtype);cells=cfg()['sample_cells']
    u=(torch.arange(cells,dtype=dtype)+.5)/cells;t=a[:,None]+(end-a)[:,None]*u
    X=o[:,None]+d[:,None]*t[:,:,None];scale=domain['mm_per_unit'];origin=torch.tensor(domain['world_origin_mm'],dtype=dtype)
    f=model.implicit_network.forward(((X-origin)/scale).reshape(-1,3))[:,0].reshape(len(ix),cells)*scale
    beta=model.density.get_beta()*scale;log_delta=torch.log((end-a)/cells)[:,None]
    logsigma=log_density(f,beta);logtau=torch.logsumexp(logsigma+log_delta,1)
    safe_tau=torch.exp(logtau.clamp_min(-20));logp=torch.where(logtau<-20,logtau,torch.log(-torch.expm1(-safe_tau)))
    y=torch.tensor(b['mask_target'][ix],dtype=dtype);w=torch.tensor(b['mask_weight'][ix],dtype=dtype)
    terms=-y*logp+(1-y)*torch.exp(logtau)
    stable=(terms*w).sum()/w.sum()
    # Preserve old arithmetic and its clamp, including FP32 failures, as baseline.
    old_sigma=opacity.official_density_func(None,f,beta=beta)
    old_tau=(old_sigma*torch.exp(log_delta)).sum(1);old_p=-torch.expm1(-old_tau)
    old_loss=opacity.masked_opacity_loss(dict(opacity=old_p),dict(mask_weight=w,mask_target=y))
    return dict(stable=stable,old=old_loss,per_ray=terms,active_ids=ix,raw_sdf=f,logtau=logtau,
        beta=beta,delta=(end-a)/cells,weights=w,targets=y,t=t,points_mm=X,
        opacity=-torch.expm1(-torch.exp(logtau)))

def weak_anchor(model,domain,b,dtype=torch.float64):
    obs=(b['depth_weight']>0)&np.isfinite(b['target_Z'])&(b['target_Z']>0)
    ids=np.flatnonzero(obs);t=b['target_Z'][ids]/b['cosine'][ids]
    assert np.all(t>=b['start'][ids])and np.all(t<=b['end'][ids]),'HERO outside certified visible segment'
    X=b['origin'][ids]+b['direction'][ids]*t[:,None]
    dtype=next(model.parameters()).dtype
    points=torch.tensor(X,dtype=dtype);x=(points-torch.tensor(domain['world_origin_mm'],dtype=dtype))/domain['mm_per_unit']
    f=model.implicit_network.forward(x)[:,0]*domain['mm_per_unit'];a=f.abs();delta=cfg()['weak_anchor']['delta_mm']
    h=torch.where(a<=delta,.5*f**2/delta,a-.5*delta);w=torch.tensor(b['depth_weight'][ids],dtype=dtype)
    return dict(loss=(h*w).sum()/w.sum(),f=f,ids=ids,points_mm=X,weights=w)

def sdf_only(model,domain,b):
    n=len(b['source_pixel']);valid=np.asarray(b['valid']);ids=np.flatnonzero(valid);cells=cfg()['sample_cells']
    a=b['start'][ids];end=b['end'][ids];u=(np.arange(cells)+.5)/cells;t=a[:,None]+(end-a)[:,None]*u
    points=b['origin'][ids,None]+b['direction'][ids,None]*t[:,:,None]
    x=(points-np.array(domain['world_origin_mm']))/domain['mm_per_unit']
    dtype=next(model.parameters()).dtype
    with torch.no_grad():
        f=model.implicit_network.forward(torch.tensor(x.reshape(-1,3),dtype=dtype))[:,0].reshape(len(ids),cells)*domain['mm_per_unit']
        start=b['origin'][ids]+b['direction'][ids]*a[:,None]
        fs=model.implicit_network.forward(torch.tensor((start-domain['world_origin_mm'])/domain['mm_per_unit'],dtype=dtype))[:,0]*domain['mm_per_unit']
        beta=model.density.get_beta()*domain['mm_per_unit'];tau=(torch.exp(log_density(f,beta))*torch.tensor((end-a)/cells,dtype=dtype)[:,None]).sum(1)
        mass=-torch.expm1(-tau);front=((f[:,:-1]>0)&(f[:,1:]<=0)).any(1)|((fs>=0)&(f[:,0]<0));hit=front&(mass>=1e-4)
    out_f=np.full((n,cells),np.nan);out_f[ids]=f.numpy();opacity_values=np.zeros(n);opacity_values[ids]=mass.numpy()
    raw_cross=np.zeros(n,bool);raw_cross[ids]=front.numpy();front_hit=np.zeros(n,bool);front_hit[ids]=hit.numpy();start_sdf=np.full(n,np.nan);start_sdf[ids]=fs.numpy()
    return dict(raw_sdf=out_f,opacity=opacity_values,raw_front_cross=raw_cross,render_hit=front_hit,
        t_mm=b['start'][:,None]+(b['end']-b['start'])[:,None]*u,start_sdf=start_sdf)
