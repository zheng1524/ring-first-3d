"""Frozen low-dimensional feasibility run. No target GT geometry access."""
import os
os.environ['E4_OPTIMIZER_ONLY']='1'
from model import *
from renderer import Renderer
from scipy.optimize import minimize
import time,datetime
def huber(x):
    x=np.asarray(x);return np.where(abs(x)<2,.5*x*x,2*abs(x)-2)
def seed(body,renderer):
    q=np.r_[body.a['V'].mean(0),0.];V,F=body.mesh(q);points=[];weights=[];arrows=[];m=trimesh.Trimesh(V,F,process=False)
    for cid in protocol()['fit_views']:
        r=renderer.silhouette(V,F,cid);d=renderer.data[cid];dist,ind=d['tree'].query(r['uv']);target=d['contour'][ind];w=np.maximum(dist-.75,0)**2
        for j in range(len(dist)):
            arrows.append(dict(view=cid,P=r['P'][j],uv=r['uv'][j],target_uv=target[j],face_id=int(r['faces'][j]),normal=r['normal'][j],distance_px=float(dist[j]),seed_weight=float(w[j])))
        points.extend(r['P']);weights.extend(w)
    weights=np.array(weights);assert weights.sum()>0,'INSUFFICIENT_VISIBLE_MASK_SIGNAL';center=np.average(points,axis=0,weights=weights);growth=sum(int(renderer.data[c]['target'].sum())-int(renderer.project(scene(V,F),c)[0].sum())for c in protocol()['fit_views']);q=np.r_[center,-.05 if growth>0 else .05];save('metrics/MASK_ONLY_INITIALIZATION.json',dict(q=q,rule=protocol()['seed_rule'],positive_target_minus_base_pixels=growth,GT_read=False));table('metrics/INITIAL_CORRESPONDENCES.csv',arrows);return q
def main():
    assert not(R/'metrics/FIT_START.json').exists(),'DO_NOT_OVERWRITE_PREVIOUS_FIT';gate=load(R/'metrics/PROJECTION_GATE.json');assert gate['passed']and gate['optimization_allowed'];assert load(R/'metrics/DMTET_DERIVATIVE_TEST.json')['passed'];freeze=load(R/'metrics/IMPLEMENTATION_FREEZE.json')
    for x in freeze['files']:assert sha(x['path'])==x['sha256'],x['path']
    try:
        open(R/'audit_only/TARGET_GT.npz','rb');raise RuntimeError('GT_FIREWALL_FAILED')
    except PermissionError:pass
    body=Body();renderer=Renderer();q0=seed(body,renderer);bounds=list(zip(*np.array(protocol()['center_bounds_mm'])));bounds.append(tuple(protocol()['amplitude_bounds_mm']));start=time.time();records=[];history=[];cache={};best=[np.inf,None];roundN=[0]
    def evaluate(q):
        V,F=body.mesh(q);mesh=trimesh.Trimesh(V,F,process=False)
        if not mesh.is_watertight or mesh.volume<=0 or len(mesh.split(only_watertight=False))!=1:return 10.,[],(V,F)
        rt=scene(V,F);per=[]
        for cid in protocol()['fit_views']:
            d=renderer.data[cid];r=renderer.silhouette(V,F,cid)
            if len(r['P'])<10:return 10.,[],(V,F)
            a=d['tree'].query(r['uv'])[0];b=cKDTree(r['uv']).query(d['contour'])[0];ch=.5*(huber(a).mean()+huber(b).mean())/9;pred=renderer.project(rt,cid)[0];target=d['target'];known=d['known'];fg=target&known;bg=~target&known;xor=.5*((pred^target)&fg).sum()/max(1,fg.sum())+.5*((pred^target)&bg).sum()/max(1,bg.sum());loss=float(ch+.2*xor);per.append(dict(view=cid,loss=loss,contour_loss=float(ch),fixed_XOR=float(xor)))
        return float(np.mean([r['loss']for r in per])),per,(V,F)
    def fun(q):
        key=tuple(np.round(q,10))
        if key in cache:return cache[key]
        val,per,geom=evaluate(q);cache[key]=val;records.append(dict(evaluation=len(records)+1,q=q.copy(),loss=val,seconds=time.time()-start,per_view=per));
        if val<best[0]-1e-7:
            best[:]=[val,q.copy()];print('BEST',len(records),round(val,7),np.round(q,4),flush=True)
        if len(records)%20==0:save('metrics/OBJECTIVE_TRACE.json',records)
        return val
    def keep(name,q,iteration,loss=None):
        V,F=body.save(name,q);rt=scene(V,F);quality=normals_quality(V,F);per=[renderer.metrics(rt,c['id'])[0]for c in renderer.views];row=dict(stage=name,iteration=iteration,q=q,objective=loss,per_view=per,quality=quality,seconds=time.time()-start);history.append(row);save('metrics/FIT_HISTORY.json',history)
    def callback(q):
        roundN[0]+=1;keep('ROUND_%02d'%roundN[0],q,roundN[0],fun(q));print('ROUND',roundN[0],flush=True)
    save('metrics/FIT_START.json',dict(timestamp=datetime.datetime.now().isoformat(),code_commit=freeze['commit'],GT_firewall_pass=True,fit_sources=protocol()['fit_views'],holdout_not_in_loss=True));keep('INITIAL',np.r_[q0[:3],0.],0);keep('START',q0,0,fun(q0))
    result=minimize(fun,q0,method='Powell',bounds=bounds,callback=callback,options=dict(maxiter=protocol()['max_iterations'],maxfev=protocol()['max_function_evaluations'],xtol=protocol()['Powell_xtol_mm'],ftol=protocol()['Powell_ftol'],direc=np.diag([.2,.2,.2,.1])))
    # Last bounded optimizer iterate, not selected by 3D GT or heldout view metrics.
    keep('FINAL',result.x,roundN[0],float(result.fun));save('metrics/OBJECTIVE_TRACE.json',records);table('metrics/OBJECTIVE_TRACE.csv',records);save('metrics/FIT_FINISHED.json',dict(finished=True,success=bool(result.success),message=str(result.message),iterations=int(result.nit),function_evaluations=int(result.nfev),q=result.x,loss=float(result.fun),seconds=time.time()-start,GT_loss=False,selected_by='last bounded optimizer iterate; no GT/holdout selection',stopped=True));print('FIT_FINISHED',result.message,time.time()-start,flush=True)
if __name__=='__main__':main()
