from common import *
import collections

def main():
 data=load(R/'metrics/NATIVE_SUMMARY.json');bg={(x['case'],x['label']):x for x in load(R/'metrics/BLENDER_GEOMETRY_CHECKS.json')};runs=[];fail=[]
 for x in data:
  b=bg[x['case'],x['label']];x.update(Blender_self_intersections_N=b['self_intersections_N'],Blender_Ring_pairs_N=b['Ring_pairs_N'])
 for n in load(R/'config/PROTOCOL.json')['cases']:
  p=R/'metrics'/(n+'_RUN.json')
  if not p.exists():runs.append(dict(case=n,status='NO_OUTPUT',numerical_output=False,prediction=None));fail.append(dict(case=n,reason='ENGINEERING_FAILURE_NO_INDEPENDENT_PREDICTION'));continue
  run=load(p);h=load(R/'metrics'/(n+'_TRAINING.json'));ts=load(R/'metrics'/(n+'_CANDIDATES.json'));causes=collections.Counter(v for t in ts if not t['accepted']for v in t['reasons']);i=next(x for x in data if x['case']==n and x['label']=='FINAL011');f=next(x for x in data if x['case']==n and x['label']=='FINAL012');run.update(numerical_output=True,FIT_IoU_initial=i['FIT_IoU'],FIT_IoU_final=f['FIT_IoU'],HOLDOUT_IoU_initial=i['HOLDOUT_IoU'],HOLDOUT_IoU_final=f['HOLDOUT_IoU'],FIT_depth_cost_initial=i['FIT_fixed_depth_cost'],FIT_depth_cost_final=f['FIT_fixed_depth_cost'],FIT_depth_coverage_initial=i['FIT_depth_coverage'],FIT_depth_coverage_final=f['FIT_depth_coverage'],Ring_pairs_initial=i['Blender_Ring_pairs_N'],Ring_pairs_final=f['Blender_Ring_pairs_N'],Ring_penetration_sample_initial_mm=i['Ring_signed_sample_penetration_mm'],Ring_penetration_sample_final_mm=f['Ring_signed_sample_penetration_mm'],self_intersections_final=f['Blender_self_intersections_N'],final_base_below_N=f['below_estimated_base_vertex_N'],rejection_counts=dict(causes),final_watertight=f['watertight'],final_nonmanifold_N=f['nonmanifold_edge_N'],final_components=f['connected_components'],maximum_accepted_step_mm=max((a['actual_step_mm']for a in h),default=0),history_loss_change=h[-1]['loss']-h[0]['loss']if h else None);runs.append(run)
  reasons=[]
  if run['status']!='ACCEPTED_TARGET_REACHED':reasons.append(run['status'])
  if f['HOLDOUT_IoU']<i['HOLDOUT_IoU']:reasons.append('HOLDOUT_MASK_REGRESSION')
  if f['FIT_depth_coverage'] is not None and f['FIT_depth_coverage']<i['FIT_depth_coverage']:reasons.append('FIXED_DENOMINATOR_DEPTH_COVERAGE_DROP')
  if f['FIT_fixed_depth_cost'] is not None and f['FIT_fixed_depth_cost']>i['FIT_fixed_depth_cost']:reasons.append('RAW_FIXED_DEPTH_COST_INCREASE')
  if f['Ring_surface_collision']:reasons.append('RESIDUAL_CAD_SURFACE_INTERSECTION')
  if f['Blender_self_intersections_N']:reasons.append('INDEPENDENT_SELF_INTERSECTION')
  fail.append(dict(case=n,reasons=reasons,rejected_candidate_causes=dict(causes),accepted=run['accepted'],attempts=run['attempts'],max_actual_displacement_mm=run['maximum_displacement_mm'],stalk_recovery='REQUIRES_HUMAN_3D_AND_IMAGE_REVIEW'if getcase(n)['morphology']=='Ip'else'NOT_APPLICABLE_AS_TYPE_DIAGNOSIS',evidence='figures/full/'+n+'_Three_Stage_Detail.png'))
 save('metrics/NATIVE_WITH_GEOMETRY.json',data);table('metrics/NATIVE_WITH_GEOMETRY.csv',data);save('metrics/NINE_CASE_RESULTS.json',runs);table('metrics/NINE_CASE_RESULTS.csv',runs);save('metrics/FAILURES.json',fail);table('metrics/FAILURES.csv',fail);print('NINE_CASE_NATIVE_SUMMARY_WRITTEN')

if __name__=='__main__':main()
