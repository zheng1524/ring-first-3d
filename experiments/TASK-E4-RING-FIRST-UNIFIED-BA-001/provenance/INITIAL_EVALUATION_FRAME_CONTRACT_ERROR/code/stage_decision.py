"""Resolve conditional B4/photo gates using preregistered RGB criteria, never HERO."""
from ucommon import *
def main():
 rows=load(N/'metrics/FOUR_GROUP_POSE_SCORECARD.json');reasons=[];paired=[]
 for g in GROUPS:
  a=next(r for r in rows if r['group']==g and r['method']=='B0'and r['role']=='FIT');b=next(r for r in rows if r['group']==g and r['method']=='B3'and r['role']=='FIT');x=a['descriptor_HELD_reprojection_px_MAE_macro'];y=b['descriptor_HELD_reprojection_px_MAE_macro'];threshold=max(1.,.25*x);bad=y-x>threshold;info=load(N/'metrics'/(g+'_JOINT_INFORMATION.json'));fd=all(r['PASS']for r in info['complete_joint_FD']);paired.append(dict(group=g,before=x,after=y,delta=y-x,preregistered_severe_delta_px=threshold,severe=bad,marginal_camera_rank=info['marginal_camera_information_rank'],dimension=info['marginal_camera_information_dimension'],joint_FD_PASS=fd))
  if bad:reasons.append(g+':PREREGISTERED_HELD_RGB_DEGRADATION')
  if not fd or info['marginal_camera_information_rank']<info['marginal_camera_information_dimension']:reasons.append(g+':JOINT_JACOBIAN_OR_DATA_RANK')
 # All four held-view epipolar proxies increased; document without inventing a new failthreshold.
 epi=[]
 for g in GROUPS:
  s=[next(r for r in rows if r['group']==g and r['method']==m and r['role']=='HOLDOUT')for m in ['B0','B3']];epi.append(dict(group=g,N_views=s[0]['target_N'],before_px=s[0]['descriptor_HELD_epipolar_px_MAE_macro'],after_px=s[1]['descriptor_HELD_epipolar_px_MAE_macro']))
 decision=dict(status='PAUSED_AFTER_COMPLETED_FOUR_GROUP_MAIN_BA'if reasons else'B3_TRUST_GATE_PASSED_REVIEW_REQUIRED',main_four_groups_run=True,Ceres_joint_executed=True,B4_run=False,photos_run=0,reasons=reasons,B4_status='NOT_RUN_B3_INDEPENDENT_RGB_CONFLICT'if reasons else'NOT_RUN_PENDING_CONTROLLED_RELEASE',independent_HERO_used_for_this_gate=False,paired_RGB=paired,HOLDOUT_relative_epipolar=epi,no_absolute_pose_GT=True,do_not_promote_any_camera_mainline=True)
 save('STAGE_DECISION.json',decision)
 for g in GROUPS:save('results/'+g+'/B4/NOT_RUN_FINAL_DECISION.json',dict(group=g,arm='B4',status=decision['B4_status'],poses=None,no_historical_fallback=True,reason=reasons))
 photos=load(P/'quick_solver_review/config/PHOTO_ASSETS.json');table('metrics/TWELVE_PHOTO_NOT_RUN.csv',[dict(id=p['id'],group=p['group'],capture_type=p['capture_type'],RGB=p['RGB'],Mask=p['Mask'],status='NOT_RUN_VIDEO_GATE',pose=None)for p in photos]);table('metrics/PREREGISTERED_STAGE_GATE_PAIRED_RGB.csv',paired)
 # Every method has an explicit scope/coverage record, including unresolved stages.
 rows=[r for r in rows if r['method']!='B4']
 for g in GROUPS:
  for role in ['FIT','HOLDOUT']:
   base=next(r for r in rows if r['group']==g and r['method']=='B0'and r['role']==role);rows.append(dict(group=g,method='B4',role=role,target_N=base['target_N'],numeric_N=0,Ring_IoU=None,status=decision['B4_status']))
 save('metrics/FOUR_GROUP_POSE_SCORECARD.json',rows);table('FOUR_GROUP_POSE_SCORECARD.csv',rows)
 files=[N/'results'/g/m/'FINAL.json'for g in GROUPS for m in METHODS]+[N/'results'/g/'B4/NOT_RUN_FINAL_DECISION.json'for g in GROUPS]+[N/'results/SENSITIVITY/G01_B3_FIXED_PERTURBATION/FINAL.json'];freeze('provenance/ALL_FINAL_CAMERA_CANDIDATES_FROZEN_BEFORE_HERO.json',files,GT=False,HERO_body=False,no_new_fit_after_this_freeze=True);print('FINAL_STAGE_GATE',decision['status'],reasons,flush=True)
if __name__=='__main__':main()
