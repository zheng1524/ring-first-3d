from common import *
import collections

def main():
 summary=load(R/'metrics/ALL_STAGE_SUMMARY.json');bpy=load(R/'metrics/BLENDER_GEOMETRY.json');idx={(x['case'],x['label'],x['step']):x for x in bpy};runs=[];fail=[];rollback=[]
 for x in summary:
  b=idx[x['case'],x['label'],x['step']];x.update(Blender_self_N=b['self_intersections_N'],Blender_Ring_pairs_N=b['Ring_pairs_N'])
 for n in load(R/'config/PROTOCOL.json')['cases']:
  h=load(R/'metrics'/(n+'_TRAINING.json'));ts=load(R/'metrics'/(n+'_CANDIDATES.json'));run=load(R/'metrics'/(n+'_RUN.json'));initial=next(x for x in summary if x['case']==n and x['label']=='INITIAL');final=next(x for x in summary if x['case']==n and x['label']=='FINAL');accepted=[x for x in ts if x['accepted']];reasons=collections.Counter(reason for x in ts if not x['accepted']for reason in x['reasons']);physical_accepted_ok=all(not x['reasons']and x['max_step_mm']<=load(R/'inputs'/n/'CHART.json')['tau_mm']+1e-8 and x['min_area_ratio']>=.1 and x['minimum_normal_dot']>0 and x['self_intersections']==0 for x in accepted);base_ok=all(x.get('min_base_height_mm',0)>=-1e-7 and x.get('max_cap_plane_distance_mm',0)<=1e-7 for x in accepted);clock=0;committed=0;restarts=0
  for step in h:
   if step['accepted']:
    if step['accepted_method']=='STEEPEST_RESTART':clock=0;restarts+=1
    else:clock+=1;committed+=1
   path=R/'local_results'/n/('STEP_%04d.pt'%step['iteration'])
   if path.exists():
    import sys
    sys.path.insert(0,str(R/'code'));from p3d import torch
    saved=torch.load(path,weights_only=False,map_location='cpu');state=saved['optimizer']['state'];actual=0 if not state or not next(iter(state.values()))else int(next(iter(state.values()))['step']);rollback.append(dict(case=n,step=step['iteration'],expected_clock=clock,actual_clock=actual,passed=clock==actual))
  run.update(FIT_IoU_initial=initial['FIT_IoU'],FIT_IoU_final=final['FIT_IoU'],HOLDOUT_IoU_initial=initial['HOLDOUT_IoU'],HOLDOUT_IoU_final=final['HOLDOUT_IoU'],FIT_depth_cost_initial=initial['FIT_raw_fixed_depth_cost'],FIT_depth_cost_final=final['FIT_raw_fixed_depth_cost'],FIT_depth_coverage_initial=initial['FIT_depth_coverage'],FIT_depth_coverage_final=final['FIT_depth_coverage'],final_self_N=final['Blender_self_N'],final_Ring_pairs_N=final['Blender_Ring_pairs_N'],initial_Ring_pairs_N=initial['Blender_Ring_pairs_N'],initial_sample_penetration_mm=initial['Ring_signed_sample_penetration_mm'],final_sample_penetration_mm=final['Ring_signed_sample_penetration_mm'],below_base_final=final['below_estimated_base_vertex_N'],maximum_displacement_mm=final['material_vertex_displacement_mm']['maximum'],candidate_rejection_counts=dict(reasons),all_logged_accepted_geometry_pass=physical_accepted_ok,all_cap_halfspaces_pass=base_ok,more_than_half_outer_rejected=run['rejected_outer_iterations']>len(h)/2,actual_Adam_proposal_calls=len(h),committed_Adam_updates_verified=committed,gradient_restarts_verified=restarts,loss_nonincrease_with_1e_7_tolerance=all(h[j]['accepted_loss']<=h[j-1]['accepted_loss']+1.0001e-7 for j in range(1,len(h))))
  runs.append(run)
  if run['more_than_half_outer_rejected']or final['Blender_self_N']or final['Ring_surface_collision']or final['below_estimated_base_vertex_N']and load(R/'inputs'/n/'BASE_SELECTION.json')['truncate_allowed']:
   fail.append(dict(case=n,outer=len(h),accepted=run['accepted_optimizer_steps'],reasons=dict(reasons),initial_penetration_mm=initial['Ring_signed_sample_penetration_mm'],final_penetration_mm=final['Ring_signed_sample_penetration_mm'],self_N=final['Blender_self_N'],below_base_N=final['below_estimated_base_vertex_N'],majority_rejected=run['more_than_half_outer_rejected']))
  # Compact review file; all candidate parameters remain in original full JSON/CSV and local index.
  compact=[{k:v for k,v in t.items()if k!='parameters'}for t in ts];table('metrics/'+n+'_CANDIDATE_REVIEW.csv',compact)
 save('metrics/ALL_STAGE_WITH_BLENDER.json',summary);table('metrics/ALL_STAGE_WITH_BLENDER.csv',summary);save('metrics/NINE_CASE_RESULTS.json',runs);table('metrics/NINE_CASE_RESULTS.csv',runs);save('metrics/FAILURES.json',fail);table('metrics/FAILURES.csv',fail);save('metrics/ADAM_CLOCK_REPLAY.json',rollback);assert all(x['passed']for x in rollback);print('POST_AUDIT_DONE')
if __name__=='__main__':main()
