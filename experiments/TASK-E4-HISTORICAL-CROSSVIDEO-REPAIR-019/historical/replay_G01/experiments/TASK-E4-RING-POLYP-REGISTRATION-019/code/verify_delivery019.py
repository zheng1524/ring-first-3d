"""Scientific delivery contracts: frozen identities, shared SE3 and complete denominators."""
from common import *
import ast

def main():
 checks=[]
 def check(name,ok,detail=None):
  checks.append(dict(check=name,passed=bool(ok),detail=detail));assert ok,(name,detail)
 vv=load(R/'config/VIEWS.json');check('68_unique_planned_views',len(vv)==len({v['id']for v in vv})==68)
 check('fixed_roles',sum(v['video']=='005'and v['role']=='FIT'for v in vv)==52 and sum(v['video']=='005'and v['role']=='HOLDOUT'for v in vv)==3)
 for scope,n in [('CROSS',52),('NEGATIVE',4)]:
  x=load(R/'metrics'/(scope+'_FULL_SEARCH.json'));check(scope+'_both_gauges_complete360',len(x)==144 and{(r['parity'],r['yaw_deg'])for r in x}=={(p,y)for p in [1,-1]for y in range(0,360,5)})
  check(scope+'_all_FIT_frames_every_angle',all(len(r['per_frame'])==n for r in x))
  seed=load(R/'results'/(scope+'_A5_ALL_INITIALIZATIONS.json'));check(scope+'_3x80_actual_candidate_iterations',len(seed)==3 and all(a['iterations']==80 for a in seed))
  f=load(R/'results'/(scope+'_A5_FINAL.json'));check(scope+'_selected_FIT_only',f['final_loss']==min(a['final_loss']for a in seed))
 original=load(R/'provenance/INPUT_FROZEN.json');freeze=load(R/'provenance/POSE_PREDICTIONS_FROZEN_BEFORE_HOLDOUT.json')
 check('all_original_asset_SHA_unchanged',all(sha(a['path'])==a['sha256']for a in original['assets']))
 check('frozen_predictions_unchanged_after_evaluation',all(sha(a['path'])==a['sha256']for a in freeze['results']))
 H=np.asarray(load(R/'derived/T004_from005.json')['T004_from005']);check('metric_proper_rigid_transform',np.allclose(H[3],[0,0,0,1])and np.allclose(H[:3,:3].T@H[:3,:3],np.eye(3),atol=1e-6)and abs(np.linalg.det(H[:3,:3])-1)<1e-6)
 d=load(R/'derived/VIDEO005_CAMERAS_IN004.json');check('all_55_derived_cameras_one_transform',len(d)==55 and all(np.allclose(a['c2w_in004'],H@a['c2w_original'])for a in d))
 check('all_same_video_relative_cameras_unchanged',load(R/'metrics/HERO_RELATIVE_POSE_INVARIANCE.json')['all_relative_poses_unchanged'])
 held={v['id']for v in vv if v['role']=='HOLDOUT'};check('no_HOLDOUT_in_FIT_features',not held&set(load(R/'provenance/FEATURE_FIT_FREEZE.json')['all_image_ids']))
 check('all55_real_frame_pixel_bindings',all(x['status']=='EXACT_RAW_PIXEL_CONTENT'for x in load(R/'metrics/VIDEO005_FRAME_BINDING.json')['rows']))
 rows=load(R/'metrics/REGISTRATION_COMPARISON.json');check('same_evaluation_denominator_all_methods',all(a['FIT_N']==52 and a['HOLDOUT_N']==3 for a in rows if a['scope']=='CROSS'))
 check('815_method_frame_records_retained',len(load(R/'metrics/ALL_FRAME_METRICS.json'))==815)
 check('68_complete_manifest_records',len(load(R/'INPUT_MANIFEST_COMPLETE.json'))==68)
 check('22_native_Ring_depth_maps_no_forced_calibration',len(load(R/'metrics/RING_HERO_DEPTH_DIAGNOSTIC.json')['rows'])==22 and not load(R/'metrics/RING_HERO_DEPTH_DIAGNOSTIC.json')['stable_trials'])
 check('6_core_actual_data_figures',len(list((R/'figures').glob('Fig*.png')))==6 and all(p.stat().st_size>50000 for p in(R/'figures').glob('Fig*.png')))
 for p in(R/'code').glob('*.py'):ast.parse(p.read_text(),filename=str(p))
 check('delivered_python_parses',True)
 for p in ['TECHNICAL_REPORT.md','TECHNICAL_REPORT_SUMMARY.md','METHOD_AND_INPUT_AUDIT.md','FAILURE_LEDGER.md','REPRODUCE.md','RESULT_INDEX.md']:check('report_'+p,(R/p).stat().st_size>500)
 save('metrics/DELIVERY_CONTRACT_CHECKS.json',dict(checks=checks,all_passed=True,meaning='Engineering/provenance consistency only; NOT a scientific accuracy PASS',source=asset(Path(__file__))))
 print('DELIVERY_CONTRACT_CHECKS_PASSED',len(checks),flush=True)
if __name__=='__main__':main()
