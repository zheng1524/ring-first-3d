from validate_pose import *

def main():
 frozen=load(R/'controls/ALL_PREDICTIONS_FROZEN.json');rows=[];per=[];ctrl=load(R/'controls/SOURCES.json')
 for s in ctrl:
  truth=np.load(R/'controls/audit_only'/(s['id']+'_TRUE.npz'));o=np.load(s['obs']);old=np.linalg.norm(o['X']-truth['X'],axis=1);base=pose_difference(np.array(s['C']),truth['C'])
  for b in ['Body-E','Body-U']:
   result=load(R/'controls/results'/s['id']/b/'CANDIDATES_FROZEN.json');val=validate(s,result,s['references']);per.append(val)
   if result['chosen']is None:rows.append(dict(control=s['id'],Body=b,status=val['status'],fixed_N=len(old),recovery_error_mm=None));continue
   H=np.array(result['chosen']['H']);C=np.array(result['chosen']['C']);X=transform(o['X'],H);error=np.linalg.norm(X-truth['X'],axis=1);pe=pose_difference(C,truth['C']);Ctrue=truth['C'];truez=(truth['X']-Ctrue[:3,3])@Ctrue[:3,2];newz=(X-Ctrue[:3,3])@Ctrue[:3,2];row=dict(control=s['id'],Body=b,status=val['status'],reasons=val.get('reasons'),fixed_N=len(error),initial_point_error_mm=stats(old),final_point_error_mm=stats(error),initial_pose=base,final_pose=pe,axial_recovery_error_mm=stats(newz-truez),raw_shape_edge_change_mm=val.get('edge_length_max_change_mm'),source_projection_drift_px=val.get('own_image_projection_max_px'),initial_region_error_mm=result['chosen']['initial_region_MAE_mm'],region_candidates_N=result['chosen']['region_N'],zero_drift_pass=bool(pe['translation_mm']<=.1 and pe['rotation_deg']<=1)if s['id']=='C0_ZERO'else None,GT_access='only control evaluation after all control predictions freeze; no real GT');rows.append(row);np.savez_compressed(R/'controls/results'/s['id']/b/'INDEPENDENT_GT_ERRORS.npz',X_original=o['X'],X_predicted=X,X_true=truth['X'],error_mm=error,uv=o['uv'],H=H)
 # Distinct patches: do not use a surface average; compare actual group separation.
 for b in ['Body-E','Body-U']:
  pair=[]
  for case in ['C4_LEFT','C4_RIGHT']:
   s=next(x for x in ctrl if x['id']==case);r=load(R/'controls/results'/case/b/'CANDIDATES_FROZEN.json');t=np.load(R/'controls/audit_only'/(case+'_TRUE.npz'));o=np.load(s['obs']);pair.append((t['X'],transform(o['X'],np.array(r['chosen']['H']))))
  d0=np.linalg.norm(pair[0][0].mean(0)-pair[1][0].mean(0));d1=np.linalg.norm(pair[0][1].mean(0)-pair[1][1].mean(0));rows.append(dict(control='C4_DISTINCT_PATCH_SEPARATION',Body=b,true_centroid_separation_mm=float(d0),predicted_centroid_separation_mm=float(d1),separation_change_mm=float(d1-d0),forced_surface_fusion=False,note='two source meshes retained, separate IDs; no fusion/averaging in algorithm'))
 save('metrics/CONTROL_RESULTS.json',rows);table('metrics/CONTROL_RESULTS.csv',rows);save('metrics/CONTROL_VALIDATION.json',per);save('controls/EVALUATION_COMPLETED.json',dict(epoch=time.time(),all_four_classes=True,zero_control=True,scientific_failures_retained=True));print('CONTROL_EVALUATED',len(rows),flush=True)
if __name__=='__main__':main()
