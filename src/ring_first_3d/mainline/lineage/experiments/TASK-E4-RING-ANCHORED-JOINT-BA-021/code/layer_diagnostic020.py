"""Fixed native CORE rays: multiple original-source first-depth hypotheses, not fusion."""
from common import *
from evaluate020 import methods
import open3d as o3d

def modes(D,gap=.5):
 z=np.sort(D,axis=0);valid=np.isfinite(z);n=valid[0].astype(int)
 with np.errstate(invalid='ignore'):n+=((np.diff(z,axis=0)>gap)&valid[1:]).sum(0)
 return n

def main():
 plan=load(R/'config/HERO_LAYER_RAY_PLAN.json')
 while not(R/'provenance/ALL_POSES_FROZEN_BEFORE_EVALUATION.json').exists():time.sleep(5)
 for a in load(R/'provenance/ALL_POSES_FROZEN_BEFORE_EVALUATION.json')['files']:assert sha(a['path'])==a['sha256']
 ss=load(R/'config/HERO_EVALUATION_SOURCES.json');ref={s['id']:s for s in ss};rv=np.load(R/'inputs/G01/RING.npz');cad=scene(rv['V'],rv['F']);refs=[]
 for cid in plan['reference_ids']:
  d=np.load(ref[cid]['observation']['path']);K=d['K'];C=d['T'];uv=d['uv'];p=np.c_[uv,np.ones(len(uv))]@np.linalg.inv(K).T;rays=np.c_[np.broadcast_to(C[:3,3],p.shape),p@C[:3,:3].T].astype(np.float32);rz=cad.cast_rays(o3d.core.Tensor(rays))['t_hit'].numpy();refs.append(dict(id=cid,N=len(uv),rays=rays,Ring_z=rz,source_native_z=d['z']))
 out=[];collision=[]
 for method in methods():
  H=np.asarray(method['T']);depths=[[]for _ in refs];videos=[]
  for s in ss:
   m=np.load(s['mesh']['path']);P=m['V'];F=m['F'];P=P@H[:3,:3].T+H[:3,3]if s['video']=='005'else P;sc=scene(P,F);videos.append(s['video']);ix=np.unique(F);X=np.r_[P[ix],P[F].mean(1)];sd=cad.compute_signed_distance(o3d.core.Tensor(X.astype(np.float32)),nsamples=11).numpy();collision.append(dict(method=method['method'],source=s['id'],video=s['video'],referenced_vertex_N=len(ix),face_center_N=len(F),vertices_inside_CAD_N=int((sd[:len(ix)]<-.02).sum()),face_centers_inside_CAD_N=int((sd[len(ix):]<-.02).sum()),min_signed_distance_mm=float(sd.min()),diagnostic_tolerance_mm=.02,parity_ray_samples=11,not_exact_triangle_intersection_certification=True))
   for i,ref0 in enumerate(refs):
    z=sc.cast_rays(o3d.core.Tensor(ref0['rays']))['t_hit'].numpy().astype(float);z[z>=ref0['Ring_z']-.05]=np.inf;depths[i].append(z)
  for ref0,dep in zip(refs,depths):
   D=np.asarray(dep);vid=np.array(videos);allm=modes(D);m4=modes(D[vid=='004']);m5=modes(D[vid=='005']);min4=D[vid=='004'].min(0);min5=D[vid=='005'].min(0);both=np.isfinite(min4)&np.isfinite(min5);res=min5[both]-min4[both];out.append(dict(method=method['method'],reference=ref0['id'],fixed_native_TRUSTED_ray_N=ref0['N'],any_hit_N=int((allm>0).sum()),multi_source_depth_modes_ge2_N=int((allm>=2).sum()),video004_only_modes_ge2_N=int((m4>=2).sum()),video005_only_modes_ge2_N=int((m5>=2).sum()),both_videos_hit_N=int(both.sum()),video005_first_in_front_004_by05mm_N=int((res<-.5).sum()),video005_first_behind004_by05mm_N=int((res>.5).sum()),cross_first_depth_difference_mm=stats(res),depth_cluster_gap_mm=.5,not_physical_wrong_layer_GT=True,not_fusion=True))
  print('HERO_LAYER020',method['method'],flush=True)
 save('metrics/HERO_MULTILAYER_NATIVE_RAY_PROXY.json',out);table('metrics/HERO_MULTILAYER_NATIVE_RAY_PROXY.csv',out);save('metrics/HERO_RING_SAMPLE_COLLISION_AUDIT.json',collision);table('metrics/HERO_RING_SAMPLE_COLLISION_AUDIT.csv',collision);print('HERO_NATIVE_RAY_MULTILAYER_COMPLETE',flush=True)
if __name__=='__main__':main()
