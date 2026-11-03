"""Official complete computational chain with explicit finite visibility/data ports.

No legacy fixed-cell renderer. All adaptive search/CDF/net/radiance calls are official.
The resource benchmark is not sufficient-training evidence.
"""
from common import *
import types,inspect,textwrap,difflib,math,importlib
os.environ['CUDA_VISIBLE_DEVICES']='0'
sys.path[:0]=[str(E0/'runtime/python'),str(R/'runtime/monosdf_import/code')]
import torch
from pyhocon import ConfigFactory
def bootstrap():
    exact=R/'runtime/official_exact/code';adapted=R/'runtime/monosdf_import/code'
    for rel in ['model/network.py','model/ray_sampler.py','model/embedder.py','model/density.py','model/loss.py','utils/rend_util.py']:
        p=adapted/rel;p.parent.mkdir(parents=True,exist_ok=True);b=(exact/rel).read_text()
        if rel=='model/network.py':
            # Exact, previously audited two-line lazy import; unused hash grid not compiled.
            b=b.replace('from hashencoder.hashgrid import _hash_encode, HashEncoder\n','')
            marker='class ImplicitNetworkGrid(nn.Module):';pre,post=b.split(marker);post=post.replace('        super().__init__()','        from hashencoder.hashgrid import _hash_encode, HashEncoder\n        super().__init__()',1);b=pre+marker+post
        p.write_text(b)
    for folder in ['utils','model']:(adapted/folder/'__init__.py').write_text('')
    importlib.invalidate_caches()
    ns=dict(torch=torch,np=np,os=os,time=time,nn=torch.nn)
    extract(exact/'utils/general.py',['get_class'],ns)
    gen=types.ModuleType('utils.general');gen.get_class=ns['get_class'];sys.modules['utils.general']=gen
    import utils
    utils.general=gen
    from model.network import MonoSDFNetwork
    from model.ray_sampler import UniformSampler,ErrorBoundSampler
    from model.loss import MonoSDFLoss
    from utils import rend_util
    edits=[]
    def patch_method(cls,name,old,new):
        original=textwrap.dedent(inspect.getsource(getattr(cls,name)));assert old in original,(cls,name,'PATCH_TARGET_MISSING');modified=original.replace(old,new,1)
        scope=dict(getattr(cls,name).__globals__);exec(compile(modified,f'<finite-port:{cls.__name__}.{name}>','exec'),scope);setattr(cls,name,scope[name]);edits.extend(difflib.unified_diff(original.splitlines(True),modified.splitlines(True),fromfile=f'official/{cls.__name__}.{name}',tofile=f'adapted/{cls.__name__}.{name}'))
    fn=textwrap.dedent(inspect.getsource(UniformSampler.get_z_vals));a=fn.index('    if not self.take_sphere_intersection:');b=fn.index('    t_vals =');patch_method(UniformSampler,'get_z_vals',fn[a:b],'    near, far = model._visibility_bounds\n\n')
    patch_method(ErrorBoundSampler,'get_z_vals','near, far = self.near * torch.ones(ray_dirs.shape[0], 1).cuda(), self.far * torch.ones(ray_dirs.shape[0],1).cuda()','near, far = model._visibility_bounds')
    patch_method(MonoSDFNetwork,'volume_rendering','torch.tensor([1e10]).cuda()','torch.tensor([0.0]).cuda()')
    # Do not change Algorithm1, adaptive search, beta line search, CDF/PDF or final sample counts.
    (R/'provenance/OFFICIAL_FINITE_VISIBILITY_PATCH.diff').write_text(''.join(edits))
    return MonoSDFNetwork,MonoSDFLoss,rend_util
MonoSDFNetwork,MonoSDFLoss,rend_util=bootstrap()
def make_model():
    p=protocol();n=p['network'];torch.manual_seed(p['seed']);torch.cuda.manual_seed_all(p['seed'])
    cfg=ConfigFactory.from_dict(dict(feature_vector_size=n['feature_vector_size'],scene_bounding_sphere=1.2,white_bkgd=False,Grid_MLP=False,
        implicit_network=dict(d_in=3,d_out=1,dims=n['dims'],geometric_init=True,bias=n['bias'],skip_in=n['skip_in'],weight_norm=True,multires=n['multires'],inside_outside=False),
        rendering_network=dict(mode='idr',d_in=9,d_out=3,dims=n['rendering_dims'],weight_norm=True,multires_view=n['multires_view']),
        density=dict(params_init=dict(beta=n['beta_init_model']),beta_min=n['beta_min_model']),
        ray_sampler=dict(near=0.,N_samples=64,N_samples_eval=128,N_samples_extra=32,eps=.1,beta_iters=10,max_total_iters=5)))
    model=MonoSDFNetwork(cfg).cuda();model.implicit_network.sdf_bounding_sphere=0.;model.train()
    return model
@lru_cache(None)
def original_anchor_points(cid):
    z=frozen(cid);n=native(cid);pixel=z['native_pixel_ID'].ravel();good=pixel>=0;X=np.full((len(pixel),3),np.nan);h,w=n['depth'].shape;ids=pixel[good];uv=np.c_[ids%w,ids//w]
    world=unproject(n['depth'].flat[ids].astype(float),n['T'],uv,n['Kn']);p=protocol()['geometry'];X[good]=(world-np.array(p['C_mm']))/p['mm_per_model_unit'];return X
@lru_cache(None)
def original_anchor_geometry(cid):
    z=frozen(cid);n=native(cid);pixel=z['native_pixel_ID'].ravel();good=pixel>=0;X=original_anchor_points(cid);p=protocol()['geometry'];origin=(n['T'][:3,3]-np.array(p['C_mm']))/p['mm_per_model_unit'];direction=X-origin;t=np.linalg.norm(direction,axis=1);direction/=np.maximum(t[:,None],1e-20)
    a=(-1-origin)/np.where(abs(direction)>1e-15,direction,1e-15);b=(1-origin)/np.where(abs(direction)>1e-15,direction,1e-15);near=np.maximum(np.minimum(a,b).max(1),0);far=np.maximum(a,b).min(1)
    j=np.flatnonzero(good);ids=pixel[j];uv=np.c_[ids%n['depth'].shape[1],ids//n['depth'].shape[1]];cad,_=cast(ringscene(SCENE),uv,n['Kn'],n['T']);rayfactor=np.linalg.norm(vis.camera_rays(uv,n['Kn'],n['T'])[:,3:],axis=1);far[j]=np.minimum(far[j],(cad-.05)*rayfactor/p['mm_per_model_unit'])
    archive=affine_uv(uv,n['K']@np.linalg.inv(n['Kn']));ij=np.floor(archive+.5).astype(int);labels=n['labels'][np.clip(ij[:,1],0,359),np.clip(ij[:,0],0,639)];eligible=np.zeros(len(pixel),bool);eligible[j]=(labels==1)&(t[j]>=near[j])&(t[j]<=far[j])&np.isfinite(X[j]).all(1)
    return dict(X=X,direction=direction,near=near,far=far,eligible=eligible)
def packet(cid,step,N=1024):
    z=frozen(cid);rng=np.random.default_rng(protocol()['seed']+step);legal=np.flatnonzero(z['eligible_HERO'].ravel());ids=rng.choice(legal,N,replace=len(legal)<N)
    def tensor(a):return torch.as_tensor(np.asarray(a),device='cuda',dtype=torch.float32)
    K=np.eye(4,dtype=np.float32);K[:3,:3]=z['K_crop'];uv=z['uv'][ids]
    data=dict(intrinsics=tensor(K)[None],uv=tensor(uv)[None],pose=tensor(z['c2w_model'])[None])
    p=dict(cid=cid,pixel_crop_id=ids,original_native_id=z['native_pixel_ID'].ravel()[ids],rgb=tensor(z['RGB'].reshape(-1,3)[ids]/255)[None],depth=tensor(z['depth_model'].ravel()[ids])[None,:,None],normal=tensor(z['normal_camera'].reshape(-1,3)[ids])[None],normal_valid=tensor(z['normal_valid'].ravel()[ids]).bool(),weight=tensor(z['reliability_weight'].ravel()[ids]),near=tensor(z['near'].ravel()[ids])[:,None],far=tensor(z['far'].ravel()[ids])[:,None],hero_X=tensor(original_anchor_points(cid)[ids]))
    a=original_anchor_geometry(cid);p.update(anchor_eligible=tensor(a['eligible'][ids]).bool(),anchor_direction=tensor(a['direction'][ids]),anchor_near=tensor(a['near'][ids]),anchor_far=tensor(a['far'][ids]));p['normal_valid']&=p['anchor_eligible']
    return data,p
class ProjectLoss(MonoSDFLoss):
    """Same official component formulas; real HERO format/normal-validity IO ports."""
    def __init__(self,arm):
        super().__init__(rgb_loss='torch.nn.L1Loss',eikonal_weight=.1,smooth_weight=.005,depth_weight=.1,normal_l1_weight=.05,normal_cos_weight=.05,end_step=12800);self.arm=arm
    def forward(self,out,batch):
        rgb=self.get_rgb_loss(out['rgb_values'],batch['rgb']);ek=self.get_eikonal_loss(out['grad_theta']);sm=self.get_smooth_loss(out)
        crossing=((out['sdf']>0).any(1)&(out['sdf']<0).any(1))
        # The official32x32 grouping is the original random1024-ray batch, not spatial patches.
        dp=out['depth_values'].reshape(1,32,32);target=batch['depth'].reshape(1,32,32);depth=self.depth_loss(dp,target,crossing.reshape(1,32,32));depth=depth if torch.is_tensor(depth)else rgb*0
        nv=crossing&batch['normal_valid'];zero=rgb*0
        if nv.any():nl,nc=self.get_normal_loss(out['normal_map'][nv],batch['normal'].reshape(-1,3)[nv])
        else:nl,nc=zero,zero
        decay=math.exp(-self.step/self.end_step*10);base=rgb+.1*ek+.005*sm+decay*(.1*depth+.05*nl+.05*nc)
        result=dict(rgb=rgb,eikonal=ek,smooth=sm,SSI_depth=depth,normal_l1=nl,normal_cos=nc,base=base)
        if self.arm=='M1':
            s=protocol()['geometry']['mm_per_model_unit'];w=batch['weight'];den=w.sum().clamp_min(1e-8)
            f_hero=model_for_loss.implicit_network(batch['hero_X'])[:,0]*s
            wh=w*batch['anchor_eligible'];denh=wh.sum().clamp_min(1e-8);surf=(torch.nn.functional.smooth_l1_loss(f_hero/.25,torch.zeros_like(f_hero),reduction='none')*wh).sum()/denh
            sdf=out['sdf'];cross=(sdf[:,:-1]>0)&(sdf[:,1:]<=0);hit=cross.any(1);k=cross.int().argmax(1);i=torch.arange(len(k),device=k.device);f0=sdf[i,k];f1=sdf[i,k+1];a=out['depth_vals'][i,k];b=out['depth_vals'][i,k+1];first=a+(b-a)*f0/(f0-f1).clamp_min(1e-8);res=(first-batch['depth'].reshape(-1))*s/.25;firstloss=(torch.nn.functional.smooth_l1_loss(res,torch.zeros_like(res),reduction='none')*w*hit).sum()/den
            _,cam=rend_util.get_camera_params(current_input['uv'],current_input['pose'],current_input['intrinsics']);dirs=batch['anchor_direction'];free=batch['hero_X']-dirs*(.5/s);t_hero=torch.linalg.norm(batch['hero_X']-cam.reshape(1,3),dim=1);ok=(t_hero-.5/s>batch['anchor_near'])&(t_hero-.5/s<batch['anchor_far'])&batch['anchor_eligible'];ff=model_for_loss.implicit_network(free)[:,0]*s
            freeloss=(torch.relu(.05-ff)/.25*w*ok).sum()/denh
            beta=model_for_loss.density.get_beta();logsig=torch.where(sdf>=0,-torch.log(2*beta)-sdf/beta,-torch.log(beta)+torch.log1p(-.5*torch.exp(torch.minimum(sdf,torch.zeros_like(sdf))/beta)))
            dt=out['z_vals'][:,1:]-out['z_vals'][:,:-1];dt=torch.cat([dt,torch.zeros_like(dt[:,:1])],1);logdt=torch.where(dt>0,torch.log(dt.clamp_min(1e-30)),torch.full_like(dt,-torch.inf));lt=torch.logsumexp(logsig+logdt,1);tau=torch.exp(lt.clamp_min(-20));ml=torch.where(lt< -20,-lt,-torch.log(-torch.expm1(-tau)));mask=(ml*w).sum()/den
            total=base+surf+.1*firstloss+.1*freeloss+.1*mask;result.update(surface=surf,first_depth=firstloss,free_space=freeloss,positive_mask=mask)
        else:total=base
        self.step+=1;result['loss']=total;return result
model_for_loss=None;current_input=None
def forward_and_loss(model,loss,data,batch):
    global model_for_loss,current_input
    model_for_loss=model;current_input=data;model._visibility_bounds=(batch['near'],batch['far']);output=model(data,torch.tensor([0],device='cuda'));return output,loss(output,batch)
def instrument(model):
    events={k:0 for k in ['adaptive_sampler','implicit_get_outputs','rendering_network','volume_rendering']}
    for obj,name,key in [(model.ray_sampler,'get_z_vals','adaptive_sampler'),(model.implicit_network,'get_outputs','implicit_get_outputs'),(model.rendering_network,'forward','rendering_network'),(model,'volume_rendering','volume_rendering')]:
        fn=getattr(obj,name)
        def wrapper(*args,_fn=fn,_key=key,**kwargs):events[_key]+=1;return _fn(*args,**kwargs)
        setattr(obj,name,wrapper)
    return events
