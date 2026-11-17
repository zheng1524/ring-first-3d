"""Joint-variable gradients and inherited real CAD Ring projection checks before BA."""
from ba021 import *
def main():
 obj=BA('CROSS',[v['id']for v in load(R/'config/VIEWS.json')if v['video']=='005'and v['role']=='FIT'][:1],'B3');hist=load(R/'config/HISTORICAL_CANDIDATES.json');H=tensor(next(v['T']for v in hist if v['tag']=='HISTORICAL_FULL_RoMa'),torch.float64);q=tensor([.03,-.02,.01,.01,.02,-.01],torch.float64).requires_grad_(True);X=obj.points.X0.clone().requires_grad_(True);F,z=obj.points.term(obj.transform(q,H),X);gq,gX=torch.autograd.grad(F,[q,X]);checks=[]
 for name,idx in [('q',0),('q',4),('X',0),('X',2)]:
  d=1e-4 if name=='q'else 1e-5
  with torch.no_grad():
   qa=q.clone();qb=q.clone();a=X.clone();b=X.clone()
   if name=='q':qa[idx]+=d;qb[idx]-=d;ad=float(gq[idx])
   else:a[0,idx]+=d;b[0,idx]-=d;ad=float(gX[0,idx])
   fa=obj.points.term(obj.transform(qa,H),a)[0];fb=obj.points.term(obj.transform(qb,H),b)[0];fd=float((fa-fb)/(2*d));rel=abs(ad-fd)/max(abs(ad),abs(fd),1e-7);checks.append(dict(parameter=name,index=idx,AD=ad,FD=fd,relative_error=rel,passed=rel<.01))
 L,p=obj.evaluate(q,X,H,True);checks.append(dict(parameter='whole_network_is_not_used',pose_grad=float(q.grad.norm()),point_grad=float(X.grad.norm()),passed=bool(torch.isfinite(q.grad).all()and torch.isfinite(X.grad).all()and X.grad.norm()>0 and q.grad.norm()>0)))
 y=[]
 for a in [-.2,0,.3]:
  ca,sa=np.cos(a),np.sin(a);Z=tensor([[ca,-sa,0,0],[sa,ca,0,0],[0,0,1,0],[0,0,0,1]],torch.float64)
  with torch.no_grad():p=obj.ring.term(Z@H,obj.ids[0],True);y.append({k:float(v)for k,v in p.items()})
 ranges={k:np.ptp([a[k]for a in y])for k in y[0]};checks.append(dict(parameter='Ring_pure_yaw_invariance',ranges=ranges,passed=max(ranges.values())<2e-5))
 shifts=[]
 for i in range(3):
  with torch.no_grad():tx=obj.points.X0.clone();tx[:,i]+=.1;shifts.append(float(obj.points.term(H,tx)[0]))
 checks.append(dict(parameter='landmarks_not_fixed_in_B2',baseline=float(obj.points.term(H,obj.points.X0)[0]),shifted=shifts,passed=np.ptp(shifts)>1e-6))
 save('metrics/BA_GRADIENT_GATE.json',dict(all_passed=all(c['passed']for c in checks),checks=checks,observations=len(obj.points.obs),landmarks=len(X),physics='real frozen cameras and CAD; no body/HERO/GT',source=asset(Path(__file__))));print('021_GATE',all(c['passed']for c in checks),checks,flush=True);assert all(c['passed']for c in checks)
if __name__=='__main__':main()
