"""Frozen geometry only. Ring scale is immutable; every registration is SE(3)."""
from common import *
from evaluate import area_samples,distance,occupied
from scipy.spatial.transform import Rotation
from scipy.spatial import ConvexHull
from scipy.spatial.distance import pdist
from scipy.stats import qmc
import itertools,open3d as o3d
EVAL_LABEL='After Ring-based Metric Recovery and 6-DoF Rigid Alignment'

def proper_frames():
 out=[]
 for order in itertools.permutations(range(3)):
  for s in itertools.product([-1.,1.],repeat=3):
   A=np.eye(3)[:,order]@np.diag(s)
   if np.linalg.det(A)>.5:out.append(A)
 return out

def pca(P):
 w,Q=np.linalg.eigh(np.cov(P.T));Q=Q[:,np.argsort(w)[::-1]]
 if np.linalg.det(Q)<0:Q[:,-1]*=-1
 return Q

def align(V,F,GV,GF,D):
 P=area_samples(V,F,4096);G=area_samples(GV,GF,20000);A=pca(P);B=pca(G);pc=o3d.geometry.PointCloud(o3d.utility.Vector3dVector(P));gc=o3d.geometry.PointCloud(o3d.utility.Vector3dVector(G));allrows=[];best=None
 for i,S in enumerate(proper_frames()):
  rot=B@S@A.T;T=np.eye(4);T[:3,:3]=rot;T[:3,3]=G.mean(0)-rot@P.mean(0)
  for ratio in [.5,.25,.1]:
   result=o3d.pipelines.registration.registration_icp(pc,gc,ratio*D,T,o3d.pipelines.registration.TransformationEstimationPointToPoint(with_scaling=False),o3d.pipelines.registration.ICPConvergenceCriteria(max_iteration=100));T=result.transformation.copy()
  X=P@T[:3,:3].T+T[:3,3];err=distance(scene(GV,GF),X);AV=V@T[:3,:3].T+T[:3,3];reverse=distance(scene(AV,F),G[::5]);score=float(.5*(err.mean()+reverse.mean()));allrows.append(dict(start=i,symmetric_mean_surface_distance_mm=score,pred_to_GT_mm=float(err.mean()),GT_to_pred_mm=float(reverse.mean()),ICP_fitness=result.fitness,ICP_RMSE=result.inlier_rmse,transform=T))
  if best is None or score<best[0]:best=(score,T.copy())
 return best[1],allrows

def feret(V,n):
 n=np.asarray(n,float);n/=np.linalg.norm(n);a=np.eye(3)[np.argmin(abs(n))];u=np.cross(n,a);u/=np.linalg.norm(u);v=np.cross(n,u);P=np.c_[V@u,V@v];h=P[ConvexHull(P).vertices]
 # A linear projection's maximum diameter is attained at hull vertices.
 return float(np.sqrt(pdist(h,'sqeuclidean').max()))

def main():
 for a in load(R/'assets_index/SCALE_LOCK_BEFORE_GT.json')['files']:assert sha(a['path'])==a['sha256']
 sources={x['case']:x for x in load(R/'evaluation_only/GT_SOURCE_LOCK.json')};scales={x['case']:x for x in load(R/'metrics/RING_SCALE_VALIDATION.json')};native={(x['case'],x['label']):x for x in load(R/'metrics/NATIVE_SUMMARY.json')};rows=[];transforms=[]
 for c in load(R/'config/CASE_LOCK.json'):
  n=c['name'];src=sources[n];gtpath=R/'evaluation_only'/n/'ORIGINAL_BLENDER_GT_MM.npz';reason=src.get('reason','NO_VERIFIED_SOURCE')
  for tag in ['C011','FINAL011','FINAL012']:
   record=dict(case=n,type=c['morphology'],label=tag,evaluation=EVAL_LABEL,target_groups=9,GT_source_status=src['status'],Dxy_GT_mm=None,Dxy_pred_mm=None,Dxy_AE_mm=None,Dxy_relative_error=None,height_max_GT_mm=None,height_max_pred_mm=None,height_max_AE_mm=None,height_max_relative_error=None,H95_GT_mm=None,H95_pred_mm=None,H95_AE_mm=None,H95_relative_error=None,IoU_3D=None,occupancy_IoU_proxy=None,Chamfer_MAE_mm=None,Chamfer_median_mm=None,Chamfer_p95_mm=None,Chamfer_max_mm=None,GT_used_for_training=False,scale_changed_by_registration=False,base_status='NOT_EVALUABLE',not_evaluable_reason=reason)
   nn=native.get((n,tag),{});record.update(FIT_2D_IoU_original_cameras=nn.get('FIT_IoU'),HOLDOUT_2D_IoU_original_cameras=nn.get('HOLDOUT_IoU'),projection_note='Original frozen camera relationship, unaffected by a common rigid frame change; no aligned-mesh-only reprojection')
   path=R/'local_results/metric'/n/(tag+'.npz')
   if not gtpath.exists()or not path.exists():rows.append(record);continue
   z=np.load(path);g=np.load(gtpath);V=z['V'];F=z['F'];Fs=z['F_solid'];GV=g['V'];GF=g['F'];D=scales[n]['true_inner_diameter_mm'];T,trials=align(V,F,GV,GF,D);assert np.linalg.det(T[:3,:3])>.999999 and np.allclose(T[:3,:3].T@T[:3,:3],np.eye(3),atol=1e-8);AV=V@T[:3,:3].T+T[:3,3];out=R/'local_results/aligned'/n;out.mkdir(parents=True,exist_ok=True);np.savez_compressed(out/(tag+'.npz'),V=AV,F=F,F_solid=Fs,inferred_base_faces=z['inferred_base_faces'],T=T);trimesh.Trimesh(AV,Fs,process=False).export(out/(tag+'_mm.ply'));save('metrics/alignment/'+n+'_'+tag+'_STARTS.json',trials);transforms.append(dict(case=n,label=tag,T=T,R=T[:3,:3],t_mm=T[:3,3],det_R=np.linalg.det(T[:3,:3]),scale=1.,method='24 PCA/cube initial rotations, point-to-point rigid ICP, fixed multi-scale budget',evaluation=EVAL_LABEL))
   pr=scene(AV,F);gr=scene(GV,GF);P=area_samples(AV,F,8192);G=area_samples(GV,GF,8192);dp=distance(gr,P);dg=distance(pr,G);combined=stats(np.r_[dp,dg]);record.update(Chamfer_MAE_mm=combined['MAE'],Chamfer_median_mm=combined['median'],Chamfer_p95_mm=combined['p95'],Chamfer_max_mm=combined['maximum'],prediction_to_GT_mm=stats(dp),GT_to_prediction_mm=stats(dg),surface_note='Prediction observation-eligible faces exclude inferred basal closure; unknown back not automatically considered observed',not_evaluable_reason='')
   evidence=np.load(R/'local_results/native_eval'/n/(tag+'_FACE_EVIDENCE.npz'))['face_supported'];fid=pr.compute_closest_points(o3d.core.Tensor(P.astype(np.float32)))['primitive_ids'].numpy().astype(int);supported=evidence[np.clip(fid,0,len(evidence)-1)];record.update(observation_supported_proxy_to_GT_mm=stats(dp[supported]),unobserved_back_to_GT_mm=stats(dp[~supported]),surface_evidence='original FIT camera/Mask/CAD visibility, not GT-selected');capfaces=Fs[z['inferred_base_faces']]
   if len(capfaces):record['inferred_bottom_to_GT_mm']=stats(distance(gr,area_samples(AV,capfaces,1024)))
   base=src.get('author_base')
   if base is not None:
    normal=np.asarray(base['normal'],float);normal/=np.linalg.norm(normal);offset=float(base['offset_mm']);h=AV@normal+offset;gh=GV@normal+offset;dx=feret(AV,normal);gx=feret(GV,normal);H=float(h.max());GH=float(gh.max());h95=float(np.quantile(P@normal+offset,.95));g95=float(np.quantile(G@normal+offset,.95));record.update(Dxy_GT_mm=gx,Dxy_pred_mm=dx,Dxy_AE_mm=abs(dx-gx),Dxy_relative_error=abs(dx-gx)/gx,height_max_GT_mm=GH,height_max_pred_mm=H,height_max_AE_mm=abs(H-GH),height_max_relative_error=abs(H-GH)/abs(GH)if GH else None,H95_GT_mm=g95,H95_pred_mm=h95,H95_AE_mm=abs(h95-g95),H95_relative_error=abs(h95-g95)/abs(g95)if g95 else None,H95_area_uniform_sample_N_each=8192,base_status=base['qualification'],base_evidence=base['evidence'])
   else:record['not_evaluable_reason']='AUTHOR_BASE_DIRECTION_NOT_ESTABLISHED_FOR_DXY_OR_HEIGHT'
   pm=trimesh.Trimesh(AV,Fs,process=False);gm=trimesh.Trimesh(GV,GF,process=False);record.update(pred_watertight=bool(pm.is_watertight),GT_watertight=bool(gm.is_watertight),pred_winding_consistent=bool(pm.is_winding_consistent),GT_winding_consistent=bool(gm.is_winding_consistent))
   # Strict volume validity also requires independent non-self-intersection evidence.
   check=next((a for a in load(R/'metrics/BLENDER_GEOMETRY_CHECKS.json')if a['case']==n and a['label']==tag),None);GTcheck=next(a for a in load(R/'metrics/GT_VALIDITY.json')if a['case']==n).get('GT_self_intersections_N')
   valid=pm.is_watertight and gm.is_watertight and pm.is_winding_consistent and gm.is_winding_consistent and check is not None and check['self_intersections_N']==0 and GTcheck==0
   if valid:
    lo=np.minimum(AV.min(0),GV.min(0));hi=np.maximum(AV.max(0),GV.max(0));Q=lo+(hi-lo)*qmc.Sobol(3,scramble=True,seed=20261108).random_base2(17);op=occupied(scene(AV,Fs),Q);og=occupied(gr,Q);union=int((op|og).sum());inter=int((op&og).sum());iou=inter/union if union else None;record.update(occupancy_IoU_proxy=iou,occupancy_sample_N=len(Q),occupancy_union_N=union,occupancy_intersection_N=inter,occupancy_sampling_note='Fixed Sobol occupancy estimate, not exact Boolean volume; proxy if inferred/unreliable bottom',IoU_3D=iou if not z['inferred_base_faces'].any()and src.get('GT_bottom_reliable',False)else None,IoU_3D_status='VALID_SOLID_SAMPLED_ESTIMATE'if not z['inferred_base_faces'].any()and src.get('GT_bottom_reliable',False)else'NOT_EVALUABLE_STRICT_INFERRED_OR_UNCERTAIN_BASE')
   else:record['IoU_3D_status']='NOT_EVALUABLE_ENTITY_VALIDITY_OR_SELF_INTERSECTION_UNCERTIFIED'
   rows.append(record);print('RIGID_EVAL',n,tag,record['Dxy_AE_mm'],record['Chamfer_MAE_mm'],flush=True)
 save('metrics/BLENDER_RIGID_ALIGNMENT.json',transforms);table('metrics/BLENDER_RIGID_ALIGNMENT.csv',transforms);save('metrics/BLENDER_GEOMETRIC_METRICS.json',rows);table('metrics/BLENDER_GEOMETRIC_METRICS.csv',rows)

if __name__=='__main__':main()
