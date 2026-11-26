"""Registered corrections to 001: original RGB loss, quadratic uncertain Ring."""
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from ring_first_3d.sim.geometry import se3,parameters,transform
from common2 import *
OLD_CFG=read(V001/'config.json')
old=original(V001/'code/registration.py',['ring_only','solve'],dict(np=np,Rotation=Rotation,least_squares=least_squares,se3=se3,parameters=parameters,transform=transform,CFG=OLD_CFG))
from ring_first_3d.contracts.coordinates import validate_c2w
old['validate_c2w']=validate_c2w

def ring_residual(T0,c,n):
 normal=T0[:3,:3]@n;normal=normal/np.linalg.norm(normal);dot=np.clip(normal[2],-1,1);q=normal[:2];mag=np.linalg.norm(q);angles=q*(np.arctan2(mag,dot)/max(mag,1e-15));return np.r_[transform(c[None],T0)[0],angles]

def mixed_loss(rgb_length,N):
 def loss(z):
  out=np.empty((3,len(z)));s=np.sqrt(1+z[:rgb_length]);out[0,:rgb_length]=2*(s-1)/N;out[1,:rgb_length]=1/s/N;out[2,:rgb_length]=-.5/(s**3)/N;out[0,rgb_length:]=z[rgb_length:];out[1,rgb_length:]=1;out[2,rgb_length:]=0;return out
 return loss

def solve_methods(A,B,ring,methods=None):
 A=np.asarray(A);B=np.asarray(B);c=np.asarray(ring['center']);n=np.asarray(ring['normal']);N=len(A);base=old['ring_only'](c,n);out={'M0':dict(T=np.eye(4),numerical='FIXED',quality='UNREGISTERED'),'M1':dict(T=base,numerical='FIXED',quality='YAW_UNIDENTIFIABLE')}
 for name in ['M2','M3','M4']:
  if methods and name not in methods:continue
  if N<CFG['min_fit_tracks']:out[name]=dict(T=None,numerical='NOT_RUN',quality='INSUFFICIENT_FIT',tracks=N);continue
  if name=='M2':
   old['CFG']=dict(OLD_CFG,ring_radius_mm=ring.get('radius_mm',5.6));t,r=old['solve'](A,B,c,n);out[name]=dict(T=t,numerical=r['status'],quality='UNASSESSED',details=r);continue
  angles=np.arange(CFG['yaw_grid'])*2*np.pi/CFG['yaw_grid'];ts=[se3([0,0,y,0,0,0])@base for y in angles];j=int(np.argmin([np.median(np.linalg.norm(transform(B,t)-A,axis=1))for t in ts]));init=ts[j]
  def rgb(t):return ((transform(B,t)-A)/CFG['sigma_rgb_mm']).ravel()
  if name=='M3' or ring['status']=='EXACT':
   def fun(p):return rgb(se3([0,0,p[0],0,0,0])@base)
   fit=least_squares(fun,[angles[j]],loss=mixed_loss(3*N,N),max_nfev=CFG['max_nfev'],ftol=1e-10,xtol=1e-10,gtol=1e-10);t=se3([0,0,fit.x[0],0,0,0])@base;out[name]=dict(T=t,numerical='CONVERGED'if fit.success else'LIMIT',quality='UNASSESSED',cost=2*fit.cost,nfev=fit.nfev,exact_ring=True,ring_residual=ring_residual(t,c,n));continue
  if ring['status']!='ESTIMATED':out[name]=dict(T=None,numerical='NOT_RUN',quality='INCONCLUSIVE_RING');continue
  covariance=np.asarray(ring['covariance']);L=np.linalg.cholesky(covariance);whiten=np.linalg.inv(L)
  def fun(p):
   t=se3(p);return np.r_[rgb(t),np.sqrt(CFG['ring_lambda'])*whiten@ring_residual(t,c,n)]
  fit=least_squares(fun,parameters(init),loss=mixed_loss(3*N,N),max_nfev=CFG['max_nfev'],ftol=1e-10,xtol=1e-10,gtol=1e-10);t=se3(fit.x);r=ring_residual(t,c,n);maha=float(np.linalg.norm(whiten@r));out[name]=dict(T=t,numerical='CONVERGED'if fit.success else'LIMIT',quality='CONFLICT'if maha>CFG['ring_guard_mahalanobis']else'UNASSESSED',cost=2*fit.cost,nfev=fit.nfev,ring_residual=r,ring_mahalanobis=maha,guard=CFG['ring_guard_mahalanobis'],candidate_only=maha>CFG['ring_guard_mahalanobis'])
 return out
