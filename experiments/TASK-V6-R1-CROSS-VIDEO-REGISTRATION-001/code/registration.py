"""Fixed-camera generalized multi-view epipolar objective plus independent Ring prior.
No pose per frame, no scene deformation, no Clean/GT read in prediction.
"""
from context import *
from scipy.optimize import least_squares
from ring_first_3d.sim.geometry import se3,parameters
from solver2 import ring_residual,old

def pack_pairs(frames,C,tr,mask,omit=None):
 ids=[];ia=[];ib=[];xa=[];xb=[];weights=[]
 for tid in np.flatnonzero(mask):
  aa=[i for i,f in enumerate(frames)if f['side']=='A'and i!=omit and np.isfinite(tr['xy'][tid,i]).all()];bb=[i for i,f in enumerate(frames)if f['side']=='B'and i!=omit and np.isfinite(tr['xy'][tid,i]).all()]
  if len(aa)<2 or len(bb)<2:continue
  count=len(aa)*len(bb)
  for i in aa:
   for j in bb:ids.append(tid);ia.append(i);ib.append(j);xa.append([*tr['xy'][tid,i],1]);xb.append([*tr['xy'][tid,j],1]);weights.append(1/count)
 n=len(set(ids));ia=np.array(ia,int);ib=np.array(ib,int);return dict(track_ids=np.array(ids,int),ia=ia,ib=ib,A=C[ia],B=C[ib],invKA=np.array([np.linalg.inv(frames[i]['K'])for i in ia]),invKB=np.array([np.linalg.inv(frames[i]['K'])for i in ib]),xa=np.array(xa).reshape(-1,3),xb=np.array(xb).reshape(-1,3),weights=np.array(weights)/max(1,n),tracks=n)

def pair_residuals(T0,p,return_flags=False):
 if not len(p['xa']):return (np.empty(0),dict(zero_baseline=np.empty(0,bool),undefined_sampson=np.empty(0,bool)))if return_flags else np.empty(0)
 A=p['A'];B=T0@p['B'];R=np.swapaxes(B[:,:3,:3],1,2)@A[:,:3,:3];t=np.einsum('nji,nj->ni',B[:,:3,:3],A[:,:3,3]-B[:,:3,3]);S=np.zeros((len(t),3,3));S[:,0,1]=-t[:,2];S[:,0,2]=t[:,1];S[:,1,0]=t[:,2];S[:,1,2]=-t[:,0];S[:,2,0]=-t[:,1];S[:,2,1]=t[:,0];F=np.swapaxes(p['invKB'],1,2)@S@R@p['invKA'];lB=np.einsum('nij,nj->ni',F,p['xa']);lA=np.einsum('nji,nj->ni',F,p['xb']);num=np.einsum('ni,ni->n',p['xb'],lB);den=np.sqrt((lB[:,:2]**2).sum(1)+(lA[:,:2]**2).sum(1));r=num/np.maximum(den,1e-15);zero=np.linalg.norm(t,axis=1)<1e-6;undefined=den<1e-15;r[zero|undefined]=50.;return (r,dict(zero_baseline=zero,undefined_sampson=undefined))if return_flags else r

def pair_loss(weights):
 def loss(z):
  n=len(weights);out=np.empty((3,len(z)));s=np.sqrt(1+z[:n]);out[0,:n]=2*(s-1)*weights;out[1,:n]=weights/s;out[2,:n]=-.5*weights/s**3;out[0,n:]=z[n:];out[1,n:]=1;out[2,n:]=0;return out
 return loss

def solve_m5(p,ring,init):
 if p['tracks']<CFG['min_fit_tracks']:return dict(T=None,numerical='NOT_RUN',quality='INSUFFICIENT_FIT',tracks=p['tracks'])
 if ring['status']!='ESTIMATED':return dict(T=None,numerical='NOT_RUN',quality='INCONCLUSIVE_RING',tracks=p['tracks'])
 c=np.array(ring['center']);n=np.array(ring['normal']);whiten=np.linalg.inv(np.linalg.cholesky(np.array(ring['covariance'])));loss=pair_loss(p['weights']);base=old['ring_only'](c,n)
 def fun(v):
  T0=se3(v);return np.r_[pair_residuals(T0,p)/CFG['sigma_epipolar_px'],whiten@ring_residual(T0,c,n)]
 candidates=[se3([0,0,y,0,0,0])@base for y in np.arange(CFG['yaw_grid'])*2*np.pi/CFG['yaw_grid']]
 if init is not None:candidates.append(np.array(init))
 costs=[float(loss(fun(parameters(t))**2)[0].sum())for t in candidates];best=int(np.argmin(costs));fit=least_squares(fun,parameters(candidates[best]),loss=loss,max_nfev=CFG['max_nfev'],ftol=1e-10,xtol=1e-10,gtol=1e-10);T0=se3(fit.x);r=ring_residual(T0,c,n);maha=float(np.linalg.norm(whiten@r));deg=int((np.linalg.norm(p['A'][:,:3,3]-(T0@p['B'])[:,:3,3],axis=1)<1e-6).sum());singular=np.linalg.svd(fit.jac,compute_uv=False);return dict(T=T0,numerical='CONVERGED'if fit.success else'LIMIT',quality='DEGENERATE_EPIPOLAR'if deg==len(p['xa'])else'CONFLICT'if maha>CFG['ring_guard_mahalanobis']else'UNASSESSED',degenerate_pairs=deg,jacobian_singular_values=singular,tracks=p['tracks'],pairs=len(p['xa']),cost=2*fit.cost,nfev=fit.nfev,initial_candidate=best,initial_cost=costs[best],ring_mahalanobis=maha,ring_residual=r,guard=CFG['ring_guard_mahalanobis'],candidate_only=True)
