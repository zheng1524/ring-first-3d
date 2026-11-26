"""Read current HIST formats and execute original V6 AST without import side effects."""
import ast,cv2
import numpy as np
from common import *

def original(name,functions,namespace):
 path=V6/name;namespace['__file__']=str(path);tree=ast.parse(path.read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in functions]
 assert {n.name for n in nodes}==set(functions)
 exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),namespace)
 return namespace

def triangle(poses,uv,K):
 ns=original('v6_common.py',['triangle'],dict(np=np,K=K));return ns['triangle'](poses,uv,K)

def track():
 frames=[r for r in read(RUN/'public/FRAMES.json') if r['role']=='FIT'];out=RUN/'tracks';out.mkdir(exist_ok=False);(out/'observations').mkdir()
 ledger=[dict(id=r['id'],raw_frame=i,RGB_path=str(RUN/'public/images'/(r['id']+'.png')),Mask_path=str(RUN/'public/images'/(r['id']+'_labels.png'))) for i,r in enumerate(frames)]
 receipts=[]
 def fr(n,paths):receipts.append(dict(stage=n,source='Original tracking main; files bound by task freeze'))
 ns=dict(np=np,cv2=cv2,Path=Path,R=out,cfg=lambda:CFG,ledger=lambda:ledger,verify=lambda n:check_freeze(read(RUN/'GENERATION_FREEZE.json')['public']),freeze=fr,image=lambda r:cv2.imread(r['RGB_path'])[:,:,::-1].copy(),labels=lambda r:cv2.imread(r['Mask_path'],0),save=lambda p,x:save(out/p,x))
 original('track005.py',['main'],ns)['main']()
 save(out/'ADAPTER.json',dict(source=str(V6/'track005.py'),sha256=sha(V6/'track005.py'),pair_offsets=CFG['pair_offsets'],FIT_only=True,GT_access=False,receipts=receipts,frames=frames))

def audit_real():
 base=Path('/home/liu/ring_first_3d_workspace/runs/v6_raw_to_hero_001/HIST');records=[]
 for video in ['004','005']:
  r=base/(CFG['case']+'_'+video);primary=read(r/'predictions/local005_primary.json');camera=r/f"predictions/local005_camera_{primary['primary_version']}.npz";a=dict(np.load(camera));ledger=read(r/'inputs/ledger005.json');tr=dict(np.load(r/'observations/tracks005.npz'));assert str(a['units'])=='mm';assert list(a['ids'])==[x['id'] for x in ledger];assert np.array_equal(tr['frame_raw'],[x['raw_frame']for x in ledger])
  for item in ledger:
   assert sha(item['RGB_path'])==item['RGB_SHA256'];assert sha(item['Mask_path'])==item['Mask_SHA256'];assert cv2.imread(item['RGB_path']).shape[:2]==(360,640)
  paths=[camera,r/'observations/tracks005.npz',r/'inputs/ledger005.json',r/'config.json',r/'PLAN_FROZEN.json',r/'CAMERA_COMPLETE.json',r/'HERO_COMPLETE.json']
  surfaces=[]
  for p in sorted((r/'predictions').glob('*_surface.npz')):
   b=dict(np.load(p));raw=r/'raw'/p.name.replace('_surface.npz','.npz');h=dict(np.load(raw));paths += [p,raw]
   surfaces.append(dict(file=str(p),sha256=sha(p),depth_shape=b['depth_mm'].shape,K=b['K'],pose=b['pose'],reference=b['reference'],source_frames=b['source_frames'],unit=str(b['unit']),raw=str(raw),raw_fields={k:dict(shape=h[k].shape,dtype=str(h[k].dtype))for k in h},raw_sha256=sha(raw)))
  meshpaths=sorted((r/'meshes').glob('*'));paths+=meshpaths
  out=T/'inputs'/('V6_HIST_'+video);out.mkdir(exist_ok=True)
  # Protect small camera/track snapshots and a single native/surface example.
  import shutil
  for p in paths[:7]:shutil.copyfile(p,out/p.name)
  for p in [Path(surfaces[0]['file']),Path(surfaces[0]['raw'])]:shutil.copyfile(p,out/p.name)
  save(out/'SURFACES.json',surfaces)
  records.append(dict(video=video,variant='HIST',run=str(r),primary=primary,frames=len(ledger),landmarks=len(a['points']),tracks=len(tr['xy']),units='mm',K_image_wh=[640,360],K=a['K'],camera='OpenCV c2w',local_gauge=primary['Ring_spin_gauge'],ring_R_mm=5.6,ring_r_mm=.6,depth_native='stored depth_mm axial Z; native 352x640; internal network uses metres',surfaces=len(surfaces),mesh_files=len(meshpaths),camera_centers=a['c2w'][:,:3,3],dependencies=[dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size)for p in paths]))
 save(T/'evidence/V6_INTERFACE.json',records)
if __name__=='__main__':
 import sys
 audit_real() if sys.argv[1]=='audit' else track()
