"""Custom residual blocks only; LM and Schur are executed by unmodified Ceres."""
from torus import *
import pyceres as ce
class Cost(ce.CostFunction):
 def __init__(self,n,sizes):super().__init__();self.set_num_residuals(n);self.set_parameter_block_sizes(sizes)
 def fill(self,jacobians,jacs):
  if jacobians is not None:
   for buf,J in zip(jacobians,jacs):
    if buf is not None:buf[:]=np.asarray(J).reshape(-1)
class RingCost(Cost):
 def __init__(self,cache,K,cp,view_weight):
  self.cache=cache;self.K=K;self.cp=cp;self.weight=np.array([view_weight/(2*max(1,cp['channel'].count(k)))for k in cp['channel']]);super().__init__(len(cp['theta'])*2,[6,6]);self.key=None;self.res=None;self.J=None
 def values(self,a,b,jac=False):
  q=np.r_[a,b]
  if self.key is None or not np.array_equal(q,self.key):
   C=self.cache.get(a,b)[0];uv=torus_uv_t(tt(C),self.K,self.cp['theta'],self.cp['branch']).numpy();self.raw=(uv-self.cp['observed'])/3.;self.key=q.copy();self.J=None
   # per-channel and view normalization, no change in candidate IDs
   self.res=robust(self.raw,weight=self.weight[:,None]).reshape(-1)if False else None
   n=np.maximum(np.linalg.norm(self.raw,axis=1),1e-14);s=np.where(n<=1,1,np.sqrt(np.maximum(2*n-1,1e-30))/n);self.res=(self.raw*s[:,None]*np.sqrt(self.weight)[:,None]).ravel()
  if jac and self.J is None:
   C,dC=self.cache.get(a,b,True);Jc=jacfwd(lambda c:torus_uv_t(c,self.K,self.cp['theta'],self.cp['branch']))(tt(C)).numpy();J=np.einsum('naij,ijd->nad',Jc,dC)/3.;_,Jr=robust(self.raw,J,1.);self.J=Jr*np.repeat(np.sqrt(self.weight),2)[:,None]
  return self.res,self.J
 def Evaluate(self,parameters,residuals,jacobians):
  r,J=self.values(*parameters,jacobians is not None);residuals[:]=r
  if jacobians is not None:self.fill(jacobians,[J[:,:6],J[:,6:]])
  return bool(np.isfinite(r).all())
class Reprojection(Cost):
 def __init__(self,cache,K,uv,weight):super().__init__(2,[6,6,3]);self.cache=cache;self.K=np.array(K);self.uv=np.array(uv);self.a=np.sqrt(weight)/3.
 def Evaluate(self,parameters,residuals,jacobians):
  C,dC=self.cache.get(parameters[0],parameters[1],jacobians is not None);X=parameters[2]
  if jacobians is None:uv,JX,z=project_dC(X,C,self.K)
  else:uv,JC,JX,z=project_dC(X,C,self.K,dC);self.fill(jacobians,[self.a*JC[:,:6],self.a*JC[:,6:],self.a*JX])
  residuals[:]=self.a*(uv-self.uv);return bool(z>0 and np.isfinite(uv).all())
class Prior(Cost):
 def __init__(self,x0,scale):self.x0=np.array(x0);self.a=np.broadcast_to(np.asarray(scale,float),self.x0.shape).copy();super().__init__(len(x0),[len(x0)])
 def Evaluate(self,parameters,residuals,jacobians):residuals[:]=(parameters[0]-self.x0)*self.a;self.fill(jacobians,[np.diag(self.a)]);return True
class RelativePrior(Cost):
 def __init__(self,a):self.a=np.array(a);super().__init__(6,[6,6])
 def Evaluate(self,parameters,residuals,jacobians):residuals[:]=(parameters[1]-parameters[0])*self.a;self.fill(jacobians,[-np.diag(self.a),np.diag(self.a)]);return True

def solver(problem,label,iterations=20,schur=True):
 options=ce.SolverOptions();options.max_num_iterations=iterations;options.trust_region_strategy_type=ce.TrustRegionStrategyType.LEVENBERG_MARQUARDT;options.linear_solver_type=ce.LinearSolverType.DENSE_SCHUR if schur else ce.LinearSolverType.DENSE_QR;options.num_threads=1;options.function_tolerance=1e-8;options.gradient_tolerance=1e-10;options.parameter_tolerance=1e-8;options.minimizer_progress_to_stdout=True
 summary=ce.SolverSummary();ce.solve(options,problem,summary);d=summary.todict();d={k:(v if isinstance(v,(str,int,float,bool,list,dict))else str(v))for k,v in d.items()};d.update(brief=summary.BriefReport(),full=summary.FullReport(),usable=summary.IsSolutionUsable(),pyceres_version=ce.__version__,ceres_version=ce.__ceres_version__);save('optimization/'+label+'/CERES_SUMMARY.json',d);print(label,summary.BriefReport(),flush=True);return d
