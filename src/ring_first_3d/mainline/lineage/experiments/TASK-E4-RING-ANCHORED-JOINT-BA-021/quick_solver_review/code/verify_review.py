"""Delivery integrity, preserving failed scientific gates; no fitting or model inference."""
from qcommon import *
import ast,collections

def main():
 checks=[]
 def check(name,ok,detail=None):checks.append(dict(check=name,PASS=bool(ok),detail=detail))
 def hashes(label,files):
  bad=[a['path']for a in files if not Path(a['path']).is_file()or sha(a['path'])!=a['sha256']];check(label,not bad,bad)
 hashes('original021 frozen inputs/results unchanged',load(Q/'provenance/ORIGINAL_021_FROZEN.json')['files'])
 frozen=load(Q/'provenance/SOLVER_CANDIDATES_FROZEN.json');hashes('mature candidates unchanged after evaluation',frozen['files']);check('BA frozen before independent evaluation',frozen['epoch']<load(Q/'runtime/SOLVER_EVALUATION_COMPLETE.json')['epoch']and not frozen['body_HERO_HOLDOUT'])
 tracks=load(P/'observations/CROSS_COMMON_TRACKS.json');check('18 common native identity tracks retained',len(tracks)==18 and sum(len(t['observations'])for t in tracks)==553 and all(o['role']=='FIT'for t in tracks for o in t['observations']))
 for arm in ['B1','B2','B3']:
  r=load(Q/'results'/arm/'FINAL.json');T=np.array(r['T']);gate=load(Q/'metrics'/(arm+'_ORIGINAL_OBJECTIVE_GATE.json'));calls=load(Q/'optimization'/arm/'CALLS.json');trace=load(Q/'optimization'/arm/'ITERATIONS.json')
  check(arm+' finite rigid feasible independently generated endpoint',np.isfinite(T).all()and np.allclose(T[:3,:3].T@T[:3,:3],np.eye(3),atol=1e-10)and abs(np.linalg.det(T[:3,:3])-1)<1e-10 and r['original_constraints_valid']and r['status']=='FEASIBLE_FINAL_FROZEN'and r['used_original_prior_centers']and not r['body_HERO_HOLDOUT_in_loss'])
  check(arm+' actual mature solver calls/iterations',r['nfev']==len(calls)and r['nit']==len(trace)and r['nfev']>0 and all(c['feasible']for c in calls),dict(infeasible_trial_calls=sum(not c['feasible']for c in calls)))
  check(arm+' original loss reproduces within original 1e-6',gate['absolute_error']<=1e-6 and gate['objective_unchanged']and gate['prior_center_not_rebased'],gate['absolute_error'])
 gr=load(Q/'metrics/GRADIENT_COMPONENT_ISOLATION.json');smooth=max(a['smooth_relative_error']for a in gr);ring=max(a['Ring_relative_error']for a in gr if a['parameter']=='pose')
 check('isolated smooth SIFT/prior AD-FD within1percent',smooth<=.01,smooth)
 scientific_full_gradient_gate=ring<=.01
 check('full Ring gradient failure preserved, not relabeled PASS',not scientific_full_gradient_gate,dict(max_Ring_relative_error=ring,scientific_gradient_gate=scientific_full_gradient_gate))
 frames=load(Q/'metrics/ALL005_FRAME_METRICS.json');agg={a['method']:a for a in load(Q/'metrics/HERO_INDEPENDENT_AGGREGATE.json')}
 check('all6 candidates each52FIT3HOLDOUT evaluated',len(frames)==330 and all(sum(a['method']==m for a in frames)==55 for m in agg))
 check('same21sources208pairs fixed2893126 HERO denominator',len(agg)==6 and all(a['source_count']==21 and a['ordered_cross_source_target_pairs']==208 and a['fixed_source_target_observation_denominator']==2893126 for a in agg.values()))
 for a in load(Q/'metrics/HERO_EXACT_COMMON_GAINED_LOST.json'):
  check(a['method']+' exact common/gain/loss conservation',a['common_N']+a['lost_N']==agg[a['baseline']]['known_N']and a['common_N']+a['gained_N']==agg[a['method']]['known_N']and a['fixed_N']==2893126)
 records=load(Q/'config/PHOTO_ASSETS.json');photos=load(Q/'metrics/PHOTO_REGISTRATION_COMPARISON.json');check('all12 photos four groups retained',len(records)==12 and collections.Counter(a['group']for a in records)==dict(G01=3,G03=3,G05=3,G06=3))
 expected=['fc04b6133cdc39c48681e371fc4d41335689dee34c97f608403132771cd25d2c','9a7264fd6b835bca6f30d7acce5f7317e5501542e1cc5c6804e722447fb9401a','f4f17fb3ab5ad9a8778b9fbebedd22e277d0b6a951bd108665181aa18f9aae00']
 for r in records:
  cid=r['id'];hashes(cid+' original RGB/Mask unchanged',[r['RGB'],r['Mask']]);check(cid+' correct cohort/native image binding',r['capture_type']=='INDEPENDENT_PHOTO'and '/smart_endoscope_20260805/raw/'in r['RGB']['path']and '/smart_endoscope_20260805/work/masks/'in r['Mask']['path']and r['RGB_same_cohort_SHA_verified'])
  if r['group']=='G01':check(cid+' authoritative original SHA and archived exact pixels',r['RGB']['sha256']==expected[int(cid[-3:])-1]and r['archived_G01_work_RGB_pixel_exact'])
 views=load(Q/'config/ALL71_CAPTURE_IDENTITY_AND_READINESS.json');check('71 unique identities,60FIT,8protectedHOLDOUT,3separatephotos',len(views)==len({v['id']for v in views})==71 and sum(v['capture_type']=='VIDEO_FRAME'for v in views)==68 and sum(v['is_protected_HOLDOUT']for v in views)==8 and sum(v['can_provide_MASK_FIT']for v in views)==60 and sum(v['can_provide_TRUSTED_HERO_FIT']for v in views)==16)
 H=np.array(load(P/'results/B3.json')['T']);dups=[]
 for row in photos:
  cid=row['id'];root=Q/'results/photos'/cid;fr=load(root/'PREDICTION_FROZEN.json');hashes(cid+' pose frozen before held/body',fr['files']);check(cid+' no body/HERO/held used in pose freeze',not any(fr[k]for k in ['photo_held','body','HERO']))
  pose=load(root/'FINAL.json');C=np.array(pose['C']);matches=load(root/'ALL_RGB_LANDMARK_MATCHES.json');pnps=load(root/'PNP_RAW_CANDIDATES.json');selected=[]
  for p in pnps:
   ids=p.get('inlier_photo_feature_ids',[]);check(cid+p['video']+' native PHOTO_HELD excluded from PnP',all(fid%5!=0 for fid in ids))
   ms=[a for a in matches if a['video']==p['video']and a['photo_feature_id']in ids and a['role']=='PHOTO_FIT'];check(cid+p['video']+' no duplicate landmark/photoID within PnP',len(ms)==len(ids)==len(set(a['landmark_id']for a in ms))==len(set(a['photo_feature_id']for a in ms)));selected.extend(ms)
  dups.append(dict(id=cid,fit_inlier_observations_N=len(selected),unique_photo_feature_N=len({a['photo_feature_id']for a in selected}),cross_video_repeat_observations_N=len(selected)-len({a['photo_feature_id']for a in selected}),not_independent_pixel_evidence=True,normalization='original video-normalized unchanged; source landmark locations remain different 004/005 reconstructions, limitation retained'))
  check(cid+' independent rigid camera, not copied frame',pose['camera_was_not_copied_from_video']and all(not np.allclose(C,np.array(v['c2w_world004']),atol=1e-8)for v in views if v['capture_type']=='VIDEO_FRAME'))
  prep=load(Q/'inputs'/cid/'HERO_PREPARATION.json');check(cid+' new gate failure not fabricated HERO',not prep['execute_inference']and prep['camera_gate_not_passed']and prep['TRUSTED_area_mm2']is None and not row['can_enter_shared_body_FIT']and row['novel_3D_visible_area_mm2']is None and len(row['current_gate_reasons'])>0 and prep['HERO_checkpoint_SHA_matches'])
  for s in prep['support_RGB']:
   hashes(cid+' supportRGB '+s['id'],[dict(path=s['path'],sha256=s['sha256'])]);check(cid+' support camera transformation '+s['id'],np.allclose(s['source_pose_mm_world004'],H@np.array(s['native_c2w'])if s['video']=='005'else s['native_c2w']))
 qtable('metrics/PHOTO_INLIER_IDENTITY_INDEPENDENCE.csv',dups);qsave('metrics/PHOTO_INLIER_IDENTITY_INDEPENDENCE.json',dups)
 h=load(Q/'runtime/HERO_PREPARATION_COMPLETE.json');check('official weights verified but no new HERO inference',h['official_checkpoint_verified']and h['new_photo_inference_runs']==0)
 fig=['Figure_A_Mature_Solver_Review','Figure_B_Independent_Photo_Ring_And_CAD','Figure_C_Photo_Video_Camera_Geometry','Figure_D_Photo_Geometry_Readiness','Photo_Heldout_RGB_Reprojection_Evidence'];check('four core figures plus real photoheld evidence',all((Q/'figures'/(f+'.png')).is_file()for f in fig))
 for p in(Q/'code').glob('*.py'):ast.parse(p.read_text())
 check('all task Python code parses',True)
 if(Q/'provenance/DELIVERY_MANIFEST.json').exists():
  m=load(Q/'provenance/DELIVERY_MANIFEST.json')
  for k in ['code','reports','solver_poses','photo_poses']:hashes('delivery manifest '+k,m[k])
 else:check('delivery manifest present',False)
 out=dict(delivery_integrity_pass=all(a['PASS']for a in checks),checks=checks,scientific_full_gradient_gate=scientific_full_gradient_gate,scientific_photo_strong_supervision_pass_N=0,targets_photos_N=3,new_HERO_inference_runs=0,measurement_fallback_N=0,absolute_GT_metrics='NOT_EVALUABLE',no_new_optimization=True)
 qsave('metrics/DELIVERY_CHECKS.json',out);print(json.dumps(dict(delivery_integrity_pass=out['delivery_integrity_pass'],check_count=len(checks),failed=[a for a in checks if not a['PASS']],scientific_full_gradient_gate=scientific_full_gradient_gate),ensure_ascii=False));return out
if __name__=='__main__':
 r=main()
 if not r['delivery_integrity_pass']:raise SystemExit(1)
