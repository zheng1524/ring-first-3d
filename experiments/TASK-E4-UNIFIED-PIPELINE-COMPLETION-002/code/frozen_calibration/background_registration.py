from g5_common import *
cv2.setNumThreads(2)
def skew(t):return np.array([[0,-t[2],t[1]],[t[2],0,-t[0]],[-t[1],t[0],0]])
def fundamental(a,b,k):
 ra=a[:3,:3].T;rb=b[:3,:3].T;rel=rb@ra.T;t=rb@(a[:3,3]-b[:3,3]);ki=np.linalg.inv(k);return ki.T@skew(t)@rel@ki

def epi(a,b,uv,q,k):
 f=fundamental(a,b,k);x=np.c_[uv,np.ones(len(uv))];y=np.c_[q,np.ones(len(q))];fx=x@f.T;fy=y@f;return np.sum(y*fx,axis=1)/np.maximum(np.sqrt(np.sum(fx[:,:2]**2+fy[:,:2]**2,axis=1)),1e-9)
def triangle(a,b,p,q,k):
 x=cv2.undistortPoints(p.reshape(-1,1,2),k,None).reshape(-1,2);y=cv2.undistortPoints(q.reshape(-1,1,2),k,None).reshape(-1,2);h=cv2.triangulatePoints(np.linalg.inv(a)[:3],np.linalg.inv(b)[:3],x.T,y.T).T;return h[:,:3]/h[:,3:]
def feat(a,sift):
 im=image(a);l=labels(a);g=cv2.cvtColor(im,cv2.COLOR_RGB2GRAY);mask=(cv2.erode((l==0).astype(np.uint8),np.ones((7,7),np.uint8))>0)&(g<245);kp,de=sift.detectAndCompute(g,mask.astype(np.uint8)*255);return np.array([x.pt for x in kp]),de

def matches(fa,fb):
 p,da=fa;q,db=fb
 if da is None or db is None:return np.zeros((0,2)),np.zeros((0,2)),np.zeros(0,int),np.zeros(0,int)
 bf=cv2.BFMatcher();x=[m for m,n in bf.knnMatch(da,db,k=2) if m.distance<cfg()['SIFT_ratio']*n.distance];y={m.queryIdx:m.trainIdx for m,n in bf.knnMatch(db,da,k=2) if m.distance<cfg()['SIFT_ratio']*n.distance};x=[m for m in x if y.get(m.trainIdx)==m.queryIdx];ii=np.array([m.queryIdx for m in x],int);jj=np.array([m.trainIdx for m in x],int);return p[ii],q[jj],ii,jj

def vec(p):
 w=np.linalg.inv(p);return np.r_[Rotation.from_matrix(w[:3,:3]).as_rotvec(),w[:3,3]]
def pose(x):
 w=np.eye(4);w[:3,:3]=Rotation.from_rotvec(x[:3]).as_matrix();w[:3,3]=x[3:];return np.linalg.inv(w)
def spin(p,y):
 T=np.eye(4);T[:3,:3]=Rotation.from_euler('z',y).as_matrix();return T@p

def main():
 verify('ring_predictions');freeze('registration_protocol',[Path(__file__),R/'scripts/g5_common.py',R/'config.json']);L=ledger();by={x['id']:x for x in L};sift=cv2.SIFT_create(nfeatures=cfg()['SIFT_features'],contrastThreshold=.01);features={a['id']:feat(a,sift) for a in L};cands={x['id']:x for x in load('predictions/ring_candidates.json')};cam=prev.cam('real','0');anchors=[('frozen_key03',cam['c2w'][3]),('frozen_key08',cam['c2w'][8]),('frozen_key13',cam['c2w'][13])];targets=[a for a in L if not a['id'].startswith('frozen')];records=[];solutions={};cameras=np.full((len(targets),4,4),np.nan)
 for ti,a in enumerate(targets):
  id=a['id'];ob=obs(id);pairs=[]
  for an,ap in anchors:
   p,q,ii,jj=matches(features[an],features[id]);held=(ii%5)==0;tr=~held;inl=np.zeros(len(p),bool)
   if tr.sum()>=12:
    cv2.setRNGSeed(cfg()['seed']);F,ix=cv2.findFundamentalMat(p[tr],q[tr],cv2.FM_RANSAC,cfg()['epipolar_RANSAC_px'],.999);inl[np.flatnonzero(tr)]=ix.ravel().astype(bool) if ix is not None else False
   pairs.append(dict(anchor=an,ap=ap,p=p,q=q,ii=ii,jj=jj,held=held,train_inlier=inl))
  pairs.sort(key=lambda x:(-x['train_inlier'].sum(),x['anchor']));best=pairs[0];ntr=int(best['train_inlier'].sum());fits=[]
  np.savez_compressed(R/f"observations/{id}_background_pairs.npz",**{f'{j}_{k}':v[k] for j,v in enumerate(pairs) for k in ['p','q','ii','jj','held','train_inlier']},anchors=[p['anchor'] for p in pairs])
  # Select pair and candidate initialisations using TRAIN observations only.
  if ntr>=12:
   ap=best['ap'];p=best['p'][best['train_inlier']];q=best['q'][best['train_inlier']];initials=[]
   for ci,c in enumerate(cands[id]['candidates']):
    base=np.array(c['c2r'])
    for yi,y in enumerate(np.linspace(-np.pi,np.pi,cfg()['yaw_grid_count'],endpoint=False)):
     sp=spin(base,y);e=epi(ap,sp,p,q,K);score=float(np.mean(2*(np.sqrt(1+e*e)-1)));initials.append((score,ci,y,sp))
   initials.sort(key=lambda x:x[0]);chosen=[]
   for it in initials:
    if all(np.linalg.norm(it[3][:3,3]-z[3][:3,3])>1. for z in chosen):chosen.append(it)
    if len(chosen)==cfg()['yaw_seeds']:break
   if len(chosen)<cfg()['yaw_seeds']:chosen=initials[:cfg()['yaw_seeds']]
   for initial in chosen:
    def residual(x):
     po=pose(x);ep=epi(ap,po,p,q,K);rg=torus_residual(po,ob);return np.r_[ep,rg*cfg()['ring_weight']*np.sqrt(len(ep)/max(len(rg),1))]
    f=least_squares(residual,vec(initial[3]),loss='soft_l1',f_scale=1.,max_nfev=cfg()['joint_max_nfev'],diff_step=1e-5)
    po=pose(f.x);X=triangle(ap,po,p,q,K);qa,za=project(X,ap,K);qb,zb=project(X,po,K);train=stats(np.r_[np.linalg.norm(qa-p,axis=1),np.linalg.norm(qb-q,axis=1)]);test=best['held'];pt=best['p'][test];qt=best['q'][test];Xt=triangle(ap,po,pt,qt,K) if len(pt) else np.zeros((0,3));ua,z1=project(Xt,ap,K);ub,z2=project(Xt,po,K);hr=stats(np.r_[np.linalg.norm(ua-pt,axis=1),np.linalg.norm(ub-qt,axis=1)]);pos=float(((z1>0)&(z2>0)).mean()) if len(pt) else 0.;epheld=stats(epi(ap,po,pt,qt,K));ringheld=stats(torus_residual(po,ob,'held'));training_objective=float(np.mean(2*(np.sqrt(1+residual(f.x)**2)-1)))
    fits.append(dict(pose=po,initial_pose=initial[3],initial_ring_branch=initial[1],initial_yaw_rad=initial[2],objective=training_objective,training_reprojection_px=train,heldout_reprojection_px=hr,heldout_epipolar_px=epheld,heldout_ring_px=ringheld,positive_fraction=pos,nfev=f.nfev,optimizer_success=f.success,initial_epipolar_px=stats(epi(ap,initial[3],pt,qt,K)),heldout_X=Xt))
   fits.sort(key=lambda x:x['objective'])
  # Multi-anchor consistency: held target matches independently seen in OTHER frozen anchor.
  independent=[]
  if fits:
   po=fits[0]['pose'];bp=best
   for other in pairs[1:]:
    _,_,bi,oi=matches(features[bp['anchor']],features[other['anchor']]);cor={int(i):int(j) for i,j in zip(bi,oi)};target_other={int(j):int(i) for i,j in zip(other['ii'],other['jj'])};rows=[]
    for j in np.flatnonzero(bp['held']):
     i0=int(bp['ii'][j]);it=int(bp['jj'][j]);i1=cor.get(i0)
     if i1 is None or target_other.get(it)!=i1:continue
     p0=bp['p'][j];p1=features[other['anchor']][0][i1];xx=triangle(bp['ap'],other['ap'],p0[None],p1[None],K);u0,z0=project(xx,bp['ap'],K);u1,z1=project(xx,other['ap'],K)
     # Filtering only frozen-anchor observations, never target error.
     if z0[0]<=0 or z1[0]<=0 or max(np.linalg.norm(u0[0]-p0),np.linalg.norm(u1[0]-p1))>3.:continue
     ut,zt=project(xx,po,K);rows.append((float(np.linalg.norm(ut[0]-bp['q'][j])),bool(zt[0]>0)))
    independent.append(dict(other_anchor=other['anchor'],n=len(rows),target_reprojection_px=stats([x[0] for x in rows]),positive_fraction=float(np.mean([x[1] for x in rows])) if rows else 0.))
  successful=False;reason='insufficient training background matches';spread=None
  if fits:
   b=fits[0];C=np.array([x['pose'][:3,3] for x in fits]);spread=float(np.linalg.norm(C[:,None]-C[None,:],axis=2).max());nheld=int(best['held'].sum());r=b['heldout_ring_px'];h=b['heldout_reprojection_px'];indn=sum(x['n'] for x in independent);inde=np.concatenate([np.zeros(0)])
   ipass=any(x['n']>=cfg()['background_min_held'] and x['target_reprojection_px']['MAE']<=3 and x['target_reprojection_px']['p95']<=6 and x['positive_fraction']>=.95 for x in independent)
   successful=bool(nheld>=8 and h['MAE']<=3 and h['p95']<=6 and r['MAE']<=3 and r['p95']<=6 and b['positive_fraction']>=.95 and spread<=2 and ipass);reason=None if successful else 'independent background / Ring / cheirality / multi-start stability gate failed'
   if successful:cameras[ti]=b['pose']
  rec=dict(id=id,source_id=a['source_id'],best_anchor=best['anchor'],background_train_F_inliers=ntr,heldout_background_matches=int(best['held'].sum()),numeric_pose=bool(fits),registered=successful,failure=reason,center_spread_mm=spread,pair_counts=[dict(anchor=x['anchor'],mutual_matches=len(x['p']),train_F_inliers=int(x['train_inlier'].sum()),held=int(x['held'].sum())) for x in pairs],independent_third_view=independent)
  if fits:rec.update({k:v for k,v in fits[0].items() if k not in ['pose','heldout_X','initial_pose']})
  records.append(rec);solutions[id]=fits;save('metrics/background_registration.json',records);save('predictions/joint_pose_candidates.json',solutions);print('JOINT',id,'train',ntr,'held',int(best['held'].sum()),'nstarts',len(fits),'pass',successful,'spread',spread,'3view',independent,flush=True)
 np.savez_compressed(R/'predictions/registered_cameras.npz',ids=[a['id'] for a in targets],c2w=cameras,K=K,registered=np.isfinite(cameras[:,0,0]),units='mm',no_GT=True);freeze('registration_predictions',[R/'metrics/background_registration.json',R/'predictions/joint_pose_candidates.json',R/'predictions/registered_cameras.npz']+list((R/'observations').glob('*background_pairs.npz')));print('REGISTRATION_DONE',sum(x['registered'] for x in records),'/',len(records),flush=True)
if __name__=='__main__':main()
