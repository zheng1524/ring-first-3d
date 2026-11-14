"""Frozen-output identity, weight, metric and stability diagnostics. No fitting."""
from joint_ba import *
def main():
 checkfreeze('provenance/ALL_FINAL_CAMERA_CANDIDATES_FROZEN_BEFORE_HERO.json');tracks=load(N/'config/TRACKS.json');fs={};obsN=0;fitH=[]
 for t in tracks:
  for o in t['observations']:
   sid=o['view']
   if sid not in fs:fs[sid]=dict(np.load(N/'features'/(sid+'.npz')))
   assert np.allclose(fs[sid]['xy'][o['feature_id']],o['uv'],atol=0,rtol=0);obsN+=1
 save('metrics/ALL_NATIVE_RGB_IDENTITIES_VERIFIED.json',dict(tracks=len(tracks),exact_feature_pixel_observations=obsN,image_files=len(fs),cross_video_shared_tracks=sum(t['cross_video']for t in tracks),identity_from='onlyfrozenRGBtrackIDand021crossRGBlinks',XYZ_nearest_identity_links=0,GT=False))
 weights=[];moves=[];relative=[]
 for g in GROUPS:
  o=Joint(g,'B3');r=load(N/'results'/g/'B3/FINAL.json');o.restore(r);tot=sum(x['weight']for x in o.obs)
  for vid in o.H:
   os=[x for x in o.obs if o.vd[x['view']]['video']==vid];weights.append(dict(group=g,video=vid,observations_N=len(os),RGB_weight_sum=sum(x['weight']for x in os),RGB_weight_fraction=sum(x['weight']for x in os)/tot,Ring_weight_sum=sum(o.weights[v['id']]for v in o.fit if v['video']==vid),normalization='pertrackwithinvideo/direction;notglobalequalvideoweightingacrosstrackcount'))
  for k,x in o.X.items():moves.append(dict(group=g,track_id=k,XYZ_displacement_mm=float(np.linalg.norm(x-o.X0[k])),identity=next(t['identity']for t in o.tracks if t['track_id']==k)))
  for m in ['B0','B1','B2','B3']:
   rr=load(N/'results'/g/m/'FINAL.json')
   if not rr.get('poses'):continue
   for vid in o.H:
    vs=[v for v in o.views if v['video']==vid]
    for a,b in zip(vs[:-1],vs[1:]):
     C0=np.linalg.inv(np.array(a['T']))@np.array(b['T']);C1=np.linalg.inv(np.array(rr['poses'][a['id']]))@np.array(rr['poses'][b['id']]);D=C1@np.linalg.inv(C0);relative.append(dict(group=g,method=m,video=vid,first=a['id'],second=b['id'],relative_translation_change_mm=float(np.linalg.norm(D[:3,3])),relative_rotation_change_deg=float(np.degrees(Rotation.from_matrix(D[:3,:3]).magnitude()))))
 a=load(N/'results/G01/B3/FINAL.json');b=load(N/'results/SENSITIVITY/G01_B3_FIXED_PERTURBATION/FINAL.json');d=[];rot=[]
 for cid in a['poses']:
  A=np.array(a['poses'][cid]);B=np.array(b['poses'][cid]);d.append(np.linalg.norm(A[:3,3]-B[:3,3]));rot.append(np.degrees(Rotation.from_matrix(A[:3,:3]@B[:3,:3].T).magnitude()))
 save('metrics/PREREGISTERED_MULTISTART_COMPARISON.json',dict(group='G01',starts=2,main_fit_loss=a['loss'],perturbed_fit_loss=b['loss'],center_dispersion_mm=stats(d),rotation_dispersion_deg=stats(rot),primary_unchanged=True,not_selected_by_HOLDOUT_HERO=True,limited_sensitivity_not_global_convergence=True));table('metrics/ACTUAL_VIDEO_WEIGHT_SHARES.csv',weights);save('metrics/ACTUAL_VIDEO_WEIGHT_SHARES.json',weights);table('metrics/LANDMARK_ACTUAL_DRIFT.csv',moves);save('metrics/LANDMARK_ACTUAL_DRIFT.json',moves);table('metrics/INTERNAL_RELATIVE_CAMERA_CHANGES.csv',relative);save('metrics/INTERNAL_RELATIVE_CAMERA_CHANGES.json',relative)
 print('FROZEN_ADDITIONAL_AUDIT',obsN,'realobs',flush=True)
if __name__=='__main__':main()
