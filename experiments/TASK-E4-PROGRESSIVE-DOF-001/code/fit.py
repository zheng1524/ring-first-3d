"""One progressive run; unchanged ORIGINAL scalar objective and Powell family."""
import os,sys,time,datetime
os.environ['E4_OPTIMIZER_ONLY']='1'
from model import *
from continuous import *
from physics import physical
from scipy.optimize import minimize
def main():
    stage=sys.argv[1];assert stage in ['S1','S2','S3'];cfg=protocol();assert load(R/'metrics/P0_ZERO_AND_FIREWALL.json')['passed']
    for x in load(R/'assets_index/PREOPT_FREEZE.json')['files']:assert sha(x['path'])==x['sha256'],x['path']
    assert not(R/'metrics'/(stage+'_START.json')).exists()
    if stage=='S1':q0=np.zeros(6)
    elif stage=='S2':
        assert load(R/'metrics/LOCAL_ZERO_CONTRACT.json')['passed'];q0=np.r_[load(R/'metrics/S1_FINISHED.json')['q'],0.,0.]
    else:
        assert load(R/'metrics/CENTER_RELEASE_GATE.json')['released'];assert (R/'metrics/S2_ACTIVE_CENTERS_SENSITIVITY.json').exists();q0=np.r_[load(R/'metrics/S2_FINISHED.json')['q'],np.zeros(3*len(load(R/'metrics/CENTER_RELEASE_GATE.json')['active_kernel_ids']))]
    body=Body();renderer=Renderer();records=[];calls=[];history=[];cache={};start=time.time();rounds=[0]
    bounds=cfg['global_bounds']+([]if len(q0)==6 else cfg['amplitude_bounds_mm'])+([[-cfg['center_offset_limit_mm'],cfg['center_offset_limit_mm']]]*(len(q0)-8) if len(q0)>8 else[])
    directions=np.r_[np.full(3,.2),.2/body.a0,([]if len(q0)==6 else [.1,.1]),(np.full(len(q0)-8,.2)if len(q0)>8 else[])]
    def keep(name,q,loss):
        V,F=body.save(stage+'/'+name,q);row=dict(stage=stage,checkpoint=name,q=q,loss=loss,seconds=time.time()-start,physical=physical(V,F),per_view=[subpixel_metrics(renderer,V,F,c['id'])for c in renderer.views]);history.append(row);save('metrics/'+stage+'_HISTORY.json',history)
    def fun(q):
        key=tuple(np.round(q,10));hit=key in cache
        if not hit:
            val,parts=objective(body,renderer,q,False);V,F=body.mesh(q);ph=physical(V,F);cache[key]=val;records.append(dict(evaluation=len(records)+1,q=q.copy(),loss=val,per_view=parts,physical=ph,seconds=time.time()-start))
        calls.append(dict(call=len(calls)+1,q=q.copy(),cache_hit=hit,loss=cache[key]));return cache[key]
    def callback(q):
        rounds[0]+=1;keep('ROUND_%02d'%rounds[0],q,fun(q));save('metrics/'+stage+'_TRACE.json',records);print(stage,'ROUND',rounds[0],history[-1]['loss'],flush=True)
    save('metrics/'+stage+'_START.json',dict(q0=q0,active_parameters=len(q0),bounds=bounds,direc=directions,GT_read=False,objective='original foreground-center symmetric NN Huber/9 +0.2 fixed XOR',timestamp=datetime.datetime.now().isoformat(),fixed_residual_not_optimizer_loss=True))
    keep('START',q0,fun(q0));out=minimize(fun,q0,method='Powell',bounds=bounds,callback=callback,options=dict(maxiter=cfg['maxiter'],maxfev=cfg['maxfev'],xtol=cfg['xtol'],ftol=cfg['ftol'],direc=np.diag(directions)))
    keep('FINAL',out.x,float(out.fun));save('metrics/'+stage+'_TRACE.json',records);table('metrics/'+stage+'_TRACE.csv',records);save('metrics/'+stage+'_CALLS.json',calls);save('metrics/'+stage+'_FINISHED.json',dict(finished=True,success=bool(out.success),message=str(out.message),q=out.x,loss=float(out.fun),iterations=int(out.nit),nfev=int(out.nfev),seconds=time.time()-start,selected_by='last bounded iterate, no GT/holdout selection',collision_candidates=sum(x['physical']['collision']for x in records)))
    if stage=='S2':
        q=np.array(out.x);without=q.copy();without[6:8]=0.;L0,_=objective(body,renderer,without,False);Ls1=load(R/'metrics/S1_FINISHED.json')['loss'];threshold=max(cfg['signal_absolute'],cfg['signal_relative']*abs(Ls1));ph=history[-1]['physical'];kernel_benefits=[]
        for k in range(2):
            disabled=q.copy();disabled[6+k]=0.;lk,_=objective(body,renderer,disabled,False);kernel_benefits.append(float(lk-out.fun))
        active=[k for k in range(2)if abs(q[6+k])>=cfg['minimum_active_amplitude_mm']and kernel_benefits[k]>threshold]
        released=Ls1-out.fun>threshold and L0-out.fun>threshold and bool(active)and not ph['collision']and ph['quality']['closed']and ph['quality']['components']==1
        save('metrics/CENTER_RELEASE_GATE.json',dict(released=bool(released),S1_loss=Ls1,S2_loss=float(out.fun),S2_global_only_loss=L0,threshold=threshold,local_component_loss_benefit=L0-out.fun,amplitudes=q[6:8],per_kernel_loss_benefit=kernel_benefits,active_kernel_ids=active if released else[],GT_or_holdout_used=False,reason='fit improvement plus actual local-component benefit and valid geometry required'))
    print(stage,'FINISHED',out.nfev,float(out.fun),time.time()-start,flush=True)
if __name__=='__main__':main()
