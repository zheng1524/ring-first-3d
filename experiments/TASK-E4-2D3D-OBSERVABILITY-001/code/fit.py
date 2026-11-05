"""Gate A short Powell pair. Same P0/seed/budget; one target-boundary change."""
import os,sys,time,datetime
os.environ['E4_OPTIMIZER_ONLY']='1'
from continuous import *
from model import Body
from physics import physical
from scipy.optimize import minimize
def main():
    arm=sys.argv[1];assert arm in ['ORIGINAL','SUBPIXEL_TARGET']
    assert load(R/'metrics/PROJECTION_GATE.json')['passed'];assert load(R/'metrics/FIREWALL.json')['passed'];assert load(R/'metrics/OBSERVABILITY.json')['no_native_GT_read']
    if arm=='SUBPIXEL_TARGET':assert load(R/'metrics/SYNTHETIC_OBJECTIVE_AUDIT.json')['trigger_single_target_boundary_correction']
    freeze=load(R/'assets_index/PREOPT_FREEZE.json')
    for f in freeze['files']:assert sha(f['path'])==f['sha256'],f['path']
    root=R/'local_results'/arm;assert not root.exists();root.mkdir()
    body=Body();renderer=Renderer();q0=np.array(load(R/'metrics/MASK_ONLY_INITIALIZATION.json')['q']);corrected=arm=='SUBPIXEL_TARGET';records=[];calls=[];history=[];cache={};start=time.time();counter=[0]
    def keep(stage,q,loss=None):
        V,F=body.mesh(q);folder=root/stage;folder.mkdir();np.savez_compressed(folder/'MODEL.npz',V=V,F=F,q=q);mesh=trimesh.Trimesh(V,F,process=False);mesh.export(folder/'BODY_mm.ply')
        history.append(dict(stage=stage,q=q,loss=loss,seconds=time.time()-start,physical=physical(V,F),per_view=[subpixel_metrics(renderer,V,F,c['id'])for c in renderer.views]))
        save('metrics/'+arm+'_HISTORY.json',history)
    def fun(q):
        key=tuple(np.round(q,10));hit=key in cache
        if not hit:
            val,per=objective(body,renderer,q,corrected);V,F=body.mesh(q);ph=physical(V,F);cache[key]=val
            records.append(dict(evaluation=len(records)+1,q=q.copy(),loss=val,per_view=per,physical=ph,seconds=time.time()-start))
        calls.append(dict(call=len(calls)+1,q=q.copy(),cache_hit=hit,loss=cache[key]))
        return cache[key]
    def callback(q):
        counter[0]+=1;keep('ROUND_%02d'%counter[0],q,fun(q));save('metrics/'+arm+'_TRACE.json',records);print(arm,'ROUND',counter[0],history[-1]['loss'],flush=True)
    save('metrics/'+arm+'_START.json',dict(timestamp=datetime.datetime.now().isoformat(),GT_not_read=True,seed=q0,code_commit=freeze['commit'],single_change='target contour at binary 0.5 level'if corrected else'original foreground-center target contour'))
    keep('P0',np.r_[q0[:3],0.]);keep('START',q0,fun(q0))
    bounds=np.array(protocol()['center_bounds_mm']).T.tolist()+[protocol()['amplitude_bounds_mm']]
    out=minimize(fun,q0,method='Powell',bounds=bounds,callback=callback,options=dict(maxiter=12,maxfev=500,xtol=.01,ftol=1e-5,direc=np.diag([.2,.2,.2,.1])))
    keep('FINAL',out.x,float(out.fun));save('metrics/'+arm+'_TRACE.json',records);table('metrics/'+arm+'_TRACE.csv',records);save('metrics/'+arm+'_CALLS.json',calls)
    save('metrics/'+arm+'_FINISHED.json',dict(finished=True,success=bool(out.success),message=str(out.message),iterations=int(out.nit),optimizer_nfev=int(out.nfev),distinct_geometry_evaluations=len(records),q=out.x,loss=float(out.fun),seconds=time.time()-start,selected_by='last bounded iterate; no GT or holdout selection',collision_candidates=sum(x['physical']['collision']for x in records),no_additional_collision_rejection_optimizer=True))
    print(arm,'FINISHED',out.nfev,time.time()-start,flush=True)
if __name__=='__main__':main()
