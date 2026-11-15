"""Original Ring-First 5DoF + RGB gauge resolution. Per-source failures retained."""
from context import *
from rgb import *
from torus import curves,nearest,correspondence,exp,S
from scipy.optimize import least_squares,minimize_scalar
import types,importlib
from matplotlib.path import Path as Polygon
RP=OLD/'experiments/ring_pose_contact_v1/scripts/recover.py';G5=OLD/'experiments/ring_first_v5_geometry_crossvideo/scripts/g5_common.py'
NS=extract(G5,['torus_residual'],dict(np=np,cv2=cv2,cKDTree=cKDTree,K=K0,contour_project=lambda C,n=256,K0=K0:torus_original(C[:3,3],C[:3,:3],K0,R=5.6,r=.6,n=n)))
def edge(m):
 y,x=np.nonzero(m[:,:-1]!=m[:,1:]);a=np.c_[x+.5,y];y,x=np.nonzero(m[:-1]!=m[1:]);return np.r_[a,np.c_[x,y+.5]]
def sample(a,n):return a[np.linspace(0,len(a)-1,min(n,len(a)),dtype=int)]if len(a)else a

def observe(v):
 path=N/'ring_evidence'/(v['id']+'.npz')
 if path.exists():return dict(np.load(path))
 a=np.load(v['cache']);lab=a['labels'];rgb=a['RGB'];rm=lab==2;pm=lab==1;bd=edge(rm);near=cv2.dilate(pm.astype(np.uint8),np.ones((5,5),np.uint8))>0;ix=np.clip(np.floor(bd+.5).astype(int),[0,0],[639,359]);unknown=near[ix[:,1],ix[:,0]];ob=dict(mask=rm,q_train=sample(bd[~unknown],128),unknown_boundary=bd[unknown]);roi=cv2.dilate(rm.astype(np.uint8),np.ones((17,17),np.uint8))>0
 for k,m in [('p',rm),('b',(lab==0)&roi)]:y,x=np.nonzero(m);ob[k+'_train']=sample(np.c_[x,y],192)
 try:
  if v['capture_type']=='INDEPENDENT_PHOTO':
   raw=np.load(Q/'inputs'/v['id']/'RING_NATIVE_EVIDENCE.npz');origin=next(p for p in load(Q/'config/PHOTO_ASSETS.json')if p['id']==v['id']);scale=np.array([origin['native_width']/640,origin['native_height']/360]);typed={k:(raw[k]+.5)/scale-.5 for k in ['inner','outer']}
  elif v.get('initial_canonical_id')and(U/'ring_evidence'/(v['initial_canonical_id']+'.npz')).exists():typed=dict(np.load(U/'ring_evidence'/(v['initial_canonical_id']+'.npz')))
  else:
   mod=types.ModuleType('dxy_mid');mod.__path__=[str(DXY/'src/dxy_mid')];sys.modules.setdefault('dxy_mid',mod);recover=importlib.import_module('dxy_mid._engine.ring_component').recover;report,payload=recover(lab,rgb[:,:,::-1],10.);typed={k:payload[k+'_points']for k in ['inner','outer']};save('ring_evidence/'+v['id']+'_DXY.json',report)
  for k in ['inner','outer']:
   p=np.asarray(typed[k]);dist,j=cKDTree(bd).query(p);q=bd[j[dist<=1.5]];ix=np.clip(np.floor(q+.5).astype(int),[0,0],[639,359]);ob[k+'_unknown']=q[near[ix[:,1],ix[:,0]]];ob[k]=sample(q[~near[ix[:,1],ix[:,0]]],96)
 except Exception as e:
  ob.update(inner=np.empty((0,2)),outer=np.empty((0,2)));save('ring_evidence/'+v['id']+'_TYPED_FAILURE.json',dict(error=repr(e),no_filled_or_extrapolated_arcs=True))
 np.savez_compressed(path,**ob);return ob

def rres(C,ob):return NS['torus_residual'](C,ob,K0=K0)
def score(C,ob,rr=None):
 r=rres(C,ob)/3.;n=abs(r);val=float(np.mean(np.where(n<=1,.5*n*n,n-.5)))if len(r)else 1e6
 if rr and rr['fit_pnp_inliers']:
  m=rr['fit_pnp_inliers'];uv,z=projection(np.array([x['X']for x in m]),C,K0);e=np.linalg.norm(uv-np.array([x['uv']for x in m]),axis=1)/3.;val+=.2*float(np.mean(np.where(e<=1,.5*e*e,e-.5)))+float(np.maximum(.1-z,0).mean())*100
 return val

def rf(v,ob,rr):
 ns=dict(np=np,cv2=cv2,Rotation=Rotation,cKDTree=cKDTree,least_squares=least_squares,K=K0,rad=5.6,tube=.6,cfg=dict(seed_depth_factors=[.85,1.,1.2],seed_inclinations_deg=[0,35,60],seed_azimuths_deg=[0,90,180,270],seed_retain=2,max_nfev=35,huber_px=1.,numerical_success_max_training_px=3.))
 extract(RP,['decode','image_seeds','solve'],ns)
 def res(a,ref,obs):
  c,Qr=ns['decode'](a,ref);C=np.eye(4);C[:3,:3]=Qr.T;C[:3,3]=-Qr.T@c;return rres(C,ob)
 ns['residual']=res;seeds=ns['image_seeds'](ob)
 for C in [rr['C'],v.get('initial_pose')]:
  if C is None:continue
  C=np.array(C);Qr=C[:3,:3].T;c=-Qr@C[:3,3];normal=Qr[:,2]
  if normal[2]<0:normal=-normal
  axis=np.cross([0,0,1],normal);rot=axis*np.arccos(np.clip(normal[2],-1,1))/max(np.linalg.norm(axis),1e-9)
  if c[2]>5:seeds.append(np.r_[c[:2]/c[2],np.log(c[2]),rot[:2]])
 result=ns['solve']([ob],np.eye(4),seeds);alts=[{k:v for k,v in result.items()if k not in ['alternatives','ambiguity_alternatives']}]+result['alternatives'];poses=[]
 for a in alts:
  C=np.eye(4);Qr=np.array(a['Q']);C[:3,:3]=Qr.T;C[:3,3]=-Qr.T@np.array(a['center']);poses.append(a|dict(C=C))
 return poses

def yaw_resolve(poses,rr,ob):
 out=[];flip=np.eye(4);flip[:3,:3]=Rotation.from_euler('x',np.pi).as_matrix()
 if not rr['fit_pnp_inliers']:return [(p['C'],score(np.array(p['C']),ob),dict(yaw='UNRESOLVED',normal=i))for i,p in enumerate(poses)]
 for i,p in enumerate(poses):
  for f in [False,True]:
   base=(flip if f else np.eye(4))@np.array(p['C'])
   def pose(a):H=np.eye(4);H[:3,:3]=Rotation.from_euler('z',a).as_matrix();return H@base
   grid=np.linspace(-np.pi,np.pi,72,endpoint=False);a=min(grid,key=lambda t:score(pose(t),ob,rr));fit=minimize_scalar(lambda t:score(pose(t),ob,rr),bounds=(a-np.pi/36,a+np.pi/36),method='bounded',options={'maxiter':20});C=pose(fit.x);out.append((C,score(C,ob,rr),dict(yaw_rad=fit.x,normal_branch=i,normal_flip=f)))
 return sorted(out,key=lambda x:x[1])

def physical(v,C,ob):
 cr=curves(C,K0,256);z=((cr['X'].reshape(-1,3)-C[:3,3])@C[:3,:3])[:,2];center=C[:3,3];sdf=np.hypot(np.linalg.norm(center[:2])-5.6,center[2])-.6;proper=np.linalg.det(C[:3,:3]);pred=np.zeros((360,640),np.uint8)
 for k,val in [('outer',1),('inner',0)]:cv2.fillPoly(pred,[np.rint(cr[k]).astype(np.int32)],val)
 lab=np.load(v['cache'])['labels'];known=lab!=1;pp=pred.astype(bool)&known;target=lab==2;d={k:stats(nearest(ob.get(k,np.empty((0,2))),cr[k])[2])for k in ['inner','outer']};d.update(Ring_IoU=int((pp&target).sum())/max(1,int((pp|target).sum())),minimum_depth_mm=float(z.min()),camera_torus_clearance_mm=float(sdf),proper_rotation=float(proper),coordinate_unit='mm',physical_valid=bool(z.min()>0 and sdf>.1 and abs(proper-1)<1e-6));return d

def one(v):
 path=N/'registration'/v['id']/'INITIAL.json'
 if path.exists():return load(path)
 if v['Mask_pending']:r=v|dict(status='MISSING_MASK',C=None);save(str(path.relative_to(N)),r);return r
 if v['role']=='HOLDOUT':
  # Do not build features / Ring objectives on protected image. Frozen camera for display/evaluation only.
  r=v|dict(C=v.get('initial_pose'),status='PROTECTED_HOLDOUT',HERO_target_eligible=False,formal=False);save(str(path.relative_to(N)),r);return r
 start=time.time();rr=pnp(v);save('inputs/'+v['id']+'/RGB_GEOMETRY.json',rr);ob=observe(v)
 if len(ob['q_train'])<20:r=v|dict(C=rr['C']if rr['C']is not None else v.get('initial_pose'),status='INSUFFICIENT_RING_OBSERVATION',formal=False,HERO_target_eligible=False)
 else:
  rings=rf(v,ob,rr);alts=yaw_resolve(rings,rr,ob);candidates=[dict(C=x[0],FIT_objective=x[1],branch=x[2],source='originalRF5DoF_RGB_yaw')for x in alts]
  for tag,C in [('REAL_RGB_PNP_LM',rr['C']),('HISTORICAL_FROZEN',v.get('initial_pose'))]:
   if C is not None:candidates.append(dict(C=C,FIT_objective=score(np.array(C),ob,rr),source=tag))
  save('registration/'+v['id']+'/RF_MULTISOLUTION.json',dict(ring_candidates=rings,full6_candidates=candidates))
  # Primary uses FIT only. Candidate 6D refinement is a separate later Ceres route.
  chosen=min(candidates,key=lambda c:c['FIT_objective']);C=np.array(chosen['C']);r=v|dict(C=C,status='NUMERIC_RGB_REGISTERED'if rr['C']is not None else'RING_ONLY_YAW_UNRESOLVED',candidate_source=chosen['source'],FIT_objective=chosen['FIT_objective'],Ring=physical(v,C,ob),original_ring5_N=len(rings),RGB_matches_N=len(rr['matches']),RGB_inliers_N=len(rr['fit_pnp_inliers']),formal=False,HERO_target_eligible=False)
 r['seconds']=time.time()-start;save(str(path.relative_to(N)),r);print('CAMERA_INITIAL',v['id'],r['status'],'RGB',len(rr['fit_pnp_inliers']),round(r['seconds'],2),flush=True);return r

def main(g):
 checkfreeze('provenance/SEGMENTED_INPUTS_FROZEN.json');vs=[v for v in load(N/'config/SEGMENTED_CANDIDATES.json')if v['group']==g];snapshot_read([Path(__file__),N/'code/rgb.py',RP,G5,N/'config/PROTOCOL.json',N/'config/NUMERICAL_PROTOCOL.json'],'CAMERA_CODE_'+g+'.json');out=[]
 for v in vs:
  try:r=one(v)
  except Exception as e:r=v|dict(C=None,status='RECOVERY_FAILED',formal=False,HERO_target_eligible=False,error=repr(e),traceback=traceback.format_exc());save('registration/'+v['id']+'/INITIAL.json',r);print('CAMERA_FAIL',v['id'],repr(e),flush=True)
  out.append(r)
 save('config/'+g+'_INITIAL_CAMERAS.json',out);print('GROUP_CAMERAS_DONE',g,len(out),flush=True)
if __name__=='__main__':main(sys.argv[1])
