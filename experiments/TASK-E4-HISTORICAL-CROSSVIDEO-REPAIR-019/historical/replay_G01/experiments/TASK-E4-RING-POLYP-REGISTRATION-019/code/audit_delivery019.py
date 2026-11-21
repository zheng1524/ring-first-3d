"""Read-only post-freeze integrity, visibility and geometry audit; no pose selection."""
from common import *
from hero_diagnosis019 import sources
from scipy.spatial.transform import Rotation
import open3d as o3d

def main():
 freeze=load(R/'provenance/POSE_PREDICTIONS_FROZEN_BEFORE_HOLDOUT.json');original=load(R/'provenance/INPUT_FROZEN.json');before=load(R/'provenance/BEFORE_SEARCH_FREEZE.json');checks=[]
 for label,arr in [('original_assets',original['assets']),('frozen_predictions',freeze['results']),('current_config',[before[k]for k in ['views','protocol','written_protocol','body']])]:
  for a in arr:checks.append(dict(kind=label,path=a['path'],expected_SHA256=a['sha256'],actual_SHA256=sha(a['path']),unchanged=sha(a['path'])==a['sha256']))
 assert all(x['unchanged']for x in checks)
 vv=load(R/'config/VIEWS.json');held={v['id']for v in vv if v['role']=='HOLDOUT'};used=set(load(R/'provenance/FEATURE_FIT_FREEZE.json')['all_image_ids']);assert not held&used
 H=np.asarray(load(R/'results/CROSS_A5_FINAL.json')['T']);b=np.load(R/'inputs/G01/BODY018.npz');rv=np.load(R/'inputs/G01/RING.npz');cad=scene(rv['V'],rv['F']);cheirality=[];cameras=[]
 for v in vv:
  C=(H@v['T'])if v['video']=='005'else np.asarray(v['T']);z=(b['V']-C[:3,3])@C[:3,2];cheirality.append(dict(view=v['id'],body_min_axial_mm=float(z.min()),all_body_in_front=bool((z>0).all())));a=np.load(v['cache']);assert np.array_equal(a['T'],np.asarray(v['T']));assert sha(v['RGB_source'])==v['RGB_SHA256'];assert sha(v['Mask_source'])==v['Mask_SHA256'];cameras.append(dict(view=v['id'],camera_cache_equal_frozen_config=True,RGB_Mask_source_unchanged=True))
 assert all(a['all_body_in_front']for a in cheirality)
 # Independent CAD visibility check of real SIFT landmark correspondences, not a retroactive FIT filter.
 vv={v['id']:v for v in vv};featurevis=[]
 for label in ['CROSS','CROSS_HOLDOUT']:
  for p in load(R/'features'/(label+'_PNP.json')):
   if not p['success']:continue
   v=vv[p['target']];T=H@v['T'];X=np.asarray(p['landmark_X']);P=(X-T[:3,3])@T[:3,:3];r=P/P[:,2:];rays=np.c_[np.broadcast_to(T[:3,3],r.shape),r@T[:3,:3].T].astype(np.float32);z=cad.cast_rays(o3d.core.Tensor(rays))['t_hit'].numpy();featurevis.append(dict(set=label,view=v['id'],N=len(X),CAD_before_landmark_N=int((z<P[:,2]-.05).sum()),behind_camera_N=int((P[:,2]<=0).sum()),not_used_to_filter_fit=True))
 collision=[]
 for s in sources():
  m=s['mesh'];P=m['V'];F=m['F'];referenced=np.unique(F);X=np.r_[P[referenced],P[F].mean(1)];half=len(referenced)
  for condition,G in [('H0_NATIVE',np.eye(4)),('H1_REGISTERED',H if s['video']=='005'else np.eye(4))]:
   Y=X@G[:3,:3].T+G[:3,3];sd=cad.compute_signed_distance(o3d.core.Tensor(Y.astype(np.float32))).numpy();collision.append(dict(source=s['id'],video=s['video'],role=s['role'],condition=condition,vertex_N=half,centroid_N=len(F),vertices_inside_CAD_N=int((sd[:half]<-.02).sum()),centroids_inside_CAD_N=int((sd[half:]<-.02).sum()),min_signed_distance_mm=float(sd.min()),diagnostic_threshold_mm=.02,scope='all vertices and face centroids; NOT exact triangle-triangle intersection certification'))
 old=R/'metrics/HERO_CAD_INTERIOR_SAMPLE_AUDIT.json';backup=R/'provenance/UNREFERENCED_VERTEX_DIAGNOSTIC_SUPERSEDED.json'
 if old.exists()and not backup.exists():save(str(backup.relative_to(R)),dict(reason='Initial post-freeze audit counted V entries unreferenced by TRUSTED F; these are not retained surface. Corrected to referenced vertices plus unchanged face centroids. Pose/optimization never used these counts.',raw=load(old)))
 save('metrics/HERO_CAD_INTERIOR_SAMPLE_AUDIT.json',collision);table('metrics/HERO_CAD_INTERIOR_SAMPLE_AUDIT.csv',collision);save('metrics/SIFT_LANDMARK_CAD_VISIBILITY_AUDIT.json',featurevis);table('metrics/FINAL_BODY_CHEIRALITY.csv',cheirality)
 data=load(R/'metrics/HERO_H0_H1_CONSISTENCY.json');aggregate=[]
 for condition in ['H0_NATIVE_UNALIGNED','H1_SHARED_REGISTRATION']:
  for rel in ['SAME_VIDEO','CROSS_VIDEO']:
   x=[a for a in data if a['condition']==condition and a['relationship']==rel];den=sum(a['fixed_source_N']for a in x);known=sum(a['known_N']for a in x);r=dict(condition=condition,relationship=rel,ordered_source_target_pairs=len(x),fixed_source_target_observation_denominator=den,known_N=known)
   for key in ['supported_N','front_disagreement_proxy_N','behind_observed_surface_N','Ring_occluded_N','unknown_N']:r[key]=sum(a[key]for a in x);r[key+'_fraction_fixed_denominator']=r[key]/den
   r['known_observation_weighted_MAE_mm']=sum(a['known_axial_difference_mm']['MAE']*a['known_N']for a in x if a['known_N'])/known;r['not_unique_surface_samples']=True;aggregate.append(r)
 same0=[a for a in data if a['condition']=='H0_NATIVE_UNALIGNED'and a['relationship']=='SAME_VIDEO'];same1=[a for a in data if a['condition']=='H1_SHARED_REGISTRATION'and a['relationship']=='SAME_VIDEO'];assert [{k:v for k,v in x.items()if k!='condition'}for x in same0]==[{k:v for k,v in x.items()if k!='condition'}for x in same1]
 save('metrics/HERO_AGGREGATE_FIXED_DENOMINATOR.json',aggregate);table('metrics/HERO_AGGREGATE_FIXED_DENOMINATOR.csv',aggregate)
 # Paired same-frame results: no dropping difficult views or missing success denominator.
 fr=load(R/'metrics/ALL_FRAME_METRICS.json');a5={x['view']:x for x in fr if x['scope']=='CROSS'and x['method']=='A5'};pairs=[]
 for tag in ['IDENTITY_CANONICAL_RING_ONLY','A0_HISTORICAL_FULL_LightGlue','A0_HISTORICAL_FULL_RoMa','A1','A2','A3','A4']:
  for role in ['FIT','HOLDOUT']:
   x=[a for a in fr if a['scope']=='CROSS'and a['method']==tag and a['role']==role];diff=np.array([a5[a['view']]['IoU']-a['IoU']for a in x]);pairs.append(dict(reference=tag,role=role,N=len(x),mean_A5_minus_reference_IoU=float(diff.mean()),A5_better_N=int((diff>0).sum()),A5_worse_N=int((diff<0).sum()),delta_IoU_distribution=stats(diff),same_frames=True))
 save('metrics/PAIRED_FRAME_COMPARISON.json',pairs);table('metrics/PAIRED_FRAME_COMPARISON.csv',pairs)
 cert=dict(assets_checked=len(checks),all_unchanged=all(x['unchanged']for x in checks),checks=checks,body_frozen=True,scale_singular_values=np.linalg.svd(H[:3,:3],compute_uv=False),rotation_determinant=float(np.linalg.det(H[:3,:3])),proper_rigid_transform=bool(abs(np.linalg.det(H[:3,:3])-1)<1e-5),HOLDOUT_not_in_fit_features=not bool(held&used),fixed_held_ids=sorted(held),all_68_cameras_and_RGB_Mask_unchanged=True,all_final_body_cheirality_positive=True,negative_control_R_deviation_deg=float(np.degrees(Rotation.from_matrix(np.asarray(load(R/'results/NEGATIVE_A5_FINAL.json')['T'])[:3,:3]).magnitude())),no_new_HERO_inference=True,no_GT=True,historical_measurement_fallback_N=0,scientific_accuracy_certified=False,post_freeze_audit_source=asset(Path(__file__)))
 save('provenance/FINAL_INTEGRITY_AUDIT.json',cert);print('FINAL_INTEGRITY_AUDIT_COMPLETE',len(checks),flush=True)
if __name__=='__main__':main()
