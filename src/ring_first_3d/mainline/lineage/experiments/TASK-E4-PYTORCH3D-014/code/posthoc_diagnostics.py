"""Frozen-prediction diagnostics; no GT, optimizer, selection, or mesh mutation."""
from common import *
from safe_geometry import self_intersections
import open3d as o3d

def video_support():
 n='G01';meta=getcase(n);observations=[v for v in meta['views']if v['role']=='FIT'];rg=np.load(R/'inputs'/n/'RING.npz');rs=scene(rg['V'],rg['F']);per=load(R/'metrics/PER_VIEW_METRICS.json');rows=[];baseline=None;Avertices=None
 for tag in ['B_A_ONLY','B0_UNCORRECTED','C1_8']:
  a=np.load(R/'arms'/tag/'local_results'/n/'FINAL.npz');V,F=a['V'],a['F'];P=V[F].mean(1);rt=scene(V,F);support={v:np.zeros(len(F),bool)for v in ['004','005']}
  for v in observations:
   b=np.load(R/'inputs'/n/(v['id']+'.npz'));T,K=b['T'],b['K'];cam=(P-T[:3,3])@T[:3,:3];zz=cam[:,2];pix=cam@K.T;uv=pix[:,:2]/pix[:,2:];inside=(zz>0)&(uv[:,0]>=0)&(uv[:,0]<640)&(uv[:,1]>=0)&(uv[:,1]<360);ij=np.clip(np.rint(uv).astype(int),[0,0],[639,359]);rr=np.c_[np.broadcast_to(T[:3,3],P.shape),(P-T[:3,3])/np.maximum(zz[:,None],1e-12)].astype(np.float32);first=rt.cast_rays(o3d.core.Tensor(rr),nthreads=2)['t_hit'].numpy();cad=rs.cast_rays(o3d.core.Tensor(rr),nthreads=2)['t_hit'].numpy();support[v['video']]|=inside&(b['labels'][ij[:,1],ij[:,0]]==1)&(zz<cad)&(abs(zz-first)<.05)
  area=trimesh.triangles.area(V[F]);total=area.sum()
  if baseline is None:baseline=V.copy();Avertices=np.unique(F[support['004']])
  drift=np.linalg.norm(V[Avertices]-baseline[Avertices],axis=1);q=dict(case=n,arm=tag,A_support_area_fraction=float(area[support['004']].sum()/total),B_only_support_area_fraction=float(area[support['005']&~support['004']].sum()/total),AB_shared_support_area_fraction=float(area[support['005']&support['004']].sum()/total),A_supported_vertex_drift_from_Aonly_mm=stats(drift),definition='FIT Mask+first-ray+CAD centroid support proxy at common frozen B1 cameras; B-only evidence is NOT new true geometry or GT coverage',GT_used=False)
  for video in ['004','005']:
   for role in ['FIT','UPDATE_HOLDOUT']:
    rr=[x for x in per if x['case']==n and x['tag']==tag and x['video']==video and x['role']==role];q[video+'_'+role+'_IoU']=float(np.mean([x['IoU']for x in rr]))
  rows.append(q)
 save('metrics/G01_VIDEO_STABILITY_AND_COVERAGE.json',rows);table('metrics/G01_VIDEO_STABILITY_AND_COVERAGE.csv',rows)

def self_contact():
 q=next(x for x in load(R/'metrics/POST_GEOMETRY_VALIDITY.json')if x['case']=='G10'and x['label']=='FINAL014');a=np.load(R/'arms/FINAL_014/local_results/G10/FINAL.npz');V,F=a['V'],a['F_solid'];rows=[]
 for i,j in q['self_pairs']:
  A=trimesh.Trimesh(V[F[i]],[[0,1,2]],process=False);B=trimesh.Trimesh(V[F[j]],[[0,1,2]],process=False);cm=trimesh.collision.CollisionManager();cm.add_object('A',A);rows.append(dict(face_i=i,face_j=j,FCL_double_pair_collision=bool(cm.in_collision_single(B)),FCL_double_min_distance_mm=float(cm.min_distance_single(B))))
 answer=dict(case='G10',label='FINAL014',Open3D_original_double=self_intersections(V,F)['intersections'],Open3D_float32_coordinates_promoted_to_double=self_intersections(V.astype(np.float32).astype(float),F)['intersections'],Blender_BVH_float32_pairs=q['self_intersections_N'],pair_diagnostics=rows,prediction_unchanged=True,original_Blender_failure_retained=True,GT_used=False)
 save('metrics/G10_SELF_INTERSECTION_DISAGREEMENT.json',answer)

def ring_contact():
 n='G01';a=np.load(R/'arms/FINAL_014/local_results'/n/'FINAL.npz');rr=np.load(R/'inputs'/n/'RING.npz');V,F=a['V'],a['F_solid'];W,G=rr['V'],rr['F'];cm=trimesh.collision.CollisionManager();cm.add_object('Ring',trimesh.Trimesh(W,G,process=False));body=trimesh.Trimesh(V,F,process=False);combined=np.r_[V,W];faces=np.r_[F,G+len(V)]
 q=next(x for x in load(R/'metrics/POST_GEOMETRY_VALIDITY.json')if x['case']==n and x['label']=='FINAL014')
 ans=dict(case=n,label='FINAL014',FCL_double_collision=bool(cm.in_collision_single(body)),FCL_double_min_distance_mm=float(cm.min_distance_single(body)),Open3D_combined_double_intersection_pairs=self_intersections(combined,faces)['intersections'],Open3D_combined_float32_intersection_pairs=self_intersections(combined.astype(np.float32).astype(float),faces)['intersections'],Blender_float32_Ring_pairs=q['Ring_pairs_N'],note='Precision-sensitive near contact; original BVH evidence retained. Contact candidates are not a measured material penetration depth. No threshold, scale, vertex or topology changes.',GT_used=False)
 save('metrics/G01_RING_CONTACT_DISAGREEMENT.json',ans)

if __name__=='__main__':
 assert(R/'provenance/ALL_014_PREDICTIONS_AND_SCALE_FROZEN_BEFORE_GT.json').exists()
 video_support()
 # Do not overwrite the independently recorded original self-contact evidence.
 if not(R/'metrics/G10_SELF_INTERSECTION_DISAGREEMENT.json').exists():self_contact()
 if not(R/'metrics/G01_RING_CONTACT_DISAGREEMENT.json').exists():ring_contact()
