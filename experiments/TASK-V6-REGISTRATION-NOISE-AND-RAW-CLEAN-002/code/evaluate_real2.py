"""Post-freeze evaluation; all geometric distances are cross-video consistency, NOT GT."""
from common2 import *
from metrics2 import bidirectional,ring_pixels,summarize
from ring_first_3d.sim.geometry import transform,scene,closest,pose_error
import trimesh

def load_geometry(folder):
 index=read(folder/'CLEAN_INDEX.json');packs=[]
 for ordinal,rec in enumerate(index):
  s=dict(rec['source']);s['mesh_path']=str(Path(s['run'])/'meshes'/(s['tag']+'_Polyp.ply'));m=trimesh.load(s['mesh_path'],process=False);V=np.asarray(m.vertices);F=np.asarray(m.faces);state=None;sample=None
  if rec.get('status')!='MISSING':
   assert sha(rec['selection_path'])==rec['selection_sha256'];state=np.load(rec['selection_path'])['state'];d=np.load(rec['raw_domain']);ids=d['original_face_id'];bary=d['bary'];sample=np.einsum('ni,nij->nj',bary,V[F[ids]])
  else:
   from ring_first_3d.multisurface.geometry import sample_mesh
   sample,ids,bary=sample_mesh(V,F,CFG['surface_samples_per_source'],20261127+ordinal)
  packs.append(dict(source=s,V=V,F=F,state=state,points=sample,ids=ids,record=rec))
 return packs

def combined(packs,side,T0,clean=False,excluded=False):
 vv=[];ff=[];offset=0
 for p in packs:
  if p['source']['side']!=side:continue
  if (clean or excluded)and p['state']is None:continue
  F=p['F'];F=F[p['state']==0]if clean else F[p['state']!=0]if excluded else F
  if not len(F):continue
  V=transform(p['V'],T0)if side=='B'else p['V'];vv.append(V);ff.append(F+offset);offset+=len(V)
 return (np.concatenate(vv),np.concatenate(ff))if vv else (np.empty((0,3)),np.empty((0,3),int))

def geometric(packs,T0,clean):
 result={}
 if clean and any(p['state']is None for p in packs):return {'status':'NOT_EVALUABLE_CLEAN_MISSING','missing_sources':sum(p['state']is None for p in packs),'raw_sample_denominator':len(packs)*CFG['surface_samples_per_source'],'missing_is_not_empty':True}
 for side,target in [('A','B'),('B','A')]:
  pts=[];ret=[];missing=0
  for p in packs:
   if p['source']['side']!=side:continue
   if p['points']is None:missing+=CFG['surface_samples_per_source'];continue
   pts.append(transform(p['points'],T0)if side=='B'else p['points']);ret.append(p['state'][p['ids']]==0 if p['state']is not None else np.zeros(len(p['ids']),bool))
  P=np.concatenate(pts);kept=np.concatenate(ret);V,F=combined(packs,target,T0,clean);d=np.linalg.norm(closest(scene(V,F),P)[0]-P,axis=1)if len(F)else np.full(len(P),np.inf)
  active=kept if clean else np.ones(len(P),bool);full=np.where(active,d,np.inf);full=np.r_[full,np.full(missing,np.inf)]
  result[side+'_to_'+target]=dict(full_raw_sample_domain=summarize(full),conditional_retained_original_faces=summarize(d[kept]),coverage_fraction=float((full<=CFG['coverage_mm']).mean()),sample_missing_clean=missing,source_sample_excluded=int((~active).sum()),domain='96 original area-sampled triangles/source; excluded samples remain uncovered; cross-video consistency not GT')
 return result

def evaluate(group):
 out=RUN/'real'/group;asset=read(T/'config'/group/'ASSETS.json');verify(asset['files']);freeze=read(out/'PREDICTION_FREEZE.json');assert sha(out/'PREDICTIONS.json')==freeze['predictions_sha256'];verify([dict(path=p,sha256=h)for p,h in freeze['inputs'].items()]);stage_freeze('EVALUATE',out,[out/'PREDICTION_FREEZE.json']);frames=read(out/'FRAMES.json');C=np.load(out/'CAMERAS.npz')['c2w'];tr=np.load(out/'tracks/observations/tracks005.npz');land=np.load(out/'LANDMARKS.npz');pred=read(out/'PREDICTIONS.json');packs=load_geometry(out);rows={};ring=read(out/'RING_PRIOR.json');details=read(out/'TRIANGULATION.json');fits=land['fit'];index=read(out/'CLEAN_INDEX.json')
 stage=dict(track_total=len(fits),held_total=int(tr['held'].sum()),fit_valid=int(fits.sum()),fit_category={str(c):int(((tr['category']==c)&fits).sum())for c in [0,1,2]},per_side={s:dict(parallax_deg=summarize([r['sides'][s]['parallax_deg']for r in details if fits[r['track']]]),max_reprojection_px=summarize([r['sides'][s]['max_px']for r in details if fits[r['track']]]))for s in ['A','B']},sources=len(index),clean_missing=sum(r.get('status')=='MISSING'for r in index),clean_reused=sum(r['origin']=='REUSED'for r in index),raw_area_mm2=sum(float(np.linalg.norm(np.cross(p['V'][p['F'][:,1]]-p['V'][p['F'][:,0]],p['V'][p['F'][:,2]]-p['V'][p['F'][:,0]]),axis=1).sum()/2)for p in packs),trusted_area_mm2=sum(r.get('trusted_area_mm2',0)for r in index),raw_faces=sum(len(p['F'])for p in packs),trusted_faces=sum(r.get('trusted_faces',0)for r in index),coordinate_change_common_faces_mm=0,raw_empty=sum(r.get('raw_faces')==0 for r in index),clean_empty=sum(r.get('trusted_faces')==0 for r in index))
 base=pred['M4']['T']
 for name,r in pred.items():
  T0=np.asarray(r['T'])if r['T']is not None else None;bidi,records=bidirectional(frames,C,tr,land['xyz'],T0);rp,_=ring_pixels(asset,frames,C,T0);row=dict(numerical=r['numerical'],quality=r['quality'],bidir=bidi,ring=rp,delta_to_M4=pose_error(T0@np.linalg.inv(base))if T0 is not None and base is not None else None)
  save(out/'evaluation'/(name+'_HELD.json'),records)
  if T0 is not None:
   # Pure coordinate change must preserve all B camera coordinates and axial Z.
   maxerr=0.
   for j,f in enumerate(frames):
    if f['side']!='B':continue
    P=land['xyz'][:,1];ok=np.isfinite(P).all(1);P=P[ok];
    if not len(P):continue
    before=(P-C[j,:3,3])@C[j,:3,:3];cc=T0@C[j];after=(transform(P,T0)-cc[:3,3])@cc[:3,:3];maxerr=max(maxerr,float(np.max(abs(before-after))))
   assert maxerr<1e-7;row['coordinate_invariance_max_mm']=maxerr
   row['raw']=geometric(packs,T0,False);row['clean']=geometric(packs,T0,True)
   save(out/'interfaces'/(name+'.json'),dict(scale=1,units='mm',T_B_to_A=T0,camera_rule='C_global=T@C_local; A unchanged',point_rule='X_global=T@X_local; A unchanged',K_and_axial_depth='UNCHANGED',sources=[dict(raw=p['source']['mesh_path'],raw_sha=p['source']['mesh_sha256'],selection=p['record'].get('selection_path'),trusted_faces_only='state==0',side=p['source']['side'])for p in packs],candidate_only=True,reason='Scientific acceptance requires held/LOO evidence; no body fitting launched'))
  rows[name]=row
 # No automatic handoff based on numerical convergence; report comparisons on same domain.
 for name,row in rows.items():
  row['relative_to']={ref:{d:(row['bidir'][d]['conditional_MAE']-rows[ref]['bidir'][d]['conditional_MAE'])if row['bidir'][d]['conditional_MAE']is not None and rows[ref]['bidir'][d]['conditional_MAE']is not None else None for d in ['A_to_B','B_to_A']}for ref in ['M1','M2']}
 save(out/'EVALUATION.json',dict(group=group,stages=stage,methods=rows,GT='NOT_AVAILABLE; consistency only',ring_prior=ring));verify(asset['files']);save(out/'INPUT_AFTER.json',dict(all_selected_sha_match=True,count=len(asset['files'])));print('REAL EVAL',group,stage,flush=True)
if __name__=='__main__':
 import traceback
 for r in read(T/'config/SELECTION.json')['groups']:
  try:evaluate(r['group'])
  except Exception as e:save(RUN/'real'/r['group']/'EVALUATE_FAILURE.json',dict(error=repr(e),traceback=traceback.format_exc()));print('EVALUATE FAILURE',r['group'],repr(e),flush=True)
