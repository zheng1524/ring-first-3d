"""One/two-case R1. Stop globally if most physical proposals are rejected."""
from inputs import *
from geometry import Model
from observations import Observations,mesh_normals
from collision import Collision
from mesh_checks import self_intersections
from scipy.optimize import minimize
import subprocess,time
BLENDER=Path('/home/liu/blender/blender-5.0.1-linux-x64/blender')
def endpoint_check(name,scene,V,F,col):
    result=col.check(V,F,True)
    # Surface contact alone is not solid penetration. Ambiguous triangle-only
    # contact is independently resolved by Blender's exact solid intersection.
    if result['triangle_collision']and min(result['body_vertex_min_signed_mm'],result['CAD_vertex_min_signed_mm'])>=-col.eps:
        b=blender_check(name,scene,V,F);result['contact_Blender']=b
        if b['EXACT_intersection_volume_mm3']<=1e-8:
            result.update(collision=False,distance_mm=0.,numerical_contact=True)
    return result
def volume(V,F):
    t=V[F];return float(np.einsum('ij,ij->i',t[:,0],np.cross(t[:,1],t[:,2])).sum()/6)
def volume_gradient(V,F,J):
    t=V[F];g=np.zeros_like(V)
    for k in range(3):np.add.at(g,F[:,k],np.cross(t[:,(k+1)%3],t[:,(k+2)%3])/6)
    return np.einsum('ij,ijk->k',g,J)
def blender_check(name,scene,V,F):
    cad=ringmesh(scene);inp=R/'local_results'/(name+'_Blender_Input.npz');out=R/'metrics'/(name+'_BLENDER.json');np.savez_compressed(inp,V=V,F=F,CAD_V=cad.vertices,CAD_F=cad.faces)
    cmd=[str(BLENDER),'--factory-startup','--background','--threads','2','--python-exit-code','2','--python',str(R/'code/blender_check.py'),'--',str(inp),str(out)]
    result=subprocess.run(cmd,capture_output=True,text=True,timeout=120);(R/'runtime'/(name+'_Blender.log')).write_text(result.stdout+result.stderr);assert result.returncode==0,result.stderr[-1000:];return load(out)
def evaluate(scene,V,F,cid):
    s=source(cid);o=obs(cid);u,v=np.meshgrid(np.arange(640),np.arange(360));uv=np.c_[u.ravel(),v.ravel()];rt=mesh_scene(V,F);z=cast(rt,uv,s['K'],s['T'])[0];cad=cast(ringscene(scene),uv,s['K'],s['T'])[0];pred=(np.isfinite(z)&(z>0)&(z<=cad)).reshape(360,640);full=s['labels']==1;known=s['labels']!=2;z=cast(rt,o['uv'],o['Kn'],s['T'])[0];hit=np.isfinite(z)&(z>0)&(z<=o['cad']+.05);pairs=o['pairs'];good=hit[pairs].all(1);p=pairs[good];err=z[p[:,0]]-z[p[:,1]]-o['delta'][good];d=rt.compute_distance(o3d.core.Tensor(o['X'].astype(np.float32))).numpy()
    return dict(source=cid,IoU=float((pred&full).sum()/max(1,(full|(pred&known)).sum())),fixed_Mask_N=int(full.sum()),Mask_hit_N=int((pred&full).sum()),Mask_miss_N=int((full&~pred).sum()),outside_N=int((pred&~full&known).sum()),native_fixed_N=len(z),native_hit_N=int(hit.sum()),native_miss_N=int((~hit).sum()),relative_depth_mm=stats(err),relative_pair_N=len(pairs),relative_valid_pair_N=int(good.sum()),HERO_point_to_mesh_mm=stats(d),camera=GATE[cid]['qualification'],role='TRAINING_POOL_NO_HELDOUT',GT='NOT_EVALUABLE'),dict(pred=pred,z=z,hit=hit,pair_hit=good)
def bounds_for(row,D,n=9):
    p=np.array(row['p']);lo=np.r_[p[:3]-.25*D,p[3:6]-.5,p[6:9]+np.log(.8),np.full(n-9,-np.inf)];hi=np.r_[p[:3]+.25*D,p[3:6]+.5,p[6:9]+np.log(1.25),np.full(n-9,np.inf)];return lo,hi
def shape_quality(V,F,reference,initial_volume):
    a=np.cross(V[F[:,1]]-V[F[:,0]],V[F[:,2]]-V[F[:,0]]);b=np.cross(reference[F[:,1]]-reference[F[:,0]],reference[F[:,2]]-reference[F[:,0]]);ratio=np.linalg.norm(a,axis=1)/np.linalg.norm(b,axis=1);fold=(a*b).sum(1)<=0;si=self_intersections(V,F);vr=volume(V,F)/initial_volume;reason=[]
    if ratio.min()<.15:reason.append('TRIANGLE_COLLAPSE')
    if fold.any():reason.append('FACE_FOLD')
    if si['intersections']or si['coplanar_candidates']:reason.append('SELF_INTERSECTION_OR_COPLANAR_UNRESOLVED')
    if vr<.85:reason.append('VOLUME_SHRINK_BELOW_REGISTERED_85PCT')
    if vr>1.5:reason.append('EXCESS_VOLUME_EXPANSION')
    return reason,dict(min_face_area_ratio=float(ratio.min()),folded_face_N=int(fold.sum()),volume_ratio=vr,**si)
class P0Constraints:
    def __init__(self,model,col):
        self.model=model;self.col=col;tri=col.V[col.F];samples=[]
        for i in range(5):
            for j in range(5-i):samples.append((i*tri[:,0]+j*tri[:,1]+(4-i-j)*tri[:,2])/4)
        self.points=np.unique(np.round(np.vstack(samples),12),axis=0);self.groups=np.array_split(np.arange(len(self.points)),256);self.cover=col.cover/4;self.target=.05+self.cover+col.eps;self.ref=model.reference.copy();self.last=None
    def level(self,p,P):
        c,Q,a=decode(p,self.model.R0);return min(a)*(np.linalg.norm((P-c)@Q/a,axis=1)-1)
    def both(self,p):
        if self.last is not None and np.array_equal(p,self.last[0]):return self.last[1:]
        f=self.level(p,self.points);ix=np.array([g[np.argmin(f[g])]for g in self.groups]);value=f[ix]-self.target;J=np.empty((256,9));h=1e-5
        for k in range(9):
            a=p.copy();b=p.copy();a[k]+=h;b[k]-=h;J[:,k]=(self.level(a,self.points[ix])-self.level(b,self.points[ix]))/(2*h)
        # Ellipsoid volume ratio is exact under the same fixed triangulation.
        vr=np.exp((p[6:9]-self.ref[6:9]).sum());value=np.r_[value,vr-.85];J=np.vstack([J,np.r_[np.zeros(6),np.full(3,vr)]]);self.last=(p.copy(),value,J);return value,J
def conservative_p0(scene,row,model,obsn,col):
    old=np.array(row['p']);V0=model.vertices(old);D=2*(3*volume(V0,model.F)/(4*np.pi))**(1/3);lo,hi=bounds_for(row,D);constraint=P0Constraints(model,col);trace=[];cached=None;best=None
    def cost(p):
        nonlocal cached,best
        if cached is not None and np.array_equal(p,cached[0]):return cached[1]
        z=obsn.linearize(p);g,_=constraint.both(p);trace.append(dict(evaluation=len(trace)+1,objective=z['E'],min_constraint_mm=float(g[:-1].min()),volume_ratio=float(g[-1]+.85),p=p.copy()))
        if g.min()>=-1e-6 and(best is None or z['E']<best[1]['E']):best=(p.copy(),z)
        cached=(p.copy(),z);return z
    result=minimize(lambda p:cost(p)['E'],old,jac=lambda p:cost(p)['g'],method='SLSQP',bounds=list(zip(lo,hi)),constraints=[dict(type='ineq',fun=lambda p:constraint.both(p)[0],jac=lambda p:constraint.both(p)[1])],options=dict(maxiter=60,ftol=1e-7,disp=False))
    cost(result.x);p=best[0]if best is not None else result.x;V=model.vertices(p);cert=constraint.both(p)[0];coll=col.check(V,model.F,True);old_ev=[evaluate(scene,V0,model.F,c)[0]for c in obsn.ids];new_ev=[evaluate(scene,V,model.F,c)[0]for c in obsn.ids];drop=np.array([b['IoU']-a['IoU']for a,b in zip(old_ev,new_ev)]);bad=[]
    if cert.min()<-1e-6 or coll['collision']or coll['distance_mm']<.05-1e-5:bad.append('POSITIVE_GAP_NOT_CERTIFIED')
    if drop.mean()<-.03 or drop.min()<-.05:bad.append('MASK_EXPLANATION_LOST')
    for a,b in zip(old_ev,new_ev):
        if b['native_hit_N']<a['native_hit_N']-.05*512:bad.append('HERO_COVERAGE_LOST:'+a['source'])
        if a['relative_depth_mm']['MAE']is not None and b['relative_depth_mm']['MAE']is not None and b['relative_depth_mm']['MAE']>a['relative_depth_mm']['MAE']+.15:bad.append('RELATIVE_HERO_WORSENED:'+a['source'])
    bl=blender_check(scene+'_HISTORICAL_P0',scene,V0,model.F);bn=blender_check(scene+'_CONSERVATIVE_P0',scene,V,model.F)
    if bn['BVH_intersecting_triangle_pairs']or bn['EXACT_intersection_volume_mm3']>1e-8:bad.append('BLENDER_INTERSECTION')
    resultdict=dict(status='P0_INFEASIBLE'if bad else'P0_FEASIBLE',reasons=bad,scope='single preregistered local solve, not a global infeasibility theorem',optimizer_success=bool(result.success),optimizer_message=result.message,optimizer_iterations=int(result.nit),trace=trace,old_p=old,new_p=p,old_evaluations=old_ev,new_evaluations=new_ev,old_collision=col.check(V0,model.F,True),new_collision=coll,old_Blender=bl,new_Blender=bn,analytic_clearance_lower_bound_mm=float(cert[:-1].min()+constraint.target-constraint.cover),CAD_cover_radius_mm=constraint.cover,CAD_certificate_sample_N=len(constraint.points),mean_IoU_change=float(drop.mean()),worst_IoU_change=float(drop.min()),volume_ratio=volume(V,model.F)/volume(V0,model.F),axis_ratios=np.exp(p[6:9]-old[6:9]))
    save('metrics/'+scene+'_P0.json',resultdict);np.savez_compressed(R/'local_results'/(scene+'_HISTORICAL_P0.npz'),V=V0,F=model.F,q=old);np.savez_compressed(R/'local_results'/(scene+'_P0_CANDIDATE.npz'),V=V,F=model.F,q=p);return resultdict,p
class MajorityStop(RuntimeError):pass
class Counter:
    def __init__(self):self.rows=[]
    def add(self,row):
        self.rows.append(row);n=len(self.rows);rejected=sum(not r['accepted']for r in self.rows);window=self.rows[-10:];trigger=n>=10 and(rejected/n>.5 or sum(not r['accepted']for r in window)/10>.5)
        save('metrics/ALL_UPDATE_PROPOSALS.json',self.rows)
        if trigger:raise MajorityStop(f'MAJORITY_REJECTED: {rejected}/{n}; recent {sum(not r["accepted"]for r in window)}/10')
def refine(scene,row,model,obsn,col,q,stage,base_quality,reference,old_volume,counter,damping=.01):
    cfg=protocol()[stage];ids=protocol()['scenes'][scene]['P1'if stage=='P1'else'P2'];D=2*(3*old_volume/(4*np.pi))**(1/3);lo,hi=bounds_for(row,D,len(q));trace=[];status='BUDGET_COMPLETED'
    for iteration in range(cfg['max_iterations']):
        current=obsn.linearize(q,ids,True);all_current=obsn.linearize(q,None);H=current['H'];g=current['g'];diag=np.maximum(np.diag(H),1e-6);unconstrained=np.linalg.solve(H+damping*np.diag(diag),-g);V=current['V'];JV=current['JV'];gs,GC,info=col.constraints(V,model.F,JV);volume_now=volume(V,model.F);gv=volume_gradient(V,model.F,JV);G=np.vstack([GC,gv/old_volume]);gap=np.r_[gs+.5*col.eps,volume_now/old_volume-.85];imageJ=np.vstack([m['J'].reshape(-1,len(q))for m in current['mapping'].values()]);errors=np.concatenate([np.r_[m['contour_error_px'],np.linalg.norm(m['uv'][m['reverse_indices']]-m['observed_boundary'],axis=1)]for m in current['mapping'].values()]);radius=max(1.,float(np.quantile(errors,.75)));selected=np.arange(0,len(imageJ),max(1,len(imageJ)//512));IJ=imageJ[selected]
        accepted=False;last_trial=None
        for trial in range(4):
            A=H+damping*np.diag(diag);linear=dict(type='ineq',fun=lambda d:gap+G@d,jac=lambda d:G);pixel=dict(type='ineq',fun=lambda d:np.r_[radius-IJ@d,radius+IJ@d],jac=lambda d:np.vstack([-IJ,IJ]));sol=minimize(lambda d:.5*d@A@d+g@d,np.zeros(len(q)),jac=lambda d:A@d+g,method='SLSQP',bounds=list(zip(lo-q,hi-q)),constraints=[linear,pixel],options=dict(maxiter=80,ftol=1e-10,disp=False));d=sol.x;aa=q+d;proposal=model.vertices(aa);reasons=[];path_info=None;predicted=float(-g@d-.5*d@H@d)
            if not sol.success:reasons.append('FEASIBLE_DIRECTION_QP_FAILED')
            colcheck=endpoint_check(f'{scene}_{stage}_{iteration}_{trial}_CONTACT',scene,proposal,model.F,col)
            if colcheck['collision']:reasons.append('RING_INTERSECTION')
            shape_reasons,shapeinfo=shape_quality(proposal,model.F,reference,old_volume);reasons+=shape_reasons
            candidate=None;all_candidate=None
            if not reasons:
                candidate=obsn.linearize(aa,ids);all_candidate=obsn.linearize(aa,None)
                if candidate['E']>=current['E']-1e-9:reasons.append('NO_ACTUAL_OBJECTIVE_IMPROVEMENT')
                for view,b0 in zip(all_candidate['per_view'],base_quality):
                    if view['contour_mean_px']>b0['contour_mean_px']+.5:reasons.append('VIEW_CONTOUR_REGRESSION:'+view['source'])
                    if view['depth_hit_N']<b0['depth_hit_N']-.05*512:reasons.append('HERO_COVERAGE_REGRESSION:'+view['source'])
                if not reasons:
                    path_ok,path_info=col.path(V,proposal,model.F)
                    if not path_ok:
                        samples=[endpoint_check(f'{scene}_{stage}_{iteration}_{trial}_SWEEP{k}',scene,(1-f)*V+f*proposal,model.F,col)for k,f in enumerate([.25,.5,.75])]
                        if any(v['collision']for v in samples):reasons.append('INTERMEDIATE_SOLID_PENETRATION')
                        path_info=dict(reason='DISCRETE_MIDPOINT_CHECK_ONLY_NOT_CERTIFIED_CCD',source=path_info,samples=samples)
            actual=current['E']-(candidate['E']if candidate else current['E']);rho=actual/max(predicted,1e-15);maxmove=float(np.linalg.norm(proposal-V,axis=1).max());rawV=model.vertices(q+unconstrained);rawmove=float(np.linalg.norm(rawV-V,axis=1).max());cos=float(unconstrained@d/max(np.linalg.norm(unconstrained)*np.linalg.norm(d),1e-15))
            if maxmove<col.eps:reasons.append('BELOW_CERTIFIED_GEOMETRIC_RESOLUTION')
            key=f'{scene}_{stage}_iter{iteration:02d}_trial{trial:02d}';np.savez_compressed(R/'local_results'/(key+'.npz'),before_V=V,proposed_V=proposal,accepted_V=V if reasons else proposal,F=model.F,q_before=q,q_proposed=aa,raw_parameter_update=unconstrained,feasible_parameter_update=d)
            # Actual contour-to-triangle correspondences and projected motion.
            mp={}
            for c,m in current['mapping'].items():
                edges=m['edges'];t=m['fraction'];P=proposal[edges[:,0]]*(1-t[:,None])+proposal[edges[:,1]]*t[:,None];s=source(c);updated=vis.project_camera(P,s['K'],s['T'])[0];mp[c]={k:v for k,v in m.items()if k!='J'}|dict(predicted_uv_displacement=np.einsum('ijk,k->ij',m['J'],d),actual_updated_uv=updated)
            save('local_results/'+key+'_CORRESPONDENCE.json',mp)
            entry=dict(case=scene,stage=stage,iteration=iteration,trial=trial,accepted=not reasons,reasons=reasons,before_objective=current['E'],candidate_objective=candidate['E']if candidate else None,predicted_reduction=predicted,actual_reduction=actual,rho=rho,damping=damping,data_pixel_radius=radius,unconstrained_max_vertex_move_mm=rawmove,candidate_max_vertex_move_mm=maxmove,direction_cosine_with_unconstrained=cos,active_contact_constraints=info['active_constraints_N'],collision=colcheck,path_check=path_info,geometry=shapeinfo,per_view_before=all_current['per_view'],per_view_after=all_candidate['per_view']if all_candidate else None,snapshot=str(R/'local_results'/(key+'.npz')))
            trace.append(entry);last_trial=entry
            if not reasons:
                q=aa;accepted=True;damping*=.33 if rho>.75 else(3 if rho<.25 else 1)
            else:damping*=3
            print('UPDATE',scene,stage,iteration,trial,'ACCEPT'if not reasons else'REJECT',reasons,'move_mm',round(maxmove,4),flush=True);counter.add(entry)
            if accepted:break
            # A collision changes constraints and the QP direction; this is
            # not multiplication of the same rejected direction by a scalar.
            if colcheck['collision']:
                gs,GC,info=col.constraints(V,model.F,JV,activation_distance=float('inf'));G=np.vstack([GC,gv/old_volume]);gap=np.r_[gs+.5*col.eps,volume_now/old_volume-.85]
        if not accepted and len(counter.rows)>=10:status='NO_ACCEPTED_STEP';break
        if accepted and actual<cfg['ftol']*max(1,current['E'])and np.linalg.norm(unconstrained)<1e-4:status='CONVERGED';break
    return q,dict(stage=stage,status=status,trace=trace,damping=damping),damping
def save_stage(scene,stage,q,model,obsn,col):
    V=model.vertices(q);folder=R/'local_results'/scene;folder.mkdir(exist_ok=True);np.savez_compressed(folder/(stage+'.npz'),V=V,F=model.F,q=q);trimesh.Trimesh(V,model.F,process=False).export(folder/(stage+'.ply'));ev=[]
    for cid in obsn.ids:
        met,ar=evaluate(scene,V,model.F,cid);ev.append(met);np.savez_compressed(folder/(stage+'__'+cid+'.npz'),**ar)
    result=dict(stage=stage,evaluations=ev,collision=endpoint_check(scene+'_'+stage+'_CONTACT',scene,V,model.F,col),Blender=blender_check(scene+'_'+stage,scene,V,model.F),q=q,volume_mm3=volume(V,model.F),bounds_mm=[V.min(0),V.max(0)]);save('metrics/'+scene+'_'+stage+'.json',result);return result
def main():
    config=protocol();counter=Counter();cases=[];stop=None
    for scene in config['case_order']:
        sc=config['scenes'][scene]
        if stop:cases.append(dict(scene=scene,status='NOT_RUN_GLOBAL_STOP',reason=stop));continue
        row=p0(scene,sc['initial']);model=Model(row);obsn=Observations(scene,model);col=Collision(scene);old_volume=volume(model.vertices(np.array(row['p'])),model.F);pre,p=conservative_p0(scene,row,model,obsn,col)
        if pre['status']!='P0_FEASIBLE':stop='P0_INFEASIBLE:'+scene;cases.append(dict(scene=scene,status='P0_INFEASIBLE',reasons=pre['reasons']));continue
        basis=model.build_basis(p,32);np.savez_compressed(R/'inputs'/(scene+'_CONSERVATIVE_BASIS.npz'),**basis);q=np.r_[p,np.zeros(12)];base=obsn.linearize(q,None)['per_view'];reference=model.vertices(q);stages=[save_stage(scene,'P0',q,model,obsn,col)];records=[];damping=.01
        try:
            q,rec,damping=refine(scene,row,model,obsn,col,q,'P1',base,reference,old_volume,counter,damping);records.append(rec);stages.append(save_stage(scene,'P1',q,model,obsn,col));before=model.vertices(q);q=np.r_[q,np.zeros(20)];transfer=float(abs(model.vertices(q)-before).max());assert transfer<1e-10;save('metrics/'+scene+'_P1_P2_TRANSFER.json',dict(max_vertex_transfer_error_mm=transfer,parameters_reset=False));q,rec,damping=refine(scene,row,model,obsn,col,q,'P2',base,reference,old_volume,counter,damping);records.append(rec);stages.append(save_stage(scene,'P2',q,model,obsn,col));cases.append(dict(scene=scene,status='P2_COMPLETED',stages=stages,records=records))
        except MajorityStop as exc:
            stop=str(exc);last=counter.rows[-1];snap=np.load(last['snapshot']);q=snap['q_proposed']if last['accepted']else snap['q_before'];stages.append(save_stage(scene,'LAST_SAFE',q,model,obsn,col));cases.append(dict(scene=scene,status='STOPPED_MAJORITY_REJECTED',reason=stop,stages=stages,records=records))
        save('metrics/CASE_RESULTS.json',cases)
    save('metrics/CASE_RESULTS.json',cases);save('metrics/STOP_STATUS.json',dict(stop=stop,candidate_N=len(counter.rows),accepted_N=sum(r['accepted']for r in counter.rows),rejected_N=sum(not r['accepted']for r in counter.rows),only_registered_cases=True,no_further_optimization_scheduled=True));print('DONE',[(x['scene'],x['status'])for x in cases],flush=True)
if __name__=='__main__':main()
