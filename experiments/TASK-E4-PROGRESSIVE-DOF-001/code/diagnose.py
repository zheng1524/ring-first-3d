"""Explain stored outputs/probes; no parameter search or reconstruction selection."""
from model import *
def main():
    post=load(R/'metrics/POSTERIOR.json');assert post['all_predictions_frozen_before_GT'];b=Body();P=np.load(R/'inputs/EVAL_POINTS.npz')['P'];w=post['fixed_space_weight_mm3'];gt=np.load(post['GT_source']['path']);lo=gt['V'].min(0);hi=gt['V'].max(0);rows=[]
    for s in post['stages']:
        a=np.load(R/'local_results'/s/'FINAL/MODEL.npz');rt=scene(a['V'],a['F']);occ=signed(rt,P)<0;data=np.load(R/'audit_only'/(s+'__FINAL_ERRORS.npz'));X=data['GT_samples'];err=data['GT_distance'];centers=np.array(load(R/'config/KERNEL_CENTERS.json')['centers_mm']);support=np.min(np.linalg.norm(X[:,None]-centers[None],axis=2),axis=1)<b.radius;bad=err>.2
        rows.append(dict(stage=s,GT_z_interval_mm=[float(lo[2]),float(hi[2])],prediction_volume_below_GT_min_z_mm3=float((occ&(P[:,2]<lo[2])).sum()*w),prediction_volume_above_GT_max_z_mm3=float((occ&(P[:,2]>hi[2])).sum()*w),GT_samples_in_local_support_N=int(support.sum()),GT_samples_outside_local_support_N=int((~support).sum()),GT_error_inside_local_support_mm=stats(err[support]),GT_error_outside_local_support_mm=stats(err[~support]),GT_error_over_0p2mm_N=int(bad.sum()),fraction_large_GT_errors_outside_local_support=float((bad&~support).sum()/max(1,bad.sum())),selection_was_fit_residual_only=True))
    components=[]
    for s in post['stages'][1:]:
        g=np.load(R/'audit_only'/('COMPONENT_'+s+'_GLOBAL_ONLY.npz'));f=np.load(R/'local_results'/s/'FINAL/MODEL.npz');V=g['V'];d=-signed(scene(f['V'],f['F']),V)+signed(scene(g['V'],g['F']),V);full=next(x for x in post['endpoints']if x['name']==s+'/FINAL');globalonly=next(x for x in post['components']if x['name']=='COMPONENT_'+s+'_GLOBAL_ONLY')
        components.append(dict(stage=s,local_actual_Eulerian_displacement_on_same_global_zero_set_mm=stats(d),largest_outward_mm=float(d.max()),largest_inward_mm=float(-d.min()),full_minus_global_only_Chamfer_MAE_mm=full['Chamfer_mm']['MAE']-globalonly['Chamfer_mm']['MAE'],full_minus_global_only_FIXED_GT_to_prediction_MAE_mm=full['GT_to_prediction_mm']['MAE']-globalonly['GT_to_prediction_mm']['MAE'],full_minus_global_only_symmetric_difference_mm3=full['volume']['symmetric_difference_mm3']-globalonly['volume']['symmetric_difference_mm3'],fixed_GT_samples_unchanged=True,sampled_symmetric_Chamfer_precision_caution='prediction-area Monte Carlo points change when mesh tessellation changes; micron-scale changes not certified as meaningful'))
        np.savez_compressed(R/'audit_only'/(s+'_LOCAL_COMPONENT_MOTION.npz'),V=V,F=g['F'],local_motion=d)
    search=[]
    for s in ['S1',post['stages'][-1]]:
        d=load(R/'metrics'/(s+'_FINAL_SENSITIVITY.json'));q=np.array(d['q']);D=np.ones(len(q));D[3:6]=1/(b.a0*np.exp(q[3:6]));cfg=protocol();bounds=np.array(cfg['global_bounds']+([]if len(q)==6 else cfg['amplitude_bounds_mm'])+([[-cfg['center_offset_limit_mm'],cfg['center_offset_limit_mm']]]*(len(q)-8)if len(q)>8 else[]));probes=[]
        for row in d['rows']:
            eps=row['epsilon_physical_mm']
            for col in row['columns']:
                j=col['parameter']
                for side,sign in [('plus',1),('minus',-1)]:
                    requested=eps*D[j];actual=np.clip(q[j]+sign*requested,*bounds[j])-q[j];probes.append(dict(eps=eps,parameter=j,side=side,loss=col[side+'_loss'],decrease=d['actual_objective']-col[side+'_loss'],raw_parameter_step=float(actual),clipped=bool(abs(actual)<requested-1e-12)))
        best=min(probes,key=lambda x:x['loss']);consistent=[]
        for j in range(len(q)):
            for side in ['plus','minus']:
                group=[x for x in probes if x['parameter']==j and x['side']==side]
                if all(x['decrease']>1e-4 for x in group):consistent.append(dict(parameter=j,side=side,probe_records=group,distinct_actual_steps=len(set(round(x['raw_parameter_step'],12)for x in group))))
        search.append(dict(stage=s,final_loss=d['actual_objective'],best_already_tested_probe=best,consistent_directions=consistent,GT_not_used=True,no_new_probe_evaluations=True,no_probe_selected_as_prediction=True))
    save('metrics/DIAGNOSIS.json',dict(regions=rows,local_components=components,search=search,GT_used_only_after_freeze=True,one_run_cannot_uniquely_separate_observation_representation_search=True));print('DIAGNOSIS_DONE',rows,components,search,flush=True)
if __name__=='__main__':main()
