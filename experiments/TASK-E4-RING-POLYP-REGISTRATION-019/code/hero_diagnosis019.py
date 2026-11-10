from common import *
import open3d as o3d
P18=REPO/'experiments/TASK-E4-HERO-BODY-ADAPT-018'

def sources():
 rows=[]
 for v in load(R/'config/VIEWS.json'):
  cid=v['id'];root=P18/('hero_fit'if v['role']=='FIT'else'holdout/hero')/cid if v['video']=='004'else R/'hero_fit'/cid
  if not(root/'OBS_TRUSTED.npz').exists():continue
  rows.append(dict(id=cid,video=v['video'],role=v['role'],root=root,obs=dict(np.load(root/'OBS_TRUSTED.npz')),mesh=dict(np.load(root/'TRUSTED_HERO.npz'))))
 return rows

def sample_in_target(X,T,K,target,ring):
 p=(X-T[:3,3])@T[:3,:3];uv=p@K.T;uv=uv[:,:2]/uv[:,2:];ij=np.floor(uv+.5).astype(int);h,w=target.shape;inside=(p[:,2]>0)&(ij[:,0]>=0)&(ij[:,0]<w)&(ij[:,1]>=0)&(ij[:,1]<h);dep=np.full(len(X),np.nan);dep[inside]=target[ij[inside,1],ij[inside,0]];known=inside&np.isfinite(dep);ids=np.flatnonzero(known);cad=np.full(len(X),np.inf)
 if len(ids):
  ray=np.c_[uv[ids],np.ones(len(ids))]@np.linalg.inv(K).T;rays=np.c_[np.broadcast_to(T[:3,3],ray.shape),ray@T[:3,:3].T].astype(np.float32);cad[ids]=ring.cast_rays(o3d.core.Tensor(rays))['t_hit'].numpy()
 cad_occ=known&(p[:,2]>=cad-.05);known&=~cad_occ;dz=p[:,2]-dep;return dict(known=known,cad_occluded=cad_occ,supported=known&(abs(dz)<=.5),front=known&(dz<-.5),behind=known&(dz>.5),dz=dz)

def main():
 assert(R/'provenance/POSE_PREDICTIONS_FROZEN_BEFORE_HOLDOUT.json').exists();ss=sources();rv=np.load(R/'inputs/G01/RING.npz');ring=scene(rv['V'],rv['F']);H=np.asarray(load(R/'results/CROSS_A5_FINAL.json')['T']);bias=load(R/'metrics/RING_HERO_DEPTH_DIAGNOSTIC.json')['stable_trials'];comparisons=[];areas=[]
 for label,Treg,bs in [('H0_NATIVE_UNALIGNED',np.eye(4),{}),('H1_SHARED_REGISTRATION',H,{})]+([('BIAS_TRIAL_NOT_ADOPTED',H,bias)]if bias else[]):
  data=[]
  for s in ss:
   a=s['obs'];b=bs.get(s['id'],0.);ray=np.c_[a['uv'],np.ones(len(a['uv']))]@np.linalg.inv(a['K']).T;X=(ray*(a['z']-b)[:,None])@a['T'][:3,:3].T+a['T'][:3,3];G=Treg if s['video']=='005'else np.eye(4);Xlocal=X.copy();X=X@G[:3,:3].T+G[:3,3];C=G@a['T'];grid=np.full(tuple(a['native_shape']),np.nan);grid[a['uv'][:,1],a['uv'][:,0]]=a['z']-b;data.append(dict(s=s,X=X,X_local=Xlocal,T=C,T_local=a['T'],K=a['K'],grid=grid))
  for a in data:
   s=a['s'];m=s['mesh'];P=m['V'];F=m['F'];cent=P[F].mean(1);G=Treg if s['video']=='005'else np.eye(4);cent=cent@G[:3,:3].T+G[:3,3];facearea=trimesh.triangles.area(P[F]);support=np.zeros(len(F),bool);known=np.zeros(len(F),bool);behind=np.zeros(len(F),bool)
   for b in data:
    if s['id']==b['s']['id']:continue
    relationship='CROSS_VIDEO'if s['video']!=b['s']['video']else'SAME_VIDEO';o=sample_in_target(a['X']if relationship=='CROSS_VIDEO'else a['X_local'],b['T']if relationship=='CROSS_VIDEO'else b['T_local'],b['K'],b['grid'],ring);N=len(a['X']);comparisons.append(dict(condition=label,relationship=relationship,source=s['id'],target=b['s']['id'],source_role=s['role'],target_role=b['s']['role'],fixed_source_N=N,known_N=int(o['known'].sum()),Ring_occluded_N=int(o['cad_occluded'].sum()),supported_N=int(o['supported'].sum()),front_disagreement_proxy_N=int(o['front'].sum()),behind_observed_surface_N=int(o['behind'].sum()),unknown_N=int((~o['known']&~o['cad_occluded']).sum()),known_axial_difference_mm=stats(o['dz'][o['known']]),behind_is_not_free_space_conflict=True,ground_truth=False))
    if relationship=='CROSS_VIDEO':
     o=sample_in_target(cent,b['T'],b['K'],b['grid'],ring);support|=o['supported'];known|=o['known'];behind|=o['behind']
   if label!='BIAS_TRIAL_NOT_ADOPTED':areas.append(dict(condition=label,source=s['id'],video=s['video'],role=s['role'],source_TRUSTED_faces=len(F),source_TRUSTED_area_mm2=float(facearea.sum()),centroid_supported_across_other_video_area_mm2=float(facearea[support].sum()),not_observed_by_other_video_area_proxy_mm2=float(facearea[~known].sum()),self_occluded_or_deeper_area_proxy_mm2=float(facearea[behind&~support].sum()),not_unique_union_area=True,not_certified_complementary_surface=True))
 # A common video-level change cannot change its internal relative camera matrices.
 vv=[v for v in load(R/'config/VIEWS.json')if v['video']=='005'];err=[]
 for i in range(len(vv)-1):
  A=np.asarray(vv[i]['T']);B=np.asarray(vv[i+1]['T']);err.append(np.max(abs(np.linalg.inv(H@A)@(H@B)-np.linalg.inv(A)@B)))
 inv=dict(max_internal_relative_matrix_difference=float(max(err)),all_relative_poses_unchanged=bool(max(err)<1e-10),H2_status='NOT_TRIGGERED_FOR_ORIGINAL_SAME_VIDEO_SUPPORTS',reason='shared left SE3 changes inter-video placement but not original HERO within-video relative cameras; adding cross-video supports would be a separate input-view-set experiment',new_HERO_inference=False,model_weights_updated=False)
 save('metrics/HERO_H0_H1_CONSISTENCY.json',comparisons);table('metrics/HERO_H0_H1_CONSISTENCY.csv',comparisons);save('metrics/HERO_CENTROID_SUPPORT_AREA_PROXIES.json',areas);table('metrics/HERO_CENTROID_SUPPORT_AREA_PROXIES.csv',areas);save('metrics/HERO_RELATIVE_POSE_INVARIANCE.json',inv);print('HERO_INDEPENDENT_DIAGNOSIS_COMPLETE',len(ss),len(comparisons),inv,flush=True)
if __name__=='__main__':main()
