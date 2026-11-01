"""Thin device/dtype port of E2 finite renderer and E2.6 stable losses."""
from common import *
log_density=extract(E26/'code/stable_losses.py',['log_density'],dict(globals()))['log_density']
_f,_info=official_method(SDF/'code/model/loss.py','MonoSDFLoss','get_eikonal_loss');_ns=dict(torch=torch)
exec(compile(ast.Module(body=[_f],type_ignores=[]),str(SDF/'code/model/loss.py'),'exec'),_ns);official_eikonal=_ns['get_eikonal_loss']

def huber(e,delta):
    a=e.abs();return torch.where(a<=delta,.5*e**2/delta,a-.5*delta)

def raw(model,points_mm,normals=False,create_graph=True):
    x=(to_tensor(points_mm,model)-to_tensor(domain()['world_origin_mm'],model))/domain()['mm_per_unit']
    if normals:x=x.requires_grad_(True)
    q=model.implicit_network.forward(x)
    grad=torch.autograd.grad(q[:,0],x,torch.ones_like(q[:,0]),create_graph=create_graph,retain_graph=True)[0] if normals else None
    return q[:,0]*domain()['mm_per_unit'],q[:,1:],grad,x

def render(model,b,cells,index=0,create_graph=True,need_color=True):
    ids=np.flatnonzero(b['valid']);n=len(b['source_pixel']);ii=torch.tensor(ids,device=next(model.parameters()).device)
    o=to_tensor(b['origin'][ids],model);d=to_tensor(b['direction'][ids],model);a=to_tensor(b['start'][ids],model);end=to_tensor(b['end'][ids],model)
    u=(torch.arange(cells,device=o.device,dtype=o.dtype)+.5)/cells;t=a[:,None]+(end-a)[:,None]*u
    points=o[:,None]+d[:,None]*t[:,:,None];f,features,normal,x=raw(model,points.reshape(-1,3),need_color,create_graph);f=f.reshape(len(ids),cells)
    beta=model.density.get_beta()*domain()['mm_per_unit'];delta=(end-a)/cells;logsigma=log_density(f,beta);energy=torch.exp(logsigma)*delta[:,None]
    trans=torch.exp(-(torch.cumsum(energy,1)-energy));weights=-torch.expm1(-energy)*trans;mass=weights.sum(1)
    mean=(weights*t).sum(1)/mass.clamp_min(1e-12);start=raw(model,o+d*a[:,None])[0]
    sequence=torch.cat([start[:,None],f],1);locations=torch.cat([a[:,None],t],1);cross=(sequence[:,:-1]>0)&(sequence[:,1:]<=0)
    cross[:,0]=(start>=0)&(f[:,0]<0)
    first=cross.to(torch.int64).argmax(1);idx=torch.arange(len(ids),device=o.device);fa=sequence[idx,first];fb=sequence[idx,first+1]
    ta=locations[idx,first];tb=locations[idx,first+1];front=cross.any(1)&(mass>=1e-4)
    front_t=torch.where(front,ta+(tb-ta)*fa/(fa-fb).clamp_min(1e-20),torch.full_like(ta,float('nan')))
    # Crossing and hit counts are detached selectors; never training losses.
    hit=np.zeros(n,bool);hit[ids]=front.detach().cpu().numpy()
    depth=torch.full((n,),float('nan'),dtype=o.dtype,device=o.device).index_copy(0,ii,torch.where(front,mean,torch.full_like(mean,float('nan'))))*to_tensor(b['cosine'],model)
    opacity=torch.zeros(n,dtype=o.dtype,device=o.device).index_copy(0,ii,mass)
    rgb=torch.zeros(n,3,dtype=o.dtype,device=o.device)
    if need_color:
        color=model.rendering_network.forward(x,normal,d[:,None].expand_as(points).reshape(-1,3),features,index)
        rgb=rgb.index_copy(0,ii,(weights[:,:,None]*color.reshape(len(ids),cells,3)).sum(1)/mass[:,None].clamp_min(1e-12))
    logtau=torch.logsumexp(logsigma+torch.log(delta)[:,None],1);safe_tau=torch.exp(logtau.clamp_min(-20));logp=torch.where(logtau<-20,logtau,torch.log(-torch.expm1(-safe_tau)))
    y=to_tensor(b['mask_target'][ids],model);w=to_tensor(b['mask_weight'][ids],model);perray=-y*logp+(1-y)*torch.exp(logtau)
    mask=(perray*w).sum()/w.sum()
    front_all=np.full(n,np.nan);front_all[ids]=front_t.detach().cpu().numpy()
    return dict(opacity=opacity,RGB=rgb,depth_mm=depth,render_hit=hit,front_t_mm=front_all,mask=mask,raw_sdf=f,
        raw_start=start,t_mm=t,active_ids=ids,delta_beta=(delta/beta).detach(),finite_bounds=True)

def anchor(model,b):
    obs=(b['depth_weight']>0)&np.isfinite(b['target_Z'])&(b['target_Z']>0);ids=np.flatnonzero(obs);t=b['target_Z'][ids]/b['cosine'][ids]
    assert np.all(t>=b['start'][ids])and np.all(t<=b['end'][ids])
    X=b['origin'][ids]+b['direction'][ids]*t[:,None];f=raw(model,X)[0];w=to_tensor(b['depth_weight'][ids],model)
    return (huber(f,.5)*w).sum()/w.sum()

def terms(model,b,p,include_anchor=True):
    obs=(b['depth_weight']>0)&np.isfinite(b['target_Z'])&(b['target_Z']>0);valid=obs&p['render_hit'];rv=(b['sampling_class']==0)&p['render_hit']&(b['mask_weight']>0)
    depth=None;rgb=None
    if valid.any():
        w=to_tensor(b['depth_weight'][valid],model);depth=(huber(p['depth_mm'][valid]-to_tensor(b['target_Z'][valid],model),.5)*w).sum()/w.sum()
    if rv.any():
        w=to_tensor(b['mask_weight'][rv],model);rgb=(huber(p['RGB'][rv]-to_tensor(b['RGB'][rv],model),.05).mean(1)*w).sum()/w.sum()
    return dict(rgb=rgb,depth=depth,mask=p['mask'],anchor=anchor(model,b) if include_anchor else p['mask']*0)

def eikonal(model):
    _,_,grad,_=raw(model,np.asarray(load(R/'config/EIKONAL_TRAIN_POINTS.json')),True,True)
    return official_eikonal(None,grad)

def data_loss(t,anchor_weight):
    if t['rgb'] is None or t['depth'] is None:raise RuntimeError('REFERENCE_MISSING_RGB_OR_DEPTH')
    return t['rgb']+.1*t['depth']+.1*t['mask']+anchor_weight*t['anchor']

def array_pred(p):
    return dict(opacity=p['opacity'].detach().cpu().numpy(),RGB=p['RGB'].detach().cpu().numpy(),depth_mm=p['depth_mm'].detach().cpu().numpy(),
        render_hit=p['render_hit'],front_t_mm=p['front_t_mm'])
