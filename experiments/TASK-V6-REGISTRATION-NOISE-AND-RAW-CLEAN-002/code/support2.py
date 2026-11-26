"""Fixed 2D original-triangle support; no T, nearest 3D points or depth replacement."""
import numpy as np

def containing_faces(point,uv,F):
 tri=uv[F];lo=tri.min(1);hi=tri.max(1);ids=np.flatnonzero(((point>=lo-1e-9)&(point<=hi+1e-9)).all(1));q=tri[ids];a=q[:,1]-q[:,0];b=q[:,2]-q[:,0];c=point-q[:,0];det=a[:,0]*b[:,1]-a[:,1]*b[:,0];good=abs(det)>1e-12;u=np.full(len(ids),np.inf);v=u.copy();u[good]=(c[good,0]*b[good,1]-c[good,1]*b[good,0])/det[good];v[good]=(a[good,0]*c[good,1]-a[good,1]*c[good,0])/det[good];return ids[good&(u>=-1e-9)&(v>=-1e-9)&(u+v<=1+1e-9)].tolist()

def classify_support(group,frames,tr,xyz,fit):
 from common2 import T,RUN,read,save
 import trimesh
 index=read(RUN/'real'/group/'CLEAN_INDEX.json');by={}
 for r in index:
  s=r['source'];key=(s['side'],s['raw_target'])
  if key not in by:by[key]=r # frozen PLAN order, never choose by clean state
 cache={};rawmask=fit.copy();cleanmask=fit.copy();records=[]
 for tid in np.flatnonzero(fit):
  if tr['category'][tid]!=1:records.append(dict(track=int(tid),category=int(tr['category'][tid]),rule='BACKGROUND_OR_RING_UNCHANGED',raw_support=True,clean_support=True));continue
  entry=dict(track=int(tid),category=1,sides={});rawgood=True;cleangood=True
  for side in ['A','B']:
   obs=sorted([j for j,r in enumerate(frames)if r['side']==side and np.isfinite(tr['xy'][tid,j]).all()],key=lambda j:frames[j]['raw_frame']);chosen=None;extra=0
   for j in obs:
    key=(side,frames[j]['raw_frame'])
    if key not in by:continue
    r=by[key]
    if r.get('status')=='MISSING':continue
    if key not in cache:
     e=np.load(r['selection_path']);s=r['source'];m=trimesh.load(str(__import__('pathlib').Path(s['run'])/'meshes'/(s['tag']+'_Polyp.ply')),process=False);cache[key]=(e['working_uv'],np.asarray(m.faces),e['state'])
    uv,F,state=cache[key];faces=containing_faces(tr['xy'][tid,j],uv,F)
    if len(faces):extra+=1
    # Select on Raw geometry only. Classification does not change this choice.
    if chosen is None and len(faces):chosen=(j,faces,state[faces],r)
   if chosen is None:rawgood=False;cleangood=False;entry['sides'][side]=dict(status='UNKNOWN_NO_RAW_FACE',other_raw_supported_observations=extra);continue
   j,faces,states,r=chosen;conflict=len(set(map(int,states)))>1;trusted=not conflict and bool((states==0).all());rawgood&=not conflict;cleangood&=trusted;entry['sides'][side]=dict(frame=j,raw_frame=frames[j]['raw_frame'],tag=r['source']['tag'],original_face_ids=faces,states=states.tolist(),status='UNKNOWN_BOUNDARY_CONFLICT'if conflict else'TRUSTED'if trusted else'RAW_ONLY',other_raw_supported_observations=extra-1)
  rawmask[tid]=rawgood;cleanmask[tid]=cleangood;entry.update(raw_support=rawgood,clean_support=cleangood);records.append(entry)
 save(RUN/'real'/group/'SUPPORT_SELECTION.json',records);np.savez_compressed(RUN/'real'/group/'SUPPORT_MASKS.npz',base=fit,raw_support=rawmask,clean_support=cleanmask)
 return rawmask,cleanmask
