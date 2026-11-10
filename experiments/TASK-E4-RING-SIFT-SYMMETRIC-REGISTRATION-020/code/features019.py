from common import *
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
import itertools
CFG=None;VIEWS=None

def features(v):
 p=R/'features'/(v['id']+'.npz');p.parent.mkdir(exist_ok=True)
 if p.exists():return dict(np.load(p))
 a=np.load(v['cache']);rgb=a['RGB'];lab=a['labels'];gray=cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY);ok=(cv2.dilate((lab==2).astype(np.uint8),np.ones((5,5),np.uint8))==0)&(gray>=12)&(gray<245);ok[:8]=False;ok[-8:]=False;ok[:,:8]=False;ok[:,-8:]=False
 k,d=cv2.SIFT_create(nfeatures=6000,contrastThreshold=.01).detectAndCompute(gray,ok.astype(np.uint8)*255);xy=np.array([x.pt for x in k]).reshape(-1,2);d=np.empty((0,128),np.float32)if d is None else d;px=np.clip(np.rint(xy).astype(int),[0,0],[639,359]);np.savez_compressed(p,xy=xy,des=d,region=lab[px[:,1],px[:,0]],RGB_SHA256=v['RGB_SHA256'],method='OpenCV SIFT on real RGB; no RootSIFT/learned matches');return dict(np.load(p))

def match_desc(a,b):
 if min(len(a),len(b))<2:return np.empty((0,2),int)
 bf=cv2.BFMatcher();f=[x for pair in bf.knnMatch(a,b,k=2)if len(pair)==2 for x,y in [pair]if x.distance<.72*y.distance];back={x.queryIdx:x.trainIdx for pair in bf.knnMatch(b,a,k=2)if len(pair)==2 for x,y in [pair]if x.distance<.72*y.distance};return np.array([(m.queryIdx,m.trainIdx)for m in f if back.get(m.trainIdx)==m.queryIdx],int).reshape(-1,2)

def matches(a,b):
 p=R/'matches'/(a['id']+'__'+b['id']+'.npz');p.parent.mkdir(exist_ok=True)
 if p.exists():return dict(np.load(p))
 fa,fb=features(a),features(b);m=match_desc(fa['des'],fb['des']);u,w=fa['xy'][m[:,0]],fb['xy'][m[:,1]];F=None;good=np.zeros(len(m),bool);cv2.setRNGSeed(20261111)
 if len(m)>=8:
  try:F,flag=cv2.findFundamentalMat(u,w,cv2.USAC_MAGSAC,1.5,.999,10000)
  except cv2.error:F,flag=None,None
  if F is not None and F.shape==(3,3):good=flag.ravel().astype(bool)
 np.savez_compressed(p,index_pairs=m,p=u,q=w,RGB_RANSAC=good,F=np.full((3,3),np.nan)if F is None or F.shape!=(3,3)else F,first_RGB_SHA256=a['RGB_SHA256'],second_RGB_SHA256=b['RGB_SHA256']);return dict(np.load(p))

def project(X,v):
 T=np.asarray(v['T']);p=(X-T[:3,3])@T[:3,:3];q=p@np.asarray(v['K']).T;return q[:,:2]/q[:,2:],p[:,2]
def fundamental(a,b):
 A=np.linalg.inv(np.asarray(b['T']))@np.asarray(a['T']);x,y,z=A[:3,3];S=np.array([[0,-z,y],[z,0,-x],[-y,x,0]]);return np.linalg.inv(np.asarray(b['K'])).T@S@A[:3,:3]@np.linalg.inv(np.asarray(a['K']))
def sampson(F,p,q):
 a=np.c_[p,np.ones(len(p))];b=np.c_[q,np.ones(len(q))];Fa=a@F.T;Fb=b@F;return np.sum(b*Fa,axis=1)/np.sqrt(np.maximum(Fa[:,:2]**2+Fb[:,:2]**2,1e-20).sum(1))

def landmarks(ids,label):
 vv=[VIEWS[x]for x in ids];parent={};members={};camera={};pairs=[]
 def root(x):
  if x not in parent:parent[x]=x;members[x]={x};camera[x]={x[0]}
  while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
  return x
 for a,b in itertools.combinations(vv,2):
  m=matches(a,b);good=m['RGB_RANSAC']&(abs(sampson(fundamental(a,b),m['p'],m['q']))<4);pairs.append(dict(first=a['id'],second=b['id'],ratio_mutual=len(good),RGB_RANSAC_N=int(m['RGB_RANSAC'].sum()),known_pose_compatible_N=int(good.sum())))
  for ia,ib in m['index_pairs'][good]:
   x,y=(a['id'],int(ia)),(b['id'],int(ib));rx,ry=root(x),root(y)
   if rx==ry or camera[rx]&camera[ry]:continue
   if len(members[rx])<len(members[ry]):rx,ry=ry,rx
   parent[ry]=rx;members[rx]|=members[ry];camera[rx]|=camera[ry]
 tracks=[sorted(members[k])for k in parent if parent[k]==k and len(members[k])>=3];Xall=[];des=[];cov=[];obs=[];quality=[]
 for tid,tr in enumerate(tracks):
  vv0=[VIEWS[x[0]]for x in tr];xy=np.array([features(v)['xy'][j]for v,(_,j)in zip(vv0,tr)]);centers=np.array([v['T']for v in vv0])[:,:3,3];i,j=max(itertools.combinations(range(len(tr)),2),key=lambda ij:np.linalg.norm(centers[ij[0]]-centers[ij[1]]));a,b=vv0[i],vv0[j];P1=np.asarray(a['K'])@np.linalg.inv(a['T'])[:3];P2=np.asarray(b['K'])@np.linalg.inv(b['T'])[:3];H=cv2.triangulatePoints(P1,P2,xy[i:i+1].T,xy[j:j+1].T);X=(H[:3,0]/H[3,0]);
  if not np.isfinite(X).all():continue
  def res(x):return np.concatenate([project(x[None],v)[0][0]-p for v,p in zip(vv0,xy)])
  result=least_squares(res,X,loss='soft_l1',f_scale=1.5,max_nfev=30);X=result.x;err=np.linalg.norm(res(X).reshape(-1,2),axis=1);z=np.array([project(X[None],v)[1][0]for v in vv0]);rays=X-centers;rays/=np.linalg.norm(rays,axis=1)[:,None];par=np.degrees(np.arccos(np.clip(rays@rays.T,-1,1))).max();valid=bool((z>0).all()and err.max()<2 and par>.5 and np.linalg.norm(X)<300);quality.append(dict(track=tid,views=len(tr),max_reprojection_px=float(err.max()),max_parallax_deg=float(par),qualified=valid))
  if not valid:continue
  Xall.append(X);des.append(features(vv0[0])['des'][tr[0][1]]);cov.append(np.linalg.pinv(result.jac.T@result.jac));obs.append(dict(track=tid,observations=[dict(view=v,feature_id=j,uv=features(VIEWS[v])['xy'][j])for v,j in tr],reprojection_px=err,parallax_deg=par,covariance_noise='unit-pixel proxy, not calibrated confidence'))
 p=R/'landmarks';p.mkdir(exist_ok=True);np.savez_compressed(p/(label+'.npz'),X=np.array(Xall).reshape(-1,3),des=np.array(des,np.float32).reshape(-1,128),covariance=np.array(cov).reshape(-1,3,3));save('landmarks/'+label+'_OBSERVATIONS.json',obs);save('metrics/'+label+'_TRIANGULATION.json',dict(tracks_min3=len(tracks),qualified=len(Xall),pair_counts=pairs,quality=quality));return dict(np.load(p/(label+'.npz')))

def cross(reference_ids,target_ids,lm,label):
 epi=[];pnp=[];measurements=[]
 for tid in target_ids:
  b=VIEWS[tid];fb=features(b)
  for aid in reference_ids:
   a=VIEWS[aid];m=matches(a,b);ii=np.flatnonzero(m['RGB_RANSAC']);ii=ii[np.linspace(0,len(ii)-1,min(128,len(ii))).astype(int)]if len(ii)else ii
   if len(ii):epi.append(dict(a=aid,b=tid,p=m['p'][ii],q=m['q'][ii],match_indices=ii))
   measurements.append(dict(scope=label,first=aid,second=tid,mutual=len(m['p']),RGB_RANSAC_N=int(m['RGB_RANSAC'].sum()),used_epi_N=len(ii)))
  mm=match_desc(lm['des'],fb['des']);rec=dict(target=tid,matches=len(mm),success=False)
  if len(mm)>=6:
   XX=lm['X'][mm[:,0]];uv=fb['xy'][mm[:,1]];cv2.setRNGSeed(20261111);ok,rr,tt,ii=cv2.solvePnPRansac(XX,uv,np.asarray(b['K']),None,iterationsCount=1000,reprojectionError=3.,confidence=.999,flags=cv2.SOLVEPNP_EPNP)
   if ok and ii is not None and len(ii)>=6:
    idx=ii.ravel();rr,tt=cv2.solvePnPRefineLM(XX[idx],uv[idx],np.asarray(b['K']),None,rr,tt);rot=cv2.Rodrigues(rr)[0];C=np.eye(4);C[:3,:3]=rot.T;C[:3,3]=-rot.T@tt.ravel();T=C@np.linalg.inv(b['T']);rec.update(success=True,inliers=len(idx),T_candidate=T,landmark_X=XX[idx],uv=uv[idx],landmark_indices=mm[idx,0],feature_indices=mm[idx,1],image_cells=len(np.unique((uv[idx]//[80,60]).astype(int),axis=0)),depth_reference='RGB-only multiframe triangulation, no HERO');pnp.append(rec)
  if not rec['success']:pnp.append(rec)
 save('features/'+label+'_PNP.json',pnp);save('features/'+label+'_EPI.json',epi);table('metrics/'+label+'_MATCH_COUNTS.csv',measurements);save('metrics/'+label+'_SIFT_SUMMARY.json',dict(epi_pairs=len(epi),epipolar_observations=sum(len(x['p'])for x in epi),PnP_success=sum(x['success']for x in pnp),landmarks=len(lm['X']),target_frames=len(target_ids)));print('SIFT',label,len(lm['X']),len(epi),sum(x['success']for x in pnp),flush=True)

def main():
 global VIEWS
 VIEWS={v['id']:v for v in load(R/'config/VIEWS.json')};refs=[k for k,v in VIEWS.items()if v['video']=='004'and v['role']=='FIT'];targets=[k for k,v in VIEWS.items()if v['video']=='005'and v['role']=='FIT'];allids=refs+targets
 for k in allids:features(VIEWS[k])
 lm=landmarks(refs,'CROSS_004');cross(refs,targets,lm,'CROSS');neg=load(R/'config/NEGATIVE_SPLIT.json');lm=landmarks(neg['reference_fit'],'NEGATIVE_004');cross(neg['reference_fit'],neg['target_fit'],lm,'NEGATIVE');save('provenance/FEATURE_FIT_FREEZE.json',dict(epoch=time.time(),all_image_ids=allids,HOLDOUT_images_used=False,GT=False,source=asset(Path(__file__)),landmarks=[asset(p)for p in(R/'landmarks').glob('*')]))
if __name__=='__main__':main()
