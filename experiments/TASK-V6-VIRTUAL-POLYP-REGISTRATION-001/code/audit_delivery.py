"""Explicit post-run audit, not misrepresented as a prior freeze."""
import ast,subprocess,csv
from common import *
from ring_first_3d.sim.geometry import transform,parameters
from scipy.spatial.transform import Rotation

def audit():
 check_freeze(read(RUN/'GENERATION_FREEZE.json')['public']);check_freeze(read(RUN/'GENERATION_FREEZE.json')['private'])
 functions=[]
 for p in (T/'inputs/V6_KERNELS').glob('*.py'):
  assert sha(p)==sha(V6/p.name);functions.append(dict(original=str(V6/p.name),protected=str(p.relative_to(T)),sha256=sha(p),binding_time='POSTRUN_AUDIT',source_commit='Original V6, same as base HIST kernel lock'))
 deps=['contracts/coordinates.py','sim/scene.py','sim/geometry.py','sim/registration.py','synthetic/raster.py','multisurface/geometry.py','multisurface/scene.py','_legacy.py','source_lock.json']
 root=T.parents[1];sources=[]
 for rel in deps:
  p=root/'src/ring_first_3d'/rel;old=subprocess.check_output(['git','show',CFG['base_commit']+':'+str(p.relative_to(root))],cwd=root);assert hashlib.sha256(old).hexdigest()==sha(p);sources.append(dict(path=str(p),sha256=sha(p),unchanged_from_base=True))
 details=[]
 V0=np.load(RUN/'predictions/V0/LANDMARKS.npz');zero={int(t):p for t,p in zip(V0['track_ids'],V0['points'])}
 truth=read(RUN/'private/TRUTH.json');records=read(RUN/'public/FRAMES.json');cid=next(r['id']for r in records if r['video']=='005')
 for c in cases():
  f=read(RUN/'predictions'/c/'FREEZE.json');check_freeze(f['predictions']);assert sha(RUN/'tracks/observations/tracks005.npz')==f['tracks_sha256'];D=np.array(truth['injections'][c][cid]['D']);lm=np.load(RUN/'predictions'/c/'LANDMARKS.npz');delta=[]
  for t,P in zip(lm['track_ids'],lm['points']):
   if int(t)in zero:delta.append(np.linalg.norm(P[1]-transform(zero[int(t)][1:2],D)[0]))
  m=read(RUN/'predictions'/c/'M2.json');tt=np.array(m['T_005']);yaw=Rotation.from_matrix((tt@D)[:3,:3]).as_euler('zyx',degrees=True)[0]
  details.append(dict(condition=c,common_landmark_N=len(delta),triangulation_delta_from_clean_median_mm=float(np.median(delta)),triangulation_delta_from_clean_p95_mm=float(np.quantile(delta,.95)),residual_yaw_deg=yaw,ring_center_after_mm=float(np.linalg.norm(transform(D[:3,3][None],tt)[0])),matrix_determinant=float(np.linalg.det(tt[:3,:3]))))
 save(T/'evidence/POSTRUN_AUDIT.json',dict(binding_time='POSTRUN; not a retroactive prediction-start freeze',external_kernels=functions,reused_sources=sources,diagnostics=details,prediction_hashes_valid=True,all_public_and_private_generation_hashes_valid=True))
 with (T/'ASSET_REUSE.csv').open('w')as f:
  w=csv.writer(f,lineterminator='\n');w.writerow(['asset','entrypoint_or_path','purpose','adaptation','protection'])
  for a in read(T/'evidence/ASSET_IDENTITIES.json'):w.writerow([a['asset'],a['source'],'Original G01 geometry/Ring/partition identity','Path migration only',a['protected']])
  for s in sources:w.writerow([Path(s['path']).name,s['path'],'Reused renderer / topology / transforms / evaluation','No algorithm changes',s['sha256']])
  for s in functions:w.writerow([Path(s['original']).name,s['original'],'Original V6 RGB tracking and DLT','AST exact functions, task I/O',s['protected']])
  for v in ['004','005']:w.writerow(['V6 HIST '+v,str(T/'inputs'/('V6_HIST_'+v)),'Real interface / angle & error reference','Read only; no real GT','Versioned small snapshots; full dependency hashes in V6_INTERFACE'])
 print('POSTRUN AUDIT PASS',len(sources),'source files',len(functions),'V6 kernels')
if __name__=='__main__':audit()
