"""Read-only HIST RGB adapter, independent two-sided DLT and FIT Ring uncertainty."""
from common2 import *
import cv2
from scipy.spatial import cKDTree
from ring_first_3d.sim.geometry import transform
from solver2 import ring_residual

def make_tracks(group):
 resource();asset=read(T/'config'/group/'ASSETS.json');verify(asset['files']);out=RUN/'real'/group;out.mkdir(parents=True,exist_ok=True);track=out/'tracks';assert not track.exists();(track/'observations').mkdir(parents=True)
 frames=[];poses=[];ba=[]
 for video in asset['videos']:
  cams=np.load(video['camera']);tr=np.load(Path(video['run'])/'observations/tracks005.npz')
  for j in video['pool']:
   row=video['frames'][j];frames.append(dict(row, id=video['side']+'__'+row['id'],side=video['side'],local_index=j,case=video['case'],K=cams['K']));poses.append(cams['c2w'][j]);ix=np.flatnonzero(np.isfinite(tr['xy'][:,j,0]));ba.append(dict(xy=tr['xy'][ix,j],ids=ix,held=tr['held'][ix]))
 config=dict(SIFT_features=CFG['features'],SIFT_ratio=CFG['ratio'],pair_offsets=list(range(1,len(frames))))
 ns=dict(np=np,cv2=cv2,Path=Path,R=track,cfg=lambda:config,ledger=lambda:frames,verify=lambda n:None,freeze=lambda n,p:None,image=lambda r:cv2.imread(r['RGB_path'])[:,:,::-1].copy(),labels=lambda r:cv2.imread(r['Mask_path'],0),save=lambda p,x:save(track/p,x))
 original(V6/'track005.py',['main'],ns)['main']();tr=np.load(track/'observations/tracks005.npz');flags=np.full(tr['xy'].shape[:2],-1,np.int8);oldids=np.full(flags.shape,-1,int)
 for j,b in enumerate(ba):
  valid=np.flatnonzero(np.isfinite(tr['xy'][:,j,0]));dist,ix=cKDTree(b['xy']).query(tr['xy'][valid,j]);good=dist<1e-4;flags[valid[good],j]=b['held'][ix[good]].astype(np.int8);oldids[valid[good],j]=b['ids'][ix[good]]
 np.savez_compressed(track/'BA_DEPENDENCIES.npz',original_held_by_observation=flags,original_video_local_track_id=oldids);np.savez_compressed(out/'CAMERAS.npz',c2w=poses);save(out/'FRAMES.json',frames);save(out/'TRACK_FROZEN.json',dict(track_sha256=sha(track/'observations/tracks005.npz'),frames_sha256=sha(out/'FRAMES.json'),camera_sha256=sha(out/'CAMERAS.npz'),protocol_sha256=sha(T/'config/PROTOCOL.json'),no_geometry_or_heldout_filter_in_matching=True));print('TRACK COMPLETE',group,len(tr['xy']),flush=True)

def triangulate(frames,poses,tr,omit=None):
 ns=original(V6/'v6_common.py',['triangle'],dict(np=np,K=np.array(frames[0]['K'])));xyz=np.full((len(tr['xy']),2,3),np.nan);fit=np.zeros(len(xyz),bool);records=[]
 for tid,xy in enumerate(tr['xy']):
  entry=dict(track=tid,held=bool(tr['held'][tid]),category=int(tr['category'][tid]),sides={});ok=True
  for sideind,side in enumerate(['A','B']):
   ix=np.array([i for i,r in enumerate(frames)if r['side']==side and i!=omit and np.isfinite(xy[i]).all()],int)
   rec=dict(observations=len(ix),frames=ix)
   if len(ix)<2:ok=False;rec['status']='LESS_THAN_2';entry['sides'][side]=rec;continue
   P=ns['triangle'](poses[ix],xy[ix],np.array(frames[ix[0]]['K']));xyz[tid,sideind]=P;cam=np.einsum('ni,nij->nj',P-poses[ix,:3,3],poses[ix,:3,:3]);q=cam@np.array(frames[ix[0]]['K']).T;uv=q[:,:2]/q[:,2:];errors=np.linalg.norm(uv-xy[ix],axis=1);rays=P-poses[ix,:3,3];rays/=np.maximum(1e-12,np.linalg.norm(rays,axis=1))[:,None];angle=float(np.rad2deg(np.arccos(np.clip((rays@rays.T).min(),-1,1))));valid=np.isfinite(P).all()and(cam[:,2]>0).all()and max(errors)<=CFG['fit_reprojection_max_px']and angle>=CFG['min_parallax_deg'];ok&=valid;rec.update(status='PASS'if valid else'GEOMETRY_FILTER_FOR_FIT_ONLY',max_px=float(max(errors)),median_px=float(np.median(errors)),parallax_deg=angle,negative_depth=int((cam[:,2]<=0).sum()));entry['sides'][side]=rec
  fit[tid]=ok and not tr['held'][tid];records.append(entry)
 return xyz,fit,records

def ring_prior(asset,frames,poses,omit=None):
 diagnostics=[];covs=[]
 for side in ['A','B']:
  video=next(v for v in asset['videos']if v['side']==side);cand=read(Path(video['run'])/'predictions/ring_candidates005.json');by={r['id']:r for r in cand};samples=[];chosen=[]
  for i,frame in enumerate(frames):
   if frame['side']!=side or i==omit:continue
   sourceid=frame['id'].split('__',1)[1];options=[]
   for j,c in enumerate(by[sourceid]['candidates']):
    if not c.get('numerical_success',c.get('optimizer_success',False)):continue
    center=transform(np.array(c['center'])[None],poses[i])[0];normal=poses[i,:3,:3]@np.array(c['normal']);normal=normal/np.linalg.norm(normal)
    if normal[2]<0:normal=-normal
    angle=np.arccos(np.clip(normal[2],-1,1));options.append((angle,float(c['loss']),j,center,normal))
   if not options:continue
   _,loss,j,c,n=min(options,key=lambda v:(v[0],v[1],v[2]));samples.append(ring_residual(np.eye(4),c,n));chosen.append(dict(frame=i,branch=j,training_loss=loss))
  X=np.array(samples);diag=dict(side=side,usable_frames=len(X),selected=chosen)
  if len(X)<3:diagnostics.append(diag);return dict(center=[0,0,0],normal=[0,0,1],covariance=None,status='INCONCLUSIVE_RING',diagnostics=diagnostics,radius_mm=video['ring_radius_mm'])
  mean=X.mean(0);cov=np.cov(X,rowvar=False)/len(X);ix=np.unique(np.rint(np.linspace(0,len(X)-1,min(3,len(X)))).astype(int));jack=np.array([np.delete(X,j,axis=0).mean(0)-mean for j in ix]);cov+=jack.T@jack/len(jack)
  # Do not interpret nominal zero Ring coordinates as absence of systematic error.
  # Conservative yaw-invariant blocks allow addition of A and B uncertainty.
  center_variance=float(np.linalg.eigvalsh(cov[:3,:3]).max())+CFG['ring_sigma_floor_mm']**2;normal_variance=float(np.linalg.eigvalsh(cov[3:,3:]).max())+np.deg2rad(CFG['ring_sigma_floor_deg'])**2;covs.append(np.diag([center_variance]*3+[normal_variance]*2));diag.update(sample_mean=mean,repeatability_covariance=cov,LOO_mean_changes=jack,systematic_floor_mm_deg=[CFG['ring_sigma_floor_mm'],CFG['ring_sigma_floor_deg']]);diagnostics.append(diag)
 C=covs[0]+covs[1];sig=np.sqrt(np.diag(C));ok=max(sig[:3])<=CFG['ring_max_sigma_mm']and max(sig[3:])<=np.deg2rad(CFG['ring_max_sigma_deg']);return dict(center=[0,0,0],normal=[0,0,1],covariance=C,status='ESTIMATED'if ok else'INCONCLUSIVE_RING',sigma=sig,diagnostics=diagnostics,radius_mm=asset['videos'][0]['ring_radius_mm'],A_uncertainty_included=True,does_not_exclude_systematic_bias=True)
