from inputs import *
from shape import Body
from objective import Objective
from physical import *
from scipy.optimize import minimize
# Controlled reuse of the exact analytic CAD certificate; no R1 optimizer import.
_p=R1/'code/run.py';_nodes=[n for n in ast.parse(_p.read_text()).body if isinstance(n,ast.ClassDef)and n.name=='P0Constraints'];exec(compile(ast.Module(body=_nodes,type_ignores=[]),str(_p),'exec'),globals())

def safe_p0(scene):
    row=p0(scene,protocol()['scenes'][scene]['initial'])
    if scene=='G01_004':
        path=R1/'local_results/G01_004/P0.npz';cp=dict(np.load(path));p=cp['q'][:9];model=Body(row,p);assert abs(model.vertices(p)-cp['V']).max()<1e-10;co=Collision(scene);z=co.check(cp['V'],cp['F'],True);b=blender_check(scene+'_SAFE_P0',scene,cp['V'],cp['F']);assert not z['collision']and z['distance_mm']>.05 and b['EXACT_intersection_volume_mm3']==0
        save('metrics/'+scene+'_SAFE_P0.json',dict(status='REUSED_R1_SAFE_P0',input=asset(path),p=p,collision=z,Blender=b));return row,p
    old=np.array(row['p']);model=Body(row,old);ob=Objective(scene,model);co=ob.col;V0=model.vertices(old);vol0=volume(V0,model.F);oldmet=ob.evaluate(old,gradient=False);initial=co.check(V0,model.F,True);constraint=P0Constraints(model,co);trace=[];best=None;cached=None
    def cost(p):
        nonlocal cached,best
        if cached is not None and np.array_equal(cached[0],p):return cached[1]
        z=ob.evaluate(p,gradient=True);g,_=constraint.both(p);trace.append(dict(evaluation=len(trace)+1,E=z['E'],minimum_certificate_constraint_mm=float(g[:-1].min()),volume_ratio=float(g[-1]+.85),p=p))
        if g.min()>=-1e-6 and(best is None or z['E']<best[1]['E']):best=(p.copy(),z)
        cached=(p.copy(),z);return z
    if not initial['collision']and initial['distance_mm']>=.05:
        p=old;result_info=dict(success=True,message='Historical nine-parameter body already passes full-triangle positive gap; no refit',nit=0)
    else:
        D=2*(3*vol0/(4*np.pi))**(1/3);lo=np.r_[old[:3]-.25*D,old[3:6]-.5,old[6:9]+np.log(.8)];hi=np.r_[old[:3]+.25*D,old[3:6]+.5,old[6:9]+np.log(1.25)]
        z=minimize(lambda p:cost(p)['E'],old,jac=lambda p:cost(p)['g'],method='SLSQP',bounds=list(zip(lo,hi)),constraints=[dict(type='ineq',fun=lambda p:constraint.both(p)[0],jac=lambda p:constraint.both(p)[1])],options=dict(maxiter=60,ftol=1e-7));cost(z.x);p=best[0]if best else z.x;result_info=dict(success=bool(z.success),message=z.message,nit=int(z.nit))
    V=model.vertices(p);col=co.check(V,model.F,True);b=blender_check(scene+'_SAFE_P0',scene,V,model.F);met=ob.evaluate(p,gradient=False);reasons=[];vr=volume(V,model.F)/vol0;drops=np.array([x['IoU']-y['IoU']for x,y in zip(met['per_view'],oldmet['per_view'])])
    if col['collision']or col['distance_mm']<.05-1e-5 or b['EXACT_intersection_volume_mm3']>1e-8:reasons.append('SAFE_POSITIVE_GAP_NOT_CERTIFIED')
    if vr<.85-1e-6:reasons.append('P0_EXCESS_SHRINK')
    if drops.mean()<-.03 or drops.min()<-.05:reasons.append('P0_MASK_EXPLANATION_LOSS')
    for a,z in zip(oldmet['per_view'],met['per_view']):
        if z['native_hit_N']<a['native_hit_N']-.05*512:reasons.append('P0_HERO_COVERAGE_LOSS:'+a['source'])
        if a['relative_depth_mm']['MAE']is not None and z['relative_depth_mm']['MAE']is not None and z['relative_depth_mm']['MAE']>a['relative_depth_mm']['MAE']+.15:reasons.append('P0_RELATIVE_DEPTH_REGRESSION:'+a['source'])
    save('metrics/'+scene+'_SAFE_P0.json',dict(status='P0_INFEASIBLE'if reasons else'P0_FEASIBLE',scope='single registered local solve, not global impossibility',reasons=reasons,p=p,old_p=old,trace=trace,optimizer=result_info,collision=col,Blender=b,volume_ratio=vr,mean_IoU_change=float(drops.mean()),old_metrics=oldmet['per_view'],new_metrics=met['per_view']))
    np.savez_compressed(R/'local_results'/(scene+'_P0_CANDIDATE.npz'),V=V,F=model.F,q=p)
    if reasons:raise RuntimeError('P0_INFEASIBLE:'+','.join(reasons))
    return row,p
