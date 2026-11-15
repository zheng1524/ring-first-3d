"""2D region-seeded rigid source-camera/HERO resection; no source 3D NN gate."""
from features import *
from scipy.optimize import least_squares
CFG=load(R/'config/PROTOCOL.json')

def robust(x):
 return x*np.sqrt(2/(np.sqrt(1+x*x)+1))

class RingConstraint:
 def __init__(self,V,F,labels,K):
  self.V=V;self.F=F;self.rt=scene(V,F);self.K=K;self.labels=labels;self.h,self.w=labels.shape;self.center=V.mean(0);_,vec=np.linalg.eigh(np.cov((V-self.center).T));n=vec[:,0];n=n if n[2]>=0 else-n;x=np.array([1.,0,0]);x-=n*(x@n);x/=np.linalg.norm(x);y=np.cross(n,x);self.frame=np.eye(4);self.frame[:3,:3]=np.c_[x,y,n];self.frame[:3,3]=self.center;m=trimesh.Trimesh(V,F,process=False);self.N=m.face_normals;self.FC=m.triangles_center;self.edges=m.face_adjacency_edges;self.adj=m.face_adjacency;ring=labels==2;self.dt=cv2.distanceTransform((~ring).astype(np.uint8),cv2.DIST_L2,cv2.DIST_MASK_PRECISE);points=contour(ring)
  if len(points):
   nearP=cv2.dilate((labels==1).astype(np.uint8),np.ones((3,3),np.uint8));pp=np.rint(points).astype(int);points=points[nearP[pp[:,1],pp[:,0]]==0]
  self.observed=points[np.linspace(0,len(points)-1,min(CFG['ring_samples'],len(points)),dtype=int)]if len(points)else np.empty((0,2));self.S=None
 def canonical(self,C):
  p=np.linalg.inv(self.frame)@C;phi=np.arctan2(p[1,3],p[0,3]);return self.frame@yaw(-np.degrees(phi))@np.linalg.inv(self.frame)@C
 def select(self,C):
  C=self.canonical(C);front=((C[:3,3]-self.FC)*self.N).sum(1)>0;ii=np.where(front[self.adj[:,0]]!=front[self.adj[:,1]])[0];edges=self.edges[ii];X=self.V[edges];mid=X.mean(1);uv,z=project(mid,C,self.K);hits=rayquery(self.rt,C,self.K,uv)['t_hit'];edges=edges[(z>0)&(hits>=z-.002)]
  if len(edges)>512:edges=edges[np.linspace(0,len(edges)-1,512,dtype=int)]
  self.S=self.V[edges]if len(edges)else np.empty((0,2,3));return self.S
 def residual(self,C):
  C=self.canonical(C)
  if self.S is None:self.select(C)
  if not len(self.S):return np.full(2*CFG['ring_samples'],100.)
  projected,z=project(self.S.reshape(-1,3),C,self.K);segments=projected.reshape(-1,2,2);points=segments.mean(1);clip=np.clip(points,[0,0],[self.w-1,self.h-1]);distance=map_coordinates(self.dt,[clip[:,1],clip[:,0]],order=1,mode='nearest')+np.linalg.norm(points-clip,axis=1);p=np.rint(clip).astype(int);unknown=self.labels[p[:,1],p[:,0]]==1;goodz=(z.reshape(-1,2)>0).all(1);forward=np.where(goodz,np.where(unknown,0,distance),100.)
  a,b=segments[:,0],segments[:,1];d=b-a;u=self.observed[:,None]-a[None];t=(u*d[None]).sum(-1)/np.maximum((d*d).sum(1),1e-12)[None];q=a[None]+np.clip(t,0,1)[:,:,None]*d[None];ds=((self.observed[:,None]-q)**2).sum(-1);ds[:,~goodz]=1e4;reverse=np.sqrt(np.maximum(ds.min(1),0))if len(ds)else np.empty(0)
  return np.r_[robust(forward/CFG['ring_sigma_px'])/np.sqrt(max(1,len(forward))),robust(reverse/CFG['ring_sigma_px'])/np.sqrt(max(1,len(reverse)))]

def load_fit_matches(rec):
 plan=next(x for x in load(R/'config/BACKGROUND_REFERENCE_PLAN.json')if x['source']==rec['id']);out=[]
 for v in plan['references']:
  p=Path(v.get('fit_match',v['match']));a=np.load(p)
  if 'FIT_index'in a:ii=a['FIT_index'];p1=a['p'][ii];p2=a['q'][ii]
  else:p1=a['p'];p2=a['q']
  if len(p1):out.append(dict(reference=v['reference'],C=np.array(v['ref_C']),K=np.array(v['ref_K']),p=p1,q=p2))
 return out

def match_residual(C,K,matches,barriers=True):
 rr=[]
 for m in matches:
  f=fundamental(C,K,m['C'],m['K']);e=sampson(f,m['p'],m['q']);rr.append(robust(e/CFG['sift_sigma_px'])/np.sqrt(max(1,len(e)*len(matches))))
  if barriers:rr.append(np.array([max(0,CFG['sift_baseline_floor_mm']-np.linalg.norm(C[:3,3]-m['C'][:3,3]))/.1]))
 return np.concatenate(rr)if rr else np.empty(0)

def region_candidates(rec,obs,V,F,body,ring,C,phase):
 a=np.load(rec['view_cache']);ids=a['anchor_index'];e=dict(center=a['ellipse_center'],axes=a['ellipse_axes'],U=a['ellipse_U']);h,w=a['labels'].shape;uv_all=np.c_[np.tile(np.arange(w),h),np.repeat(np.arange(h),w)];r=rayquery(body,C,a['K'],uv_all);z=r['t_hit'].reshape(h,w);mask=np.isfinite(z)
 if mask.sum()<20:return None,dict(status='BODY_NOT_VISIBLE',N=0)
 be=ellipse_descriptor(mask);norm=a['q'][ids];ang=np.radians(phase);Rot=np.array([[np.cos(ang),-np.sin(ang)],[np.sin(ang),np.cos(ang)]]);mapped=(norm@Rot.T)*be['axes'];mapped=mapped@be['U'].T+be['center'];hit=rayquery(body,C,a['K'],mapped);rz=hit['t_hit'];cad=rayquery(ring.rt,C,a['K'],mapped)['t_hit'];ok=np.isfinite(rz)&(rz>0)&(rz<cad-.05)&(mapped[:,0]>=0)&(mapped[:,0]<w)&(mapped[:,1]>=0)&(mapped[:,1]<h);p=rays(C,a['K'],mapped);Q=p[:,:3]+p[:,3:]*np.where(np.isfinite(rz),rz,0)[:,None];face=hit['primitive_ids'];normal=np.zeros_like(Q);valid=np.flatnonzero(ok);nn=face_normals_local(V,F)
 if len(valid):normal[valid]=nn[face[valid]]
 Hseed=C@np.linalg.inv(np.array(rec['C']));hero_normal=obs['normal'][ids]@Hseed[:3,:3].T;ok&=(hero_normal*normal).sum(1)>=CFG['normal_candidate_min_cos'];ids=ids[ok]
 if len(ids)<CFG['min_region_anchors']:return None,dict(status='INSUFFICIENT_REGION_CANDIDATES',N=len(ids),initial_3D_distance_gating=False)
 return dict(index=ids,Q=Q[ok],body_face=face[ok],mapped_uv=mapped[ok],source_uv=a['uv'][ids],normalized_uv=norm[ok],phase=phase,Body_ellipse=be),dict(status='REGION_CANDIDATE',N=len(ids),fixed_source_core_N=len(a['anchor_index']),initial_3D_distance_gating=False)
def face_normals_local(V,F):
 n=np.cross(V[F[:,1]]-V[F[:,0]],V[F[:,2]]-V[F[:,0]]);return n/np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-15)

def solve_fixed(X,Q,source_uv,Cseed,C0,K,ring,matches,tag,folder):
 # A genuine shared rigid source+camera update; immutable local shape.
 Hinit=proper_rigid(X,Q);seedC=Hinit@C0;ring.select(seedC);trace=[];best=[np.inf];count=[0]
 def residual(x,record=True,include_body=True,include_prior=True):
  G=pose_delta(x);C=G@seedC;H=C@np.linalg.inv(C0);rr=[]
  if include_body:
   rr.append(robust((transform(X,H)-Q).ravel()/CFG['body_sigma_mm'])*np.sqrt(CFG['region_metric_weight']/(3*len(X))))
   uv,zz=project(Q,C,K);rr.append(robust(np.where(zz[:,None]>0,uv-source_uv,100.).ravel()/CFG['region_projection_sigma_px'])*np.sqrt(CFG['region_projection_weight']/(2*len(X))))
  rr.append(ring.residual(C));rr.append(match_residual(C,K,matches,barriers=include_prior))
  if include_prior:
   delta=C@np.linalg.inv(C0);p=np.r_[delta[:3,3]/CFG['prior_sigma_translation_mm'],Rotation.from_matrix(delta[:3,:3]).as_rotvec()/np.radians(CFG['prior_sigma_rotation_deg'])];rr.append(p*np.sqrt(CFG['prior_weight']))
  r=np.concatenate(rr);r=np.nan_to_num(r,nan=100.,posinf=100.,neginf=-100.)
  if record:count[0]+=1;trace.append(np.r_[x,np.sum(r*r)])
  return r
 sol=least_squares(residual,np.zeros(6),method='trf',loss='linear',bounds=(np.r_[np.full(3,-CFG['pose_translation_increment_bound_mm']),np.full(3,-np.pi)],np.r_[np.full(3,CFG['pose_translation_increment_bound_mm']),np.full(3,np.pi)]),max_nfev=CFG['pose_nfev'],ftol=1e-5,xtol=1e-5,gtol=1e-5,x_scale=np.r_[np.ones(3),np.full(3,.1)]);C=pose_delta(sol.x)@seedC;H=C@np.linalg.inv(C0);r=residual(sol.x,False);objective=float(np.sum(r*r));np.savez_compressed(folder/(tag+'_TRACE.npz'),x_cost=np.array(trace),X_original=X,Q_fixed=Q,H=H,C=C,initial_C=seedC)
 return C,dict(tag=tag,H=H,C=C,objective=objective,solver_success=bool(sol.success),message=sol.message,nfev=sol.nfev,residual_calls=count[0],region_MAE_mm=float(np.linalg.norm(transform(X,H)-Q,axis=1).mean()),initial_region_MAE_mm=float(np.linalg.norm(X-Q,axis=1).mean()),prior_from_original=pose_difference(C,C0))

def independent_information(C,K,ring,matches):
 # No Body/prior/baseline barrier counted as measurement information.
 ring.select(C)
 def fun(x):
  cc=pose_delta(x)@C;return np.r_[ring.residual(cc),match_residual(cc,K,matches,barriers=False)]
 scale=np.r_[np.ones(3),np.full(3,np.radians(1.))];cols=[]
 for j in range(6):
  d=np.zeros(6);d[j]=scale[j]*1e-3;cols.append((fun(d)-fun(-d))/(2e-3))
 J=np.array(cols).T;sv=np.linalg.svd(J,compute_uv=False);rank=int((sv>max(sv[0],1e-20)*CFG['information_relative_rank']).sum());cond=float(sv[0]/max(sv[-1],1e-20));return dict(rank=rank,condition=cond,singular_values=sv,parameter_scaling='1mm translation /1degree rotation; relative rank1e-6',no_Body_prior=True)

def run_source(rec,bodyname,V,F,matches=None,folder=None):
 obs=dict(np.load(rec['obs']));a=np.load(rec['view_cache']);C0=np.array(rec['C']);K=np.array(rec['K']);rr=np.load(R/'inputs'/rec['group']/'RING.npz')if 'ring_path'not in rec else np.load(rec['ring_path']);ring=RingConstraint(rr['V'],rr['F'],a['labels'],K);body=scene(V,F);matches=load_fit_matches(rec)if matches is None else matches;folder=folder or R/'local_results'/rec['group']/bodyname/rec['id'];folder.mkdir(parents=True,exist_ok=True);results=[]
 for angle in CFG['pose_yaw_seeds_deg']:
  for phase in CFG['region_phase_deg']:
   C=yaw(angle)@C0;last=None;regions=[]
   for iteration in range(CFG['correspondence_rounds']):
    reg,info=region_candidates(rec,obs,V,F,body,ring,C,phase);regions.append(info)
    if reg is None:break
    tag='Y%03d_P%03d_R%d'%(angle,phase,iteration);np.savez_compressed(folder/(tag+'_REGION.npz'),source_native_index=reg['index'],source_pixel_id=obs['pixel_id'][reg['index']],Q=reg['Q'],body_face=reg['body_face'],mapped_uv=reg['mapped_uv'],source_uv=reg['source_uv']);C,last=solve_fixed(obs['X'][reg['index']],reg['Q'],reg['source_uv'],C,C0,K,ring,matches,tag,folder);last.update(yaw_seed_deg=angle,phase_deg=phase,region_N=len(reg['index']),region_status=regions)
   if last is not None:results.append(last)
   else:results.append(dict(yaw_seed_deg=angle,phase_deg=phase,status='NO_REGION',objective=None,regions=regions))
 numerical=[r for r in results if r.get('objective')is not None];numerical.sort(key=lambda x:(x['objective'],x['yaw_seed_deg'],x['phase_deg']));chosen=numerical[0]if numerical else None;ambiguous=[]
 if chosen:
  for r in numerical[1:]:
   delta=pose_difference(np.array(r['C']),np.array(chosen['C']));near=r['objective']<=chosen['objective']*(1+CFG['ambiguity_relative_objective'])+1e-5
   if near and(delta['rotation_deg']>CFG['ambiguity_pose_deg']or delta['translation_mm']>CFG['ambiguity_pose_mm']):ambiguous.append(dict(tag=r['tag'],**delta,objective=r['objective']))
  info=independent_information(np.array(chosen['C']),K,ring,matches);status='FROZEN_NUMERICAL_CANDIDATE';chosen['information']=info
 else:status='NO_NUMERICAL_CANDIDATE'
 record=dict(source=rec['id'],group=rec['group'],Body=bodyname,status=status,chosen=chosen,candidates=results,ambiguous_alternatives=ambiguous,selection='FIT objective only; no HOLDOUT/peer HERO/GT accessed',camera_and_HERO_same_rigid_transform=True,raw_shape_fixed=True,initial_proximity_gate=False);save(str(folder.relative_to(R)/'CANDIDATES_FROZEN.json'),record);print('RESECTION',rec['id'],bodyname,status,chosen['objective']if chosen else None,len(ambiguous),flush=True);return record
