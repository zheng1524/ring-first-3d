"""Create all-denominator statistics and interfaces from completed, fixed fits."""
from run import *
def summarize():
    rr=load(R/'metrics/S2_PRIMARY.json');allr=load(R/'metrics/S2_ALL_STARTS.json');jj=load(R/'metrics/S4_JACOBIANS.json');pert=load(R/'metrics/S4_PERTURBATIONS.json');ranges=load(R/'metrics/PARAMETER_EMPIRICAL_RANGES.json');rows=[];paired=[];coverage=[]
    for m in rr:
        b=m['B_metrics'][0];g=m['geometry'];j=next(x for x in jj if x['key']==key(m['scene'],m['arm']))
        span=next(x['center_range_mm']for x in ranges if(x['scene'],x['arm'])==(m['scene'],m['arm']))
        rows.append(dict(scene=m['scene'],arm=m['arm'],kind=m['kind'],B_IoU=b['head_IoU'],B_hit_fraction=b['head_hit_fraction'],B_outside_fraction=b['outside_fraction'],boundary_median_px=b['boundary_px']['median'],boundary_p95_px=b['boundary_px']['p95'],boundary_max_px=b['boundary_px']['maximum'],depth_hit_fraction=b['depth_ray_hit_fraction'],relative_depth_MAE_mm=b['relative_depth_mm']['MAE'],relative_depth_p95_mm=b['relative_depth_mm']['p95'],relative_depth_max_mm=b['relative_depth_mm']['maximum'],numerical_failures=';'.join(m['numerical_failures'])or'NONE',J=j['status'],J_singular_ratio=j['singular_ratio'],condition_number=j['condition_number'],J_two_steps_difference=j['relative_two_step_J_difference'],empirical_center_range_mm=span))
    for scene,sc in protocol()['scenes'].items():
        for a,b in [('A1-0','A1-2'),('A1-1','A1-2'),('A1-2','A1-3')]+([('A1-2','A1-2+H'),('A1-3','A1-3+H')]if sc['EH_extra']else[]):
            l=next(x for x in rr if(x['scene'],x['arm'])==(scene,a));r=next(x for x in rr if(x['scene'],x['arm'])==(scene,b));lm=l['B_metrics'][0];rm=r['B_metrics'][0];dw=rm['relative_depth_mm']['MAE']-lm['relative_depth_mm']['MAE'];hit=rm['depth_ray_hit_fraction']-lm['depth_ray_hit_fraction'];paired.append(dict(scene=scene,kind=sc['kind'],baseline=a,candidate=b,qualification=sc['tier'],holdout='CONDITIONAL',delta_B_IoU=rm['head_IoU']-lm['head_IoU'],delta_depth_hit_fraction=hit,delta_B_relative_depth_MAE_mm=dw,relative_IoU_improvement=rm['head_IoU']/lm['head_IoU']-1,relative_D_MAE_reduction=1-rm['relative_depth_mm']['MAE']/lm['relative_depth_mm']['MAE'],coverage_loss_flag=hit<0,lower_error_with_lower_coverage=hit<0 and dw<0,physically_verified='NOT_EVALUABLE'))
    # Keep all failed groups as explicit NaN records, not empty cells.
    with (R/'04_ABLATION_METRICS.csv').open()as f:metrics=list(csv.DictReader(f))
    metrics=[x for x in metrics if not x['scene'].startswith(('G04','G05'))]
    for scene in ['G04_004','G05_004']:
        for arm in ['A1-0','A1-1','A1-2','A1-3']:metrics.append(dict(scene=scene,physical_group=scene[:3],kind='Is',arm=arm,A_only_selected=False,tier='NOT_EVALUABLE_UNQUALIFIED_ARCHIVED_CAMERA',numerical_failures='NO_QUALIFIED_INPUT',B_IoU='NaN',relative_depth_MAE_mm='NaN',physical_truth_accuracy='NOT_EVALUABLE',historical_measurement_fallback=0))
    for x in metrics:
        if x['scene']=='G01_005':
            for k in ['B_IoU','B_head_hit_fraction','B_outside_fraction','boundary_median_px','boundary_p95_px','boundary_max_px','fixed_depth_hit_fraction','relative_depth_MAE_mm','relative_depth_p95_mm','relative_depth_max_mm']:x[k]='NaN'
    table('04_ABLATION_METRICS.csv',metrics);table('metrics/PRIMARY_COMPARISON.csv',rows);table('metrics/PAIRED_COMPARISON.csv',paired)
    # Initial/final same A fixed pixels; no optimizer change, coverage never a loss.
    for m in rr:
        prob=Problem(m['scene'],m['arm']);initial=np.asarray(m['initial']);final=np.asarray(m['p']);R0=np.asarray(m['R0'])
        for cid,rays in zip(prob.ids,prob.rays):
            z0=first_depth(initial,R0,m['family'],rays);z1=first_depth(final,R0,m['family'],rays);o=observation(cid);pair=o['pairs'];h0=np.isfinite(z0);h1=np.isfinite(z1);valid0=h0[pair].all(1);valid1=h1[pair].all(1);e0=stats(z0[pair[valid0,0]]-z0[pair[valid0,1]]-o['depth_delta_mm'][valid0]);e1=stats(z1[pair[valid1,0]]-z1[pair[valid1,1]]-o['depth_delta_mm'][valid1])
            coverage.append(dict(scene=m['scene'],arm=m['arm'],source=cid,fixed_N=len(z0),initial_hit_N=int(h0.sum()),final_hit_N=int(h1.sum()),final_lost_original_hits=int((h0&~h1).sum()),depth_MAE_initial_mm=e0['MAE'],depth_MAE_final_mm=e1['MAE'],coverage_loss_potential_failure=bool(h1.sum()<h0.sum()),candidate_CAD_visibility='Source prequalified; model-depth CAD eligibility evaluated separately; zero fitted A rays behind CAD in audit'))
    table('metrics/COVERAGE_DEGENERACY.csv',coverage)
    aggregates=[]
    for arm in ['A1-0','A1-1','A1-2','A1-3']:
        r=[x for x in rows if x['arm']==arm]
        aggregates.append(dict(arm=arm,target_physical_groups=6,numeric_output_groups=4,NaN_groups=['G04','G05'],strict_independent_qualified_groups=0,conditional_groups=['G01','G06'],pressure_groups=['G07','G08'],IoU=stats([x['B_IoU']for x in r]),relative_depth_MAE_across_groups_mm=stats([x['relative_depth_MAE_mm']for x in r]),outside_fraction=stats([x['B_outside_fraction']for x in r]),true_GT_relative_error='NOT_EVALUABLE',aggregation='descriptive mix of conditional and pressure; not a formal success statistic'))
    save('metrics/AGGREGATE_FIXED_DENOMINATORS.json',aggregates)
    # A2 raw background index; inspect only frozen file identities, no base fitting.
    with (R/'metrics/A2_BACKGROUND_CATALOG.csv').open()as f:bg=list(csv.DictReader(f))
    paths=[]
    for cid in sorted({x['reference']for x in bg}):
        p=INC/'local_results/background'/(cid+'.npz');paths.append(dict(reference=cid,asset=asset(p)if p.exists()else None,identity='EXISTING_BACKGROUND_XYZ_FROM_HERO; not new independent sensor',raw_depth_pack=CC[cid]['pack']if cid in CC else None,current_gate=GATE[cid]['qualification']if cid in GATE else'NO_CURRENT_GATE',A2_execution=False))
    save('provenance/A2_EXISTING_BACKGROUND_PATHS.json',paths)
    interface=[]
    for m in rr:
        interface.append(dict(scene=m['scene'],kind=m['kind'],arm=m['arm'],representation=m['family'],parameters=m['p'],R0=m['R0'],coordinate_frame='single_video_Ring_world_mm',validated_for_A2=False,gate='G1_NOT_PASSED_INDEPENDENT_QUALIFICATION_MISSING',uncertainty=next(x for x in ranges if(x['scene'],x['arm'])==(m['scene'],m['arm'])),mesh=asset(R/'local_results'/(key(m['scene'],m['arm'])+'.ply')),head_is_model_inferred=True,body_not_original_HERO=True,no_stalk=True,background_plane=None))
    save('metrics/A2_BODY_INTERFACE_UNVALIDATED.json',interface)
    angles=[];part=load(PART/'metrics/view_distribution.json')
    for scene,sc in protocol()['scenes'].items():
        ids=sc['A']+sc['B']
        for cid in ids:
            c=CC[cid];p=next((p for p in part if p.get('source_id')==c['group']+'_video'+c['video']and p.get('index')==c['reference_index']),{})
            for b in sc['B']:
                T=source(cid)['T'];Tb=source(b)['T'];x=T[:3,3];y=Tb[:3,3];angles.append(dict(scene=scene,source=cid,role='A'if cid in sc['A']else'B',view_partition_block=p.get('block','UNKNOWN'),B=b,optical_axis_angle_deg=float(np.rad2deg(np.arccos(np.clip(T[:3,2]@Tb[:3,2],-1,1)))),camera_center_distance_mm=float(np.linalg.norm(x-y)),Ring_orbit_angle_deg=float(np.rad2deg(np.arccos(np.clip(x@y/(np.linalg.norm(x)*np.linalg.norm(y)),-1,1))))))
    table('metrics/FROZEN_VIEW_PARTITION_AND_ANGLES.csv',angles)
    save('metrics/EXPERIMENT_SUMMARY.json',dict(freeze_commit='7cd3c47',target_qualification_groups=6,actual_fitted_physical_groups=4,models=len(rr),starts=len(allr),fit_solver_success=sum(x['solver_success']for x in allr),fit_seconds=sum(x['seconds']for x in allr),actual_residual_evaluations=sum(x['actual_residual_evaluations']for x in allr),perturbations=len(pert),perturb_seconds=sum(x['seconds']for x in pert),J_status_counts={s:sum(x['status']==s for x in jj)for s in sorted({x['status']for x in jj})},coverage_loss_pairs=[x for x in paired if x['coverage_loss_flag']],A2_executions=0,B1_B2_executions=0,GPU=0,new_HERO=0,real_GT_read=0,historical_prediction_fallback=0,G0='QUALIFICATION_AUDIT_COMPLETE_FORMAL_EVIDENCE_INCOMPLETE',G1='NOT_PASSED',strict_G1_pass_cases=0))
    for name in ['fit','jacobian','stability','audit','visualize']:
        p=R/'runtime'/(name+'.log')
        if p.exists():(R/'metrics'/(name.upper()+'_EXECUTION.log')).write_bytes(p.read_bytes())
    save('provenance/ENVIRONMENT.json',dict(Python=sys.version,numpy=np.__version__,scipy=__import__('scipy').__version__,opencv=cv2.__version__,trimesh=trimesh.__version__,open3d=o3d.__version__,CPU_only=True))
    print('SUMMARY_DONE',flush=True)
if __name__=='__main__':summarize()
