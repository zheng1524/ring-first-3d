from refine import *
import collections

def main():
 rows=load(M/'metrics/ALL_VIDEO_METHOD_METRICS.json');pairs=[];fails=[];rundata=[]
 for g in GROUPS:
  rundata+=load(M/'metrics'/(g+'_ACTUAL_VIDEO_RUNS.json'))
  for aa,bb in [('P0','S0'),('P0','A2'),('S0','A1'),('A2','A3'),('S0','A2'),('A1','A3')]:
   a={r['id']:r for r in rows if r['group']==g and r['method']==aa and r['role']=='FIT'and r.get('Ring_IoU')is not None};b0={r['id']:r for r in rows if r['group']==g and r['method']==bb and r['role']=='FIT'and r.get('Ring_IoU')is not None};common=sorted(set(a)&set(b0));pose_d=[];rot=[]
   for cid in common:
    A=np.array(a[cid]['C']);B=np.array(b0[cid]['C']);pose_d.append(np.linalg.norm(B[:3,3]-A[:3,3]));rot.append(np.degrees(Rotation.from_matrix(B[:3,:3]@A[:3,:3].T).magnitude()))
   rec=dict(group=g,baseline=aa,candidate=bb,target_FIT_N=sum(r['group']==g and r['method']=='P0'and r['role']=='FIT'for r in rows),common_N=len(common),baseline_numeric_N=len(a),candidate_numeric_N=len(b0),common_ids=common,final_pose_center_difference_mm=stats(pose_d),final_pose_rotation_difference_deg=stats(rot))
   for key in ['Ring_IoU','inner_MAE_px','outer_MAE_px','body_IoU']:
    rec[key+'_before']=float(np.mean([a[k][key]for k in common]))if common else None;rec[key+'_after']=float(np.mean([b0[k][key]for k in common]))if common else None
   pp=[k for k in common if a[k].get('SIFT_HELD')and b0[k].get('SIFT_HELD')and a[k]['SIFT_HELD']['N']and b0[k]['SIFT_HELD']['N']];rec.update(held_SIFT_common_view_N=len(pp),held_SIFT_before_px=float(np.mean([a[k]['SIFT_HELD']['MAE']for k in pp]))if pp else None,held_SIFT_after_px=float(np.mean([b0[k]['SIFT_HELD']['MAE']for k in pp]))if pp else None);pairs.append(rec)
 for r in rundata:
  if r['status']=='FROZEN_NUMERIC_POSE':continue
  p=M/'initialization'/r['group']/(r['id']+'.json');s=load(p);fails.append(r|dict(stage='CONICS_INITIALIZATION',reason=s['reason'],candidates_N=len(s['candidates']),evidence=str(p),prediction=None,historical_fallback=0))
 save('metrics/PAIRED_COMMON_VIEW_COMPARISONS.json',pairs);table('metrics/PAIRED_COMMON_VIEW_COMPARISONS.csv',pairs);save('metrics/FAILED_CAMERA_ROUTES.json',fails);table('metrics/FAILED_CAMERA_ROUTES.csv',fails)
 logs=[]
 for g in GROUPS:
  for arm in ['S0','A1','A2','A3']:
   rr=[r for r in rundata if r['group']==g and r['method']==arm];runs=[load(M/'results'/g/arm/r['id']/'FINAL.json')for r in rr if r['status']=='FROZEN_NUMERIC_POSE'];logs.append(dict(group=g,method=arm,target_FIT_N=len(rr),numeric_N=len(runs),failed_N=len(rr)-len(runs),actual_solver_function_evals=sum(r['nfev']for r in runs),outer_updates=sum(r['accepted_outer']for r in runs),sum_process_seconds=sum(r['seconds']for r in runs),max_center_change_mm=max([r['center_change_mm']for r in runs],default=None),max_rotation_change_deg=max([r['rotation_change_deg']for r in runs],default=None),rank6_N=sum(r['data_information']['rank']==6 for r in runs),worst_condition_J=max([r['data_information']['condition']for r in runs],default=None)))
 save('metrics/ACTUAL_SOLVER_COUNTS.json',logs);table('metrics/ACTUAL_SOLVER_COUNTS.csv',logs)
 scopes=[]
 for g,video,method,role in dict.fromkeys((r['group'],r['video'],r['method'],r['role'])for r in rows):
  rr=[r for r in rows if (r['group'],r['video'],r['method'],r['role'])==(g,video,method,role)];valid=[r for r in rr if r.get('Ring_IoU')is not None]
  rec=dict(group=g,video=video,method=method,role=role,target_N=len(rr),numeric_N=len(valid))
  for key in ['Ring_IoU','inner_MAE_px','outer_MAE_px']:
   vv=[r[key]for r in valid if r.get(key)is not None];rec[key]=float(np.mean(vv))if vv else None
  vv=[r['SIFT_HELD']['MAE']for r in valid if r.get('SIFT_HELD')and r['SIFT_HELD']['N']];rec['SIFT_HELD_MAE_px']=float(np.mean(vv))if vv else None;scopes.append(rec)
 save('metrics/PER_VIDEO_SCOPE_SUMMARY.json',scopes);table('metrics/PER_VIDEO_SCOPE_SUMMARY.csv',scopes)
 photos=load(P/'quick_solver_review/config/PHOTO_ASSETS.json');table('metrics/PHOTO_STAGE_NOT_RUN.csv',[dict(id=r['id'],group=r['group'],capture_type=r['capture_type'],RGB=r['RGB'],Mask=r['Mask'],new_pose=None,status='NOT_RUN_VIDEO_COMPLETENESS_GATE')for r in photos]);print('FACTS_AND_PAIRED_COMPARISONS_COMPLETE',flush=True)
if __name__=='__main__':main()
