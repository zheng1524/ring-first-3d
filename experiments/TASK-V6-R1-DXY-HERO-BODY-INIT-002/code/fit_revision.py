"""002 adapters around the audited 001 ellipsoid objective.

All b-dependent terms use source_parts both in the full objective and coordinate
minimization. CAD and P/Q evidence are fixed inputs, never fitted observations.
"""
from common import *
import fit as legacy_fit
from fit import initialize, weights
from observations import *
from scipy.optimize import least_squares, minimize_scalar
from scipy.special import expit
sys.path.insert(0, '/home/liu/new-polyp-dxy/src')
from dxy_mid._engine.soft_geometry import interval_residual

class Problem(legacy_fit.Problem):
 def __init__(self, frames, sources, p0, plane=None, cad=None):
  super().__init__(frames,sources,np.asarray(p0).copy(),plane)
  self.cad_scene=scene(cad['V'],cad['F']) if cad is not None else None
  if self.cad_scene is not None:
   for f in self.frames:
    f['cad_z']=cast(self.cad_scene,f['rays'])[0]
   for s in self.sources:s['cad_z']=cast(self.cad_scene,s['rays'])[0]
  self.Q=[]
  for f in frames:
   q=np.asarray(f.get('boundary_Q',[])).reshape(-1,2)
   normals=np.asarray(f.get('Q_normals',[])).reshape(-1,2)
   lo=np.asarray(f.get('Q_lo',[]));hi=np.asarray(f.get('Q_hi',[]))
   assert len(q)==len(normals)==len(lo)==len(hi)
   self.Q.append([dict(q=a,n=n,lo=l,hi=h)for a,n,l,h in zip(q,normals,lo,hi)])
 def model_depth(self,p,s):
  z,hit,cap=clipped_depth(p,s['rays'],self.plane)
  cad=s.get('cad_z',np.full(len(z),np.inf))
  return z,hit&(z<cad-CFG['cad_tolerance_mm']),cap
 def source_parts(self,p,i,b):
  s=self.sources[i];r=s['rays'];D=s['D'];w=self.w[i];N=max(1,len(D))
  z,hit,cap=self.model_depth(p,s)
  err=np.full(len(D),np.sqrt(CFG['missing_depth_cost']))
  err[hit]=robust((z[hit]+b-D[hit])/CFG['depth_sigma_mm'])
  A,B,C,disc=ray_components(p,np.eye(3),r)
  q=np.logaddexp(0,(C-B*B/A)/.05)*.05
  h=np.zeros(len(D))
  if self.plane is not None:
   X=corrected_points(r,D,b);h=np.maximum(0,-(X@self.plane[:3]+self.plane[3]))/.5
  return dict(depth=err*np.sqrt(CFG['depth_weight']*w/N),coverage=robust(q+h)*np.sqrt(w/N),bias_prior=np.array([b/CFG['bias_prior_sigma_mm']*np.sqrt(w*CFG['depth_weight'])]))
 def bias_common(self,b):
  return np.array([float(self.w@b)/CFG['bias_common_sigma_mm']*np.sqrt(CFG['depth_weight'])]) if len(b) else np.empty(0)
 def pieces(self,p,b):
  parts=super().pieces(p,b)
  # Reuse the old boundary/clipped contour and shape regularization. P is the
  # only equality boundary; official Q retains its one-sided normal interval.
  parts['visible_boundary']*=np.concatenate([np.full(len(f['boundary']),np.sqrt(f.get('boundary_weight',1.)))for f in self.frames]) if self.frames else 1
  parts['dxy_completion']*=np.concatenate([np.full(32,np.sqrt(f['DXY'].get('weight',1.)))for f in self.frames if f['DXY']['available']]) if len(parts['dxy_completion']) else 1
  masks=[];qs=[]
  for f,w,Q in zip(self.frames,self.fw,self.Q):
   try:
    center,M,ax,curve=ellipse_projection(p,np.eye(3),f['K'],f['C'])
    sd=signed_distance(f['uv'],center,M,ax);prob=expit(-sd/2.)
    z,hit,cap=clipped_depth(p,f['rays'],self.plane)
    if self.plane is not None:
     A,B,C,disc=ray_components(p,np.eye(3),f['rays']);root=np.sqrt(np.maximum(disc,0));lo=(-B-root)/A;hi=(-B+root)/A;h=f['rays'][:,:3]@self.plane[:3]+self.plane[3];v=f['rays'][:,3:]@self.plane[:3]
     prob*=expit(np.maximum(h+lo*v,h+hi*v)/.15)
    cad=f.get('cad_z',np.full(len(z),np.inf));finite=np.isfinite(cad)&np.isfinite(z)
    vis=np.ones(len(z));vis[finite]=expit((cad[finite]-z[finite]-CFG['cad_tolerance_mm'])/CFG['cad_occlusion_soft_mm']);prob*=vis
    masks.append(robust((prob-f['target'])/.25)*np.sqrt(w*f['grid_weight']*CFG['mask_weight']))
    if Q:
     vals,U=np.linalg.eigh(M);p2=np.r_[center,np.log(1/np.sqrt(vals)),np.arctan2(U[1,0],U[0,0])]
     qr=interval_residual(p2,Q)
     qs.append(robust(qr/CFG['boundary_sigma_px'])*np.sqrt(w*CFG['q_weight']/len(Q)))
   except (ValueError,np.linalg.LinAlgError):
    masks.append(np.full(len(f['uv']),100*np.sqrt(w/max(1,len(f['uv'])))))
    if Q:qs.append(np.full(len(Q),100*np.sqrt(w*CFG['q_weight']/len(Q))))
  parts['mask']=np.concatenate(masks)if masks else np.empty(0)
  parts['occlusion_Q_interval']=np.concatenate(qs)if qs else np.empty(0)
  source_values=[self.source_parts(p,i,b[i])for i in range(len(self.sources))]
  for key in ['depth','coverage','bias_prior']:
   parts[key]=np.concatenate([value[key]for value in source_values])if self.sources else np.empty(0)
  parts['bias_common']=self.bias_common(b)
  if self.cad_scene is not None:
   V,F=body_mesh(p);signed=self.cad_scene.compute_signed_distance(o3d.core.Tensor(V.astype(np.float32))).numpy()
   active=np.ones(len(V)) if self.plane is None else (V@self.plane[:3]+self.plane[3]>=0).astype(float)
   penetration=np.maximum(0,-signed-CFG['cad_tolerance_mm'])*active
   parts['CAD_penetration']=robust(penetration/CFG['cad_penetration_sigma_mm'])*np.sqrt(CFG['cad_penetration_weight']/len(V))
  else:parts['CAD_penetration']=np.empty(0)
  return parts
 def bias_coordinate_value(self,p,b,i,x):
  proposal=b.copy();proposal[i]=x
  v=self.source_parts(p,i,x)
  return sum(float(y@y/2)for y in v.values())+float(self.bias_common(proposal)@self.bias_common(proposal)/2)
 def solve_bias(self,p,b):
  result=b.copy();steps=[]
  for i,s in enumerate(self.sources):
   if not len(s['D']):continue
   before=self.bias_coordinate_value(p,result,i,result[i])
   opt=minimize_scalar(lambda x:self.bias_coordinate_value(p,result,i,x),bounds=(-CFG['bias_bound_mm'],CFG['bias_bound_mm']),method='bounded',options={'xatol':1e-7})
   accepted=opt.fun<=before+1e-12
   if accepted:result[i]=opt.x
   steps.append(dict(source_id=s['meta']['source_id'],accepted=bool(accepted),before=before,after=float(opt.fun),nfev=opt.nfev))
  return result,steps
 def solve(self,p,b,cycles,stage):
  p=np.asarray(p).copy();b=np.asarray(b).copy();log=[]
  for k in range(cycles):
   before=self.values(p,b);old=sum(before.values())
   fit=least_squares(lambda q:self.residual(q,b),np.clip(p,self.lo+1e-8,self.hi-1e-8),bounds=(self.lo,self.hi),max_nfev=CFG['theta_nfev'],ftol=1e-4,xtol=1e-4,gtol=1e-4,x_scale='jac',diff_step=1e-4)
   q=fit.x;alpha=1.
   while sum(self.values(q,b).values())>old+1e-9 and alpha>1/128:alpha/=2;q=p+alpha*(fit.x-p)
   accepted=sum(self.values(q,b).values())<=old+1e-9
   if accepted:p=q
   aftertheta=sum(self.values(p,b).values());proposal,bl=self.solve_bias(p,b)
   after=sum(self.values(p,proposal).values());biasaccepted=after<=aftertheta+1e-9
   if biasaccepted:b=proposal
   log.append(dict(stage=stage,iteration=k,objective_before=old,objective_after_theta=aftertheta,objective_after=sum(self.values(p,b).values()),theta_accepted=bool(accepted),bias_accepted=bool(biasaccepted),bias_steps=bl,nfev=fit.nfev,optimizer_success=bool(fit.success),stop=str(fit.message),alpha=alpha,components=self.values(p,b)))
  return p,b,log
 def solve_multistart(self,starts,b,cycles,stage):
  results=[]
  for label,p in starts:
   q,bq,log=self.solve(p,b.copy(),cycles,stage+':'+label);results.append((sum(self.values(q,bq).values()),label,q,bq,log))
  best=min(results,key=lambda x:x[0])
  receipt=dict(selection='fixed_complete_FIT_objective_only',fixed_prior_reference=self.p0,selected=best[1],candidates=[dict(label=r[1],objective=r[0],p=r[2],b=r[3],stages=r[4])for r in results])
  return best[2],best[3],best[4],receipt

def evaluate(p,b,frames,sources,plane,cad=None):
 result=legacy_fit.evaluate(p,b,frames,sources,plane)
 # Evaluation uses exactly the same fixed CAD visibility convention as fitting.
 problem=Problem(frames,sources,p,plane,cad)
 for row,f in zip(result['projections'],frames):
  z,hit,cap=clipped_depth(p,f['rays'],plane);cad_z=f.get('cad_z',np.full(len(z),np.inf));pred=np.isfinite(z)&(z<cad_z-CFG['cad_tolerance_mm']);target=f['target'].astype(bool)
  row.update(foreground_hit_N=int((target&pred).sum()),foreground_miss_N=int((target&~pred).sum()),false_positive_N=int((~target&pred).sum()),IoU=float((target&pred).sum()/max(1,(target|pred).sum())),CAD_occluded_N=int((np.isfinite(z)&~pred).sum()))
 for row,s,i in zip(result['depth'],sources,range(len(sources))):
  z,hit,cap=problem.model_depth(p,s);e=np.abs(z[hit]+b[i]-s['D'][hit]);row.update(valid_N=int(hit.sum()),invalid_N=int((~hit).sum()),MAE_mm=float(e.mean())if len(e)else None,p95_mm=float(np.percentile(e,95))if len(e)else None)
 if problem.cad_scene is not None:
  V,F=body_mesh(p);signed=problem.cad_scene.compute_signed_distance(o3d.core.Tensor(V.astype(np.float32))).numpy();keep=np.ones(len(V),bool)if plane is None else V@plane[:3]+plane[3]>=0
  penetration=np.maximum(0,-signed[keep]);result['CAD_model']=dict(retained_vertex_N=int(keep.sum()),inside_N=int((penetration>0).sum()),over_tolerance_N=int((penetration>CFG['cad_tolerance_mm']).sum()),max_penetration_mm=float(penetration.max())if len(penetration)else None,tolerance_mm=CFG['cad_tolerance_mm'],scope='fixed CAD signed distance at retained mother vertices; not exhaustive triangle collision')
 return result
