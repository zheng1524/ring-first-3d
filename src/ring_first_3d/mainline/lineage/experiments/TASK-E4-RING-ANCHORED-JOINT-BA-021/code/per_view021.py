"""Every005/004 view retained, including absent feature correspondences (N=0, NaN)."""
from geometry021 import *
from objective020 import SymmetricFeatures
from eval021 import methods
def main():
 wait_freeze()
 while not(R/'runtime/BA_INDEPENDENT_EVALUATION_COMPLETE.json').exists():time.sleep(5)
 vv=load(R/'config/VIEWS.json');tracks=load(R/'observations/CROSS_COMMON_TRACKS.json');excluded=[{t['source_landmark004']for t in tracks},{t['source_landmark005']for t in tracks}];ban={}
 for t in tracks:
  for o in t['observations']:ban.setdefault(o['view'],[]).append(o['uv'])
 F={role:SymmetricFeatures('CROSS',held=role=='HOLDOUT')for role in ['FIT','HOLDOUT']};out=[]
 for m in methods():
  H=np.asarray(m['T']);X=np.asarray(load(R/'results'/(m['method']+'.json')).get('X',[t['X0']for t in tracks]))
  for v in vv:
   direction=0 if v['video']=='005'else 1;lst=F[v['role']].directions[direction];found=next((a for a in lst if a['view']==v['id']),None);err=np.empty(0);unused=np.empty(0)
   if found is not None:
    a=found;C=a['T'].cpu().numpy();P=a['X'].cpu().numpy();K=a['K'].cpu().numpy();uv=a['uv'].cpu().numpy()
    if direction==0:C=H@C
    else:P=P@H[:3,:3].T+H[:3,3]
    Q=(P-C[:3,3])@C[:3,:3];w=Q@K.T;pred=w[:,:2]/w[:,2:];err=np.linalg.norm(pred-uv,axis=1);keep=np.array([i not in excluded[direction]for i in a['landmark']])
    if v['id']in ban:keep&=(np.linalg.norm(uv[:,None]-np.asarray(ban[v['id']])[None],axis=-1).min(1)>1e-4)
    unused=err[keep]
   common=[]
   for t,x in zip(tracks,X):
    for o in t['observations']:
     if o['view']!=v['id']:continue
     C=np.asarray(o['native_C']);C=H@C if o['side']else C;Q=(x-C[:3,3])@C[:3,:3];q=Q@np.asarray(o['K']).T;common.append(np.linalg.norm(q[:2]/q[2]-o['uv']))
   out.append(dict(method=m['method'],view=v['id'],video=v['video'],role=v['role'],original_camera_qualification=v.get('qualification'),fixed_020_anchor_error_px=stats(err),unused_track_and_target_pixel_error_px=stats(unused),joint_point_error_px=stats(common),joint_point_status='OPTIMIZED_FOR_THIS_ARM'if'X'in load(R/'results'/(m['method']+'.json'))else'RETRIANGULATED_RoMa_X0_DIAGNOSTIC_NOT_TRAINED',no_correspondence_status='N0_NOT_EVALUABLE'if not len(err)else'COMPUTED',source_original_pose=v['pose_source']))
 save('metrics/SIFT_ALL68_PER_VIEW.json',out);table('metrics/SIFT_ALL68_PER_VIEW.csv',out)
 # Exact shared transform receipts: original004 cameras immutable,005 relative poses invariant.
 for name in ['B1','B2','B3']:
  H=np.asarray(load(R/'results'/(name+'.json'))['T']);derived=[]
  for v in vv:
   C=np.asarray(v['T']);derived.append(dict(id=v['id'],video=v['video'],role=v['role'],K=v['K'],original_c2w_mm=C,derived_c2w_mm=H@C if v['video']=='005'else C,qualification=v.get('qualification'),original_pose_source=v['pose_source']))
  save('derived/T004_from005_'+name+'.json',dict(direction='004 <- 005; X004 = R X005 + t',matrix_mm=H,scale=1.,all_original_poses_unchanged=True,not_pose_GT=True));save('derived/ALL68_CAMERAS_'+name+'.json',derived)
 save('runtime/PER_VIEW_COMPLETE.json',dict(epoch=time.time(),rows=len(out)));print('PER_VIEW021_COMPLETE',len(out),flush=True)
if __name__=='__main__':main()
