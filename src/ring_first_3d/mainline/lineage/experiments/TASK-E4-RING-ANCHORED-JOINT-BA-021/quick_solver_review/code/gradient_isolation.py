"""Separate smooth SIFT/prior derivatives from nondifferentiable/noisy Ring component."""
from qcommon import *
from ba021 import BA,tensor,torch

def main():
 while not(Q/'provenance/SOLVER_CANDIDATES_FROZEN.json').exists():time.sleep(5)
 ids=[v['id']for v in load(P/'config/VIEWS.json')if v['video']=='005'and v['role']=='FIT'];rows=[]
 for arm in ['B1','B2','B3']:
  a=load(P/'results'/(arm+'.json'));obj=BA('CROSS',ids,arm);q=tensor(a['q'],torch.float64).requires_grad_(True);X=tensor(a['X'],torch.float64).requires_grad_(True);seed=tensor(a['seed_T'],torch.float64);full,p=obj.evaluate(q,X,seed,True);gq=q.grad.detach().clone();gx=X.grad.detach().clone();F,_=obj.points.term(obj.transform(q,seed),X);tail=.2*F+.01*q.square().mean()+.001*obj.points.point_prior(X);tq,tx=torch.autograd.grad(tail,[q,X]);smoothq=tq.detach().cpu().numpy();smoothx=tx.detach().cpu().numpy();q0=np.array(a['q']);X0=np.array(a['X'])
  for label,k in [('pose',0),('pose',2),('pose',4),('point',0)]:
   for h in [.01,.001]:
    qa=q0.copy();qb=q0.copy();xa=X0.copy();xb=X0.copy()
    if label=='pose':qa[k]+=h;qb[k]-=h;ad=float(gq[k]);sad=float(smoothq[k])
    else:xa[0,0]+=.6*h;xb[0,0]-=.6*h;ad=float(gx[0,0])*.6;sad=float(smoothx[0,0])*.6
    with torch.no_grad():
     la,pa=obj.evaluate(tensor(qa,torch.float64),tensor(xa,torch.float64),seed);lb,pb=obj.evaluate(tensor(qb,torch.float64),tensor(xb,torch.float64),seed)
    st=lambda p:.2*p['reprojection']+.01*p['pose_prior']+.001*p['point_prior'];fd=(la-lb)/(2*h);sfd=(st(pa)-st(pb))/(2*h);rows.append(dict(arm=arm,parameter=label,index=k,h=h,full_AD=ad,full_FD=fd,smooth_AD=sad,smooth_FD=sfd,smooth_relative_error=abs(sad-sfd)/max(abs(sad),abs(sfd),1e-8),Ring_curves_AD=ad-sad,Ring_curves_FD=fd-sfd,Ring_relative_error=abs((ad-sad)-(fd-sfd))/max(abs(ad-sad),abs(fd-sfd),1e-8),point_FD_full_contaminated_by_constant_pose_Ring_noise=label=='point'))
  torch.cuda.empty_cache();print('GRADIENT_ISOLATION',arm,flush=True)
 qsave('metrics/GRADIENT_COMPONENT_ISOLATION.json',rows);qtable('metrics/GRADIENT_COMPONENT_ISOLATION.csv',rows);qsave('runtime/GRADIENT_ISOLATION_COMPLETE.json',dict(epoch=time.time(),original_objective_unchanged=True));print('GRADIENT_ISOLATION_COMPLETE',flush=True)
if __name__=='__main__':main()
