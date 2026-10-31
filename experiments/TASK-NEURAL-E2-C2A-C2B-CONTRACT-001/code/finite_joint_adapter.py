"""Thin CPU finite-cell bridge for official raw implicit/radiance APIs.

Accepts injected callables only. No official network construction, inference,
checkpoint, sampler execution or optimizer. CPU tests use explicit analytic doubles.
"""
from continuation_context import *
from opacity import finite_cell_weights,clip_sampler_edges,world_to_network,masked_opacity_loss,shared_depth_loss
import torch

_f,_e=official_method(SDF/'code/model/loss.py','MonoSDFLoss','get_eikonal_loss')
_ns=dict(torch=torch)
exec(compile(ast.Module(body=[_f],type_ignores=[]),str(SDF/'code/model/loss.py'),'exec'),_ns)
official_eikonal_loss=_ns['get_eikonal_loss']


class IncompleteReferenceError(ValueError):
    def __init__(self,counts):
        super().__init__('INCOMPLETE_REFERENCE_SUPERVISION: '+str(counts));self.counts=counts


class FiniteJointAdapter:
    def __init__(self,implicit,radiance,origin_mm,mm_per_unit,beta_network):
        self.implicit=implicit;self.radiance=radiance
        self.origin=np.asarray(origin_mm,float);self.scale=float(mm_per_unit)
        self.beta=beta_network
        if not np.isfinite(self.scale)or self.scale<=0:raise ValueError('PHYSICAL_SCALE_REQUIRED')
        if not torch.is_tensor(beta_network)or beta_network.numel()!=1 or beta_network.device.type!='cpu' or not bool(beta_network>0):
            raise ValueError('EXPLICIT_POSITIVE_CPU_BETA_REQUIRED')
        # The current authorization forbids running official neural modules.
        # Keep this guard until a separately approved bounded runtime task.
        for obj in [implicit,radiance]:
            if type(obj).__module__.split('.')[0] in ['model','mapanything']:
                raise PermissionError('OFFICIAL_NEURAL_EXECUTION_NOT_AUTHORIZED')

    def raw_outputs(self,points_mm):
        if points_mm.device.type!='cpu':raise ValueError('CPU_CONTRACT_ONLY')
        x=world_to_network(points_mm,self.origin,self.scale)
        if not x.requires_grad:x=x.requires_grad_(True)
        # Official get_outputs/get_sdf_vals clamp with absorbing sphere. The
        # injected raw forward is the only valid Polyp field access here.
        raw=self.implicit.forward(x)
        if raw.ndim!=2 or raw.shape[0]!=len(x)or raw.shape[1]<1 or not bool(torch.isfinite(raw).all()):
            raise ValueError('INVALID_RAW_IMPLICIT_OUTPUT')
        sdf_net=raw[:,:1]
        grad=torch.autograd.grad(sdf_net,x,torch.ones_like(sdf_net),create_graph=True,retain_graph=True)[0]
        return dict(points_net=x,sdf_mm=sdf_net[:,0]*self.scale,features=raw[:,1:],gradient=grad)

    def render(self,packet,proposed_t_network,reference_index):
        """Consume detached sampler distances in network units; do not run it.

        Distances are along UNIT world rays. Official sample proposals must be
        unit checked by the future runtime binding, never axial camera Z.
        Variable finite cell lists are grouped by length for batching.
        """
        o=torch.as_tensor(packet['origin'],dtype=torch.float64);d=torch.as_tensor(packet['direction'],dtype=torch.float64)
        if o.requires_grad or d.requires_grad:raise ValueError('FROZEN_CAMERA_REQUIRED')
        if not np.allclose(np.linalg.norm(d.numpy(),axis=1),1,atol=1e-8):raise ValueError('UNIT_RAY_REQUIRED')
        proposed=np.asarray(proposed_t_network,float)
        n=len(o)
        if proposed.ndim==1:proposed=np.broadcast_to(proposed,(n,len(proposed)))
        if proposed.ndim!=2 or proposed.shape[0]!=n:raise ValueError('SAMPLER_SHAPE_MISMATCH')
        beta_mm=self.beta*self.scale;groups={}
        for i in np.flatnonzero(packet['valid']):
            edges=clip_sampler_edges(proposed[i]*self.scale,float(packet['start'][i]),float(packet['end'][i]))
            if len(edges)>1:groups.setdefault(len(edges),[]).append((i,edges))
        opacity=torch.zeros(n,dtype=torch.float64);color=torch.zeros(n,3,dtype=torch.float64)
        depth=torch.full((n,),float('nan'),dtype=torch.float64);hit=np.zeros(n,bool)
        query_N=0;query_limits=[]
        for size,items in groups.items():
            ids=torch.tensor([x[0] for x in items]);edges=torch.tensor(np.stack([x[1] for x in items]),dtype=torch.float64)
            t=(edges[:,:-1]+edges[:,1:])/2;points=o[ids,None]+d[ids,None]*t[:,:,None]
            q=self.raw_outputs(points.reshape(-1,3));sdf=q['sdf_mm'].reshape(len(ids),-1)
            colors=self.radiance.forward(q['points_net'],q['gradient'],d[ids,None].expand_as(points).reshape(-1,3),q['features'],reference_index)
            if colors.shape!=(points.numel()//3,3)or not bool(torch.isfinite(colors).all()):raise ValueError('INVALID_RADIANCE_OUTPUT')
            weights=finite_cell_weights(sdf,edges,beta_mm);mass=weights.sum(1)
            rgb=(weights[...,None]*colors.reshape(len(ids),-1,3)).sum(1)/mass[:,None].clamp_min(1e-12)
            mean=(weights*t).sum(1)/mass.clamp_min(1e-12)
            boundary=self.raw_outputs(o[ids]+d[ids]*edges[:,0,None])['sdf_mm']
            crosses=((sdf[:,:-1]>0)&(sdf[:,1:]<=0)).any(1)|((boundary>=0)&(sdf[:,0]<0))
            front=crosses&(mass>=1e-4);hit[ids.numpy()]=front.detach().numpy()
            depth=depth.index_copy(0,ids,torch.where(front,mean,torch.full_like(mean,float('nan'))))
            opacity=opacity.index_copy(0,ids,mass);color=color.index_copy(0,ids,rgb)
            query_N+=len(ids)*size
            query_limits.extend([dict(ray=int(i),min_t_mm=float(e[0]),max_t_mm=float(e[-1]),cells=size-1) for i,e in items])
        return dict(opacity=opacity,rgb_values=color,axial_depth_mm=depth*torch.as_tensor(packet['cosine']),render_hit=hit,
            raw_query_N=query_N,query_limits=query_limits,RGB_policy='conditional_on_finite_Polyp_mass; P_INTERIOR/front-hit only; no learned background')

    def eikonal(self,points_mm):
        grad=self.raw_outputs(torch.as_tensor(points_mm,dtype=torch.float64))['gradient']
        return official_eikonal_loss(None,grad)


def joint_losses(predictions,packets,scene_ids,source_weights,eikonal,coefficients):
    """Strict three-reference reduction; never renormalize away a failed view."""
    if len(predictions)!=3 or len(packets)!=3 or len({x['source'] for x in packets})!=3:
        raise ValueError('EXACT_THREE_DISTINCT_REFERENCES_REQUIRED')
    if len(set(scene_ids))!=1 or len(scene_ids)!=3:raise ValueError('CROSS_VIDEO_SUPERVISION_FORBIDDEN')
    if any(not p['source'].startswith(scene_ids[0]+'_') for p in packets):raise ValueError('SOURCE_SCENE_IDENTITY_MISMATCH')
    z=torch.cat([p['axial_depth_mm'] for p in predictions]);target=np.concatenate([b['target_Z'] for b in packets])
    dw=np.concatenate([b['depth_weight'] for b in packets]);views=[b['source'] for b in packets for _ in b['target_Z']]
    scenes=[scene_ids[0]]*len(views);rh=np.concatenate([p['render_hit'] for p in predictions])
    depth,per_view=shared_depth_loss(z,target,dw,views,scenes,source_weights=source_weights,render_hit=rh)
    counts={v:{k:int(x[k]) for k in ['observed_N','valid_N','miss_N']} for v,x in per_view.items()}
    if any(x['valid_N']==0 for x in per_view.values()):raise IncompleteReferenceError(counts)
    masks=[];rgb=[];vw=[]
    for p,b in zip(predictions,packets):
        masks.append(masked_opacity_loss(p,dict(mask_weight=b['mask_weight'],mask_target=b['mask_target'])))
        w=torch.as_tensor(b['mask_weight'],dtype=z.dtype)
        valid=torch.as_tensor((b['sampling_class']==0)&p['render_hit'])&(w>0)
        if not bool(valid.any()):raise IncompleteReferenceError(dict(source=b['source'],RGB_valid_N=0))
        target_rgb=torch.as_tensor(b['RGB'],dtype=z.dtype)
        if not bool(torch.isfinite(target_rgb[valid]).all()):raise ValueError('NONFINITE_SOURCE_RGB')
        err=p['rgb_values'][valid]-target_rgb[valid];delta=.05;ae=err.abs()
        huber=torch.where(ae<=delta,.5*err**2/delta,ae-.5*delta).mean(-1)
        rgb.append((huber*w[valid]).sum()/w[valid].sum());vw.append(float(source_weights[b['source']]))
        counts[b['source']]['RGB_N']=int(valid.sum());counts[b['source']]['Mask_N']=int((w>0).sum())
    source=torch.tensor(vw,dtype=z.dtype)
    terms=dict(depth=depth,mask=(torch.stack(masks)*source).sum()/source.sum(),
        rgb=(torch.stack(rgb)*source).sum()/source.sum(),eikonal=eikonal)
    if set(coefficients)!=set(terms)or any(not np.isfinite(x)or x<0 for x in coefficients.values()):raise ValueError('EXPLICIT_LOSS_COEFFICIENTS_REQUIRED')
    terms['total']=sum(terms[k]*float(coefficients[k]) for k in coefficients)
    return terms,counts
