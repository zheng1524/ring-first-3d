from context import *
from real2 import make_tracks,triangulate,ring_prior
from solver2 import solve_methods
from registration import pack_pairs,solve_m5,pair_residuals
from ring_first_3d.sim.geometry import pose_error
import traceback

def predict(group):
 out=RUN/'real'/group;asset=read(T/'config'/group/'ASSETS.json');verify(asset['files']);freeze('MATCH',out,[T/'config'/group/'ASSETS.json']);make_tracks(group)
 frames=read(out/'FRAMES.json');C=np.load(out/'CAMERAS.npz')['c2w'];tr=dict(np.load(out/'tracks/observations/tracks005.npz'));freeze('PREDICT',out,[out/'TRACK_FROZEN.json']);xyz,fit,details=triangulate(frames,C,tr);ring=ring_prior(asset,frames,C);save(out/'RING_PRIOR.json',ring);save(out/'TRIANGULATION.json',details);np.savez_compressed(out/'LANDMARKS.npz',xyz=xyz,fit=fit,held=tr['held'],category=tr['category']);p=pack_pairs(frames,C,tr,~tr['held']);save(out/'M5_FIT_DOMAIN.json',dict(track_ids=sorted(set(map(int,p['track_ids']))),pairs=len(p['xa']),M4_tracks=np.flatnonzero(fit),additional_2D_tracks=sorted(set(map(int,p['track_ids']))-set(np.flatnonzero(fit))),reason='M5 uses >=2 observations/side without rejecting by independent DLT; all observations and FIT split shared'))
 results=solve_methods(xyz[fit,0],xyz[fit,1],ring,methods=['M4']);results['M5']=solve_m5(p,ring,results['M4']['T']);save(out/'PREDICTIONS.json',results);save(out/'PREDICTION_FREEZE.json',dict(predictions_sha256=sha(out/'PREDICTIONS.json'),inputs={str(q):sha(q)for q in [out/'FRAMES.json',out/'CAMERAS.npz',out/'LANDMARKS.npz',out/'RING_PRIOR.json',out/'tracks/observations/tracks005.npz',out/'M5_FIT_DOMAIN.json']},source_receipt_sha256=sha(out/'PREDICT_START.json')));print('PREDICT',group,'M4 fit',fit.sum(),'M5 fit',p['tracks'],{m:r['quality']for m,r in results.items()},flush=True)
 # FIT-only sensitivity. No held pixels are available to this calculation.
 fittr=dict(tr);fittr['xy']=tr['xy'].copy();fittr['xy'][tr['held']]=np.nan;loo=[]
 for side in ['A','B']:
  ix=[i for i,f in enumerate(frames)if f['side']==side]
  for drop in [ix[i]for i in np.unique(np.rint(np.linspace(0,len(ix)-1,CFG['LOO_per_side'])).astype(int))]:
   X,valid,_=triangulate(frames,C,fittr,drop);prior=ring_prior(asset,frames,C,drop);m4=solve_methods(X[valid,0],X[valid,1],prior,methods=['M4'])['M4'];pairs=pack_pairs(frames,C,fittr,~tr['held'],drop);m5=solve_m5(pairs,prior,m4['T']);r=dict(side=side,drop_frame=drop,raw_frame=frames[drop]['raw_frame'],M4_fit=int(valid.sum()),M5_fit=pairs['tracks'],results={'M4':m4,'M5':m5},delta={})
   for name,rec in [('M4',m4),('M5',m5)]:
    if rec['T']is not None and results[name]['T']is not None:r['delta'][name]=pose_error(np.array(rec['T'])@np.linalg.inv(results[name]['T']))
   loo.append(r)
 save(out/'FIT_LOO.json',loo)
if __name__=='__main__':
 for row in read(T/'config/SELECTION.json')['groups']:
  try:predict(row['group'])
  except Exception as e:save(RUN/'real'/row['group']/'PREDICT_FAILURE.json',dict(error=repr(e),traceback=traceback.format_exc()));print('PREDICT FAILURE',row['group'],repr(e),flush=True)
