from models import *
from scipy.optimize import least_squares

def initialize(ids,kind,only_H=False):
    obs=[observation(cid)for cid in ids];ss=[source(cid)for cid in ids]
    if only_H:
        X=np.concatenate([o['HERO_X_mm']for o in obs]);c=np.median(X,axis=0)if len(X)else np.zeros(3)
    else:
        lhs=np.zeros((3,3));rhs=np.zeros(3)
        for o,s in zip(obs,ss):
            v,u=np.nonzero(o['head']);uv=np.array([[np.mean(u),np.mean(v)]]);ray=vis.camera_rays(uv,s['K'],s['T'])[0,3:];ray/=np.linalg.norm(ray);A=np.eye(3)-np.outer(ray,ray);lhs+=A;rhs+=A@s['T'][:3,3]
        c=np.linalg.lstsq(lhs,rhs,rcond=1e-8)[0]
    c=np.clip(c,-10,10);normal=np.mean([s['T'][:3,3]-c for s in ss],axis=0);R0=camera_frame(normal,ss[0]['T'][:3,0])
    if only_H and len(X):
        q=(X-c)@R0;a=np.maximum(.5,np.quantile(abs(q),.9,axis=0)*1.5);a[2]=.75 if kind=='IIa'else max(a[2],min(a[:2])*.7)
    else:
        radii=[]
        for o,s in zip(obs,ss):
            v,u=np.nonzero(o['head']);depth=vis.project_camera(c[None],s['K'],s['T'])[1][0];radii.append([np.ptp(u)*max(5,depth)/(2*s['K'][0,0]),np.ptp(v)*max(5,depth)/(2*s['K'][1,1])])
        xy=np.clip(np.mean(radii,axis=0),.5,8);a=np.r_[xy,.75 if kind=='IIa'else .8*np.sqrt(np.prod(xy))]
    a=np.clip(a,[.3,.3,.1],[10,10,2.5 if kind=='IIa' else 10]);return np.r_[c,np.zeros(3),np.log(a)],R0

def robustify(x):return x*np.sqrt(2/(np.sqrt(1+x*x)+1))

class Problem:
    def __init__(self,scene,arm,ids=None,support_shift=0.,depth_weight=1.,camera_delta=False):
        self.scene=scene;self.sc=protocol()['scenes'][scene];self.kind=self.sc['kind'];self.arm=arm;self.ids=ids or self.sc['A'];self.obs=[observation(c)for c in self.ids];self.cameras=[source(c)for c in self.ids];self.support_shift=support_shift;self.depth_weight=depth_weight;self.calls=0
        self.family=({'Ip':'star','Is':'cap','IIa':'height'}[self.kind]if arm.startswith('A1-3')else'ellipsoid');self.terms=protocol()['arms'][arm];base,self.R0=initialize(self.ids,self.kind,arm=='A1-1')
        if self.family=='height':base[8]=np.log(.75)
        self.base=np.r_[base,np.zeros(size(self.family)-9)];self.lo,self.hi=bounds(self.base,self.kind,self.family)
        self.rays=[];self.cad=[];self.T=[]
        for j,(cid,o,s)in enumerate(zip(self.ids,self.obs,self.cameras)):
            T=s['T'].copy()
            if j==0 and camera_delta:
                delta=np.eye(4);delta[:3,:3]=Rotation.from_rotvec([0,np.deg2rad(.1),0]).as_matrix();delta[0,3]=.05;T=T@delta
            self.T.append(T);self.rays.append(vis.camera_rays(o['depth_native_uv'],o['Kn'],T))
        # Source family overlap weights: same upstream RGB is not independent evidence.
        inputs=[{v['sha256']for v in CC[c].get('HERO_input_views',[])if v.get('sha256')}for c in self.ids];w=[]
        for i,cid in enumerate(self.ids):
            corr=sum(len(inputs[i]&inputs[j])/max(1,len(inputs[i]|inputs[j]))for j in range(len(inputs))if j!=i);quality=1. if GATE[cid]['qualification']=='CONDITIONAL_USABLE'else .25
            w.append(quality/(1+corr))
        self.weights=np.array(w)/sum(w)

    def parts(self,p,fixed_visibility=None):
        vertices,faces=mesh(p,self.R0,self.family);parts={'C':[],'D':[],'H':[],'R':[]};mass={k:[]for k in parts};visibility=[]
        for i,(cid,o,s,T,w,rays)in enumerate(zip(self.ids,self.obs,self.cameras,self.T,self.weights,self.rays)):
            if 'C'in self.terms:
                uv,z=vis.project_camera(vertices,s['K'],T)
                if fixed_visibility is None:
                    cad,_=cast(ringscene(CC[cid]['scene_id']),uv,s['K'],T);v=np.isfinite(uv).all(1)&(z>0)&(z<=cad+.05)
                else:v=fixed_visibility[i]
                visibility.append(v)
                # Convex visible projection support is explicitly a contour descriptor, not exact raster IoU.
                pred=(uv[v]@o['directions'].T).max(0)if v.any()else np.full(24,1e3)
                rr=(pred-o['support']-self.support_shift)/3;sc=np.sqrt(o['support_weights']*w/max(1,len(rr)));parts['C'].append(rr*sc);mass['C'].append(sc)
                if 'D'in self.terms and len(o['depth_archive_uv']):
                    gap=np.maximum(0,(o['depth_archive_uv']@o['directions'].T-pred).max(1))/3;sc=np.full(len(gap),np.sqrt(w/len(gap)));parts['C'].append(gap*sc);mass['C'].append(sc)
            else:visibility.append(np.ones(len(vertices),bool))
            if 'D'in self.terms:
                t=first_depth(p,self.R0,self.family,rays);pairs=o['pairs'];good=np.isfinite(t[pairs]).all(1);rr=np.zeros(len(pairs));rr[good]=(t[pairs[good,0]]-t[pairs[good,1]]-o['depth_delta_mm'][good])/.25
                sc=np.full(len(rr),np.sqrt(self.depth_weight*w/max(1,len(rr))));parts['D'].append(rr*sc);mass['D'].append(sc)
            if 'H'in self.terms:
                rr=support_residual_points(p,self.R0,self.family,o['HERO_X_mm'])/.25;sc=np.repeat(np.sqrt(o['HERO_weights']*w/3),3);parts['H'].append(rr.ravel()*sc);mass['H'].append(sc)
        # Priors refer only to allowed initialization; priors are excluded from observational J.
        parts['R']=[np.r_[(p[:3]-self.base[:3])/10,p[3:6]/.8,(p[6:9]-self.base[6:9])/1.2,p[9:]/.2]*np.sqrt(.05)]
        self.row_scales={k:np.concatenate(v)if v else np.empty(0)for k,v in mass.items()}
        return {k:np.concatenate(v)if v else np.empty(0)for k,v in parts.items()},visibility

    def residual(self,p,white=False,observation_only=False,fixed_visibility=None):
        self.calls+=1;parts,_=self.parts(p,fixed_visibility);rows=[]
        for k,v in parts.items():
            if observation_only and k=='R':continue
            if white or k=='R':rows.append(v)
            else:
                sc=self.row_scales[k];rows.append(robustify(v/np.maximum(sc,1e-20))*sc)
        return np.concatenate(rows)

    def solve(self,start=0,nfev=60,initial=None):
        rng=np.random.default_rng(20261104+start);p=self.base.copy()if initial is None else initial.copy()
        if start and initial is None:
            p[:3]+=rng.normal(0,.4,3);p[3:6]+=rng.normal(0,.08,3);p[6:9]+=rng.normal(0,.12,3)
        p=np.clip(p,self.lo+1e-7,self.hi-1e-7);self.calls=0;t0=time.monotonic();initial_p=p.copy();initial_r=self.residual(p)
        result=least_squares(self.residual,p,jac='3-point',bounds=(self.lo,self.hi),method='trf',loss='linear',max_nfev=nfev,ftol=1e-5,xtol=1e-5,gtol=1e-5,x_scale=np.r_[np.full(3,1.),np.full(3,.1),np.full(3,.2),np.full(len(p)-9,.1)])
        return dict(scene=self.scene,kind=self.kind,arm=self.arm,family=self.family,start=start,parameter_N=len(p),initial=initial_p,p=result.x,R0=self.R0,seconds=time.monotonic()-t0,nfev=result.nfev,actual_residual_evaluations=self.calls,solver_success=bool(result.success),solver_status=int(result.status),termination=str(result.message),initial_objective=float(initial_r@initial_r/2),objective=float(result.fun@result.fun/2),active_bounds=np.asarray(result.active_mask),source_ids=self.ids,source_weights=self.weights)

def head_metric(pred,head,full):
    inter=int((pred&head).sum());union=int((pred|head).sum());bd1=contour(pred);bd2=contour(head)
    distances=np.r_[cKDTree(bd2).query(bd1)[0],cKDTree(bd1).query(bd2)[0]]if len(bd1)and len(bd2)else np.empty(0)
    return dict(head_denominator=int(head.sum()),full_polyp_denominator=int(full.sum()),predicted_N=int(pred.sum()),hit_N=inter,miss_N=int((head&~pred).sum()),outside_N=int((pred&~head).sum()),head_IoU=inter/max(1,union),head_hit_fraction=inter/max(1,int(head.sum())),outside_fraction=float((pred&~head).sum()/max(1,pred.sum())),full_Polyp_hit_fraction=float((pred&full).sum()/max(1,full.sum())),boundary_px=stats(distances))

def evaluate(model,cid,dest=None):
    """Called only after an A-only model exists. Exact mesh first hits, frozen B pixels."""
    o=observation(cid);s=source(cid);P,F=mesh(np.array(model['p']),np.array(model['R0']),model['family'],True);rt=mesh_scene(P,F)
    uv=np.c_[np.tile(np.arange(640),360),np.repeat(np.arange(360),640)];z,face=cast(rt,uv,s['K'],s['T']);cad,_=cast(ringscene(CC[cid]['scene_id']),uv,s['K'],s['T']);raw=np.isfinite(z)&(z>0);valid=raw&(z<=cad+.05);pred=valid.reshape(360,640)
    met=head_metric(pred,o['head'],o['full_polyp']);met.update(reference=cid,CAD_occluded_N=int((raw&~valid).sum()),CAD_occluded_fraction=float((raw&~valid).sum()/max(1,raw.sum())),evaluation='CONDITIONAL_NOT_PARAMETER_FIT',GT='NOT_EVALUABLE')
    rays=vis.camera_rays(o['depth_native_uv'],o['Kn'],s['T']);t=first_depth(np.array(model['p']),np.array(model['R0']),model['family'],rays);cadray,_=cast(ringscene(CC[cid]['scene_id']),o['depth_native_uv'],o['Kn'],s['T']);hit=np.isfinite(t)&(t>0)&(t<=cadray+.05);pairs=o['pairs'];good=hit[pairs].all(1);res=t[pairs[good,0]]-t[pairs[good,1]]-o['depth_delta_mm'][good]
    met.update(relative_depth_fixed_pair_N=len(pairs),relative_depth_hit_pair_N=int(good.sum()),relative_depth_miss_pair_N=int((~good).sum()),relative_depth_mm=stats(res),depth_fixed_ray_N=len(hit),depth_hit_ray_N=int(hit.sum()),depth_ray_hit_fraction=float(hit.mean())if len(hit)else None,censored_relative_depth_score_mm=float((abs(res).sum()+.25*(~good).sum())/max(1,len(pairs))))
    if dest is not None:
        dest=Path(dest);dest.parent.mkdir(parents=True,exist_ok=True);np.savez_compressed(dest,predicted_mask=pred,first_Z_mm=z.reshape(360,640),CAD_Z_mm=cad.reshape(360,640),fixed_ray_hit=hit,first_ray_Z_mm=t,head=o['head'],full_polyp=o['full_polyp'])
    return met
