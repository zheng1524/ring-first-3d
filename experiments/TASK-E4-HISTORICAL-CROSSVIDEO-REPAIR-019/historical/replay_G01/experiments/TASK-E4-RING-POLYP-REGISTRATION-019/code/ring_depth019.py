"""Independent native Ring-depth bias diagnosis; never a main-registration input."""
from common import *
import open3d as o3d
P18=REPO/'experiments/TASK-E4-HERO-BODY-ADAPT-018'
def ellipse_band(shape,inner,outer):
 yy,xx=np.mgrid[:shape[0],:shape[1]];p=np.stack([xx,yy],-1)
 def inside(e):
  t=np.radians(e['angle_deg']);v=p-[e['cx'],e['cy']];a=v[...,0]*np.cos(t)+v[...,1]*np.sin(t);b=-v[...,0]*np.sin(t)+v[...,1]*np.cos(t);return(a/e['major_radius'])**2+(b/e['minor_radius'])**2<=1
 return inside(outer)&~inside(inner)
def main():
 assert(R/'provenance/POSE_PREDICTIONS_FROZEN_BEFORE_HOLDOUT.json').exists();rv=np.load(R/'inputs/G01/RING.npz');cad=scene(rv['V'],rv['F']);rows=[];views=load(R/'config/VIEWS.json');bias={}
 for v in views:
  cid=v['id'];root=P18/('hero_fit'if v['role']=='FIT'else'holdout/hero')/cid if v['video']=='004'else R/'hero_fit'/cid;p=root/'OBS_TRUSTED.npz';native=root/'HERO_native.npz'
  if not(p.exists()and native.exists()):
   extra=v.get('HERO_sources',[])
   if not extra:continue
   native=Path(extra[0])
   if not native.exists()or'depth_mm'not in np.load(native).files:continue
  z=np.load(native)['depth_mm'].astype(float)
  if p.exists():a=np.load(p);K,T=a['K'],a['T']
  else:
   K=np.asarray(v['K']).copy();A=np.diag([z.shape[1]/640,z.shape[0]/360,1.]);A[:2,2]=np.array([z.shape[1]/640,z.shape[0]/360])*.5-.5;K=A@K;T=np.asarray(v['T'])
  lab=cv2.resize(np.load(v['cache'])['labels'],(640,352),interpolation=cv2.INTER_NEAREST_EXACT);rgb=cv2.resize(np.load(v['cache'])['RGB'],(640,352),interpolation=cv2.INTER_AREA);gray=cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY).astype(np.float32);mu=cv2.blur(gray,(5,5));std=np.sqrt(np.maximum(cv2.blur(gray**2,(5,5))-mu**2,0));grad=np.hypot(cv2.Sobel(gray,cv2.CV_32F,1,0,ksize=3)/8,cv2.Sobel(gray,cv2.CV_32F,0,1,ksize=3)/8);orig=lab==2;ed=cv2.distanceTransform(orig.astype(np.uint8),cv2.DIST_L2,cv2.DIST_MASK_PRECISE);bandj=load(R/'ring'/(cid+'.json'));band=ellipse_band((360,640),bandj['inner'],bandj['outer']);band=cv2.resize(band.astype(np.uint8),(640,352),interpolation=cv2.INTER_NEAREST_EXACT)>0;dd=cast(cad,K,T,352,640);depth_valid=np.isfinite(z)&(z>0);photo=(ed>1.5)&band&(cv2.blur(orig.astype(np.float32),(5,5))>=.9)&(gray<245)&(std>=3)&(grad>=2)&(cv2.dilate((lab==1).astype(np.uint8),np.ones((3,3),np.uint8))==0);good=photo&np.isfinite(dd)&depth_valid;yy,xx=np.nonzero(good);ray=np.c_[xx,yy,np.ones(len(xx))]@np.linalg.inv(K).T;X=(ray*dd[yy,xx,None])@T[:3,:3].T+T[:3,3];sector=(np.floor(np.arctan2(X[:,1],X[:,0])/(2*np.pi)*8).astype(int)%8);res=z[good]-dd[good];sec=[dict(sector=s,N=int((sector==s).sum()),median_mm=float(np.median(res[sector==s])),MAD_mm=float(np.median(abs(res[sector==s]-np.median(res[sector==s])))))for s in np.unique(sector)if(sector==s).sum()>=8];med=float(np.median(res))if len(res)else None;MAD=float(np.median(abs(res-med)))if len(res)else None;even=sector%2==0;split=even.sum()>=16 and (~even).sum()>=16;fitb=float(np.median(res[even]))if split else None;held_before=float(abs(res[~even]).mean())if split else None;held_after=float(abs(res[~even]-fitb).mean())if split else None;spread=float(np.ptp([s['median_mm']for s in sec]))if len(sec)>1 else None;stable=bool(len(res)>=64 and len(sec)>=3 and spread is not None and spread<=.5 and MAD<=.25 and split and held_after<held_before)
  record=dict(view=cid,video=v['video'],role=v['role'],original_Ring_pixels=int(orig.sum()),native_Ring_valid_N=int((orig&depth_valid).sum()),native_Ring_valid_fraction=float((orig&depth_valid).sum()/max(1,orig.sum())),photometric_material_candidate_N=int(photo.sum()),reliable_N=len(res),median_bias_mm=med,MAD_mm=MAD,p95_abs_residual_mm=float(np.quantile(abs(res),.95))if len(res)else None,sectors=sec,sector_median_spread_mm=spread,disjoint_sector_fit_bias_mm=fitb,disjoint_Ring_before_MAE_mm=held_before,disjoint_Ring_after_MAE_mm=held_after,stable_source_bias_trial_allowed=stable,not_a_calibrated_depth_bias_truth=True,registration_use=False)
  rows.append(record);folder=R/'ring_depth';folder.mkdir(exist_ok=True);np.savez_compressed(folder/(cid+'.npz'),original_depth=z,CAD_first_axial_mm=dd,Ring=orig,selected=good,residual_mm=np.where(good,z-dd,np.nan),sector=sector,selected_uv=np.c_[xx,yy])
  if stable:
   trial=z-med;np.savez_compressed(folder/(cid+'_BIAS_TRIAL_NOT_ADOPTED.npz'),depth_mm=trial,bias_mm=med,K=K,T=T,original_native_SHA256=sha(native));bias[cid]=med
 save('metrics/RING_HERO_DEPTH_DIAGNOSTIC.json',dict(rows=rows,stable_trials=bias,original_depth_never_modified=True,HOLDOUT_after_freeze_only=True,not_main_optimization=True));table('metrics/RING_HERO_DEPTH_DIAGNOSTIC.csv',rows);print('RING_HERO_DEPTH_DIAGNOSIS_DONE',len(rows),'stable candidates',len(bias),flush=True)
if __name__=='__main__':main()
