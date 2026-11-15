"""Frozen real RGB identities and map-held PnP. No nearest-XYZ links."""
from context import *
BF=cv2.BFMatcher(cv2.NORM_L2)
def features(v):
 p=N/'features'/(v['id']+'.npz')
 if not p.exists():
  d=np.load(v['cache']);rgb=d['RGB'];lab=d['labels'];s=cv2.SIFT_create(nfeatures=6000,contrastThreshold=.01);k,des=s.detectAndCompute(cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY),None);xy=np.array([q.pt for q in k],float).reshape(-1,2);des=np.empty((0,128),np.float32)if des is None else des;pix=np.clip(np.rint(xy).astype(int),[0,0],[639,359]);region=lab[pix[:,1],pix[:,0]];np.savez_compressed(p,xy=xy,des=des,region=region,RGB_content_SHA256=hashlib.sha256(rgb.tobytes()).hexdigest())
 return dict(np.load(p))
def mutual(a,b):
 if len(a)<2 or len(b)<2:return []
 ab={m.queryIdx:m for m,n in BF.knnMatch(np.asarray(a,np.float32),np.asarray(b,np.float32),k=2)if m.distance<.72*n.distance};ba={m.queryIdx:m.trainIdx for m,n in BF.knnMatch(np.asarray(b,np.float32),np.asarray(a,np.float32),k=2)if m.distance<.72*n.distance};return [(i,m.trainIdx,float(m.distance))for i,m in ab.items()if ba.get(m.trainIdx)==i]
def rgb_map(g):
 a=dict(np.load(G/'landmarks'/(g+'_004.npz')));obs=load(G/'landmarks'/(g+'_004_OBSERVATIONS.json'));a['obs']=obs;return a

def pnp(v):
 f=features(v);m=rgb_map(v['group']);pairs=mutual(m['des'],f['des']);rows=[dict(landmark=k,feature=j,distance=d,X=m['X'][k],uv=f['xy'][j],region=int(f['region'][j]),role='FEATURE_HELD'if k%5==0 else'FIT')for k,j,d in pairs];fit=[r for r in rows if r['role']=='FIT'];C=None;inrows=[]
 if len(fit)>=6:
  X=np.array([r['X']for r in fit]);uv=np.array([r['uv']for r in fit]);cv2.setRNGSeed(20261115);ok,r,t,ids=cv2.solvePnPRansac(X,uv,np.array(v['K']),None,iterationsCount=1000,reprojectionError=3.,confidence=.999,flags=cv2.SOLVEPNP_EPNP)
  if ok and ids is not None and len(ids)>=6:
   ii=ids.ravel();r,t=cv2.solvePnPRefineLM(X[ii],uv[ii],np.array(v['K']),None,r,t);W=np.eye(4);W[:3,:3]=cv2.Rodrigues(r)[0];W[:3,3]=t.ravel();C=np.linalg.inv(W);inrows=[fit[j]for j in ii]
 return dict(matches=rows,fit_pnp_inliers=inrows,C=C,map_source=asset(G/'landmarks'/(v['group']+'_004.npz')),map_ancestry='historical004RGBtriangulation; canonical calibration may inherit old HOLDOUT; newmatchesIDmod5held neverfit; all candidates share same map',features_N=len(f['xy']))
def errors(v,C,rr):
 out={}
 for role in ['FIT','FEATURE_HELD']:
  rs=rr['fit_pnp_inliers']if role=='FIT'else[r for r in rr['matches']if r['role']==role]
  if rs:
   X=np.array([r['X']for r in rs]);uv,z=projection(X,C,np.array(v['K']));out[role]=stats(np.linalg.norm(uv-np.array([r['uv']for r in rs]),axis=1));out[role+'_positive_fraction']=float((z>0).mean());out[role+'_cells']=len(set((int(r['uv'][0]//80),int(r['uv'][1]//60))for r in rs))
  else:out[role]=stats([]);out[role+'_cells']=0
 return out
