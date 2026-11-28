"""One ellipsoid and bounded per-source axial bias. Fixed domains within each stage."""
from observations import *
from scipy.optimize import least_squares,minimize_scalar
from scipy.special import expit
def initialize(frames):
 origins=[];dirs=[];pix=[]
 for f in frames:
  if f['DXY']['available']:uv=np.array(f['DXY']['center_px']);axes=np.linalg.svd(f['DXY']['basis_px'],compute_uv=False)
  else:
   mask=cv2.imread(f['Mask'],0)==1;y,x=np.where(mask)
   if not len(x):continue
   uv=np.array([x.mean(),y.mean()]);axes=2*np.sqrt(np.maximum(np.linalg.eigvalsh(np.cov(np.c_[x,y].T)),1))[::-1]
  r=rays(uv[None],f['K'],f['C'])[0];d=r[3:]/np.linalg.norm(r[3:]);origins.append(r[:3]);dirs.append(d);pix.append((axes,f))
 if not dirs:raise ValueError('NO_FOREGROUND_2D')
 origins=np.array(origins);dirs=np.array(dirs);A=np.eye(3)[None]-dirs[:,:,None]*dirs[:,None,:];H=A.sum(0);center=np.linalg.solve(H+np.eye(3)*.002,np.einsum('nij,nj->i',A,origins))
 depth=np.array([(center-f['C'][:3,3])@f['C'][:3,2]for _,f in pix]);fallback=False
 if not np.isfinite(center).all()or (depth<=1).any()or np.linalg.norm(center)>80:
  # Weak triangulation gets an explicit Ring-neighborhood depth prior, never a learned/GT body.
  center=np.mean(origins+dirs*np.maximum(2,-(origins*dirs).sum(1))[:,None],axis=0);fallback=True
 sizes=[]
 for ax,f in pix:
  z=max(1.,float((center-f['C'][:3,3])@f['C'][:3,2]));sizes.append(ax*z/f['K'][0,0])
 size=np.clip(np.median(sizes,axis=0),.3,30);n=np.mean([f['C'][:3,2]for _,f in pix],axis=0);n/=np.linalg.norm(n);u=np.cross(np.eye(3)[np.argmin(abs(n))],n);u/=np.linalg.norm(u);Q=np.c_[u,np.cross(n,u),n]
 axes=np.r_[size,.6*np.sqrt(np.prod(size))];p=np.r_[center,Rotation.from_matrix(Q).as_rotvec(),np.log(axes)]
 return p,dict(method='DXY_or_visible_Mask_center_rays_and_pixel_extent_only',H_condition=float(np.linalg.cond(H)),weak_Ring_neighborhood_prior=fallback,initial_axes_mm=axes,uses_HERO=False)
def weights(sources):
 cases=sorted({s['meta']['case']for s in sources});out=np.zeros(len(sources))
 for case in cases:
  ix=[i for i,s in enumerate(sources)if s['meta']['case']==case];sets=[{sources[i]['meta']['raw_target'],*sources[i]['meta']['support']}for i in ix];normal=np.array([sources[i]['C'][:3,2]for i in ix]);corr=np.array([1+sum(len(a&b)/max(1,len(a|b))for j,b in enumerate(sets)if j!=k)for k,a in enumerate(sets)])
  direction=np.array([max(1,int((normal@v>.94).sum()))for v in normal]);w=1/(corr*direction);out[ix]=w/w.sum()/len(cases)
 return out
class Problem:
 def __init__(self,frames,sources,p0,plane=None):
  self.frames=frames;self.sources=sources;self.p0=p0;self.plane=plane;self.w=weights(sources);self.calls=0
  cases=sorted({f['case']for f in frames});self.fw=np.array([1/len(cases)/sum(g['case']==f['case']for g in frames)for f in frames])
  self.lo=np.r_[p0[:3]-20,np.full(3,-2*np.pi),np.log(np.full(3,.2))];self.hi=np.r_[p0[:3]+20,np.full(3,2*np.pi),np.log(np.full(3,40.))]
 def pieces(self,p,b):
  self.calls+=1;parts={k:[]for k in ['visible_boundary','mask','dxy_completion','depth','coverage','bias_prior','shape_prior']}
  for f,w in zip(self.frames,self.fw):
   try:
    center,M,ax,curve=ellipse_projection(p,np.eye(3),f['K'],f['C'])
    sd=signed_distance(f['uv'],center,M,ax);prob=expit(-sd/2.)
    if self.plane is not None:
     A,B,C,disc=ray_components(p,np.eye(3),f['rays']);lo=(-B-np.sqrt(np.maximum(disc,0)))/A;hi=(-B+np.sqrt(np.maximum(disc,0)))/A;h=f['rays'][:,:3]@self.plane[:3]+self.plane[3];v=f['rays'][:,3:]@self.plane[:3];prob*=expit(np.maximum(h+lo*v,h+hi*v)/.15)
    parts['mask'].append(robust((prob-f['target'])/.25)*np.sqrt(w*f['grid_weight']*CFG['mask_weight']))
    boundary_distance=signed_distance(f['boundary'],center,M,ax)
    if self.plane is not None and len(f['boundary']):
     # Convex clipped ellipsoid projection: a pixel is inside iff the ray hits
     # the ellipsoid and its chord reaches the retained halfspace. Both zero
     # contours enter the signed distance proxy, including the cut contour.
     def chord_height(uv):
      rr=rays(uv,f['K'],f['C']);A,B,C,disc=ray_components(p,np.eye(3),rr);lo=(-B-np.sqrt(np.maximum(disc,0)))/A;hi=(-B+np.sqrt(np.maximum(disc,0)))/A;h=rr[:,:3]@self.plane[:3]+self.plane[3];v=rr[:,3:]@self.plane[:3];return np.maximum(h+lo*v,h+hi*v)
     uv=f['boundary'];h=chord_height(uv);eps=.05;gx=(chord_height(uv+[eps,0])-chord_height(uv-[eps,0]))/(2*eps);gy=(chord_height(uv+[0,eps])-chord_height(uv-[0,eps]))/(2*eps)
     cut_distance=-h/np.maximum(np.hypot(gx,gy),.005);boundary_distance=np.maximum(boundary_distance,cut_distance)
    parts['visible_boundary'].append(robust(boundary_distance/CFG['boundary_sigma_px'])*np.sqrt(w/max(1,len(f['boundary']))))
    d=f['DXY']
    if d['available']:
     theta=np.arange(32)*2*np.pi/32;u=np.array(d['center_px'])+np.c_[np.cos(theta),np.sin(theta)]@np.array(d['basis_px']).T
     parts['dxy_completion'].append(robust(signed_distance(u,center,M,ax)/CFG['boundary_sigma_px'])*np.sqrt(w*CFG['dxy_weight']/len(u)))
   except (ValueError,np.linalg.LinAlgError):
    parts['mask'].append(np.full(len(f['uv']),100*np.sqrt(w/len(f['uv']))));parts['visible_boundary'].append(np.full(len(f['boundary']),100*np.sqrt(w/max(1,len(f['boundary'])))))
    if f['DXY']['available']:parts['dxy_completion'].append(np.full(32,100*np.sqrt(w*CFG['dxy_weight']/32)))
  for i,(s,w)in enumerate(zip(self.sources,self.w)):
   r=s['rays'];D=s['D'];z,hit,cap=clipped_depth(p,r,self.plane);err=np.full(len(D),np.sqrt(CFG['missing_depth_cost']));err[hit]=robust((z[hit]+b[i]-D[hit])/CFG['depth_sigma_mm'])
   parts['depth'].append(err*np.sqrt(CFG['depth_weight']*w/max(1,len(D))))
   A,B,C,disc=ray_components(p,np.eye(3),r);miss=np.logaddexp(0,(C-B*B/A)/.05)*.05
   if self.plane is not None:
    X=corrected_points(r,D,b[i]);miss+=np.maximum(0,-(X@self.plane[:3]+self.plane[3]))/.5
   parts['coverage'].append(robust(miss)*np.sqrt(w/max(1,len(D))))
   parts['bias_prior'].append(np.array([b[i]/CFG['bias_prior_sigma_mm']*np.sqrt(w*CFG['depth_weight'])]))
  prior=np.r_[(p[:3]-self.p0[:3])/10,(p[3:6]-self.p0[3:6])/2,(p[6:9]-self.p0[6:9])/1.2]
  parts['shape_prior']=[prior*np.sqrt(CFG['shape_prior_weight'])]
  return {k:np.concatenate(v)if v else np.zeros(0)for k,v in parts.items()}
 def residual(self,p,b):return np.concatenate(list(self.pieces(p,b).values()))
 def values(self,p,b):return {k:float(v@v/2)for k,v in self.pieces(p,b).items()}
 def solve(self,p,b,cycles,stage):
  log=[]
  for k in range(cycles):
   before=self.values(p,b);fun=lambda q:self.residual(q,b)
   fit=least_squares(fun,np.clip(p,self.lo+1e-8,self.hi-1e-8),bounds=(self.lo,self.hi),max_nfev=CFG['theta_nfev'],ftol=1e-4,xtol=1e-4,gtol=1e-4,x_scale='jac')
   old=sum(before.values());q=fit.x;alpha=1.
   while sum(self.values(q,b).values())>old+1e-9 and alpha>1/128:alpha/=2;q=p+alpha*(fit.x-p)
   accepted=sum(self.values(q,b).values())<=old+1e-9
   if accepted:p=q
   aftertheta=sum(self.values(p,b).values());proposal=b.copy()
   for i,s in enumerate(self.sources):
    if not len(s['D']):continue
    z,hit,cap=clipped_depth(p,s['rays'],self.plane)
    def f(x):
     err=np.full(len(z),np.sqrt(CFG['missing_depth_cost']));err[hit]=robust((z[hit]+x-s['D'][hit])/CFG['depth_sigma_mm']);value=float(np.mean(err**2)+ (x/CFG['bias_prior_sigma_mm'])**2)
     if self.plane is not None:
      h=corrected_points(s['rays'],s['D'],x)@self.plane[:3]+self.plane[3];value+=float(np.mean(robust(np.maximum(0,-h)/.5)**2))/CFG['depth_weight']
     return value
    proposal[i]=minimize_scalar(f,bounds=(-CFG['bias_bound_mm'],CFG['bias_bound_mm']),method='bounded').x
   after=sum(self.values(p,proposal).values());biasaccepted=after<=aftertheta+1e-9
   if biasaccepted:b=proposal
   log.append(dict(stage=stage,iteration=k,objective_before=old,objective_after_theta=aftertheta,objective_after=sum(self.values(p,b).values()),theta_accepted=bool(accepted),bias_accepted=bool(biasaccepted),nfev=fit.nfev,optimizer_success=bool(fit.success),stop=str(fit.message),alpha=alpha,components=self.values(p,b)))
  return p,b,log
def evaluate(p,b,frames,sources,plane):
 rows=[]
 for f in frames:
  z,hit,cap=clipped_depth(p,f['rays'],plane);pred=np.isfinite(z);target=f['target'].astype(bool)
  rows.append(dict(case=f['case'],frame=f['id'],role=f['role'],foreground_N=int(target.sum()),foreground_hit_N=int((target&pred).sum()),foreground_miss_N=int((target&~pred).sum()),background_N=int((~target).sum()),false_positive_N=int((~target&pred).sum()),IoU=float((target&pred).sum()/max(1,(target|pred).sum())),inferred_cap_pixels_N=int(cap.sum())))
 depth=[]
 for i,s in enumerate(sources):
  z,hit,cap=clipped_depth(p,s['rays'],plane);e=abs(z[hit]+b[i]-s['D'][hit]);h=s['raw_X']@plane[:3]+plane[3]if plane is not None else np.ones(len(z))
  cad=s.get('cad_z',np.full(len(z),np.inf));corrected=s['D']-b[i]
  depth.append(dict(source_id=s['meta']['source_id'],fixed_N=len(z),valid_N=int(hit.sum()),invalid_N=int((~hit).sum()),cap_only_N=int(cap.sum()),bias_mm=float(b[i]),MAE_mm=float(e.mean())if len(e)else None,p95_mm=float(np.percentile(e,95))if len(e)else None,original_on_cut_side_N=int((h<0).sum()),original_CAD_conflict_N=int((s['D']>=cad-.05).sum()),corrected_CAD_conflict_N=int((corrected>=cad-.05).sum()),corrected_negative_Z_N=int((corrected<=0).sum()),model_CAD_occluded_N=int((hit&(z>=cad-.05)).sum())))
 return dict(projections=rows,depth=depth,real_GT='NOT_EVALUABLE')
