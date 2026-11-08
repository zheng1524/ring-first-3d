"""New raw-frame poses from static-background RGB landmarks and mature PnP.
Frozen historical c2w remain immutable. No Polyp/HERO XYZ is used here.
"""
from common import *
import itertools,traceback
from scipy.spatial.transform import Rotation

def features(v):
 path=R/'runtime/features'/ (v['id']+'.npz');path.parent.mkdir(exist_ok=True)
 if path.exists():return dict(np.load(path))
 im=cv2.imread(v.get('RGB_source',v.get('RGB_path')));lab=cv2.imread(v.get('Mask_source',v.get('Mask_path')),0);gray=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
 ok=(cv2.dilate((lab!=0).astype(np.uint8),np.ones((7,7),np.uint8))==0)&(gray<245);ok[:8]=False;ok[-8:]=False;ok[:,:8]=False;ok[:,-8:]=False
 kp,de=cv2.SIFT_create(nfeatures=6000,contrastThreshold=.01).detectAndCompute(gray,ok.astype(np.uint8)*255)
 xy=np.array([k.pt for k in kp]).reshape(-1,2);de=np.empty((0,128),np.float32)if de is None else de
 np.savez_compressed(path,xy=xy,des=de);return dict(xy=xy,des=de)

def matches(a,b,ratio=.72):
 if min(len(a),len(b))<2:return np.empty((0,2),int)
 bf=cv2.BFMatcher();f=[x for mn in bf.knnMatch(a,b,k=2)if len(mn)==2 for x,y in [mn]if x.distance<ratio*y.distance];back={x.queryIdx:x.trainIdx for mn in bf.knnMatch(b,a,k=2)if len(mn)==2 for x,y in [mn]if x.distance<ratio*y.distance}
 return np.array([(m.queryIdx,m.trainIdx)for m in f if back.get(m.trainIdx)==m.queryIdx],int).reshape(-1,2)

def project(X,T,K):
 cam=(X-np.asarray(T)[:3,3])@np.asarray(T)[:3,:3];z=cam[:,2];uv=cam@np.asarray(K).T;return uv[:,:2]/uv[:,2:],z

def landmarks(vv):
 Xs=[];Ds=[];origin=[];pairrows=[]
 # All archived posed observations are eligible. Distributed pairs limit duplicate descriptors.
 pairs=list(itertools.combinations(range(len(vv)),2));pairs=sorted(pairs,key=lambda ij:abs(ij[0]-ij[1]));pairs=pairs[:len(vv)*6]
 for i,j in pairs:
  a,b=vv[i],vv[j];fa,fb=features(a),features(b);mm=matches(fa['des'],fb['des']);rec=dict(first=a['id'],second=b['id'],BG_matches=len(mm),valid_triangulated=0)
  if len(mm)<6:pairrows.append(rec);continue
  Ta,Tb=np.asarray(a['T']),np.asarray(b['T']);Ka,Kb=np.asarray(a['K']),np.asarray(b['K']);pa,pb=fa['xy'][mm[:,0]],fb['xy'][mm[:,1]]
  Y=cv2.triangulatePoints(Ka@np.linalg.inv(Ta)[:3],Kb@np.linalg.inv(Tb)[:3],pa.T,pb.T);X=(Y[:3]/Y[3]).T;ua,za=project(X,Ta,Ka);ub,zb=project(X,Tb,Kb)
  da=X-Ta[:3,3];db=X-Tb[:3,3];cos=(da*db).sum(1)/(np.linalg.norm(da,axis=1)*np.linalg.norm(db,axis=1));ang=np.degrees(np.arccos(np.clip(cos,-1,1)));good=np.isfinite(X).all(1)&(za>0)&(zb>0)&(np.linalg.norm(ua-pa,axis=1)<2)&(np.linalg.norm(ub-pb,axis=1)<2)&(ang>.5)&(np.linalg.norm(X,axis=1)<300)
  ids=np.flatnonzero(good);rec['valid_triangulated']=len(ids);pairrows.append(rec)
  if len(ids):Xs.append(X[ids]);Ds.append(fa['des'][mm[ids,0]]);origin.extend([(a['id'],b['id'])for k in ids])
 if not Xs:return dict(X=np.empty((0,3)),des=np.empty((0,128),np.float32),origin=np.empty((0,2),str)),pairrows
 X=np.concatenate(Xs);des=np.concatenate(Ds);origin=np.array(origin);_,idx=np.unique(des,axis=0,return_index=True);idx=np.sort(idx)
 return dict(X=X[idx],des=des[idx],origin=origin[idx]),pairrows

def pnp(v,lm,K):
 f=features(v);mm=matches(lm['des'],f['des']);rec=dict(BG_descriptor_matches=len(mm),success=False)
 if len(mm)<6:return None,dict(rec,reason='INSUFFICIENT_REAL_BG_MATCHES')
 X=lm['X'][mm[:,0]];uv=f['xy'][mm[:,1]];cv2.setRNGSeed(20261108)
 ok,rv,tv,inl=cv2.solvePnPRansac(X,uv,K,None,iterationsCount=1000,reprojectionError=3.,confidence=.999,flags=cv2.SOLVEPNP_EPNP)
 if not ok or inl is None or len(inl)<6:return None,dict(rec,reason='BACKGROUND_PNP_RANSAC_NO_FINITE_SIX_POINT_SOLUTION')
 idx=inl.ravel();rv,tv=cv2.solvePnPRefineLM(X[idx],uv[idx],K,None,rv,tv);rr=cv2.Rodrigues(rv)[0];T=np.eye(4);T[:3,:3]=rr.T;T[:3,3]=-rr.T@tv.ravel();pu,z=project(X[idx],T,K);err=np.linalg.norm(pu-uv[idx],axis=1);cells=np.unique((uv[idx]//[80,60]).astype(int),axis=0)
 if not np.isfinite(T).all()or np.linalg.det(rr)<.999 or (z>0).mean()<.8:return None,dict(rec,reason='MATHEMATICALLY_INVALID_PNP')
 rec.update(success=True,inliers=len(idx),BG_reprojection_px=stats(err),image_cells=len(cells),camera_distance_mm=float(np.linalg.norm(T[:3,3])),source='static-background SIFT triangulated with frozen archival cameras; OpenCV EPnP RANSAC+LM; no HERO',qualification='CONDITIONAL_RESEARCH_CAMERA_NOT_GT')
 return T,rec

def main():
 existing=load(R/'config/EXISTING_VIEWS.json');allout=[];fail=[];pairrows=[];runs=[]
 for case in load(R/'config/CASE_LOCK.json'):
  n=case['name'];vold=[v for v in existing if v['case']==n];lms={}
  for sid in sorted({v['sid']for v in vold}):
   p=R/'runtime'/ (sid+'_BG_LANDMARKS.npz')
   if p.exists():lm=dict(np.load(p))
   else:lm,pp=landmarks([v for v in vold if v['sid']==sid]);pairrows+=pp;np.savez_compressed(p,**lm)
   lms[sid]=lm;print('BG_LANDMARKS',sid,len(lm['X']),flush=True)
  aa=[a for a in load(R/'config/RAW_ASSETS.json')if a['case']==n and a['type']=='video']
  for a in aa:
   p=R/'new_views'/a['sid']/'inputs/ledger_all.json'
   while not p.exists():
    if (R/'provenance/PREPARED_VIEWS_FREEZE.json').exists():break
    time.sleep(5)
   if not p.exists():fail.append(dict(sid=a['sid'],reason='PREPARATION_NOT_AVAILABLE'));continue
   vv=load(p);sid=a['sid'];lm=lms.get(sid,lms[sorted(lms)[0]]);K=np.array(vold[0]['K']);derived=[]
   for v in vv:
    target=R/'inputs'/n/(v['id']+'.npz');recordp=R/'new_views'/sid/'predictions'/(v['id']+'_CAMERA.json')
    if recordp.exists():rec=load(recordp);runs.append(rec);derived+=rec.get('view',[]);continue
    try:
     alias=next((x for x in vold if x['id']in v['exact_existing_aliases']),None)
     if alias is not None:T=np.array(alias['T']);rec=dict(success=True,source='EXACT_PIXEL_ARCHIVAL_CAMERA',qualification=alias['qualification'])
     else:T,rec=pnp(v,lm,K)
     if T is not None:
      out=dict(v,RGB_sha=v['RGB_SHA256'],Mask_sha=v['Mask_SHA256'],K=K,T=T,available_camera=True,original013=False,HERO_sources=[],aliases=[v['id']],qualification=rec['qualification'],pose_source=str(recordp),admission='INPUT_INTEGRITY_ONLY',is_photo=False)
      # Exact archived HOLDOUT never re-enters FIT under a new ID.
      if alias is not None and alias['role']!='FIT':out['role']=alias['role']
      np.savez_compressed(target,RGB=np.array(Image.open(v['RGB_path']).convert('RGB')),labels=np.array(Image.open(v['Mask_path'])),K=K,T=T);derived.append(out);rec['view']=[out]
     else:fail.append(dict(case=n,id=v['id'],sid=sid,reason=rec['reason']))
     rec.update(case=n,id=v['id'],sid=sid);save(recordp.relative_to(R),rec);runs.append(rec)
    except Exception:fail.append(dict(case=n,id=v['id'],reason='CAMERA_EXCEPTION',traceback=traceback.format_exc()));print(fail[-1],flush=True)
   allout+=derived;save('config/DERIVED_VIEWS.json',allout);save('metrics/CAMERA_EXPANSION_RUNS.json',runs);table('metrics/CAMERA_EXPANSION_FAILURES.csv',fail);table('metrics/BG_TRIANGULATION_PAIRS.csv',pairrows);print('VIDEO_CAMERAS',sid,len(derived),len(vv),flush=True)
 save('provenance/CAMERA_EXPANSION_FREEZE.json',dict(epoch=time.time(),code=asset(Path(__file__)),views=asset(R/'config/DERIVED_VIEWS.json'),GT_used=False,HERO_Polyp_used=False));print('CAMERA_EXPANSION_DONE',len(allout),flush=True)
if __name__=='__main__':main()
