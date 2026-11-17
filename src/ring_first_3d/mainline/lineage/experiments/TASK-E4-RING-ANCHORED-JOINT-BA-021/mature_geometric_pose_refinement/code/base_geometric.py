"""Float64 geometric residuals and exact forward-mode AD; no soft raster derivatives."""
from gcommon import *
from ring020 import CADCurves
import torch
from torch.func import jacfwd
from scipy.optimize import least_squares
DT=torch.float64;torch.set_num_threads(2)
S=np.r_[np.full(3,.6),np.full(3,np.deg2rad(5))]
def tt(a):return torch.as_tensor(np.asarray(a),dtype=DT)
def skew(v):
 z=v[0]*0;x,y,w=v.unbind();return torch.stack([z,-w,y,w,z,-x,-y,x,z]).reshape(3,3)
def pose(q,C0,shared=False):
 # Camera-centred left perturbation = Exp(Ad_Trans(c0) xi) C0.
 xi=q*tt(S);A=torch.cat([torch.cat([skew(xi[3:]),xi[:3,None]],1),torch.zeros((1,4),dtype=DT)],0);D=torch.matrix_exp(A);c=torch.zeros(3,dtype=DT)if shared else tt(C0[:3,3]);G=torch.eye(4,dtype=DT);G=G+torch.cat([torch.cat([torch.zeros((3,3),dtype=DT),c[:,None]],1),torch.zeros((1,4),dtype=DT)],0);Gi=torch.eye(4,dtype=DT)-(G-torch.eye(4,dtype=DT));return G@D@Gi@tt(C0)
def canonical(C):
 a=-torch.atan2(C[1,3],C[0,3]);c,s=a.cos(),a.sin();z=a*0;o=z+1;G=torch.stack([c,-s,z,z,s,c,z,z,z,z,o,z,z,z,z,o]).reshape(4,4);return G@C
def project_t(X,C,K):
 p=(X-C[:3,3])@C[:3,:3];uv=p@K.T;return uv[...,:2]/uv[...,2:]
def robust_vector(r,weight):
 # ||returned residual||^2 /2 = normalized vector-Huber(||pixel_error||/3).
 n=torch.sqrt((r*r).sum(-1)+1e-24);h=torch.where(n<=1,.5*n*n,n-.5);scale=torch.sqrt(2*h/(n*n));return (r*scale[:,None]*np.sqrt(weight/max(1,len(r)))).reshape(-1)
def skew_np(v):return np.array([[0.,-v[2],v[1]],[v[2],0.,-v[0]],[-v[1],v[0],0.]])

def correspondence(V,segments,C,K,obs):
 X=V[segments];p=projection(X.reshape(-1,3),C,K)[0].reshape(-1,2,2);a,b=p[:,0],p[:,1];v=b-a;D=obs[:,None]-a[None];t=np.clip((D*v[None]).sum(-1)/np.maximum((v*v).sum(-1),1e-15),0,1);di=((D-t[...,None]*v[None])**2).sum(-1);return X[di.argmin(1)]

class Problem:
 def __init__(self,views,shared=False,with_sift=True):
  self.views=views;self.shared=shared;self.with_sift=with_sift;self.cads={v['ring_path']:CADCurves(v['ring_path'])for v in views};self.protocol=load(M/'config/PROTOCOL.json');self.rings=[];self.sifts=[];self.epis=[];self.parts={};self.C0s={v['id']:np.array(v['T'])for v in views};self.lastq=np.zeros(6)
  for v in views:
   d=np.load(M/'ring_evidence'/(v['id']+'.npz'));self.rings.append({k:np.asarray(d[k])[np.linspace(0,len(d[k])-1,min(128,len(d[k])),dtype=int)]if len(d[k])else np.empty((0,2))for k in ['inner','outer']});r=load(M/'inputs'/v['id']/'RGB_GEOMETRY.json');self.sifts.append(r['fit_pnp_inliers']if with_sift else[]);self.epis.append([e for e in r['epipolar']if e['role']=='FEATURE_FIT']if with_sift and not r['fit_pnp_inliers']else[])
  self.refviews={v['id']:v for v in load(M/'config/VIEWS.json')};self.relinearize(np.zeros(6))
 def C(self,q,v):return pose(q,self.C0s[v['id']],self.shared)
 def relinearize(self,q):
  self.X=[];self.selection=[]
  for v,ob in zip(self.views,self.rings):
   C=canon_np(self.C(tt(q),v).detach().numpy());cad=self.cads[v['ring_path']];ss=cad.segments(C,np.array(v['K']));self.selection.append(ss);sel={}
   for k in ['inner','outer']:
    if len(ob[k])and not len(ss[k]):raise ValueError('NO_CAD_VISIBLE_'+k+' '+v['id'])
    sel[k]=correspondence(cad.V,ss[k],C,np.array(v['K']),ob[k])if len(ob[k])else np.empty((0,2,3))
   self.X.append(sel)
 def residual_t(self,q,part='all'):
  z=[];nview=len(self.views)
  for v,ob,XX,features,epis in zip(self.views,self.rings,self.X,self.sifts,self.epis):
   C=self.C(q,v);K=tt(v['K']);Cr=canonical(C)
   for k in ['inner','outer']:
    if part not in ['all',k,'data']:continue
    if not len(ob[k]):continue
    p=project_t(tt(XX[k]),Cr,K);a,b=p[:,0],p[:,1];d=b-a;D=tt(ob[k])-a;t=((D*d).sum(-1)/(d*d).sum(-1).clamp_min(1e-15)).clamp(0,1);err=(a+t[:,None]*d-tt(ob[k]))/3.;z.append(robust_vector(err,1/(2*nview)))
   if part in ['all','SIFT','data']and features:
    uv=project_t(tt([f['X']for f in features]),C,K);z.append(robust_vector((uv-tt([f['uv']for f in features]))/3.,.2/nview))
   if part in ['all','SIFT','data']and epis:
    # Symmetric normalized epipolar scalar, real RGB identities only.
    counts={sid:sum(e['reference']==sid for e in epis)for sid in {e['reference']for e in epis}}
    for sid,nn in counts.items():
     ee=[e for e in epis if e['reference']==sid];ref=self.refviews[sid];W=torch.linalg.inv(C)@tt(ref['T']);F=torch.linalg.inv(K).T@skew(W[:3,3])@W[:3,:3]@torch.linalg.inv(tt(ref['K']));a=tt([list(e['p'])+[1]for e in ee]);b=tt([list(e['q'])+[1]for e in ee]);fa=a@F.T;fb=b@F;err=(b*fa).sum(-1)/torch.sqrt((fa[:,:2]**2+fb[:,:2]**2).sum(-1)+1e-24);z.append(robust_vector(err[:,None]/3.,.2/nview/len(counts)))
  if part in ['all','prior']:z.append(q*np.sqrt(.01/6))
  return torch.cat(z)if z else q[:0]
 def fun(self,q,part='all'):return self.residual_t(tt(q),part).detach().numpy()
 def jac(self,q,part='all'):return jacfwd(lambda x:self.residual_t(x,part))(tt(q)).detach().numpy()
 def true_cost(self,q):
  old=self.X;oldsel=self.selection;self.relinearize(q);r=self.fun(q);self.X=old;self.selection=oldsel;return float(r@r/2)
 def physical(self,q):
  for v in self.views:
   C=self.C(tt(q),v).detach().numpy();B=self.C0s[v['id']];dC=np.linalg.norm(C[:3,3]-B[:3,3]);rot=np.degrees(Rotation.from_matrix(C[:3,:3]@B[:3,:3].T).magnitude());cad=self.cads[v['ring_path']];p=(cad.V-C[:3,3])@C[:3,:3]
   if dC>1.2+1e-10 or rot>10 or p[:,2].min()<=0:return False,dict(view=v['id'],center_change_mm=dC,rotation_deg=rot,minimum_CAD_depth_mm=float(p[:,2].min()))
  return True,{}
 def information(self,q):
  J=self.jac(q,'data');u,s,v=np.linalg.svd(J,full_matrices=False);rank=int((s>max(s[0]*1e-6,1e-10)).sum())if len(s)else 0
  return dict(rank=rank,singular_values=s,condition=float(s[0]/s[-1])if len(s)==6 and s[-1]>0 else None,weak_normalized_twists=v[-2:].tolist()if len(s)else[],priors_excluded=True)

def solve(problem,label):
 out=M/'results'/label
 if(out/'FINAL.json').exists():return load(out/'FINAL.json')
 out.mkdir(parents=True,exist_ok=True);q=np.zeros(6);trace=[];loss0=problem.true_cost(q);start=time.time();calls=[]
 for outer in range(problem.protocol['outer_iterations']):
  problem.relinearize(q);before=problem.true_cost(q);previous_q=q.copy()
  def fun(x):
   y=problem.fun(x);calls.append(dict(outer=outer,nfev=len(calls),loss=float(y@y/2),q=x));return y
  fit=least_squares(fun,q,jac=problem.jac,method='trf',bounds=(-.95*np.ones(6),.95*np.ones(6)),max_nfev=problem.protocol['inner_max_nfev'],ftol=1e-8,xtol=1e-8,gtol=1e-8,x_scale='jac')
  accepted=False;trials=[]
  for j in range(problem.protocol['backtracks']):
   qq=q+(fit.x-q)*(.5**j);valid,why=problem.physical(qq);actual=problem.true_cost(qq)if valid else None;ok=valid and actual<=before+1e-10;trials.append(dict(factor=.5**j,cost=actual,physical=valid,reason=why,accepted=ok))
   if ok:q=qq;accepted=True;break
  trace.append(dict(outer=outer,initial_cost=before,trial_local_cost=float(fit.cost),actual_cost=problem.true_cost(q),accepted=accepted,solver_status=int(fit.status),solver_message=fit.message,nfev=int(fit.nfev),njev=int(fit.njev),trials=trials,q=q));save('optimization/'+label+'/TRACE.json',trace);save('optimization/'+label+'/CALLS.json',calls)
  if not accepted or np.linalg.norm(q-previous_q)<1e-8:break
 problem.relinearize(q);poses={v['id']:problem.C(tt(q),v).detach().numpy()for v in problem.views};rec=dict(label=label,q=q,poses=poses,initial_loss=loss0,final_loss=problem.true_cost(q),iterations=len(trace),accepted_outer_updates=sum(a['accepted']for a in trace),seconds=time.time()-start,original_physical_bounds_pass=problem.physical(q)[0],data_information=problem.information(q),pose_changed_depth_not_reinferred=True,HERO_body_GT_in_loss=False,solver='SciPy least_squares TRF exact float64 autodiff',source=asset(Path(__file__)));save('results/'+label+'/FINAL.json',rec);save('results/'+label+'/FROZEN.json',dict(epoch=time.time(),file=asset(out/'FINAL.json'),held_body_HERO_used=False));return rec
