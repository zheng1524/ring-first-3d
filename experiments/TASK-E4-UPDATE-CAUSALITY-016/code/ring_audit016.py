"""Actual CAD witnesses and frozen initializer collision categories; CPU only."""
from common import *
from safe_geometry import dense_face_distance
import open3d as o3d

def main():
 old=REPO/'experiments/TASK-E4-MULTIVIEW-INIT-STALK-015';a=load(old/'metrics/PHASE_A_ALL_METRICS.json');rows=[]
 for n in ['G03','G07','G05','G06']:
  rr=[x for x in a if x['case']==n];base=next(x['geometry']for x in rr if x['arm']=='Init-A'and x['stage']=='INITIAL')['dense_Ring_penetration_mm']
  for tag in ['Init-A','Init-B','Init-C']:
   gi=next(x['geometry']for x in rr if x['arm']==tag and x['stage']=='INITIAL');gf=next(x['geometry']for x in rr if x['arm']==tag and x['stage']=='FINAL');initial=gi['dense_Ring_penetration_mm'];final=gf['dense_Ring_penetration_mm'];rows.append(dict(case=n,arm=tag,common_original_penetration_mm=base,initial_penetration_mm=initial,final_penetration_mm=final,initial_status='NEW_PENETRATION'if base==0 and initial>1e-5 else'PREEXISTING_WORSENED_INITIALIZATION'if initial>base+1e-5 else'PREEXISTING'if initial>0 else'NO_SAMPLED_PENETRATION',update_status='WORSENED'if final>initial+1e-5 else'IMPROVED'if final<initial-1e-5 else'WITHIN_1E_5_MM_TOLERANCE',original_geometry=gi,final_geometry=gf))
 save('metrics/INITIALIZATION_COLLISION_CAUSES.json',rows);table('metrics/INITIALIZATION_COLLISION_CAUSES.csv',rows)
 for n in ['G03','G01']:
  root=R/'arms/DIAGNOSTIC';p=root/'local_results'/(n+'_FULL_ORIGINAL_SHADOW.npz');z=np.load(p);fixed=np.load(root/'local_results'/(n+'_FULL_CONTACT_FACE_FIXED_SHADOW.npz'));rg=np.load(R/'inputs'/n/'RING.npz');rs=scene(rg['V'],rg['F']);V0,V1,F=z['before_V'],z['V'],z['F_solid'];g=np.load(root/'metrics'/(n+'_CAUSAL_TAPE.npz'));sd0=dense_face_distance(rs,V0,F,rg['V'],32,rg['F']);sd1=dense_face_distance(rs,V1,F,rg['V'],32,rg['F']);sd64=dense_face_distance(rs,V1,F,rg['V'],64,rg['F']);violation=sd1-np.minimum(sd0,0);ids=np.argsort(violation)[:min(20,len(F))];bary=np.array([(i/32,j/32,1-(i+j)/32)for i in range(33)for j in range(33-i)]);before=[];after=[];bs=[];witness=[]
  full=sum(g[k]for k in ['silhouette','missing','extra','contour','absolute','relative','prior']);step_scale=.2/max(1e-30,np.linalg.norm(full,axis=1).max())
  for fid in ids:
   ps=bary@V1[F[fid]];ss=rs.compute_signed_distance(o3d.core.Tensor(ps.astype(np.float32)),nsamples=3).numpy();j=int(ss.argmin());b=bary[j];oldp=b@V0[F[fid]];newp=ps[j];eps=.001;dd=[]
   for axis in range(3):
    e=np.eye(3)[axis]*eps;s=rs.compute_signed_distance(o3d.core.Tensor(np.array([oldp+e,oldp-e],np.float32)),nsamples=3).numpy();dd.append(float((s[0]-s[1])/(2*eps)))
   normal=np.array(dd);normal/=max(1e-30,np.linalg.norm(normal));components={k:float(normal@(-step_scale*(b@g[k][F[fid]])))for k in ['silhouette','missing','extra','contour','absolute','relative','prior']};byview={k:float(normal@(-step_scale*(b@g[k][F[fid]])))for k in g.files if'__'in k};witness.append(dict(case=n,original_face_id=int(fid),original_vertex_ids=F[fid],barycentric=b,before_point_mm=oldp,candidate_point_mm=newp,CAD_outward_normal=normal,actual_normal_displacement_mm=float(normal@(newp-oldp)),predicted_component_normal_motion_mm=components,per_view_component_normal_motion_mm=byview,initial_face_signed_mm=float(sd0[fid]),candidate_face_signed_mm=float(sd1[fid]),guard_face_limit_mm=float(min(sd0[fid],0)-1e-5),penetration_worsened=bool(sd1[fid]<min(sd0[fid],0)-1e-5),SDF32_vs64_difference_mm=float(sd1[fid]-sd64[fid]),visibility_unknown_not_a_collision_exemption=True));before.append(oldp);after.append(newp);bs.append(b)
  np.savez_compressed(R/'local_results'/(n+'_RING_WITNESSES.npz'),V0=V0,V1=V1,Vfixed=fixed['V'],F=F,ringV=rg['V'],ringF=rg['F'],witness_faces=ids,witness_before=np.array(before),witness_after=np.array(after),face_SD0=sd0,face_SD1=sd1,face_SD64=sd64,pinned_vertices=z['pinned_vertices']);save('metrics/'+n+'_RING_WITNESS_ATTRIBUTION.json',witness)
 print('RING_WITNESS_AUDIT_COMPLETE',flush=True)
if __name__=='__main__':main()
