"""Bounded real RGB2D evidence/essential candidates; never claims reconstructed common XYZ."""
from qcommon import *
from photo_registration import K,Ke,ring_observation,ring_res,robust_res,pose_delta,curves
from features019 import match_desc,sampson
from scipy.optimize import least_squares
import collections

def fundamental(Ca,Cb,Ka):
 W=np.linalg.inv(Cb)@Ca;x,y,z=W[:3,3];S=np.array([[0,-z,y],[z,0,-x],[-y,x,0]]);return np.linalg.inv(K).T@S@W[:3,:3]@np.linalg.inv(Ka)
def main():
 selected=load(Q/'config/PHOTO_SOURCE_BANKS.json')['selected_FIT_video_views'];vv={v['id']:v for v in load(P/'config/VIEWS.json')};H=np.array(load(P/'results/B3.json')['T']);allsummary=[]
 for rec in load(Q/'config/PHOTO_ASSETS.json'):
  if rec['group']!='G01':continue
  cid=rec['id'];dest=Q/'results/photos'/cid;pf=np.load(Q/'photo_features'/(cid+'.npz'));rows=[];data=[];essential=[];C0=np.array(load(dest/'FINAL.json')['C']);radius=float(np.linalg.norm(C0[:3,3]));d=np.load(rec['cache']);ob=ring_observation(d)
  # Record the full Ring symmetry family rather than inventing a distinct underside observation.
  flip=np.eye(4);flip[:3,:3]=Rotation.from_euler('x',np.pi).as_matrix();qsave('results/photos/'+cid+'/RING_GAUGE_FAMILY.json',dict(raw_Ring_C=C0,opposite_normal_gauge_C=flip@C0,yaw='continuous UNOBSERVABLE Ring-only family; no 360degree search',cannot_claim_novel_observation_direction=True))
  for vid in selected:
   v=vv[vid];f=np.load(P/'features'/(vid+'.npz'));mm=match_desc(f['des'],pf['des']);p=f['xy'][mm[:,0]];u=pf['xy'][mm[:,1]];fit=mm[:,1]%5!=0;held=~fit;good=np.zeros(len(mm),bool);F=None
   if fit.sum()>=8:
    cv2.setRNGSeed(20261112);F,flag=cv2.findFundamentalMat(p[fit],u[fit],cv2.USAC_MAGSAC,1.5,.999,10000)
    if F is not None and F.shape==(3,3):good[np.flatnonzero(fit)[flag.ravel().astype(bool)]]=True
   C=np.asarray(v['T']);C=H@C if v['video']=='005'else C;status=dict(photo=cid,video_view=vid,video=v['video'],mutual_RGB_N=len(mm),PHOTO_FIT_N=int(fit.sum()),PHOTO_HELD_N=int(held.sum()),FIT_RGB_F_inlier_N=int(good.sum()),FIT_inlier_fraction=float(good.sum()/max(fit.sum(),1)),PHOTO_HELD_Sampson_px=stats(sampson(F,p[held],u[held]))if F is not None and F.shape==(3,3)else stats([]),source_RGB=v['RGB_source'],photo_original_RGB=rec['RGB']['path'],only_real2D_correspondence_no_XYZ_invented=True)
   np.savez_compressed(dest/(vid+'_2D_MATCHES.npz'),source_feature_id=mm[:,0],photo_feature_id=mm[:,1],source_uv=p,photo_uv=u,FIT=fit,HELD=held,FIT_F_inlier=good,F=F if F is not None else np.full((3,3),np.nan));rows.append(status)
   if good.sum()>=8:
    ids=np.flatnonzero(good);data.append(dict(view=vid,video=v['video'],C=C,K=np.asarray(v['K']),p=p[good],u=u[good],source_ids=mm[good,0],photo_ids=mm[good,1]))
    E,mask=cv2.findEssentialMat(p[good],u[good],K,method=cv2.RANSAC,prob=.999,threshold=1.5)
    if E is not None:
     E=E[:3];n,Rba,t,m=cv2.recoverPose(E,p[good],u[good],K,mask=mask);Cb=np.eye(4);Cb[:3,:3]=C[:3,:3]@Rba.T;direction=-Cb[:3,:3]@t.ravel();dot=float(C[:3,3]@direction);disc=dot*dot-(np.linalg.norm(C[:3,3])**2-radius**2)
     if disc>=0 and n>=8:
      for scale in [-dot-np.sqrt(disc),-dot+np.sqrt(disc)]:
       if scale<=.01:continue
       Cb[:3,3]=C[:3,3]+scale*direction;rr=ring_res(Cb,ob);essential.append(dict(source_view=vid,source_video=v['video'],C=Cb.copy(),positive_RGB2D_N=n,metric_baseline_from_Ring_distance_mm=float(scale),initial_Ring_mean_Huber=float(hubsum(rr)),not_2D3D=True,source_role='FIT_ONLY',type='Essential_rotation_translation_direction_plus_Ring_distance'))
   print('PHOTO_RGB2D',cid,vid,len(mm),int(good.sum()),flush=True)
  qsave('results/photos/'+cid+'/RGB2D_PER_VIEW_AUDIT.json',rows);qtable('metrics/'+cid+'_RGB2D_PER_VIEW_AUDIT.csv',rows);qsave('results/photos/'+cid+'/ESSENTIAL_RING_CANDIDATES.json',essential);qsave('results/photos/'+cid+'/RGB2D_OPTIMIZATION_OBSERVATIONS.json',data)
  # At most two image-only starts, ranked by FIT Ring score, no yaw scan or holdout/body/HERO.
  ranked=sorted(essential,key=lambda a:a['initial_Ring_mean_Huber']);starts=[]
  for e in ranked:
   if all(np.linalg.norm(np.asarray(e['C'])[:3,3]-np.asarray(a['C'])[:3,3])>.05 or np.degrees(Rotation.from_matrix(np.asarray(e['C'])[:3,:3]@np.asarray(a['C'])[:3,:3].T).magnitude())>.2 for a in starts):starts.append(e)
   if len(starts)==2:break
  native=np.load(Q/'inputs'/cid/'RING_NATIVE_EVIDENCE.npz');typed={name:(native[name]+.5)/3 for name in ['inner','outer']}
  counts=collections.Counter(a['video']for a in data);refined=[]
  for e in starts:
   seed=np.asarray(e['C'])
   def fun(q):
    Cb=pose_delta(q,seed);res=[robust_res(ring_res(Cb,ob))]
    cr=curves(Cb);areas=[abs(cv2.contourArea(x.astype(np.float32)))for x in cr];cc={'inner':cr[np.argmin(areas)],'outer':cr[np.argmax(areas)]}
    for name in ['inner','outer']:
     if len(typed[name]):res.append(robust_res(cKDTree(cc[name]).query(typed[name])[0],.05))
    for a in data:
     F=fundamental(a['C'],Cb,a['K']);dist=sampson(F,a['p'],a['u']);res.append(robust_res(dist,.2/len(counts)/counts[a['video']]))
    res.append(np.sqrt(2*.01/6)*q);return np.concatenate(res)
   result=least_squares(fun,np.zeros(6),bounds=(-2*np.ones(6),2*np.ones(6)),max_nfev=45,diff_step=1e-4,loss='linear',ftol=1e-7,gtol=1e-7,xtol=1e-7);r=fun(result.x);refined.append(dict(C=pose_delta(result.x,seed),initial_C=seed,q=result.x,fit_objective=float(r@r/2),nfev=result.nfev,solver_success=bool(result.success),source_essential=e,method='Ring + real2D Sampson only; NO 2D3D claim; weak seed prior retained',no_photoHELD_body_HERO_in_fit=True))
  qsave('results/photos/'+cid+'/RGB_EPI_POSE_CANDIDATES.json',refined);qsave('results/photos/'+cid+'/EPI_CANDIDATES_FROZEN.json',dict(epoch=time.time(),file=asset(dest/'RGB_EPI_POSE_CANDIDATES.json'),photoHELD=False));allsummary.append(dict(id=cid,RGB2D_pairs=len(rows),FIT_RGB_F_inliers=sum(a['FIT_RGB_F_inlier_N']for a in rows),PHOTO_HELD_pairs=sum(a['PHOTO_HELD_N']for a in rows),essential_metric_candidates=len(essential),refined_EPI_candidates=len(refined),original_landmark_PnP_results_unchanged=True));print('PHOTO_EPI_DONE',cid,len(essential),len(refined),flush=True)
 qsave('metrics/PHOTO_RGB2D_SUMMARY.json',allsummary);qtable('metrics/PHOTO_RGB2D_SUMMARY.csv',allsummary);qsave('runtime/PHOTO_EPI_ATTEMPTS_COMPLETE.json',dict(epoch=time.time()));print('PHOTO_EPI_ATTEMPTS_COMPLETE',flush=True)
def hubsum(r):return np.mean(np.where(abs(r/3)<=1,.5*(r/3)**2,abs(r/3)-.5))
if __name__=='__main__':main()
