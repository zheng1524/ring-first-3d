from common2 import *
from real2 import triangulate,ring_prior
from solver2 import solve_methods
from support2 import classify_support
from ring_first_3d.sim.geometry import pose_error

def predict(group):
 out=RUN/'real'/group;asset=read(T/'config'/group/'ASSETS.json');verify(asset['files']);tf=read(out/'TRACK_FROZEN.json');assert sha(out/'tracks/observations/tracks005.npz')==tf['track_sha256'];assert sha(out/'FRAMES.json')==tf['frames_sha256'];assert sha(out/'CAMERAS.npz')==tf['camera_sha256'];frames=read(out/'FRAMES.json');poses=np.load(out/'CAMERAS.npz')['c2w'];tr=dict(np.load(out/'tracks/observations/tracks005.npz'));xyz,fit,details=triangulate(frames,poses,tr);prior=ring_prior(asset,frames,poses);save(out/'RING_PRIOR.json',prior);save(out/'TRIANGULATION.json',details);np.savez_compressed(out/'LANDMARKS.npz',xyz=xyz,fit=fit,held=tr['held'],category=tr['category']);raw,cleanmask=classify_support(group,frames,tr,xyz,fit)
 stage_freeze('PREDICT',out,[out/'RING_PRIOR.json',out/'LANDMARKS.npz',out/'SUPPORT_MASKS.npz',out/'CLEAN_INDEX.json']);results=solve_methods(xyz[fit,0],xyz[fit,1],prior)
 for name,mask in [('M4_raw_support',raw),('M4_clean_support',cleanmask)]:
  r=solve_methods(xyz[mask,0],xyz[mask,1],prior,methods=['M4'])['M4'];r['tracks']=int(mask.sum());r['same_coordinates_same_prior']=True;r['retained_track_ids']=np.flatnonzero(mask);results[name]=r
  if np.array_equal(mask,fit):
   a,b=r['T'],results['M4']['T'];assert (a is None and b is None)or np.array_equal(a,b)
 save(out/'PREDICTIONS.json',results);save(out/'PREDICTION_FREEZE.json',dict(predictions_sha256=sha(out/'PREDICTIONS.json'),inputs={str(p):sha(p)for p in [out/'LANDMARKS.npz',out/'RING_PRIOR.json',out/'SUPPORT_MASKS.npz',out/'FRAMES.json',out/'CAMERAS.npz',out/'tracks/observations/tracks005.npz',out/'CLEAN_INDEX.json']},source_receipt_sha256=sha(out/'PREDICT_START.json')))
 # Six fixed FIT sensitivity checks; held observations are masked out entirely.
 fittr=dict(tr);fittr['xy']=tr['xy'].copy();fittr['xy'][tr['held']]=np.nan;loo=[]
 for side in ['A','B']:
  indices=[i for i,f in enumerate(frames)if f['side']==side];drops=[indices[i]for i in np.unique(np.rint(np.linspace(0,len(indices)-1,CFG['LOO_per_side'])).astype(int))]
  for drop in drops:
   X,valid,_=triangulate(frames,poses,fittr,drop);ring=ring_prior(asset,frames,poses,drop);fitresult=solve_methods(X[valid,0],X[valid,1],ring,methods=['M4'])['M4'];entry=dict(drop_frame=drop,side=side,raw_frame=frames[drop]['raw_frame'],fit_tracks=int(valid.sum()),surviving_base_tracks=int((valid&fit).sum()),ring_status=ring['status'],result=fitresult)
   if fitresult['T']is not None and results['M4']['T']is not None:entry['delta_from_base']=pose_error(np.asarray(fitresult['T'])@np.linalg.inv(results['M4']['T']))
   loo.append(entry)
 save(out/'FIT_LOO.json',loo);print('REAL PREDICT',group,'fit',fit.sum(),'raw',raw.sum(),'clean',cleanmask.sum(),'ring',prior['status'],flush=True)
if __name__=='__main__':
 import traceback
 for row in read(T/'config/SELECTION.json')['groups']:
  try:predict(row['group'])
  except Exception as e:save(RUN/'real'/row['group']/'PREDICT_FAILURE.json',dict(error=repr(e),traceback=traceback.format_exc()));print('PREDICT FAILURE',row['group'],repr(e),flush=True)
