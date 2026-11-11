"""Postfreeze independent-photo candidates, heldout gates and missing native depth."""
from qcommon import *
from geometry021 import cpu_curve_distance,cast,contour_stats
from ring020 import CADCurves
from photo_registration import K,Ke,project
from features019 import match_desc,sampson
import itertools

def main():
 while not(Q/'runtime/PHOTO_EPI_ATTEMPTS_COMPLETE.json').exists():time.sleep(5)
 assets=load(Q/'config/PHOTO_ASSETS.json');v=load(P/'config/VIEWS.json');H=np.array(load(P/'results/B3.json')['T']);rv=np.load(P/'inputs/G01/RING.npz');cad=scene(rv['V'],rv['F']);cv=CADCurves(P/'inputs/G01/RING.npz');body=np.load(P/'inputs/G01/BODY018.npz');bs=scene(body['V'],body['F']);cams=[(H@np.asarray(x['T'])if x['video']=='005'else np.asarray(x['T']))for x in v];dirs=np.array([C[:3,3]/np.linalg.norm(C[:3,3])for C in cams]);video_polar=np.degrees(np.arccos(np.clip(abs(dirs[:,2]),0,1)));rows=[];pairs=[]
 for a,b in itertools.combinations([a for a in assets if a['group']=='G01'],2):
  fa=np.load(Q/'photo_features'/(a['id']+'.npz'));fb=np.load(Q/'photo_features'/(b['id']+'.npz'));m=match_desc(fa['des'],fb['des']);F=None;inl=None
  if len(m)>=8:cv2.setRNGSeed(20261112);F,inl=cv2.findFundamentalMat(fa['xy'][m[:,0]],fb['xy'][m[:,1]],cv2.USAC_MAGSAC,1.5,.999,10000)
  pairs.append(dict(photoA=a['id'],photoB=b['id'],mutual_N=len(m),RGB2D_F_inlier_N=int(inl.sum())if inl is not None else 0,does_not_link_component_to_video_world=True));np.savez_compressed(Q/'photo_features'/(a['id']+'__'+b['id']+'.npz'),index_pairs=m,FIT_F_inliers=np.asarray(inl)if inl is not None else np.zeros((len(m),1),np.uint8))
 qsave('metrics/PHOTO_PHOTO_RGB_COMPONENT_AUDIT.json',pairs);qtable('metrics/PHOTO_PHOTO_RGB_COMPONENT_AUDIT.csv',pairs)
 # Audited existing native-source registries: actual targets are all VIDEO_FRAME identities.
 conf=load(P/'config/FOUR_GROUP_INPUTS.json');source_receipts=[]
 for g in conf:
  for s in g['sources']:source_receipts.append(dict(group=g['group'],native_source_id=s['id'],origin=s['origin'],native_asset=s['original_native']if'original_native'in s else s['observation'],target_capture_type='VIDEO_FRAME',exact_photo_id_match=False))
 qsave('assets_index/EXISTING_HERO_TARGET_IDENTITY_AUDIT.json',source_receipts)
 for rec in assets:
  if rec['group']!='G01':continue
  cid=rec['id'];d=np.load(rec['cache']);result=load(Q/'results/photos'/cid/'FINAL.json');C=np.array(result['C']);raw=np.load(Q/'inputs'/cid/'RING_NATIVE_EVIDENCE.npz');edge=cv.segments(C,K);rr={}
  for name in ['inner','outer']:
   p=(raw[name]+.5)/3-.5;rr[name]=stats(cpu_curve_distance(p,rv['V'],edge[name],C,K))
  rz=cast(cad,K,C,360,640);target=d['labels']==2;pred=np.isfinite(rz);known=d['labels']!=1;ct=contour_stats(pred&known,target);M=.5*(np.mean((~pred)[target])+np.mean(pred[(d['labels']==0)]));bz=cast(bs,K,C,360,640);bm=np.isfinite(bz)&(bz<rz);iou=(bm&(d['labels']==1)).sum()/max(1,(bm|(d['labels']==1)).sum());cp=C[:3,3]/np.linalg.norm(C[:3,3]);polar=np.degrees(np.arccos(np.clip(abs(cp[2]),0,1)));A=Rotation.from_euler('x',np.pi).as_matrix();flip=np.eye(4);flip[:3,:3]=A;Cg=flip@C;zg=cast(bs,K,Cg,360,640);rg=cast(cad,K,Cg,360,640);mg=np.isfinite(zg)&(zg<rg);ig=(mg&(d['labels']==1)).sum()/max(1,(mg|(d['labels']==1)).sum());matches=load(Q/'results/photos'/cid/'ALL_RGB_LANDMARK_MATCHES.json');all2=load(Q/'results/photos'/cid/'RGB2D_PER_VIEW_AUDIT.json');qsave('evaluation/photos/'+cid+'/RING_BODY_GAUGE_DIAGNOSTIC.json',dict(C=C,opposite_normal_gauge_C=Cg,body_IoU_at_frozen_independent_photo_pose=float(iou),body_IoU_at_other_normal_gauge=float(ig),not_used_for_pose_selection=True,opposite_normal_is_Ring_only_symmetry_not_SIFT_equivalence=True,body=asset(P/'inputs/G01/BODY018.npz')));np.savez_compressed(Q/'inputs'/cid/'AUDIT_PROJECTION.npz',Ring_z_mm=rz,body_pred_at_independent_photo_pose=bm,ring_pred=pred)
  held=[m for m in matches if m['role']=='PHOTO_HELD'];uv,z=project(np.array([m['XYZ004_mm']for m in held]),C)if held else(np.empty((0,2)),np.empty(0));herr=stats(np.linalg.norm(uv-np.array([m['photo_uv']for m in held]),axis=1))if held else stats([]);spread=[]
  for c in result['candidates']:
   D=np.asarray(c['C'])@np.linalg.inv(C);spread.append(dict(seed_video=c['seed_video'],camera_center_distance_mm=float(np.linalg.norm(np.asarray(c['C'])[:3,3]-C[:3,3])),rotation_difference_deg=float(np.degrees(Rotation.from_matrix(D[:3,:3]).magnitude()))))
  maxdist=max([x['camera_center_distance_mm']for x in spread]or[float('inf')]);maxrot=max([x['rotation_difference_deg']for x in spread]or[float('inf')]);reasons=[]
  if result['FIT_PnP_inlier_N']<6:reasons.append('NO_6_MATCH_PNP')
  if herr['N']<4:reasons.append('PHOTO_HELD_N_LT4')
  if herr['MAE']is not None and herr['MAE']>3:reasons.append('PHOTO_HELD_MAE_GT3PX')
  if herr['p95']is not None and herr['p95']>6:reasons.append('PHOTO_HELD_P95_GT6PX')
  if ct['MAE']is not None and ct['MAE']>3 or ct['p95']is not None and ct['p95']>6:reasons.append('RING_CONTOUR_GATE')
  if maxdist>2 or maxrot>5:reasons.append('POSE_SEED_SPREAD')
  usable=not reasons;angles=np.degrees(np.arccos(np.clip(dirs@cp,-1,1)));nearest=int(np.argmin(angles));qsave('evaluation/photos/'+cid+'/CAMERA_QUALIFICATION.json',dict(status='CONDITIONAL_USABLE'if usable else'NUMERIC_PHOTO_POSE_NOT_READY_FOR_STRONG_HERO',reasons=reasons,HERO_inference_authorized_by_input_gate=usable,held_error_px=herr,seed_spread=spread,old_v13_status_not_used_as_gate=True,source=asset(Path(__file__))))
  row=dict(id=cid,capture_type='INDEPENDENT_PHOTO',original_filename=rec['original_filename'],RGB_status='FOUND_ORIGINAL',Mask_status='FOUND_BOUND_SAME_CAPTURE_NATIVE_MULTICLASS_CACHE',historical_reason=rec.get('old_reason'),current_DXY_Ring_valid=rec['Ring_current_valid'],Ring_boundary_px=ct,Ring_hard_balanced_MSE=float(M),Inner_MAE_px=rr['inner']['MAE'],Inner_p95_px=rr['inner']['p95'],Inner_N=rr['inner']['N'],Outer_MAE_px=rr['outer']['MAE'],Outer_p95_px=rr['outer']['p95'],Outer_N=rr['outer']['N'],SIFT_landmark_matches_N=len(matches),SIFT_FIT_PnP_inliers_N=result['FIT_PnP_inlier_N'],SIFT_real_RGB2D_F_inliers_N=sum(x['FIT_RGB_F_inlier_N']for x in all2),camera_status='CONDITIONAL_USABLE'if usable else'NUMERIC_RING_SIFT_POSE_WEAK_HELD_VALIDATION',current_gate_reasons=reasons,PHOTO_HELD_error_px=herr,seed_pose_spread=spread,SIFT_yaw_constraint_exists=bool(result['primary']),nearest_existing_video_view=v[nearest]['id'],minimum_direction_difference_deg=float(angles[nearest]),intrinsics_status=rec['K_status'],camera_unique=False,can_enter_shared_body_FIT=usable,HERO_action='READY_FOR_OFFICIAL_INFERENCE'if usable else'NOT_RUN_NEW_CAMERA_VALIDATION_FAILED',native_HERO_status='MISSING_IN_AUDITED_NATIVE_REGISTRIES',TRUSTED_HERO_area_mm2=None,existing_HERO_compatibility_mm=None,body_native_HERO_residual_mm=None,body_uncovered_TRUSTED_fraction=None,novel_3D_visible_area_mm2=None,novel_3D_visibility_status='NOT_EVALUABLE_WITHOUT_ALIGNED_POSE_AND_NATIVE_HERO',Ring_gauge_invariant_polar_deg=float(polar),existing_video_polar_deg_min=float(video_polar.min()),existing_video_polar_deg_max=float(video_polar.max()),azimuth_difference_deg=None,frozen_independent_photo_pose_body_IoU=float(iou),opposite_Ring_normal_gauge_body_IoU=float(ig),body_diagnostic_not_pose_selection=True)
  rows.append(row)
 qsave('metrics/PHOTO_REGISTRATION_COMPARISON.json',rows);qtable('PHOTO_REGISTRATION_COMPARISON.csv',rows)
 # The original68 roles stay unchanged; three stills are candidates, NOT new heldout video frames.
 hero={s['id']:s for g in conf if g['group']=='G01'for s in g['sources']};ready=[]
 for a in v:
  s=hero.get(a['id']);ready.append(dict(id=a['id'],capture_type='VIDEO_FRAME',video=a['video'],original_role=a['role'],original_camera_qualification=a.get('qualification'),camera_status='EXISTING021_FROZEN_CONDITIONAL',RGB=a['RGB_source'],K=a['K'],c2w_world004=H@np.asarray(a['T'])if a['video']=='005'else np.asarray(a['T']),can_provide_MASK_FIT=a['role']=='FIT',native_HERO_status='EXISTS_TRUSTED'if s else'MISSING_FOR_THIS_FRAME',can_provide_TRUSTED_HERO_FIT=bool(s and a['role']=='FIT'),HERO_source=s['observation']if s else None,is_protected_HOLDOUT=a['role']=='HOLDOUT',new_training_authorized=False))
 for a in rows:ready.append(dict(id=a['id'],capture_type='INDEPENDENT_PHOTO',original_role='NEW_CANDIDATE_NOT_HISTORICAL_HOLDOUT',camera_status=a['camera_status'],can_provide_MASK_FIT=a['can_enter_shared_body_FIT'],native_HERO_status=a['native_HERO_status'],can_provide_TRUSTED_HERO_FIT=False,is_protected_HOLDOUT=False,new_training_authorized=False))
 qsave('config/ALL71_CAPTURE_IDENTITY_AND_READINESS.json',ready);qtable('ALL_VIEW_BODY_ADAPT_READINESS.csv',ready);qsave('runtime/PHOTO_AUDIT_COMPLETE.json',dict(epoch=time.time(),all71=len(ready),native_HERO_inference_executed=False,reason='photo poses are numerically recovered, but new fixed heldout camera criteria failed; original labels are not used as a gate'));print('PHOTO_AUDIT_COMPLETE',len(ready),flush=True)
if __name__=='__main__':main()
