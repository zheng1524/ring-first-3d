from common import *
import open3d as o3d

def main():
 assert(R/'assets_index/SCALE_LOCK_BEFORE_GT.json').exists();rows=[]
 for src in load(R/'evaluation_only/GT_SOURCE_LOCK.json'):
  n=src['case'];p=R/'evaluation_only'/n/'ORIGINAL_BLENDER_GT_MM.npz'
  if not p.exists():rows.append(dict(case=n,status='NOT_EVALUABLE',reason=src.get('reason','GT_NOT_EXPORTED'),GT_self_intersections_N=None));continue
  z=np.load(p);m=trimesh.Trimesh(z['V'],z['F'],process=False);o=o3d.geometry.TriangleMesh(o3d.utility.Vector3dVector(z['V']),o3d.utility.Vector3iVector(z['F']));pairs=np.asarray(o.get_self_intersecting_triangles());rows.append(dict(case=n,status='EXPORTED_AND_CHECKED',GT_self_intersections_N=len(pairs),self_pairs=pairs[:100],watertight=bool(m.is_watertight),winding_consistent=bool(m.is_winding_consistent),connected_components=len(m.split(only_watertight=False)),vertices=len(z['V']),faces=len(z['F']),source=asset(p),backend='Open3D TriangleMesh.get_self_intersecting_triangles',source_geometry_unchanged=True));print('GT_VALIDITY',n,len(pairs),m.is_watertight,flush=True)
 save('metrics/GT_VALIDITY.json',rows);table('metrics/GT_VALIDITY.csv',rows)

if __name__=='__main__':main()
