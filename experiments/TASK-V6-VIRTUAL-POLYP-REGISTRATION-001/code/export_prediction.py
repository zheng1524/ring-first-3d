"""GT-free materialization of one rigid transform per video on every observation."""
from common import *
from registration import install_guard
from ring_first_3d.sim.geometry import transform
from ring_first_3d.contracts.coordinates import validate_c2w,project

def export():
 install_guard();rows=[]
 for cond in cases():
  pred=RUN/'predictions'/cond;fr=read(pred/'FREEZE.json');check_freeze(fr['predictions']);public=read(RUN/'public/conditions'/(cond+'.json'));lm=np.load(pred/'LANDMARKS.npz');frameinfo={r['id']:r for r in read(RUN/'public/FRAMES.json')}
  for method in ['M0','M1','M2']:
   r=read(pred/(method+'.json'))
   if r['T_005'] is None:rows.append(dict(condition=cond,method=method,status='REJECT'));continue
   out=RUN/'exports'/cond/method;out.mkdir(parents=True,exist_ok=False);Ts={'004':np.eye(4),'005':np.array(r['T_005'])};Cs=[];maxpix=0.;maxz=0.;index=[]
   for f in public['frames']:
    cid=f['id'];C=np.array(f['C']);t=Ts[f['video']];cg=t@C;validate_c2w(cg);a=np.load(RUN/'public/meshes'/(cid+'.npz'));local=transform(a['V'],C);globalV=transform(local,t);Cs.append(cg);K=np.array(frameinfo[cid]['K']);uv,z=project(local[::97],K,C);q,d=project(globalV[::97],K,cg);maxpix=max(maxpix,float(np.max(abs(q-uv))));maxz=max(maxz,float(np.max(abs(z-d))));np.savez_compressed(out/(cid+'.npz'),V=globalV,F=a['F'],K=K,c2w=cg,uv=a['uv']);index.append(dict(id=cid,video=f['video'],role=f['role'],file=cid+'.npz'))
   points=lm['points'].copy();points[:,1]=transform(points[:,1],Ts['005']);np.savez_compressed(out/'GLOBAL_LANDMARKS.npz',points=points,track_ids=lm['track_ids'],held=lm['held']);np.savez_compressed(out/'GLOBAL_CAMERAS.npz',c2w=Cs,ids=[f['id']for f in public['frames']]);save(out/'INDEX.json',dict(proxy=CFG['proxy'],mesh_frames=index,transforms=Ts,GT_read=False,scale=1))
   assert maxpix<1e-8 and maxz<1e-8;rows.append(dict(condition=cond,method=method,status='EXPORTED',meshes=len(index),projection_invariance_max_px=maxpix,axial_Z_invariance_max_mm=maxz,files=freeze(out.glob('*'))))
 save(T/'evidence/EXPORTS.json',rows)
if __name__=='__main__':export()
