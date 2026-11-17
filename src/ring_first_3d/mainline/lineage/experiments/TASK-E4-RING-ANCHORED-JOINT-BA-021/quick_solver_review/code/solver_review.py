"""One mature SciPy L-BFGS-B implementation, unchanged feasible021 loss/priors."""
from qcommon import *
from ba021 import BA,tensor,torch,device,exp_se3
from scipy.optimize import minimize
import copy

def one(arm):
 out=Q/'results'/arm
 if(out/'FINAL.json').exists():return load(out/'FINAL.json')
 out.mkdir(exist_ok=True);old=load(P/'results'/(arm+'.json'));ids=[v['id']for v in load(P/'config/VIEWS.json')if v['video']=='005'and v['role']=='FIT'];obj=BA('CROSS',ids,arm);q=tensor(old['q'],torch.float64).requires_grad_(True);X=tensor(old['X'],torch.float64).requires_grad_(True);seed=tensor(old['seed_T'],torch.float64);joint=arm!='B1';x0=obj.points.X0.detach().cpu().numpy();xscale=.6;y0=np.r_[old['q'],((np.asarray(old['X'])-x0)/xscale).ravel()]if joint else np.asarray(old['q']);calls=[];accepted=[];trace=[];start=time.time();fixedX=np.array(old['X']);last=[None]
 def decode(y):return y[:6],x0+y[6:].reshape(-1,3)*xscale if joint else fixedX
 def feasible(qq,xx):
  d=exp_se3(tensor(qq,torch.float64)*obj.scale).detach().cpu().numpy();white=np.einsum('kij,kj->ki',obj.points.W.cpu().numpy(),xx-x0);reasons=[]
  if np.linalg.norm(d[:3,3])>1.2 or np.linalg.norm(qq[3:]*obj.p['pose_scale'][3:])>np.deg2rad(10):reasons.append('ORIGINAL_LOCAL_SE3_BOUND')
  if np.linalg.norm(xx-x0,axis=1).max()>3 or np.linalg.norm(white,axis=1).max()>6:reasons.append('ORIGINAL_LANDMARK_BOUND')
  with torch.no_grad():z=obj.points.residual(obj.transform(tensor(qq,torch.float64),seed),tensor(xx,torch.float64))[1]
  if not np.isfinite(qq).all()or not np.isfinite(xx).all()or float(z.min())<=0:reasons.append('ORIGINAL_NONFINITE_OR_NEGATIVE_DEPTH')
  return reasons
 def ev(y,grad=True):
  qq,xx=decode(y);bad=feasible(qq,xx)
  if bad:return np.inf,np.zeros_like(y),dict(infeasible=bad)
  with torch.no_grad():q.copy_(tensor(qq,torch.float64));X.copy_(tensor(xx,torch.float64))
  L,p=obj.evaluate(q,X,seed,grad)
  g=np.r_[q.grad.detach().cpu().numpy(),X.grad.detach().cpu().numpy().ravel()*xscale]if joint and grad else q.grad.detach().cpu().numpy().copy()if grad else np.zeros_like(y)
  return L,g,p
 # A0: reproduce the exact021 endpoint using its original q, X0, and RoMa prior center.
 reps=[ev(y0,False)[0]for _ in range(3)];L0,g0,p0=ev(y0,True);gate=[]
 # Actual directional full-parameter AD/FD; isolate Ring and reprojection numerical changes.
 dirs=[]
 for k in [0,2,4]:
  d=np.zeros_like(y0);d[k]=1;dirs.append(('pose_'+str(k),d))
 if joint:
  d=np.zeros_like(y0);d[6]=1;dirs.append(('first_point_X',d))
 d=g0/max(np.linalg.norm(g0),1e-30);dirs.append(('full_gradient_direction',d))
 for name,d in dirs:
  for h in [.01,.001]:
   la,_,pa=ev(y0+h*d,False);lb,_,pb=ev(y0-h*d,False);fd=(la-lb)/(2*h);ad=float(g0@d);row=dict(direction=name,h_optimizer_units=h,AD=ad,central_FD=fd,relative_error=abs(ad-fd)/max(abs(ad),abs(fd),1e-8),Ring_M_FD=(pa['M']-pb['M'])/(2*h),reprojection_FD=(pa['reprojection']-pb['reprojection'])/(2*h),point_prior_FD=(pa['point_prior']-pb['point_prior'])/(2*h),gradient_agrees_1percent=abs(ad-fd)<=.01*max(abs(ad),abs(fd),1e-8));gate.append(row)
 qsave('metrics/'+arm+'_ORIGINAL_OBJECTIVE_GATE.json',dict(old_loss=old['loss'],reproduced_losses=reps,absolute_error=max(abs(v-old['loss'])for v in reps),repeat_range=max(reps)-min(reps),gradient_norm=float(np.linalg.norm(g0)),directions=gate,objective_unchanged=True,prior_center_not_rebased=True))
 def fun(y):
  L,g,p=ev(y,True);calls.append(dict(call=len(calls),loss=L,gradient_norm=float(np.linalg.norm(g)),parts=p,y=y,feasible=np.isfinite(L),seconds=time.time()-start));last[0]=(y.copy(),L,g.copy(),p);qsave('optimization/'+arm+'/CALLS.json',calls)
  if len(calls)%10==0:print('QUICK_LBFGSB',arm,'calls',len(calls),'loss',L,flush=True)
  return L,g
 def cb(y):
  trace.append(dict(iteration=len(trace)+1,y=y,loss=last[0][1]if np.array_equal(last[0][0],y)else ev(y,False)[0]));qsave('optimization/'+arm+'/ITERATIONS.json',trace)
 # Box is only an outer envelope; original coupled norm/whitened/cheirality constraints
 # are retained as an infinite-domain barrier. No feasible loss is modified.
 result=minimize(fun,y0,jac=True,method='L-BFGS-B',bounds=[(-4.,4.)]*6+([(-5.,5.)]*54 if joint else[]),callback=cb,options=dict(maxiter=25,maxfun=90,maxls=12,ftol=1e-12,gtol=1e-7,maxcor=10))
 yy=result.x;Lf,gf,pf=ev(yy,True);qq,xx=decode(yy);valid=not feasible(qq,xx)
 if not(valid and np.isfinite(Lf)and Lf<=L0+1e-6):yy=y0;Lf,gf,pf=ev(yy,True);qq,xx=decode(yy);status='FINAL_REJECTED_RETAINED_ORIGINAL'
 else:status='FEASIBLE_FINAL_FROZEN'
 H=obj.transform(tensor(qq,torch.float64),seed).detach().cpu().numpy();D=H@np.linalg.inv(old['T']);rec=dict(arm=arm,method={'B1':'A1','B2':'A2','B3':'A3'}[arm],T=H,X=xx,q=qq,X0=x0,seed_T=old['seed_T'],scale=1.,initial_loss=L0,loss=Lf,initial_gradient_norm=float(np.linalg.norm(g0)),final_gradient_norm=float(np.linalg.norm(gf)),parts=pf,solver='SciPy L-BFGS-B',solver_success=bool(result.success),solver_message=str(result.message),nfev=result.nfev,nit=result.nit,status=status,translation_change_mm=float(np.linalg.norm(D[:3,3])),rotation_change_deg=float(np.degrees(Rotation.from_matrix(D[:3,:3]).magnitude())),max_point_change_mm=float(np.linalg.norm(xx-fixedX,axis=1).max()),seconds=time.time()-start,body_HERO_HOLDOUT_in_loss=False,old_endpoint=asset(P/'results'/(arm+'.json')),objective_code=asset(P/'code/ba021.py'),original_constraints_valid=valid,used_original_prior_centers=True)
 qsave('results/'+arm+'/FINAL.json',rec);print('QUICK_SOLVER_DONE',arm,L0,Lf,result.message,flush=True);torch.cuda.empty_cache();return rec

def main():
 qguard();qsave('provenance/ORIGINAL_021_FROZEN.json',dict(files=[asset(p)for p in(P/'results').glob('*.json')]+[asset(P/'code/ba021.py'),asset(P/'config/PROTOCOL.json'),asset(P/'observations/CROSS_COMMON_TRACKS.json')],no_original_overwrite=True));out=[]
 for arm in ['B1','B2','B3']:out.append(one(arm))
 qtable('SOLVER_COMPARISON.csv',out);qsave('provenance/SOLVER_CANDIDATES_FROZEN.json',dict(epoch=time.time(),files=[asset(Q/'results'/a/'FINAL.json')for a in ['B1','B2','B3']],body_HERO_HOLDOUT=False));print('QUICK_SOLVER_ALL_FROZEN',flush=True)
if __name__=='__main__':main()
