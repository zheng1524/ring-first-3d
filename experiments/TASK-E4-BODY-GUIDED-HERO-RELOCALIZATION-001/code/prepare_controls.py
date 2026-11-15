"""Isolated Blender control construction; never imported by real optimizer."""
from fit_body import body_fit
from geometry import *
import shutil
ROOT=REPO/'experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/PROGRESSIVE_HERO_001'

def triangulate_grid(z,mask,K,C):
 h,w=z.shape;uv=np.c_[np.tile(np.arange(w),h),np.repeat(np.arange(h),w)];ids=np.flatnonzero(mask.ravel());uv=uv[ids];r=rays(C,K,uv);X=r[:,:3]+r[:,3:]*z.ravel()[ids,None];idx=np.full(h*w,-1,int);idx[ids]=np.arange(len(ids));idx=idx.reshape(h,w);F=[]
 for yy,xx in zip(*np.where(mask[:-1,:-1]&mask[1:,:-1]&mask[:-1,1:]&mask[1:,1:])):F.extend([[idx[yy,xx],idx[yy+1,xx],idx[yy+1,xx+1]],[idx[yy,xx],idx[yy+1,xx+1],idx[yy,xx+1]]])
 F=np.array(F,int);normal=face_normals_grid(X,F);return X,F,uv,ids,normal

def face_normals_grid(X,F):
 N=np.zeros_like(X);n=np.cross(X[F[:,1]]-X[F[:,0]],X[F[:,2]]-X[F[:,0]])
 # Image-index ordering follows camera facing: ensure normals toward source camera.
 for i in range(3):np.add.at(N,F[:,i],n)
 N/=np.maximum(np.linalg.norm(N,axis=1)[:,None],1e-15);return N

def main():
 root=R/'controls';(root/'inputs').mkdir(exist_ok=True);(root/'audit_only').mkdir(exist_ok=True);gtpath=REPO/'experiments/TASK-E4-2D3D-OBSERVABILITY-001/audit_only/NATIVE_CAD_GT.npz';gt=np.load(gtpath);gs=scene(gt['V'],gt['F']);rv=np.load(ROOT/'inputs/virtual/RING.npz');np.savez_compressed(root/'inputs/RING.npz',V=rv['V'],F=rv['F']);rs=scene(rv['V'],rv['F']);meta=load(ROOT/'inputs/virtual/CASE.json');views=[];gates=[]
 for v in meta['views']:
  a=np.load(ROOT/'inputs/virtual'/(v['id']+'.npz'));h,w=a['labels'].shape;uv=np.c_[np.tile(np.arange(w),h),np.repeat(np.arange(h),w)];hit=rayquery(gs,a['T'],a['K'],uv);z=hit['t_hit'].reshape(h,w);cz=rayquery(rs,a['T'],a['K'],uv)['t_hit'].reshape(h,w);polyp=np.isfinite(z)&(z<cz);target=a['labels']==1;IoU=(polyp&target).sum()/max(1,(polyp|target).sum());gates.append(dict(view=v['id'],IoU=float(IoU),PASS=bool(IoU>=.99),K=a['K'],C=a['T']));np.savez_compressed(root/'inputs'/(v['id']+'_BASE.npz'),labels=a['labels'],K=a['K'],C=a['T'],z=z,RGB_label_only=a['RGB']);views.append(dict(id=v['id'],K=a['K'],C=a['T'],role=v['role'],width=w,height=h))
 save('controls/PROJECTION_GATE.json',gates);assert all(x['PASS']for x in gates),'BLENDER_GT_CAMERA_IDENTITY_GATE_FAILED'
 np.savez_compressed(root/'audit_only/SCENE_GT.npz',V=gt['V'],F=gt['F']);save('controls/SCENE.json',dict(views=views,GT_source=asset(gtpath),Ring_source=asset(ROOT/'inputs/virtual/RING.npz'),geometry_static_all_views=True,world_unit='mm; 1 Blender unit=1mm',RGB_source='NEW control-only textured-background rendering; archived colored masks are NOT RGB evidence',GT_real_fitting=False))
 bodyviews=[dict(id=v['id'],K=np.array(v['K']),C=np.array(v['C']),labels=np.load(root/'inputs'/(v['id']+'_BASE.npz'))['labels'])for v in views if v['role']=='FIT'];body_fit('CONTROL_IIa',bodyviews,rv['V'],rv['F'],root/'inputs');u=np.load(ROOT/'local_results/virtual/D/FINAL.npz');np.savez_compressed(root/'inputs/Body-U.npz',V=u['V'],F=u['F']);save('controls/BODY_INPUT_RECEIPT.json',dict(Body_E='fresh mask-only fit',Body_U=asset(ROOT/'local_results/virtual/D/FINAL.npz'),Body_U_history='prior virtual D uses IDEAL_GT_DEPTH_UPPER_BOUND; not unbiased evidence and not real HERO',current_GT_only_control_generation_and_audit=True));print('CONTROL_INPUTS_GATE_PASSED',flush=True)
if __name__=='__main__':main()
