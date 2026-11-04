"""Fixed-denominator paired comparison and actual mesh stability; no refitting."""
from fitting import *
from itertools import combinations,product
def geom(m):return decode(np.array(m['p']),np.array(m['R0']))
def sample_mesh(m,count=2048):
    P,F=mesh(np.array(m['p']),np.array(m['R0']));area=trimesh.triangles.area(P[F]);cdf=np.cumsum(area);ids=np.searchsorted(cdf,(np.arange(count)+.5)/count*cdf[-1]);rng=np.random.default_rng(20261104);u=rng.random(count);v=rng.random(count);su=np.sqrt(u);b=np.c_[1-su,su*(1-v),su*v];return np.einsum('ij,ijk->ik',b,P[F[ids]])
def surface_distance(a,b):
    P,F=mesh(np.array(a['p']),np.array(a['R0']));Q,G=mesh(np.array(b['p']),np.array(b['R0']));sa=mesh_scene(P,F);sb=mesh_scene(Q,G);d1=sb.compute_distance(o3d.core.Tensor(sample_mesh(a).astype(np.float32))).numpy();d2=sa.compute_distance(o3d.core.Tensor(sample_mesh(b).astype(np.float32))).numpy();return stats(np.r_[d1,d2])
def canonical_orientation(m):
    c,Q,a=geom(m);ix=np.argsort(-a);Q=Q[:,ix];a=a[ix]
    if np.linalg.det(Q)<0:Q[:,-1]*=-1
    return Q,a
def difference(a,b):
    c,Q,x=geom(a);d,U,y=geom(b);Q,x=canonical_orientation(a);U,y=canonical_orientation(b);rot=min(Rotation.from_matrix(Q.T@U@np.diag(sign)).magnitude()for sign in product([-1,1],repeat=3)if np.prod(sign)>0)
    return dict(center_mm=float(np.linalg.norm(c-d)),sorted_semiaxis_change_mm=y-x,maximum_semiaxis_change_mm=float(abs(y-x).max()),rotation_symmetry_aligned_deg=float(np.rad2deg(rot)),orientation_ambiguous=bool((x[:-1]/x[1:]<1.05).any()or(y[:-1]/y[1:]<1.05).any()),surface_distance_mm=surface_distance(a,b))
def main():
    records=load(R/'metrics/ALL_FITS.json');primary=load(R/'metrics/PRIMARY_A_ONLY.json');stability=[];changes=[];metrics=[]
    for r in records:
        b=r['B'][0];c,Q,a=geom(r);failure=[]
        if not r['optimizer_success']:failure.append('BUDGET_NOT_CONVERGED')
        if max(a)/min(a)>20:failure.append('AXIS_RATIO_GT20')
        if b['full_mask_IoU']<.5:failure.append('LOW_B_FULL_MASK_IOU')
        if b['outside_per_fixed_mask']>.35:failure.append('EXCESS_B_OUTSIDE')
        if b['depth_hit_fraction']<.8:failure.append('LOW_FIXED_B_DEPTH_COVERAGE')
        best=next(x for x in primary if(x['scene'],x['arm'],x['variant'])==(r['scene'],r['arm'],r['variant']))
        metrics.append(dict(scene=r['scene'],physical_group=r['scene'][:3],class_reporting_only=protocol()['scenes'][r['scene']]['kind'],tier=protocol()['scenes'][r['scene']]['tier'],arm=r['arm'],variant=r['variant'],start=r['start'],primary_A_only=r['start']==best['start'],parameters=9,optimizer_success=r['optimizer_success'],nfev=r['nfev'],actual_residual_calls=r['actual_residual_calls'],seconds=r['seconds'],A_objective=r['objective'],initial_A_objective=r['initial_objective'],B=b['reference'],full_original_mask_N=b['full_mask_denominator'],B_IoU=b['full_mask_IoU'],B_hit_N=b['intersection_N'],B_miss_N=b['miss_N'],B_miss_fraction=b['miss_per_fixed_mask'],B_outside_N=b['outside_N'],B_outside_fixed_fraction=b['outside_per_fixed_mask'],boundary_median_px=b['boundary_bidir_px']['median'],boundary_MAE_px=b['boundary_bidir_px']['MAE'],boundary_p95_px=b['boundary_bidir_px']['p95'],boundary_max_px=b['boundary_bidir_px']['maximum'],fixed_source_boundary_N=b['boundary_source_N'],fixed_source_boundary_MAE_px=b['boundary_fixed_source_px']['MAE'],fixed_depth_N=b['depth_fixed_N'],fixed_depth_hit_N=b['depth_hit_N'],fixed_depth_miss_N=b['depth_miss_N'],fixed_depth_hit_fraction=b['depth_hit_fraction'],relative_depth_fixed_pair_N=b['relative_depth_fixed_pair_N'],relative_depth_hit_pair_N=b['relative_depth_hit_pair_N'],relative_depth_MAE_mm=b['relative_depth_mm']['MAE'],relative_depth_p95_mm=b['relative_depth_mm']['p95'],relative_depth_max_mm=b['relative_depth_mm']['maximum'],CAD_occluded_N=b['CAD_occluded_N'],CAD_occluded_fraction=b['CAD_occluded_fraction'],visible_prediction_in_Ring_mask_N=b['unknown_ring_prediction_N'],center_mm=c,semiaxes_mm=a,rotation_matrix=Q,axis_ratio=b['axis_ratio'],volume_mm3=b['volume_mm3'],active_bound_N=int(np.count_nonzero(r['active_bounds'])),failures=';'.join(failure)or'NONE',real_GT='NOT_EVALUABLE',historical_measurement_fallback=0))
    for scene in protocol()['scenes']:
        for arm in protocol()['arms']:
            full=[r for r in records if(r['scene'],r['arm'],r['variant'])==(scene,arm,'full')]
            if not full:continue
            diffs=[difference(a,b)for a,b in combinations(full,2)];cent=np.array([geom(x)[0]for x in full]);axes=np.array([np.sort(geom(x)[2])for x in full]);stability.append(dict(scene=scene,arm=arm,initializations=len(full),solver_success_N=sum(x['optimizer_success']for x in full),center_pairwise_mm=stats([x['center_mm']for x in diffs]),center_axis_range_mm=np.ptp(cent,axis=0),sorted_semiaxes_axis_range_mm=np.ptp(axes,axis=0),max_semiaxis_spread_mm=float(np.ptp(axes,axis=0).max()),rotation_pairwise_deg=stats([x['rotation_symmetry_aligned_deg']for x in diffs]),rotation_ambiguous=any(x['orientation_ambiguous']for x in diffs),surface_pairwise_MAE_mm=stats([x['surface_distance_mm']['MAE']for x in diffs]),surface_pairwise_p95_mm=stats([x['surface_distance_mm']['p95']for x in diffs]),surface_pairwise_maximum_mm=max(x['surface_distance_mm']['maximum']for x in diffs),all_start_details=diffs))
            base=next(x for x in primary if(x['scene'],x['arm'],x['variant'])==(scene,arm,'full'))
            for variant in ['drop_last_A','camera_copy']:
                altered=next(x for x in primary if(x['scene'],x['arm'],x['variant'])==(scene,arm,variant));diff=difference(base,altered);changes.append(dict(scene=scene,arm=arm,variant=variant,**diff,B_IoU_change=altered['B'][0]['full_mask_IoU']-base['B'][0]['full_mask_IoU'],B_depth_hit_change=altered['B'][0]['depth_hit_fraction']-base['B'][0]['depth_hit_fraction'],B_relative_depth_MAE_change_mm=altered['B'][0]['relative_depth_mm']['MAE']-base['B'][0]['relative_depth_mm']['MAE']))
    paired=[]
    for scene in protocol()['scenes']:
        pair=[next((x for x in primary if(x['scene'],x['arm'],x['variant'])==(scene,a,'full')),None)for a in ['E1','E2']]
        if None in pair:continue
        a,b=[x['B'][0]for x in pair];sa,sb=[next(x for x in stability if(x['scene'],x['arm'])==(scene,arm))for arm in ['E1','E2']]
        paired.append(dict(scene=scene,delta_E2_minus_E1_IoU=b['full_mask_IoU']-a['full_mask_IoU'],relative_IoU_improvement=b['full_mask_IoU']/a['full_mask_IoU']-1,delta_boundary_MAE_px=b['boundary_bidir_px']['MAE']-a['boundary_bidir_px']['MAE'],delta_outside_fixed=b['outside_per_fixed_mask']-a['outside_per_fixed_mask'],delta_depth_hit=b['depth_hit_fraction']-a['depth_hit_fraction'],delta_relative_depth_MAE_mm=b['relative_depth_mm']['MAE']-a['relative_depth_mm']['MAE'],E1_center_multistart_max_mm=sa['center_pairwise_mm']['maximum'],E2_center_multistart_max_mm=sb['center_pairwise_mm']['maximum'],E1_surface_multistart_MAE_mm=sa['surface_pairwise_MAE_mm']['MAE'],E2_surface_multistart_MAE_mm=sb['surface_pairwise_MAE_mm']['MAE'],camera_displacement_E1_mm=next(x['center_mm']for x in changes if(x['scene'],x['arm'],x['variant'])==(scene,'E1','camera_copy')),camera_displacement_E2_mm=next(x['center_mm']for x in changes if(x['scene'],x['arm'],x['variant'])==(scene,'E2','camera_copy')),coverage_loss=b['depth_hit_fraction']<a['depth_hit_fraction'],contour_better_depth_worse=b['full_mask_IoU']>a['full_mask_IoU']and b['relative_depth_mm']['MAE']>a['relative_depth_mm']['MAE'],holdout='CONDITIONAL',GT='NOT_EVALUABLE'))
    save('metrics/MULTISTART_STABILITY.json',stability);save('metrics/VARIANT_STABILITY.json',changes);save('metrics/PAIRED_COMPARISON.json',paired);table('metrics/PAIRED_COMPARISON.csv',paired);table('03_E1_E2_METRICS.csv',metrics)
    # A source denominators and coverage degeneracy stay explicit.
    coverage=[]
    for m in primary:
        if m['variant']!='full':continue
        for cid,b in zip(protocol()['scenes'][m['scene']]['A'],m['A']):
            initial=dict(m,p=m['initial']);a=evaluate(initial,cid);coverage.append(dict(scene=m['scene'],arm=m['arm'],source=cid,fixed_depth_N=b['depth_fixed_N'],initial_hit_N=a['depth_hit_N'],final_hit_N=b['depth_hit_N'],coverage_decreased=b['depth_hit_N']<a['depth_hit_N'],full_mask_N=b['full_mask_denominator'],final_mask_hit_N=b['intersection_N'],relative_depth_MAE_mm=b['relative_depth_mm']['MAE']))
    table('metrics/A_COVERAGE_DEGENERACY.csv',coverage)
    save('metrics/SUMMARY.json',dict(target_groups=4,actual_groups=len(protocol()['scenes']),E1_required_A_available_groups=sum(x['E1_available']for x in protocol()['scenes'].values()),total_fits=len(records),solver_success=sum(x['optimizer_success']for x in records),fit_seconds=sum(x['seconds']for x in records),actual_residual_calls=sum(x['actual_residual_calls']for x in records),primary_conditions=len(primary),independent_full_pipeline_B_groups=0,GT='NOT_EVALUABLE',A2_B1_B2_executed=0))
    print('ANALYSIS_COMPLETE',len(paired),'paired groups',flush=True)
if __name__=='__main__':main()
