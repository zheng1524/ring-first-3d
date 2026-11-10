"""Residual-supported candidate coverage and explicit centerline/radius chart.
These are project additions, not an official PyTorch3D stalk model.
"""
from multiview import *
from normalized_local import local_normalized

def associations(obj,V):
    N=len(V);far=np.zeros(N,bool);targets=[]
    for cid,last in obj.contour.last.items():
        residual=last['reverse_native_px'];take=residual>=10.
        if take.any():far[np.unique(last['eid'][last['nn'][take]])]=True
        d=obj.c.views[cid];ct=last['target_contour_uv'];ij=np.clip(np.rint((ct+.5)*.5-.5).astype(int),[0,0],[319,179]);known=~np.isin(d['classes'].detach().cpu().numpy()[ij[:,1],ij[:,0]],[1,2,4]);ids=np.flatnonzero(known&(residual>1.))
        if not len(ids):continue
        edge=last['eid'][last['nn'][ids]];tt=last['t'][last['nn'][ids]];P=V[edge[:,0]]*(1-tt[:,None])+V[edge[:,1]]*tt[:,None];T=d['T'];z=((P-T[:3,3])@T[:3,:3])[:,2];ray=np.c_[ct[ids],np.ones(len(ids))]@np.linalg.inv(d['K']).T;X=(ray*z[:,None])@T[:3,:3].T+T[:3,3]
        for x,e,err,uv in zip(X,edge,residual[ids],ct[ids]):targets.append(dict(view=cid,X=x,edge=e,residual_px=float(err),uv=uv,depth_source='current apparent contour axial depth; NOT HERO or true correspondence'))
    return far,targets

def image_gradient(obj,q):
    g=torch.zeros_like(q);ramp=.25+.75*min(1.,obj.attempt/40.)
    for cid in obj.c.fit:
        m=obj.ch.mesh(q);fr=obj.c.fragments(m,cid);sil,alpha,w,*_=obj.c.aware(fr,cid,True);t=obj.c.views[cid]['target'];fg=((1-alpha)**2*t).sum()/t.sum().clamp_min(1);known=w*(1-t);fp=(alpha**2*known).sum()/known.sum().clamp_min(1);cd,_=obj.contour(obj.ch.vertices(q),cid);term=obj.w[cid]*(sil+ramp*(.05*(fg+fp)+.01*cd));d=torch.autograd.grad(term,q,allow_unused=True)[0]
        if d is not None:g+=d.detach()
    return g

def expanded_directions(ch,before,grad,obj):
    gi=image_gradient(obj,before.detach().clone().requires_grad_(True));V=ch.vertices(before).detach().cpu().numpy();far,_=associations(obj,V);F=ch.c.F;edges=np.unique(np.sort(np.r_[F[:,[0,1]],F[:,[1,2]],F[:,[2,0]]],axis=1),axis=0);band=far.copy()
    for _ in range(2):touch=band[edges].any(1);band[np.unique(edges[touch])]=True
    out=[]
    if far.any():
        d=-gi*tensor(band[:,None],torch.float64);move=float((ch.vertices(before+d).detach()-ch.vertices(before).detach()).norm(dim=1).max())
        if move>1e-15:out.append(('ALL_FAR_IMAGE_COVERAGE',d*(ch.tau/move)))
        # Decompose all connected active bands without dropping far vertices.
        from scipy.sparse import coo_matrix
        from scipy.sparse.csgraph import connected_components
        e=edges[band[edges].all(1)];A=coo_matrix((np.ones(2*len(e)),(np.r_[e[:,0],e[:,1]],np.r_[e[:,1],e[:,0]])),shape=(len(V),len(V))).tocsr();_,lab=connected_components(A,directed=False);groups=sorted(set(lab[far]),key=lambda k:-float(np.linalg.norm(gi.detach().cpu().numpy()[lab==k])))
        for k in groups[:8]:
            mask=band&(lab==k);d=-gi*tensor(mask[:,None],torch.float64);move=float((ch.vertices(before+d).detach()-ch.vertices(before).detach()).norm(dim=1).max())
            if move>1e-15:out.append(('FAR_COMPONENT_'+str(k),d*(ch.tau/move)))
    covered=np.zeros(len(V),bool)
    for _,d in out:covered|=d.norm(dim=1).detach().cpu().numpy()>0
    rec=dict(far_associated_N=int(far.sum()),expanded_geometric_band_N=int(band.sum()),far_with_actual_nonzero_candidate_N=int((far&covered).sum()),image_gradient_norm=float(gi.norm()),full_gradient_norm=float(grad.norm()),image_full_gradient_cosine=float((gi*grad).sum()/(gi.norm()*grad.norm()).clamp_min(1e-30)),coverage_is_proxy_not_true_stalk=True)
    return out,rec

def make_seed(c,V,obj):
    far,targets=associations(obj,V);C=np.median(V,axis=0)
    if not targets:return dict(status='NO_KNOWN_VISIBLE_RESIDUAL_SIGNAL',GT_read=False,reason='No target-contour residual >1px outside Ring-unknown band; no justified centerline direction')
    targets=sorted(targets,key=lambda q:-q['residual_px'])[:256];X=np.array([t['X']for t in targets]);w=np.minimum([t['residual_px']for t in targets],50.);tip=np.average(X,axis=0,weights=w);direction=tip-C;norm=np.linalg.norm(direction)
    if norm<1e-6:return dict(status='NO_KNOWN_VISIBLE_RESIDUAL_SIGNAL',GT_read=False,reason='Residual directions cancel')
    direction/=norm;t=(V-C)@direction;cut=float(np.quantile(t,.65));L=max(.05,float(t.max()-cut));root=C+cut*direction;e=np.eye(3)[np.argmin(abs(direction))];u=np.cross(direction,e);u/=np.linalg.norm(u);v=np.cross(direction,u);s=np.clip((t-cut)/L,0,1);radial=V-(root+s[:,None]*L*direction);r=np.linalg.norm(radial,axis=1);rho=[]
    for k in [.2,.5,.8]:
        rr=r[(s>0)&(abs(s-k)<.2)&(r>1e-8)];rho.append(float(np.median(rr))if len(rr)else .1)
    return dict(status='RESIDUAL_ASSOCIATION_PROXY',root_mm=root,direction=direction,basis_u=u,basis_v=v,length0_mm=L,s=s,radial_mm=radial,radius_profile_s=[.2,.5,.8],radius0_mm=rho,patch_vertex_N=int((s>0).sum()),far_associated_N=int(far.sum()),source_targets=targets,GT_read=False,anatomical_stalk_identity_verified=False,interpretation='Centerline-supported deformation of existing connected patch; proxy seed inferred from FIT Mask and current projected geometry, not certified correspondence')

class StalkChart(FreeVertices):
    """C0(s)+g(s)(C_p(s)-C0(s)), R0(s)exp(interp(log radius)).

    Eleven genuine curve parameters plus local 3D residuals; original topology
    and C1 blend at the head/patch junction. Coefficient is not measured length.
    """
    def __init__(self,c):
        super().__init__(c);self.seed=load(R/'inputs'/c.name/'STALK_SEED.json');assert self.seed['status']=='RESIDUAL_ASSOCIATION_PROXY';self.parameter_shape=(3*self.N+11,);self.s=tensor(self.seed['s'],torch.float64);self.g=self.s**2*(3-2*self.s);self.root=tensor(self.seed['root_mm'],torch.float64);self.d0=tensor(self.seed['direction'],torch.float64);self.e1=tensor(self.seed['basis_u'],torch.float64);self.e2=tensor(self.seed['basis_v'],torch.float64);self.L0=self.seed['length0_mm'];self.radial=tensor(self.seed['radial_mm'],torch.float64)
    def curve(self,p,s):
        direction=self.d0+p[3]*self.e1+p[4]*self.e2;direction=direction/direction.norm().clamp_min(1e-12);L=self.L0*torch.exp(p[5].clamp(-1.5,2.));bend=p[6]*self.e1+p[7]*self.e2;return self.root+p[:3]+s[:,None]*L*direction+4*(s*(1-s))[:,None]*bend
    def vertices(self,q):
        p=q[3*self.N:];res=q[:3*self.N].reshape(self.N,3);C0=self.root+self.s[:,None]*self.L0*self.d0;Cp=self.curve(p,self.s);t=self.s;w0=(1-t*2).clamp(0,1);w2=(t*2-1).clamp(0,1);w1=1-w0-w2;logr=p[8]*w0+p[9]*w1+p[10]*w2;ratio=torch.exp(logr.clamp(-1.5,1.5));delta=self.g[:,None]*(Cp-C0+(ratio-1)[:,None]*self.radial+res);return super().vertices(delta)
    def curve_record(self,q):
        p=q[3*self.N:].detach();s=torch.linspace(0,1,101,device=device,dtype=torch.float64);C0=self.root+s[:,None]*self.L0*self.d0;g=s*s*(3-2*s);C=C0+g[:,None]*(self.curve(p,s)-C0);length=float((C[1:]-C[:-1]).norm(dim=1).sum());w0=(1-2*s).clamp(0,1);w2=(2*s-1).clamp(0,1);w1=1-w0-w2;scale=torch.exp((p[8]*w0+p[9]*w1+p[10]*w2).clamp(-1.5,1.5));return dict(parameters=p.cpu().numpy(),effective_centerline_mm=C.cpu().numpy(),effective_centerline_arclength_mm=length,nominal_radius_scales=scale.cpu().numpy(),length_coefficient_is_not_actual_displacement=True,seed=self.seed)

def curve_directions(ch,before,grad):
    N=3*ch.N;p=torch.zeros_like(grad);p[N:]=-grad[N:];r=torch.zeros_like(grad);r[:N]=-grad[:N];out=[]
    for name,d in [('CENTERLINE_11PARAM',p),('LOCAL_FREE_RESIDUAL',r)]:
        move=float((ch.vertices(before+d).detach()-ch.vertices(before).detach()).norm(dim=1).max())
        if move>1e-15:out.append((name,d*(ch.tau/move)))
    return out
