"""Predictor: only public observed Ring, cameras, RGB tracks; no GT or injections."""
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.optimize import least_squares
from ring_first_3d.sim.geometry import se3,parameters,transform
from ring_first_3d.contracts.coordinates import validate_c2w,project
from common import *
from v6_adapter import triangle

def ring_only(center,normal):
 normal=np.asarray(normal)/np.linalg.norm(normal);target=np.array([0.,0.,1.]);axis=np.cross(normal,target);angle=np.arctan2(np.linalg.norm(axis),normal@target)
 if np.linalg.norm(axis)<1e-12:rot=Rotation.from_rotvec([np.pi if normal@target<0 else 0,0,0]).as_matrix()
 else:rot=Rotation.from_rotvec(axis/np.linalg.norm(axis)*angle).as_matrix()
 T0=np.eye(4);T0[:3,:3]=rot;T0[:3,3]=-rot@center;return T0

def solve(A,B,center,normal):
 if len(A)<CFG['min_tracks']:return None,dict(status='REJECT_INSUFFICIENT_TRACKS',tracks=len(A))
 base=ring_only(center,normal);candidates=[se3([0,0,2*np.pi*k/CFG['yaw_grid'],0,0,0])@base for k in range(CFG['yaw_grid'])]
 cost=[np.median(np.linalg.norm(transform(B,t)-A,axis=1))for t in candidates];init=candidates[int(np.argmin(cost))]
 def residual(p):
  t=se3(p);rgb=((transform(B,t)-A)/CFG['rgb_sigma_mm']).ravel();ring=np.r_[transform(np.asarray(center)[None],t)[0],CFG['ring_radius_mm']*(t[:3,:3]@normal-np.array([0,0,1.]))]/CFG['ring_sigma_mm']*np.sqrt(len(A));return np.r_[rgb,ring]
 fit=least_squares(residual,parameters(init),loss=CFG['loss'],max_nfev=CFG['max_nfev'],ftol=1e-10,xtol=1e-10,gtol=1e-10)
 t=se3(fit.x);validate_c2w(t)
 return t,dict(status='ACCEPT' if fit.success else 'REJECT_SOLVER_LIMIT',tracks=len(A),nfev=fit.nfev,cost=fit.cost,initial_yaw_grid=int(np.argmin(cost)),parameterization='six rotvec_rad + translation_mm; fixed scale',success=fit.success)

def landmarks(frames,poses,tr):
 points=[];records=[];ids=[];held=[]
 for tid,xy in enumerate(tr['xy']):
  pair=[];rec=dict(track=int(tid),held=bool(tr['held'][tid]),video={});valid=True
  for video in ['004','005']:
   ix=np.array([i for i,r in enumerate(frames) if r['video']==video and np.isfinite(xy[i]).all()],int)
   if len(ix)<2:valid=False;rec['video'][video]=dict(status='LESS_THAN_TWO_VIEWS',observations=len(ix));continue
   K=np.array(frames[ix[0]]['K']);P=triangle(poses[ix],xy[ix],K)
   try:
    errors=np.array([np.linalg.norm(project(P[None],K,poses[i])[0][0]-xy[i])for i in ix]);rays=P-poses[ix,:3,3];rays/=np.linalg.norm(rays,axis=1)[:,None];angle=float(np.rad2deg(np.arccos(np.clip((rays@rays.T).min(),-1,1))));ok=np.isfinite(P).all() and max(errors)<=CFG['triangulation_max_px'] and angle>=CFG['min_parallax_deg']
   except ValueError:errors=np.array([np.inf]);angle=0;ok=False
   valid &= ok;pair.append(P);rec['video'][video]=dict(status='PASS' if ok else 'REJECT_GEOMETRY',observations=len(ix),max_px=float(max(errors)),parallax_deg=angle)
  records.append(rec)
  if valid:points.append(pair);ids.append(tid);held.append(bool(tr['held'][tid]))
 return np.array(points).reshape(-1,2,3),np.array(ids),np.array(held,bool),records

def predict(condition):
 check_freeze(read(RUN/'GENERATION_FREEZE.json')['public']);frames=read(RUN/'tracks/ADAPTER.json')['frames'];tr=dict(np.load(RUN/'tracks/observations/tracks005.npz'));public=read(RUN/'public/conditions'/(condition+'.json'));by={r['id']:r for r in public['frames']};poses=np.array([by[r['id']]['C']for r in frames]);pts,ids,held,details=landmarks(frames,poses,tr);ring=public['ring']['005'];c=np.array(ring['center']);n=np.array(ring['normal']);out=RUN/'predictions'/condition;out.mkdir(parents=True,exist_ok=False)
 np.savez_compressed(out/'LANDMARKS.npz',points=pts,track_ids=ids,held=held);save(out/'TRIANGULATION.json',details)
 T2,rec=solve(pts[~held,0],pts[~held,1],c,n)
 for name,t,record in [('M0',np.eye(4),dict(status='ACCEPT')),('M1',ring_only(c,n),dict(status='YAW_UNIDENTIFIABLE')),('M2',T2,rec)]:
  save(out/(name+'.json'),dict(method=name,T_004=np.eye(4),T_005=t,solver=record,GT_read=False,train_tracks=int((~held).sum()),held_tracks=int(held.sum())))
 save(out/'FREEZE.json',dict(config_sha256=sha(T/'config.json'),sources=freeze((T/'code').glob('*.py')),public_input_freeze=sha(RUN/'GENERATION_FREEZE.json'),tracks_sha256=sha(RUN/'tracks/observations/tracks005.npz'),predictions=freeze(p for p in out.iterdir() if p.name!='FREEZE.json')))
 print(condition,rec,'held',held.sum(),flush=True)
if __name__=='__main__':
 import sys
 for c in sys.argv[1:] or cases():predict(c)
