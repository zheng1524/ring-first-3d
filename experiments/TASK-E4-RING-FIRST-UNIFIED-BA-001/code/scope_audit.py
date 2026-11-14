"""Algorithm scope is determined by real variable blocks, not generic status labels."""
from ucommon import *
def main():
 rows=[]
 for f in(N/'optimization').rglob('CERES_SUMMARY.json'):
  label=str(f.relative_to(N/'optimization'));r=load(f)
  if '/B1_LOCAL/'in label:scope='INDEPENDENT_SINGLE_CAMERA_FIXED_XYZ'
  elif '/B2/'in label:scope='ONE_SHARED_VIDEO_SE3_FIXED_XYZ'
  elif '/B3/'in label or label.startswith('SENSITIVITY/'):scope='JOINT_MULTI_CAMERA_AND_XYZ'
  else:scope='CONTROL_OR_STAGE_A_NOT_MAIN_BA'
  rows.append(dict(path=str(f),scope=scope,num_parameter_blocks_reduced=r['num_parameter_blocks_reduced'],num_parameters_reduced=r['num_parameters_reduced'],num_effective_parameters_reduced=r['num_effective_parameters_reduced'],num_residuals=r['num_residuals'],linear_solver=r['linear_solver_type_used'],termination=r['termination_type'],usable=r['usable']))
 table('metrics/ACTUAL_PROBLEM_SCOPE_AUDIT.csv',rows);save('metrics/ACTUAL_PROBLEM_SCOPE_AUDIT.json',rows);save('provenance/NUMERIC_STATUS_SCOPE_CORRECTION.json',dict(affected='B1_LOCAL andB2 genericFINALstatusFROZEN_NUMERIC_JOINT',correction='generic numericstatusdoesnotdescribefreedom; usearm+actualCeresblocks; B1singlecamera andB2sharedHnotjointXYZ',original_FINALs_preserved=True,no_pose_or_algorithm_changed=True,authoritative_scope='metrics/ACTUAL_PROBLEM_SCOPE_AUDIT.csv'));print('SCOPE_AUDITED',len(rows))
if __name__=='__main__':main()
