"""One preregistered CPU evolution. Validation never enters a solve/acceptance."""
from solver import *
from collision import Collision
from preflight import blender
import time,datetime
def native_metrics(rt,cid):
    o=obs(cid);z,_=cast(rt,o['uv'],o['Kn'],source(cid)['T']);hit=np.isfinite(z)&(z>0)&(z<=o['cad']+.05);pairs=o['pairs'];ph=hit[pairs].all(1);rel=z[pairs[ph,0]]-z[pairs[ph,1]]-o['delta'][ph];dist=rt.compute_distance(o3d.core.Tensor(o['X'].astype(np.float32))).numpy()
    return dict(source=cid,native_N=len(z),hit_N=int(hit.sum()),miss_N=int((~hit).sum()),first_depth_mm=stats(z[hit]-o['z'][hit]),pair_N=len(pairs),pair_hit_N=int(ph.sum()),relative_depth_mm=stats(rel),HERO_distance_mm=stats(dist)),dict(z=z,hit=hit,pair_hit=ph,distance=dist)
def evaluate(name,e,phi,V,F,physical=None):
    rt=mesh_scene(V,F);rows=[];native=[]
    for cid in e.d.ids:
        r,pred=e.d.mask_metrics(rt,cid);n,arr=native_metrics(rt,cid);r.update(n);rows.append(r);native.append(arr);np.savez_compressed(R/'local_results'/name/(cid+'_EVAL.npz'),pred=pred,**arr)
    obj,_=e.objective(phi,V,F);g=e.g;grad=np.linalg.norm(g.gradient(phi),axis=1);ne=abs(phi)<.5;drift=np.r_[abs(signed(e.initial_rt,V)),abs(signed(rt,e.initial_mesh[0]))];constraints,geo=e.cheap_constraints(phi,phi,V,F,V,F)
    out=dict(stage=name,objective=obj,per_source=rows,geometry=geo,initial_surface_drift_mm=stats(drift),Ring=physical or e.col.check(V,F),gradient_near_surface=stats(grad[ne]),phi_at_HERO_mm=stats(e.H@phi),protected_HERO_mm=stats(e.HP@phi),volume_mm3=volume(V,F),timestamp=datetime.datetime.now().isoformat())
    save('metrics/'+name+'.json',out);return out
def main():
    assert not(R/'metrics/RUN_START.json').exists(),'ONE_FORMAL_RUN_ONLY';assert load(R/'metrics/NUMERICAL_PREFLIGHT.json')['passed']
    freeze=load(R/'metrics/IMPLEMENTATION_FREEZE.json')
    for a in freeze['files']:assert sha(a['path'])==a['sha256'],a['path']
    a=np.load(R/'inputs/INITIAL_FIELD.npz');g=Field(a['origin'],a['shape'],float(a['h']));phi=a['phi'].copy();data=Data();e=Evolution(g,phi,data);e.col=Collision('G01_004');V,F=g.mesh(phi);save('metrics/RUN_START.json',dict(timestamp=datetime.datetime.now().isoformat(),code_commit=freeze['commit'],configuration=asset(R/'config/LOCKED_PROTOCOL.json'),no_validation_in_optimization=True));start=time.time();log=[];history=[];noaccept=0
    history.append(evaluate('INITIAL',e,phi,V,F));objective,_=e.objective(phi,V,F)
    for iteration in range(1,protocol()['iterations']+1):
        t0=time.time();delta,ls,rows=e.propose(phi,V,F,iteration);save('metrics/iter_%02d_SOLVER.json'%iteration,ls);accepted=False
        if not np.isfinite(delta).all():raise FloatingPointError('NONFINITE_SPARSE_SOLUTION')
        for alpha in protocol()['line_search']:
            candidate=phi+alpha*delta;vv,ff=g.mesh(candidate);reasons,geo=e.cheap_constraints(phi,candidate,vv,ff,V,F);col=e.col.check(vv,ff)
            if col['collision']:reasons.append('CAD_ACTUAL_MESH_COLLISION')
            obj,view=e.objective(candidate,vv,ff)
            if obj['total']>=objective['total']-protocol()['minimum_objective_decrease']:reasons.append('NO_FIXED_TRAIN_OBJECTIVE_IMPROVEMENT')
            rec=dict(iteration=iteration,alpha=alpha,accepted=not reasons,reasons=reasons,before=objective,after=obj,geometry=geo,Ring=col,solver=ls,elapsed_seconds=time.time()-t0);log.append(rec);print('ITER',iteration,'alpha',alpha,'accepted',not reasons,'objective',round(obj['total'],7),'reasons',reasons,flush=True)
            if not reasons:
                oldphi=phi;phi=candidate;V,F=vv,ff;objective=obj;accepted=True;noaccept=0;name='ACCEPTED_%02d'%iteration;snapshot(name,g,phi,iteration=iteration,alpha=alpha,status='ACCEPTED')
                history.append(evaluate(name,e,phi,V,F,col));break
        if not accepted:noaccept+=1
        save('metrics/UPDATE_LOG.json',log);table('metrics/UPDATE_LOG.csv',log);save('metrics/EVOLUTION_HISTORY.json',history)
        if noaccept>=protocol()['stop_after_no_accept']:break
    snapshot('FINAL',g,phi,status='BUDGET_COMPLETED'if iteration==protocol()['iterations']else'NO_ACCEPTED_IMPROVEMENT_STOP',iteration=iteration)
    final=evaluate('FINAL',e,phi,V,F);final['Blender']=blender('FINAL_SDF',V,F);save('metrics/FINAL.json',final)
    accepted=[x for x in log if x['accepted']]
    if accepted:
        mid=accepted[(len(accepted)-1)//2]['iteration'];aa=np.load(R/'local_results'/('ACCEPTED_%02d'%mid)/'FIELD.npz');b=blender('MIDDLE_SDF',aa['V'],aa['F']);save('metrics/MIDDLE.json',dict(stage='ACCEPTED_%02d'%mid,Blender=b))
    save('metrics/RUN_FINISHED.json',dict(finished=True,iterations=iteration,accepted_N=len(accepted),rejected_N=len(log)-len(accepted),actual_proposals=len(log),elapsed_seconds=time.time()-start,stop='BUDGET_COMPLETED'if iteration==protocol()['iterations']else'3_COMPLETE_ITERATIONS_WITHOUT_IMPROVEMENT',timestamp=datetime.datetime.now().isoformat(),no_next_stage=True));print('FINISHED',len(accepted),'accepted',time.time()-start,flush=True)
if __name__=='__main__':main()
