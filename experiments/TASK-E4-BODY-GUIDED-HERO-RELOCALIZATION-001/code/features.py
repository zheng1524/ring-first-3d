"""019 SIFT mutual-ratio mechanism; background only, split BEFORE RGB RANSAC."""
from geometry import *
CFG=load(R/'config/PROTOCOL.json')
def features(key,cache):
 out=R/'inputs'/'sift';out.mkdir(exist_ok=True);p=out/(key+'.npz')
 if p.exists():return dict(np.load(p))
 a=np.load(cache);rgb=a['RGB'];lab=a['labels'];gray=cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY);bg=cv2.dilate((lab!=0).astype(np.uint8),np.ones((5,5),np.uint8))==0;bg&=(gray>=12)&(gray<245);bg[:8]=False;bg[-8:]=False;bg[:,:8]=False;bg[:,-8:]=False;k,d=cv2.SIFT_create(nfeatures=CFG['sift_max_features'],contrastThreshold=.01).detectAndCompute(gray,bg.astype(np.uint8)*255);xy=np.array([x.pt for x in k],np.float64).reshape(-1,2);d=np.empty((0,128),np.float32)if d is None else d;np.savez_compressed(p,xy=xy,des=d,RGB_content_SHA256=hashlib.sha256(rgb.tobytes()).hexdigest(),labels_content_SHA256=hashlib.sha256(lab.tobytes()).hexdigest(),native_image_shape=lab.shape);return dict(np.load(p))
def match_desc(a,b):
 if min(len(a),len(b))<2:return np.empty((0,2),int)
 bf=cv2.BFMatcher();f=[m for pair in bf.knnMatch(a,b,k=2)if len(pair)==2 for m,n in[pair]if m.distance<CFG['sift_match_ratio']*n.distance];back={m.queryIdx:m.trainIdx for pair in bf.knnMatch(b,a,k=2)if len(pair)==2 for m,n in[pair]if m.distance<CFG['sift_match_ratio']*n.distance};return np.array([(m.queryIdx,m.trainIdx)for m in f if back.get(m.trainIdx)==m.queryIdx],int).reshape(-1,2)
def fundamental(C1,K1,C2,K2):
 H=np.linalg.inv(C2)@C1;x,y,z=H[:3,3];S=np.array([[0,-z,y],[z,0,-x],[-y,x,0.]]);return np.linalg.inv(K2).T@S@H[:3,:3]@np.linalg.inv(K1)
def sampson(F,p,q):
 a=np.c_[p,np.ones(len(p))];b=np.c_[q,np.ones(len(q))];Fa=a@F.T;Fb=b@F;return(b*Fa).sum(1)/np.sqrt(np.maximum((Fa[:,:2]**2).sum(1)+(Fb[:,:2]**2).sum(1),1e-20))

def prepare():
 refs={};receipts=[]
 for g in CFG['case_order']:
  meta=load(P/'inputs'/g/'CASE.json');refs[g]=[]
  for v in meta['views']:
   if v['role']!='FIT' or v['video']!='004':continue
   p=P/'inputs'/g/(v['id']+'.npz');a=np.load(p);key='REF__'+v['id'];refs[g].append(dict(id=v['id'],key=key,cache=str(p),C=a['T'],K=a['K'],RGB_content_SHA256=hashlib.sha256(a['RGB'].tobytes()).hexdigest()));features(key,p);receipts.append(dict(kind='SIFT_reference',**asset(p)))
 allrows=[];plan=[]
 for g in CFG['case_order']:
  for s in [a for a in load(R/'config/REAL_SOURCES.json')if a['group']==g]:
   fs=features(s['id'],s['view_cache']);records=[]
   for v in refs[g]:
    if s['view_id']==v['id']or s['RGB_content_SHA']==v['RGB_content_SHA256']:continue
    fr=features(v['key'],v['cache']);mm=match_desc(fs['des'],fr['des']);pp=fs['xy'][mm[:,0]];qq=fr['xy'][mm[:,1]];seed=int(hashlib.sha256((s['RGB_content_SHA']+'__'+v['RGB_content_SHA256']+'__'+str(CFG['seed'])).encode()).hexdigest()[:8],16);rng=np.random.default_rng(seed);indices=rng.permutation(len(mm));cut=int(len(mm)*CFG['sift_fit_fraction']);fit=indices[:cut];held=indices[cut:];good=np.zeros(len(fit),bool);F=None
    if len(fit)>=8:
     cv2.setRNGSeed(CFG['seed'])
     try:F,flag=cv2.findFundamentalMat(pp[fit],qq[fit],cv2.USAC_MAGSAC,CFG['sift_MAGSAC_px'],.999,10000)
     except cv2.error:F,flag=None,None
     if F is not None and F.shape==(3,3)and flag is not None:good=flag.ravel().astype(bool)
    fixed=fit[good];fixed=fixed[np.linspace(0,len(fixed)-1,min(CFG['sift_max_pair_points'],len(fixed)),dtype=int)]if len(fixed)else fixed;near_identical=len(fit)>0 and np.median(np.linalg.norm(pp[fit]-qq[fit],axis=1))<.75
    if near_identical:fixed=np.array([],int)
    path=R/'inputs/sift'/(s['id']+'__REF__'+v['id']+'_MATCH.npz');np.savez_compressed(path,index_pairs=mm,p=pp,q=qq,FIT_index=fixed,HOLDOUT_index=held,pre_RANSAC_fit_index=fit,RGB_RANSAC_fit=good,F=np.full((3,3),np.nan)if F is None else F,target_RGB_SHA=fs['RGB_content_SHA256'],ref_RGB_SHA=fr['RGB_content_SHA256']);fitpath=path.with_name(path.stem+'_FIT.npz');np.savez_compressed(fitpath,p=pp[fixed],q=qq[fixed],feature_pairs=mm[fixed]);rec=dict(source=s['id'],reference=v['id'],fit_match=str(fitpath),ref_C=v['C'],ref_K=v['K'],match=str(path),mutual_N=len(mm),FIT_N=len(fixed),HOLDOUT_N=len(held),near_identical_degenerate=bool(near_identical),feature_generation='real background OpenCV SIFT; no HERO depth/model-predicted matches');records.append(rec);allrows.append(dict(group=g,**rec))
   chosen=sorted(records,key=lambda a:(-a['FIT_N'],a['reference']))[:CFG['reference_cameras']];plan.append(dict(source=s['id'],group=g,references=chosen,FIT_N=sum(x['FIT_N']for x in chosen),HOLDOUT_N=sum(x['HOLDOUT_N']for x in chosen),selection='top3 FIT-only RGB-RANSAC counts, same image excluded, no HOLDOUT selection'));print('SIFT',s['id'],sum(x['FIT_N']for x in chosen),sum(x['HOLDOUT_N']for x in chosen),flush=True)
 save('config/BACKGROUND_REFERENCE_PLAN.json',plan);table('metrics/BACKGROUND_MATCH_INVENTORY.csv',allrows);save('provenance/SIFT_INPUTS.json',receipts);save('provenance/SIFT_SPLIT_FROZEN.json',dict(epoch=time.time(),plan=asset(R/'config/BACKGROUND_REFERENCE_PLAN.json'),sift_params={k:v for k,v in CFG.items()if k.startswith('sift')},HOLDOUT_used_for_identity_fitting=False,GT=False))
if __name__=='__main__':prepare()
