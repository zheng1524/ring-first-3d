"""Same objective across seeds; frozen-material-point local solves + actual CAD objective acceptance."""
import base_geometric as b
from base_geometric import *
from cad_render import RenderedCAD,material_points
from scipy.linalg import logm
b.CADCurves=RenderedCAD
class Problem(b.Problem):
 def __init__(self,views,ring_enabled=True):self.ring_enabled=ring_enabled;super().__init__(views)
 def relinearize(self,q):
  self.X=[];self.selection=[];self.visibility=[]
  for v,obs in zip(self.views,self.rings):
   if not self.ring_enabled:self.X.append({k:np.empty((0,3))for k in ['inner','outer']});self.selection.append({});continue
   C=canon_np(self.C(tt(q),v).detach().numpy());cad=self.cads[v['ring_path']];ss=cad.segments(C,np.array(v['K']));self.selection.append(ss);self.visibility.append(cad.last_audit.copy());self.X.append({k:material_points(cad.V,ss[k],C,np.array(v['K']),obs[k])for k in ['inner','outer']})
 def residual_t(self,q,part='all'):
  zs=[]
  if self.ring_enabled:
   for v,obs,X in zip(self.views,self.rings,self.X):
    C=canonical(self.C(q,v));K=tt(v['K'])
    for key in ['inner','outer']:
     if part in ['all','data',key]and len(obs[key]):zs.append(robust_vector((project_t(tt(X[key]),C,K)-tt(obs[key]))/3.,1/(2*len(self.views))))
  if part in ['all','data','SIFT']:zs.append(b.Problem.residual_t(self,q,'SIFT'))
  if part in ['all','prior']:zs.append(q*np.sqrt(.01/6))
  return torch.cat(zs)if zs else q[:0]

def q_from_pose(C,C0):
 G=np.eye(4);G[:3,3]=C0[:3,3];D=np.linalg.inv(G)@C@np.linalg.inv(C0)@G;A=np.real_if_close(logm(D)).real;return np.r_[A[:3,3],[A[2,1],A[0,2],A[1,0]]]/S

def solve(p,label,qstart=None,extra=None):
 out=M/'results'/label
 if(out/'FINAL.json').exists():return load(out/'FINAL.json')
 out.mkdir(parents=True,exist_ok=True);q=np.zeros(6)if qstart is None else np.array(qstart);qinitial=q.copy();trace=[];calls=[];t0=time.time();valid,why=p.physical(q)
 if not valid or abs(q).max()>=2:
  r=dict(label=label,status='INFEASIBLE_INITIALIZATION',pose=None,reason=why,q=q,no_prediction_fallback=True,extra=extra);save('results/'+label+'/FINAL.json',r);return r
 L0=p.true_cost(q)
 for outer in range(p.protocol['outer_iterations']):
  p.relinearize(q);Lold=p.true_cost(q);qold=q.copy()
  def fun(x):
   r=p.fun(x);calls.append(dict(outer=outer,loss=float(r@r/2),q=x));return r
  fit=least_squares(fun,q,jac=p.jac,method='trf',bounds=(-2*np.ones(6),2*np.ones(6)),max_nfev=p.protocol['inner_max_nfev'],ftol=1e-8,xtol=1e-8,gtol=1e-8,x_scale='jac');trials=[];accepted=False
  for j in range(p.protocol['backtracks']):
   qnew=qold+(fit.x-qold)*2**(-j);ok,why=p.physical(qnew);actual=p.true_cost(qnew)if ok else None;accept=ok and actual<=Lold+1e-10;trials.append(dict(factor=2**(-j),physical=ok,reason=why,relinearized_cost=actual,accepted=accept))
   if accept:q=qnew;accepted=True;break
  trace.append(dict(outer=outer,before=Lold,local_candidate_cost=float(fit.cost),after=p.true_cost(q),accepted=accepted,solver_status=int(fit.status),message=fit.message,nfev=int(fit.nfev),njev=int(fit.njev),q=q,trials=trials))
  save('optimization/'+label+'/TRACE.json',trace)
  if not accepted or np.linalg.norm(q-qold)<1e-7:break
 p.relinearize(q);v=p.views[0];C=p.C(tt(q),v).detach().numpy();C0=np.array(v['T']);vis=p.visibility[0]if p.ring_enabled else{};r=dict(label=label,status='FROZEN_NUMERIC_POSE',pose=C,q=q,initial_q=qinitial,initial_loss=L0,final_loss=p.true_cost(q),accepted_outer=sum(t['accepted']for t in trace),outer_iterations=len(trace),seconds=time.time()-t0,solver='SciPy bounded TRF float64 AD',nfev=len(calls),physical=p.physical(q),center_change_mm=float(np.linalg.norm(C[:3,3]-C0[:3,3])),rotation_change_deg=float(np.degrees(Rotation.from_matrix(C[:3,:3]@C0[:3,:3].T).magnitude())),data_information=p.information(q),visibility_counts={k:int(np.sum(vis['states']==i))for i,k in enumerate(['VISIBLE','OCCLUDED','UNKNOWN'])}if vis else{},depth_status='POSE_CHANGED_DEPTH_NOT_REINFERRED',HERO_body_GT_in_loss=False,extra=extra)
 save('optimization/'+label+'/CALLS.json',calls);save('results/'+label+'/FINAL.json',r);save('results/'+label+'/FROZEN.json',dict(epoch=time.time(),file=asset(out/'FINAL.json'),held_HERO_body_used=False));return r
