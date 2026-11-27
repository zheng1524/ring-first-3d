from context import *
from metrics2 import bidirectional,ring_pixels,summarize
from evaluate_real2 import load_geometry,geometric
from registration import pack_pairs,pair_residuals
from ring_first_3d.sim.geometry import transform,pose_error,se3,parameters
import traceback

def evaluate(group):
 out=RUN/'real'/group;asset=read(T/'config'/group/'ASSETS.json');verify(asset['files']);frozen=read(out/'PREDICTION_FREEZE.json');assert sha(out/'PREDICTIONS.json')==frozen['predictions_sha256'];verify([dict(path=p,sha256=h)for p,h in frozen['inputs'].items()]);freeze('EVALUATE',out,[out/'PREDICTION_FREEZE.json',out/'CLEAN_INDEX.json',out/'DEPENDENCY_REPLAY.json']);frames=read(out/'FRAMES.json');C=np.load(out/'CAMERAS.npz')['c2w'];tr=dict(np.load(out/'tracks/observations/tracks005.npz'));lm=np.load(out/'LANDMARKS.npz');pred=read(out/'DEPENDENCY_REPLAY.json')['results'];packs=load_geometry(out)
 key=lambda s:(s['side'],s['case'],s['tag'])
 assert len(packs)==len(asset['sources'])and len({key(p['source'])for p in packs})==len(packs)and {key(p['source'])for p in packs}=={key(s)for s in asset['sources']},'INCOMPLETE_OR_DUPLICATE_SOURCE_INDEX'
 domain_records=[]
 for p in packs:
  if p['state']is not None:
   q=Path(p['record']['raw_domain']);domain_records.append(dict(path=str(q),sha256=sha(q)))
 save(out/'DOMAIN_FREEZE.json',dict(before_metrics=True,files=domain_records,missing_sources=sum(p['state']is None for p in packs),samples_per_source=CFG['surface_samples_per_source'],seed_rule='20261127 + frozen source ordinal; original sample_mesh'))
 results={};ep=pack_pairs(frames,C,tr,tr['held']);ft=pack_pairs(frames,C,tr,~tr['held']);fitids=np.unique(ft['track_ids']);fittr=dict(tr,held=np.isin(np.arange(len(tr['xy'])),fitids));stage=dict(all_tracks=len(tr['xy']),all_held_tracks=int(tr['held'].sum()),M4_fit=int(lm['fit'].sum()),M5_fit=ft['tracks'],M5_pairs=len(ft['xa']),M5_held_pair_tracks=ep['tracks'],M5_held_pairs=len(ep['xa']),M4_fit_category={str(k):int(((tr['category']==k)&lm['fit']).sum())for k in [0,1,2]},M5_fit_category={str(k):int((tr['category'][fitids]==k).sum())for k in [0,1,2]},sources=len(packs),clean_missing=sum(p['state']is None for p in packs),raw_faces=sum(len(p['F'])for p in packs),clean_faces=sum(int((p['state']==0).sum())for p in packs if p['state']is not None),raw_area_mm2=sum(float(np.linalg.norm(np.cross(p['V'][p['F'][:,1]]-p['V'][p['F'][:,0]],p['V'][p['F'][:,2]]-p['V'][p['F'][:,0]]),axis=1).sum()/2)for p in packs),clean_area_mm2=sum(p['record'].get('trusted_area_mm2',0)for p in packs),shared_face_extra_movement_mm=0)
 for method,r in pred.items():
  T0=np.array(r['T'])if r['T']is not None else None;bidi,rows=bidirectional(frames,C,tr,lm['xyz'],T0);ring,_=ring_pixels(asset,frames,C,T0);fitb,fitrows=bidirectional(frames,C,fittr,lm['xyz'],T0);result=dict(numerical=r['numerical'],quality=r['quality'],bidir=bidi,ring=ring,FIT_cross_projection=fitb,held_epipolar_px=summarize(abs(pair_residuals(T0,ep)))if T0 is not None else dict(status='NO_TRANSFORM'),FIT_epipolar_px=summarize(abs(pair_residuals(T0,ft)))if T0 is not None else dict(status='NO_TRANSFORM'));save(out/'evaluation'/(method+'_HELD.json'),rows)
  if T0 is not None:
   result['raw']=geometric(packs,T0,False)
   _,flags=pair_residuals(T0,ft,return_flags=True);result['epipolar_degeneracy']={k:int(v.sum())for k,v in flags.items()}
   pp=parameters(T0);cols=[]
   for k in range(6):
    step=1e-6 if k<3 else 1e-4;delta=np.zeros(6);delta[k]=step;cols.append((pair_residuals(se3(pp+delta),ft)-pair_residuals(se3(pp-delta),ft))/(2*step))
   J=np.stack(cols,axis=1)*np.sqrt(ft['weights'])[:,None]/CFG['sigma_epipolar_px'];result['image_only_J_singular']=np.linalg.svd(J,compute_uv=False);result['J_parameter_units']='rotvec radians, translation mm; descriptive only; no GT gate'
   np.savez_compressed(out/(method+'_LANDMARKS_GLOBAL.npz'),points=np.stack([lm['xyz'][:,0],transform(lm['xyz'][:,1],T0)],1),held=tr['held'],M4_fit=lm['fit'],units='mm')
   if method=='M5':result['clean']=geometric(packs,T0,True)
   err=0.;worldcams=[]
   for v in asset['videos']:
    full=np.load(v['camera']);cam=full['c2w'];globalcam=(T0@cam)if v['side']=='B'else cam;np.savez_compressed(out/(method+'_CAMERAS_'+v['side']+'.npz'),c2w=globalcam,K=full['K'],ids=full['ids'],units='mm');worldcams.append(dict(side=v['side'],case=v['case'],local_source=v['camera'],transformed=str(out/(method+'_CAMERAS_'+v['side']+'.npz'))))
   for j,f in enumerate(frames):
    if f['side']!='B':continue
    X=lm['xyz'][:,1];X=X[np.isfinite(X).all(1)]
    if len(X):before=(X-C[j,:3,3])@C[j,:3,:3];cc=T0@C[j];after=(transform(X,T0)-cc[:3,3])@cc[:3,:3];err=max(err,float(np.max(abs(before-after))))
   assert err<1e-7;result['coordinate_invariance_max_mm']=err;save(out/'interfaces'/(method+'.json'),dict(group=group,method=method,T_A=np.eye(4),T_B=T0,scale=1,units='mm',cameras=worldcams,rule='C_global=T_v@C_local; X_global=T_v@X_local; K and native axial Z unchanged',Raw_sources=[dict(case=p['source']['case'],side=p['source']['side'],tag=p['source']['tag'],raw=p['source']['mesh_path'],raw_sha256=p['source']['mesh_sha256'],target=p['source']['raw_target'],support=p['source']['raw_support'],clean_selection=p['record'].get('selection_path')if method=='M5'else None,clean_coordinate_frame='M5 shared frame ONLY'if method=='M5'else None)for p in packs],clean_rule='F[state==0], all original V transformed once by T, no extra vertex change',candidate_only=True,body_update_authorized=False))
  results[method]=result
 # Secondary comparison only: identical finite observation IDs across methods.
 allrows={m:read(out/'evaluation'/(m+'_HELD.json'))for m in results};common={}
 for direction in ['A_to_B','B_to_A']:
  key=lambda r:(r['track'],r['frame'])
  sets=[{key(r)for r in rows if r['direction']==direction and r['error_px']is not None}for rows in allrows.values()];domain=set.intersection(*sets)
  common[direction]=dict(observation_ids=sorted(domain),N=len(domain),interpretation='secondary common-finite diagnostic ONLY; full unfiltered held counts retained above',methods={m:summarize([r['error_px']for r in rows if r['direction']==direction and key(r)in domain])for m,rows in allrows.items()})
 save(out/'COMMON_FINITE_DIAGNOSTIC.json',common)
 # FIT spatial rank is a descriptive diagnostic, not a GT-based gate.
 spatial=[]
 for si,side in enumerate(['A','B']):
  x=lm['xyz'][fitids,si];x=x[np.isfinite(x).all(1)];spatial.append(dict(side=side,points=len(x),singular_values=np.linalg.svd(x-x.mean(0),compute_uv=False)if len(x)else[],extent_mm=np.ptp(x,axis=0)if len(x)else[]))
 save(out/'EVALUATION.json',dict(group=group,stages=stage,methods=results,FIT_spatial=spatial,M5_observability=pred['M5'],GT='NO_3D_GROUND_TRUTH; cross-video consistency and independent source DLT only',BA_independence='new correspondence holdout only; upstream camera BA held flags retained in tracks/BA_DEPENDENCIES.npz'))
 verify(asset['files']);verify(domain_records);save(out/'INPUT_AFTER.json',dict(all_selected_hashes_match=True,count=len(asset['files'])));print('EVALUATED',group,{m:[r['bidir'][d]['conditional_MAE']for d in ['A_to_B','B_to_A']]for m,r in results.items()},flush=True)
if __name__=='__main__':
 for row in read(T/'config/SELECTION.json')['groups']:
  try:evaluate(row['group'])
  except Exception as e:save(RUN/'real'/row['group']/'EVALUATION_FAILURE.json',dict(error=repr(e),traceback=traceback.format_exc()));print('EVALUATE FAILURE',row['group'],repr(e),flush=True)
