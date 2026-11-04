"""One nine-parameter model and solver for both target choices; no class input."""
from losses import *
from scipy.optimize import least_squares
class Problem:
    def __init__(self,scene,arm,variant='full'):
        self.scene=scene;self.arm=arm;self.variant=variant;sc=protocol()['scenes'][scene];self.full_ids=sc['A'];self.ids=self.full_ids[:-1]if variant=='drop_last_A'else self.full_ids
        if arm=='E1':
            dxy={x['source']:x for x in load(R/'provenance/DXY_GENERATED.json')}
            if any(not dxy[c]['available']for c in self.full_ids):raise ValueError('NOT_EVALUABLE_E1_REQUIRED_A_ELLIPSE_MISSING')
        self.targets=[];self.rays=[];self.o=[];self.cameras=[];self.calls=0;self.invalid_calls=0
        self.R0=np.array(protocol()['initialization']['R0_by_scene'][scene]);self.base=np.array(protocol()['initialization']['base']);self.lo=np.r_[np.full(3,-10.),np.full(3,-.8),np.log(np.full(3,.25))];self.hi=np.r_[np.full(3,10.),np.full(3,.8),np.log(np.full(3,15.))]
        for i,cid in enumerate(self.ids):
            o=obs(cid);s=source(cid);T=s['T'].copy()
            if variant=='camera_copy'and i==0:
                delta=np.eye(4);delta[:3,:3]=Rotation.from_rotvec([0,np.deg2rad(.1),0]).as_matrix();delta[0,3]=.05;T=T@delta
            target=o['ellipse_target']if arm=='E1'else o['full_polyp'];grid=o['region_grid'];cad=cast(ringscene(scene),grid,s['K'],T)[0]
            self.targets.append(target_data(target,s['labels'],cad,T,s['K']));self.rays.append(vis.camera_rays(o['depth_native_uv'],o['Kn'],T));self.o.append(o);self.cameras.append(dict(K=s['K'],T=T))
        rgbsets=[{v['sha256']for v in CC[c].get('HERO_input_views',[])if v.get('sha256')}for c in self.ids];w=[]
        for i,c in enumerate(self.ids):
            corr=sum(len(rgbsets[i]&rgbsets[j])/max(1,len(rgbsets[i]|rgbsets[j]))for j in range(len(self.ids))if i!=j);quality=1. if GATE[c]['qualification']=='CONDITIONAL_USABLE'else .25;w.append(quality/(1+corr))
        self.weights=np.array(w)/sum(w)
        self.N=sum(128+len(t['boundary'])+14400+len(o['pairs'])+len(r)for t,o,r in zip(self.targets,self.o,self.rays))+9
    def residual(self,p):
        self.calls+=1;parts=[]
        try:
            for target,s,o,rays,w in zip(self.targets,self.cameras,self.o,self.rays,self.weights):
                C=two_d_parts(p,self.R0,target,s['K'],s['T'],ringscene(self.scene));D,z=depth_parts(p,self.R0,rays,o['pairs'],o['depth_delta_mm']);parts.extend([x*np.sqrt(w)for x in C+D])
            prior=np.r_[(p[:3]-self.base[:3])/10,p[3:6]/.8,(p[6:9]-self.base[6:9])/1.2]*np.sqrt(.05);parts.append(prior)
            result=np.concatenate(parts)
            if not np.isfinite(result).all():raise ValueError('nonfinite residual')
            return result
        except (ValueError,np.linalg.LinAlgError):
            self.invalid_calls+=1;return np.full(self.N,1000.)
    def solve(self,start=0):
        rng=np.random.default_rng(20261104+start);p=self.base.copy()
        if start:p[:3]+=rng.normal(0,.4,3);p[3:6]+=rng.normal(0,.08,3);p[6:9]+=rng.normal(0,.12,3)
        p=np.clip(p,self.lo+1e-7,self.hi-1e-7);initial=p.copy();self.calls=0;self.invalid_calls=0;t0=time.monotonic();initial_r=self.residual(p)
        result=least_squares(self.residual,p,jac='3-point',bounds=(self.lo,self.hi),method='trf',loss='linear',max_nfev=60,ftol=1e-5,xtol=1e-5,gtol=1e-5,x_scale=np.r_[np.ones(3),np.full(3,.1),np.full(3,.2)])
        return dict(scene=self.scene,arm=self.arm,variant=self.variant,start=start,p=result.x,R0=self.R0,initial=initial,initial_objective=float(initial_r@initial_r/2),objective=float(result.fun@result.fun/2),nfev=result.nfev,actual_residual_calls=self.calls,seconds=time.monotonic()-t0,optimizer_success=bool(result.success),termination=str(result.message),active_bounds=np.asarray(result.active_mask),invalid_projection_calls=self.invalid_calls,source_ids=self.ids,weights=self.weights,parameter_N=9)

def evaluate(m,cid,save_arrays=False):
    p=np.array(m['p']);R0=np.array(m['R0']);s=source(cid);o=obs(cid);u,v=np.meshgrid(np.arange(640),np.arange(360));uv=np.c_[u.ravel(),v.ravel()];rays=vis.camera_rays(uv,s['K'],s['T']);z=first_depth(p,R0,rays);cad=cast(ringscene(CC[cid]['scene_id']),uv,s['K'],s['T'])[0];raw=np.isfinite(z)&(z>0);visible=raw&(z<=cad+.05);pred=visible.reshape(360,640);full=o['full_polyp'];ring=s['labels']==2
    # All original foreground pixels remain in the denominator. Ring is unknown,
    # never counted as a false negative Polyp observation or background truth.
    known=~ring;intersection=int((pred&full).sum());outside=int((pred&~full&known).sum());miss=int((full&~pred).sum());union=int((full|(pred&known)).sum());obsb=contour(full);predb=contour(pred&known);adj=cv2.dilate(ring.astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool)
    ob=obsb[~adj[obsb[:,1].astype(int),obsb[:,0].astype(int)]];pb=predb[~adj[predb[:,1].astype(int),predb[:,0].astype(int)]]
    d1=cKDTree(pb).query(ob)[0]if len(pb)and len(ob)else np.empty(0);d2=cKDTree(ob).query(pb)[0]if len(pb)and len(ob)else np.empty(0)
    rz=first_depth(p,R0,vis.camera_rays(o['depth_native_uv'],o['Kn'],s['T']));rcad=cast(ringscene(CC[cid]['scene_id']),o['depth_native_uv'],o['Kn'],s['T'])[0];hit=np.isfinite(rz)&(rz>0)&(rz<=rcad+.05);pair=o['pairs'];good=hit[pair].all(1);err=rz[pair[good,0]]-rz[pair[good,1]]-o['depth_delta_mm'][good]
    X,Q,a=decode(p,R0);P,F=mesh(p,R0);met=dict(reference=cid,full_mask_denominator=int(full.sum()),canvas_denominator=230400,predicted_visible_N=int(pred.sum()),intersection_N=intersection,miss_N=miss,outside_N=outside,full_mask_IoU=intersection/max(1,union),hit_per_fixed_mask=intersection/max(1,int(full.sum())),miss_per_fixed_mask=miss/max(1,int(full.sum())),outside_per_fixed_mask=outside/max(1,int(full.sum())),outside_per_fixed_canvas=outside/230400,unknown_ring_prediction_N=int((pred&ring).sum()),boundary_bidir_px=stats(np.r_[d1,d2]),boundary_fixed_source_px=stats(d1),boundary_source_N=len(ob),boundary_predicted_N=len(pb),depth_fixed_N=len(rz),depth_hit_N=int(hit.sum()),depth_miss_N=int((~hit).sum()),depth_hit_fraction=float(hit.mean()),relative_depth_fixed_pair_N=len(pair),relative_depth_hit_pair_N=int(good.sum()),relative_depth_miss_pair_N=int((~good).sum()),relative_depth_mm=stats(err),CAD_occluded_N=int((raw&~visible).sum()),CAD_occluded_fraction=float((raw&~visible).sum()/max(1,raw.sum())),center_mm=X,semiaxes_mm=a,rotation_matrix=Q,full_axis_lengths_mm=2*a,world_extents_mm=np.ptp(P,axis=0),volume_mm3=float(4*np.pi/3*np.prod(a)),axis_ratio=float(max(a)/min(a)),real_GT='NOT_EVALUABLE')
    if save_arrays:
        name=m['scene']+'__'+m['arm']+'__'+m['variant'];np.savez_compressed(R/'local_results'/(name+'__'+cid+'.npz'),first_Z_mm=z.reshape(360,640),predicted_mask=pred,full_mask=full,ring=ring,depth_ray_Z=rz,depth_ray_hit=hit)
    return met
