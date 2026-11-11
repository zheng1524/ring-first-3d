"""Independent Ring-First photo poses + existing RGB landmark tracks. No copied frame pose."""
from qcommon import *
from features019 import match_desc
from scipy.optimize import least_squares
import ast,collections
from matplotlib.path import Path as Poly
RP=Path('/home/liu/polyp_research/ring_anchor_3d/experiments/ring_pose_contact_v1/scripts/recover.py')
TORUS=Path('/home/liu/polyp_research/ring_anchor_3d/experiments/ring_pose_contact_v1/scripts/torus_geometry.py')
def extract(path,names,ns):
 for n in ast.parse(path.read_text()).body:
  if isinstance(n,ast.FunctionDef)and n.name in names:exec(compile(ast.Module(body=[n],type_ignores=[]),str(path),'exec'),ns)
 return ns
GN=extract(TORUS,['torus_contours'],dict(np=np));torus=GN['torus_contours']
K=np.array([[490.,0,319.5],[0,490.,179.5],[0,0,1.]]);Ke=K.copy();Ke[:2,2]+=.5;SCALE=np.r_[np.full(3,.6),np.full(3,np.deg2rad(5))]
def curves(C):return torus(C[:3,3],C[:3,:3],Ke,R=5.6,r=.6,n=256)
def project(P,C):
 p=(P-C[:3,3])@C[:3,:3];uv=p@K.T;return uv[:,:2]/uv[:,2:],p[:,2]
def pose_delta(q,C):
 H=np.eye(4);H[:3,:3]=Rotation.from_rotvec(q[3:]*SCALE[3:]).as_matrix();H[:3,3]=q[:3]*SCALE[:3];return H@C

def ring_observation(d):
 lab=d['labels'];p=lab==1;r=lab==2;ys,xs=np.nonzero(r);q=contour(r);near=cv2.distanceTransform((~p).astype(np.uint8),cv2.DIST_L2,cv2.DIST_MASK_PRECISE);qi=np.rint(q).astype(int);q=q[near[qi[:,1],qi[:,0]]>1.];q=q[np.linspace(0,len(q)-1,min(256,len(q)),dtype=int)]+.5;roi=np.zeros_like(r);roi[max(0,ys.min()-20):min(360,ys.max()+21),max(0,xs.min()-20):min(640,xs.max()+21)]=True
 out=dict(mask=r,q_train=q)
 for key,m in [('p',r),('b',(lab==0)&roi)]:
  y,x=np.nonzero(m);p=np.c_[x,y]+.5;out[key+'_train']=p[np.linspace(0,len(p)-1,min(640,len(p)),dtype=int)]
 return out
G5=Path('/home/liu/polyp_research/ring_anchor_3d/experiments/ring_first_v5_geometry_crossvideo/scripts/g5_common.py')
NS=extract(G5,['torus_residual'],dict(np=np,cv2=cv2,cKDTree=cKDTree,K=Ke,contour_project=lambda p,n=256,K0=Ke:torus(p[:3,3],p[:3,:3],K0,R=5.6,r=.6,n=n)))
def ring_res(C,ob):return NS['torus_residual'](C,ob,K0=Ke)
def hub(x):return np.where(abs(x)<=1,.5*x*x,abs(x)-.5)
def robust_res(r,weight=1.):return np.sqrt(2*hub(np.asarray(r)/3)*weight/max(1,len(r)))
def ring_initial(ob,cid):
 ns=dict(np=np,cv2=cv2,Rotation=Rotation,cKDTree=cKDTree,least_squares=least_squares,K=Ke,rad=5.6,tube=.6,cfg=dict(seed_depth_factors=[.85,1.,1.2],seed_inclinations_deg=[0,35,60],seed_azimuths_deg=[0,90,180,270],seed_retain=4,max_nfev=45,huber_px=1.,numerical_success_max_training_px=3.))
 extract(RP,['decode','image_seeds','solve'],ns)
 def res(a,ref,observations):
  center,Qr=ns['decode'](a,ref);C=np.eye(4);C[:3,:3]=Qr.T;C[:3,3]=-Qr.T@center;return ring_res(C,ob)
 ns['residual']=res;seeds=ns['image_seeds'](ob);result=ns['solve']([ob],np.eye(4),seeds);allc=[{k:v for k,v in result.items()if k not in ['alternatives','ambiguity_alternatives']}]+result['alternatives'];poses=[]
 for a in allc:
  C=np.eye(4);Qr=np.array(a['Q']);C[:3,:3]=Qr.T;C[:3,3]=-Qr.T@np.array(a['center']);poses.append(a|dict(C=C,Ring_yaw_unobservable=True,not_a_full6DoF_certificate=True))
 qsave('results/photos/'+cid+'/RING_ONLY_CANDIDATES.json',poses);return poses

def source_banks():
 views=load(P/'config/VIEWS.json');selected=[v['id']for v in views if v['video']=='004'and v['role']=='FIT']
 for block in sorted({v['direction_block019']for v in views if v['video']=='005'and v['role']=='FIT'}):
  vv=[v for v in views if v['video']=='005'and v['role']=='FIT'and v['direction_block019']==block];selected.extend([vv[0]['id'],vv[-1]['id']])
 banks=[];H=np.array(load(P/'results/B3.json')['T'])
 for video,label in [('004','CROSS_004'),('005','INDEPENDENT_005')]:
  lm=np.load(P/'landmarks'/(label+'.npz'));obs=load(P/'landmarks'/(label+'_OBSERVATIONS.json'));by=collections.defaultdict(list)
  for k,t in enumerate(obs):
   for o in t['observations']:
    if o['view']in selected:by[o['view']].append((k,o))
  for vid,oo in by.items():
   f=np.load(P/'features'/(vid+'.npz'));idx=np.array([o['feature_id']for k,o in oo]);ids=np.array([k for k,o in oo]);X=lm['X'][ids];X=X@H[:3,:3].T+H[:3,3]if video=='005'else X;banks.append(dict(view=vid,video=video,feature_id=idx,landmark_id=ids,des=f['des'][idx],uv=f['xy'][idx],X=X))
 qsave('config/PHOTO_SOURCE_BANKS.json',dict(selected_FIT_video_views=selected,source_landmarks004=153,source_landmarks005=980,video005_to004=asset(P/'results/B3.json'),selection='all8 original004FIT + first/last existing005FIT per frozen direction block, no photo/holdout/GT ranking',no_new_video_SIFT=True));return banks

def one(rec,banks):
 cid=rec['id'];root=Q/'results/photos'/cid
 if(root/'FINAL.json').exists():return load(root/'FINAL.json')
 root.mkdir(parents=True,exist_ok=True);d=np.load(rec['cache']);rgb=d['RGB'];lab=d['labels'];gray=cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY);mask=(cv2.dilate((lab==2).astype(np.uint8),np.ones((5,5),np.uint8))==0)&(gray>=12)&(gray<245);mask[:8]=False;mask[-8:]=False;mask[:,:8]=False;mask[:,-8:]=False;key,des=cv2.SIFT_create(nfeatures=6000,contrastThreshold=.01).detectAndCompute(gray,mask.astype(np.uint8)*255);xy=np.array([k.pt for k in key]).reshape(-1,2);des=np.empty((0,128),np.float32)if des is None else des;(Q/'photo_features').mkdir(exist_ok=True);np.savez_compressed(Q/'photo_features'/(cid+'.npz'),xy=xy,des=des,RGB_SHA256=rec['RGB']['sha256']);ob=ring_observation(d);ring=ring_initial(ob,cid);matches={}
 for b in banks:
  mm=match_desc(b['des'],des)
  for a,j in mm:
   ident=(b['video'],int(b['landmark_id'][a]),int(j));m=matches.setdefault(ident,dict(video=b['video'],landmark_id=int(b['landmark_id'][a]),photo_feature_id=int(j),photo_uv=xy[j],photo_native_uv=(xy[j]+.5)*3-.5,XYZ004_mm=b['X'][a],support_RGB_views=[],descriptor_L2=float(np.linalg.norm(b['des'][a]-des[j])),role='PHOTO_HELD'if int(j)%5==0 else'PHOTO_FIT'));m['support_RGB_views'].append(dict(view=b['view'],feature_id=int(b['feature_id'][a]),uv=b['uv'][a]))
 # Resolve conflicting descriptor-only assignments within each video without spatial-nearest identity.
 grouped=collections.defaultdict(list)
 for m in matches.values():grouped[m['video'],m['photo_feature_id']].append(m)
 allmatches=[];conflicts=[]
 for key,vals in grouped.items():
  vals.sort(key=lambda x:(-len(x['support_RGB_views']),x['descriptor_L2']));allmatches.append(vals[0]);conflicts.extend(v|dict(reason='descriptor-only alternate identity, not fit')for v in vals[1:])
 qsave('results/photos/'+cid+'/ALL_RGB_LANDMARK_MATCHES.json',allmatches);qsave('results/photos/'+cid+'/ALTERNATE_RGB_IDENTITIES.json',conflicts);pnps=[];fit=[]
 for video in ['004','005']:
  ms=[m for m in allmatches if m['video']==video and m['role']=='PHOTO_FIT'];r=dict(video=video,matches_N=len(ms),success=False)
  if len(ms)>=6:
   X=np.array([m['XYZ004_mm']for m in ms]);uv=np.array([m['photo_uv']for m in ms]);cv2.setRNGSeed(20261112);ok,rot,t,inl=cv2.solvePnPRansac(X,uv,K,None,iterationsCount=1000,reprojectionError=3.,confidence=.999,flags=cv2.SOLVEPNP_EPNP)
   if ok and inl is not None and len(inl)>=6:
    ii=inl.ravel();rot,t=cv2.solvePnPRefineLM(X[ii],uv[ii],K,None,rot,t);rr=cv2.Rodrigues(rot)[0];C=np.eye(4);C[:3,:3]=rr.T;C[:3,3]=-rr.T@t.ravel();r.update(success=True,C=C,inliers_N=len(ii),inlier_photo_feature_ids=[ms[k]['photo_feature_id']for k in ii]);fit.extend(ms[k]for k in ii)
  pnps.append(r)
 qsave('results/photos/'+cid+'/PNP_RAW_CANDIDATES.json',pnps);candidates=[]
 # Photo pose objective is mature V5 Mask-region/contour + typed visible arcs + same RGB track points.
 # Original021 BA objective is NOT replaced; these are separate independent-photo variables.
 native=np.load(Q/'inputs'/cid/'RING_NATIVE_EVIDENCE.npz');typed={}
 for name in ['inner','outer']:
  p=native[name];p=(p+.5)/3;typed[name]=p[np.linspace(0,len(p)-1,min(256,len(p)),dtype=int)]if len(p)else p
 counts=collections.Counter(m['video']for m in fit);videos=len(counts)
 def loss(q,seed):
  C=pose_delta(q,seed);parts=[robust_res(ring_res(C,ob))];cr=curves(C);areas=[abs(cv2.contourArea(c.astype(np.float32)))for c in cr];curve={'outer':cr[np.argmax(areas)],'inner':cr[np.argmin(areas)]}
  for name in ['inner','outer']:
   if len(typed[name]):parts.append(robust_res(cKDTree(curve[name]).query(typed[name])[0],.05))
  for video in counts:
   mm=[m for m in fit if m['video']==video];uv,z=project(np.array([m['XYZ004_mm']for m in mm]),C);err=np.linalg.norm(uv-np.array([m['photo_uv']for m in mm]),axis=1);parts.append(robust_res(err,.2/videos));parts.append(np.maximum(0,.1-z)*10/np.sqrt(len(z)))
  parts.append(np.sqrt(2*.01/6)*q);return np.concatenate(parts)
 for init in [p for p in pnps if p['success']]:
  seed=np.array(init['C']);fun=lambda q:loss(q,seed);z=least_squares(fun,np.zeros(6),bounds=(-2*np.ones(6),2*np.ones(6)),max_nfev=60,diff_step=1e-4,loss='linear',ftol=1e-7,gtol=1e-7,xtol=1e-7);C=pose_delta(z.x,seed);v=fun(z.x);candidates.append(dict(seed_video=init['video'],C=C,q=z.x,fit_objective=float(v@v/2),nfev=z.nfev,optimizer_success=bool(z.success),raw_PnP_C=seed,photo_relative_pose_inherited=False,shared_world='004 Ring-First;005 landmarks transformed by frozen021 B3',pose_prior_center='independent RGB PnP candidate, not a video camera'))
 if candidates:primary=min(candidates,key=lambda a:a['fit_objective']);C=np.array(primary['C']);posekind='RING_RGB_PNP_REFINED_CONDITIONAL'
 else:primary=None;C=np.array(ring[0]['C']);posekind='RING_ONLY_YAW_UNRESOLVED_NOT_METRIC_SUPERVISION'
 # Freeze BEFORE any photo-held/body/HERO diagnostics.
 result=dict(id=cid,capture_type='INDEPENDENT_PHOTO',C=C,primary=primary,candidates=candidates,Ring_only_candidates_path=str(root/'RING_ONLY_CANDIDATES.json'),pose_status=posekind,matching_N=len(allmatches),FIT_PnP_inlier_N=len(fit),PHOTO_HELD_MATCHES_N=sum(m['role']=='PHOTO_HELD'for m in allmatches),pose_unique_certified=False,intrinsics_status=rec['K_status'],no_body_HERO_GT_used=True,no_HOLDOUT_in_fit=True,source=asset(Path(__file__)),camera_was_not_copied_from_video=True)
 qsave('results/photos/'+cid+'/FINAL.json',result);qsave('results/photos/'+cid+'/PREDICTION_FROZEN.json',dict(epoch=time.time(),files=[asset(root/'FINAL.json')],photo_held=False,body=False,HERO=False));print('PHOTO_POSE_FROZEN',cid,posekind,'matched',len(allmatches),'FIT inliers',len(fit),flush=True);return result

def main():
 banks=source_banks();records=[]
 for rec in load(Q/'config/PHOTO_ASSETS.json'):
  if rec['group']=='G01':records.append(one(rec,banks))
 qsave('config/G01_PHOTO_POSES.json',records);qsave('runtime/PHOTO_POSES_COMPLETE.json',dict(epoch=time.time(),count=len(records)));print('PHOTO_POSES_COMPLETE',flush=True)
if __name__=='__main__':main()
