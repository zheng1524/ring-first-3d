"""Frozen-only nearest-face feasibility audit, NEVER a loss or selection signal."""
from common import *
import open3d as o3d

def main():
 assert(R/'provenance/ALL_OPTIMIZED_PREDICTIONS_FROZEN.json').exists();rows=[];plan=load(R/'config/VIEW_PLAN.json')
 for g in ['G06','G05','G01','G03']:
  rv=np.load(R/'inputs'/g/'RING.npz');ring=scene(rv['V'],rv['F'])
  for arm in ['B0_FROZEN','B2_TRUSTED_COH16']:
   zz=np.load(R/'inputs'/g/'INITIAL.npz'if arm=='B0_FROZEN'else R/'arms'/arm/'local_results'/g/'FINAL.npz');V,F=zz['V'],zz['F'];rt=scene(V,F);norm=trimesh.Trimesh(V,F,process=False).face_normals
   for r in plan:
    if r['group']!=g or r['role']!='FIT':continue
    cid=r['view_id'];a=np.load(R/'hero_fit'/cid/'OBS_TRUSTED.npz');ev=np.load(R/'evaluation/local_results'/g/arm/(cid+'_EVAL.npz'));miss=~ev['active'];X=a['X'][miss];uv=a['uv'][miss];K,T=a['K'],a['T']
    if not len(X):rows.append(dict(group=g,arm=arm,view=cid,missing_N=0));continue
    hit=rt.compute_closest_points(o3d.core.Tensor(X.astype(np.float32)));Q=hit['points'].numpy().astype(float);fid=hit['primitive_ids'].numpy().astype(int);P=(Q-T[:3,3])@T[:3,:3];U=P@K.T;proj=U[:,:2]/U[:,2:];gap=np.linalg.norm(proj-uv,axis=1);rays=np.c_[np.broadcast_to(T[:3,3],Q.shape),(Q-T[:3,3])/P[:,2:3]].astype(np.float32);bodyz=rt.cast_rays(o3d.core.Tensor(rays))['t_hit'].numpy();ringz=ring.cast_rays(o3d.core.Tensor(rays))['t_hit'].numpy();hidden_body=bodyz<P[:,2]-.05;hidden_ring=ringz<P[:,2]-.05;back=(norm[fid]*(T[:3,3]-Q)).sum(1)<0
    rows.append(dict(group=g,arm=arm,view=cid,missing_N=len(X),unrestricted_closest_distance_mm=stats(np.linalg.norm(Q-X,axis=1)),closest_point_reprojection_gap_native_px=stats(gap),closest_backfacing_N=int(back.sum()),closest_occluded_by_body_N=int(hidden_body.sum()),closest_occluded_by_CAD_N=int(hidden_ring.sum()),missing_HERO_XYZ_min=X.min(0),missing_HERO_XYZ_max=X.max(0),global_closest_not_a_validated_correspondence=True,optimization_use=False))
    out=R/'evaluation/local_results'/g/arm/(cid+'_MISSING_GLOBAL_CLOSEST_DIAGNOSTIC.npz');np.savez_compressed(out,source_pixel_id=a['pixel_id'][miss],HERO_X=X,closest_body_point=Q,closest_body_face_id=fid,source_uv=uv,closest_point_projected_uv=proj,hidden_body=hidden_body,hidden_CAD=hidden_ring,backfacing=back)
 api=REPO/'experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runtime/pytorch3d/pytorch3d/loss/point_mesh_distance.py';save('evaluation/metrics/NO_HIT_POINT_MESH_FEASIBILITY.json',dict(rows=rows,official_API=asset(api),API_semantics='point_face_distance is closest unsigned squared distance across all faces within each batch item; source-camera visibility/projective-neighbour restrictions are not automatically enforced',current_implementation='no missing-depth gradient; silhouette still active; Open3D closest queries here are frozen-only diagnostics, never added to optimizer',GT=False));table('evaluation/metrics/NO_HIT_POINT_MESH_FEASIBILITY.csv',rows);print('FROZEN_ONLY_NO_HIT_FEASIBILITY_DIAGNOSTIC_DONE',flush=True)
if __name__=='__main__':main()
