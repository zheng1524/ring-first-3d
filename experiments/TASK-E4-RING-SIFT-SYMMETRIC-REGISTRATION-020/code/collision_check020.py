"""Repair an independently diagnosed single-ray CAD sign ambiguity; never optimize poses."""
from common import *
from evaluate020 import methods
import open3d as o3d
import shutil

def main():
 old=R/'provenance/single_ray_collision_before_repair';old.mkdir(exist_ok=True)
 for name in ['HERO_RING_SAMPLE_COLLISION_AUDIT.json','HERO_RING_SAMPLE_COLLISION_AUDIT.csv']:
  if not(old/name).exists():shutil.copyfile(R/'metrics'/name,old/name)
 rv=np.load(R/'inputs/G01/RING.npz');cad=scene(rv['V'],rv['F']);mesh=trimesh.Trimesh(rv['V'],rv['F'],process=False)
 # Tube center, hole center, and the observed false-negative sample. Known CAD only.
 X=np.array([[5.6,0,0],[0,0,0],[-5.5959363,-3.18684125,-7.85248423]],np.float32)
 S=o3d.core.Tensor(X);one=cad.compute_signed_distance(S).numpy();multi=cad.compute_signed_distance(S,nsamples=11).numpy();unsigned=cad.compute_distance(S).numpy()
 assert mesh.is_watertight and mesh.is_winding_consistent
 assert multi[0]<0 and multi[1]>0 and multi[2]>7 and np.allclose(abs(multi),unsigned)
 save('provenance/SIGNED_DISTANCE_PARITY_REPAIR.json',dict(reason='Single parity ray misclassified a point 7.297mm outside a 0.6mm-radius CAD tube as inside; 11-ray majority resolves edge-hit ambiguity. Evaluation-only; original results preserved; no pose/loss/threshold changes.',cad=asset(R/'inputs/G01/RING.npz'),points_mm=X,single_ray_mm=one,eleven_ray_mm=multi,unsigned_distance_mm=unsigned,old_files=[asset(old/n)for n in ['HERO_RING_SAMPLE_COLLISION_AUDIT.json','HERO_RING_SAMPLE_COLLISION_AUDIT.csv']],watertight=True,winding_consistent=True))
 out=[]
 for method in methods():
  H=np.asarray(method['T'])
  for s in load(R/'config/HERO_EVALUATION_SOURCES.json'):
   d=np.load(s['mesh']['path']);P=d['V'];F=d['F'];P=P@H[:3,:3].T+H[:3,3]if s['video']=='005'else P
   ix=np.unique(F);X=np.r_[P[ix],P[F].mean(1)];sd=cad.compute_signed_distance(o3d.core.Tensor(X.astype(np.float32)),nsamples=11).numpy()
   out.append(dict(method=method['method'],source=s['id'],video=s['video'],referenced_vertex_N=len(ix),face_center_N=len(F),vertices_inside_CAD_N=int((sd[:len(ix)]<-.02).sum()),face_centers_inside_CAD_N=int((sd[len(ix):]<-.02).sum()),min_signed_distance_mm=float(sd.min()),diagnostic_tolerance_mm=.02,parity_ray_samples=11,not_exact_triangle_intersection_certification=True))
  print('CAD_PARITY_CHECK020',method['method'],flush=True)
 save('metrics/HERO_RING_SAMPLE_COLLISION_AUDIT.json',out);table('metrics/HERO_RING_SAMPLE_COLLISION_AUDIT.csv',out)
 print('CAD_PARITY_CHECK020_COMPLETE',flush=True)
if __name__=='__main__':main()
