"""Shared mesh-only observations; no class, camera or RGB fit parameters."""
from inputs import *
from camera_renderer import *
def robust(x):return 2*(torch.sqrt(1+x*x)-1)
def exact_depth(V,F,uv,K,T,rt=None):
    """Discrete first-face visibility; exact ray/triangle intersection derivative."""
    if rt is None:rt=mesh_scene(V.detach().cpu().numpy(),F)
    rays=vis.camera_rays(uv,K,T);hit=rt.cast_rays(o3d.core.Tensor(rays.astype(np.float32)));ids=hit['primitive_ids'].numpy().astype(np.int64);ok=(ids>=0)&(ids<len(F))&np.isfinite(hit['t_hit'].numpy())
    face=tensor(F[np.clip(ids,0,len(F)-1)],torch.long);p=V[face];n=torch.linalg.cross(p[:,1]-p[:,0],p[:,2]-p[:,0]);r=tensor(rays);den=(n*r[:,3:]).sum(1);z=(n*(p[:,0]-r[:,:3])).sum(1)/torch.where(den.abs()>1e-10,den,torch.ones_like(den))
    return z,ok,ids
def anchors(V,F,X,T,K,scene,rt):
    q=rt.compute_closest_points(o3d.core.Tensor(np.asarray(X,np.float32)));ids=q['primitive_ids'].numpy().astype(int);b=q['primitive_uvs'].numpy();bary=np.c_[1-b.sum(1),b]
    nearest=(V[tensor(F[ids],torch.long)]*tensor(bary)[:,:,None]).sum(1)
    uv,z=vis.project_camera(nearest.detach().cpu().numpy(),K,T);rh=cast(rt,uv,K,T)[0];cad=cast(ringscene(scene),uv,K,T)[0]
    valid=np.isfinite(rh)&(z>0)&(abs(rh-z)<.05)&(z<=cad+.05)&(uv[:,0]>=0)&(uv[:,0]<640)&(uv[:,1]>=0)&(uv[:,1]<360)
    residual=nearest-tensor(X);return residual,valid
class Problem:
    def __init__(self,scene,initial):
        self.scene=scene;self.initial=initial;self.pr=protocol();self.ids=self.pr['scenes'][scene]['A'];self.b=dict(np.load(R/'inputs'/f'{scene}_{initial}_basis.npz'));self.F=self.b['F'];self.renderer=Renderer(scene);self.o=[obs(cid)for cid in self.ids]
        self.V0=tensor(self.b['V']);self.n=tensor(self.b['n']);self.phi=tensor(self.b['phi']);self.lam=tensor(self.b['lam']/self.b['lam'][0]);self.unknown=None
        rgb=[{v['sha256']for v in CC[c].get('HERO_input_views',[])if v.get('sha256')}for c in self.ids]
        w=[(1. if GATE[c]['qualification']=='CONDITIONAL_USABLE'else .25)/(1+sum(len(rgb[i]&rgb[j])/max(1,len(rgb[i]|rgb[j]))for j in range(len(rgb))if i!=j))for i,c in enumerate(self.ids)]
        self.weights=np.array(w)/sum(w);self.visible=self.visibility(self.b['V']);self.unknown=tensor(~np.any(self.visible,axis=0));self.diameter=float(2*(3*abs(trimesh.Trimesh(self.b['V'],self.F,process=False).volume)/(4*np.pi))**(1/3));self.tau=float(np.clip(.0125*self.diameter,.075,.2))
        self.tensor_obs=[{k:tensor(o[k])for k in ['target','weights','contour_weight']}for o in self.o]
    def vertices(self,a):return self.V0+self.n*(self.phi@a)[:,None]
    def visibility(self,V):
        rt=mesh_scene(V,self.F);visibles=[]
        for cid in self.ids:
            s=source(cid);uv,z=vis.project_camera(V,s['K'],s['T']);inside=np.isfinite(uv).all(1)&(z>0)&(uv[:,0]>=0)&(uv[:,0]<640)&(uv[:,1]>=0)&(uv[:,1]<360);safe=uv.copy();safe[~inside]=0;xy=np.rint(safe).astype(int);xy=np.clip(xy,[0,0],[639,359]);depth=cast(rt,safe,s['K'],s['T'])[0];cad=cast(ringscene(self.scene),safe,s['K'],s['T'])[0]
            visibles.append(inside&(s['labels'][xy[:,1],xy[:,0]]==1)&(abs(depth-z)<.1)&(z<=cad+.05))
        return np.array(visibles)
    def parts(self,V,schedule=None,return_vector=False):
        rt=mesh_scene(V.detach().cpu().numpy(),self.F);views=[];allvectors=[]
        for i,(cid,o,t)in enumerate(zip(self.ids,self.o,self.tensor_obs)):
            K=vis.scaled_intrinsics(o['K'],(640,360),(320,180));r=self.renderer.render(V,self.F,K,o['T']);diff=r['alpha']-t['target'];mr=diff*torch.sqrt(t['weights'])*(1+.1*t['contour_weight']);M=(mr*mr).sum()
            z,valid,_=exact_depth(V,self.F,o['uv'],o['Kn'],o['T'],rt);valid&=z.detach().cpu().numpy()<=o['cad']+.05
            pp=o['pairs'];good=valid[pp].all(1);pix=np.arange(len(pp))if schedule is None else schedule[0];sel=pix[good[pix]];pairs=tensor(pp[sel],torch.long)
            drs=(z[pairs[:,0]]-z[pairs[:,1]]-tensor(o['delta'][sel]))/.25;D=robust(drs).sum()/len(pix)
            hr,hv=anchors(V,self.F,o['X'],o['T'],o['K'],self.scene,rt);hi=np.arange(len(hv))if schedule is None else schedule[1];hi=hi[hv[hi]];hvec=hr[tensor(hi,torch.long)];hd=torch.sqrt((hvec*hvec).sum(1)+1e-12);H=(4*torch.tanh(hd/2)**2).sum()/.25/(len(hv)if schedule is None else len(schedule[1]));L=M+D+.1*H
            views.append(dict(loss=L,M=M,D=D,H=H,hit=int(valid.sum()),pair_hit=int(good.sum()),H_N=int(hv.sum()),H_MAE=float(torch.linalg.norm(hr.detach()[tensor(np.flatnonzero(hv),torch.long)],dim=1).mean())if hv.any()else np.nan,z=z.detach().cpu().numpy(),valid=valid,hr=hr.detach().cpu().numpy(),hv=hv))
            if return_vector:
                # Fixed-dimensional white residuals. Invalid rows are marked,
                # and finite differences use only rows valid on BOTH sides.
                q=mr.flatten()[::56]*np.sqrt(56);dp=torch.full((len(pp),),float('nan'),device='cuda');pg=tensor(np.flatnonzero(good),torch.long);pps=tensor(pp[good],torch.long);dp[pg]=(z[pps[:,0]]-z[pps[:,1]]-tensor(o['delta'][good]))/.25/np.sqrt(len(pp))
                hq=hr/.5*np.sqrt(.1/len(hr));hq=torch.where(tensor(hv)[:,None]>0,hq,torch.full_like(hq,float('nan')))
                allvectors.append(torch.cat([q,dp,hq.flatten()])*np.sqrt(self.weights[i]))
        if return_vector:return torch.cat(allvectors).detach().cpu().numpy(),views
        return views
    def objective(self,a,schedule=None):
        V=self.vertices(a);parts=self.parts(V,schedule);data=sum(float(w)*v['loss']for w,v in zip(self.weights,parts));u=self.phi@a
        freq=((a*self.lam)**2).mean();bend=(tensor(self.b['L'])@u)**2;reg=.02*(freq+.1*bend.mean()+4*(u*u*self.unknown).mean())
        return data+reg,parts,dict(data=data,reg=reg)
    def schedule(self,seed,step):
        rng=np.random.default_rng(20261104+10000*seed+step);return(rng.permutation(256)[:128],rng.permutation(512)[:256])
