"""Finite, restartable A1 experiment. B is evaluated only after A-only fitting."""
from fitting import *
import argparse

def jobs():
    return [(scene,arm)for scene,sc in protocol()['scenes'].items()for arm in protocol()['arms']if '+H'not in arm or sc['EH_extra']]
def key(scene,arm):return scene+'__'+arm
def read_results(name):
    p=R/'metrics'/name;return load(p)if p.exists()else []
def asmodel(rec):return dict(rec,p=np.array(rec['p']),R0=np.array(rec['R0']))
def primaries():
    rr=read_results('S2_ALL_STARTS.json');return [min([r for r in rr if r['scene']==s and r['arm']==a],key=lambda r:r['objective'])for s,a in jobs()]
def numerical_gate(m,met):
    g=geometry_diagnostics(np.asarray(m['p']),np.asarray(m['R0']),m['family'])
    reasons=[]
    if not m['solver_success']:reasons.append('OPTIMIZATION_BUDGET_EXHAUSTED')
    if not g['finite']or g['degenerate_faces']or g['components']!=1:reasons.append('INVALID_GEOMETRY')
    if g['axis_ratio']>20:reasons.append('EXTREME_AXIS_RATIO')
    if met['head_IoU']<.5:reasons.append('LOW_B_HEAD_IOU')
    if met['outside_fraction']>.35:reasons.append('EXCESS_B_OUTSIDE')
    if met['depth_ray_hit_fraction']<.8:reasons.append('LOW_FIXED_B_RAY_COVERAGE')
    return g,reasons
def flatten(m,met,selected):
    g,reasons=numerical_gate(m,met)
    return dict(scene=m['scene'],physical_group=protocol()['scenes'][m['scene']]['group'],kind=m['kind'],arm=m['arm'],family=m['family'],parameters=m['parameter_N'],start=m['start'],A_only_selected=selected,tier=protocol()['scenes'][m['scene']]['tier'],B=met['reference'],B_independence='CONDITIONAL',solver_converged=m['solver_success'],nfev=m['nfev'],actual_residual_evaluations=m['actual_residual_evaluations'],seconds=m['seconds'],A_objective=m['objective'],head_denominator=met['head_denominator'],B_IoU=met['head_IoU'],B_head_hit_fraction=met['head_hit_fraction'],B_miss_N=met['miss_N'],B_outside_fraction=met['outside_fraction'],boundary_median_px=met['boundary_px']['median'],boundary_p95_px=met['boundary_px']['p95'],boundary_max_px=met['boundary_px']['maximum'],fixed_depth_ray_N=met['depth_fixed_ray_N'],fixed_depth_hit_N=met['depth_hit_ray_N'],fixed_depth_hit_fraction=met['depth_ray_hit_fraction'],relative_depth_pair_N=met['relative_depth_fixed_pair_N'],relative_depth_hit_pair_N=met['relative_depth_hit_pair_N'],relative_depth_MAE_mm=met['relative_depth_mm']['MAE'],relative_depth_p95_mm=met['relative_depth_mm']['p95'],relative_depth_max_mm=met['relative_depth_mm']['maximum'],censored_relative_depth_score_mm=met['censored_relative_depth_score_mm'],CAD_occluded_fraction=met['CAD_occluded_fraction'],center_mm=g['center_mm'],axes_mm=g['axes_mm'],full_model_extents_mm=g['model_axis_full_extents_mm'],peak_above_MODEL_plane_mm=g['peak_above_model_plane_mm'],axis_ratio=g['axis_ratio'],components=g['components'],watertight=g['watertight'],active_bound_N=int(np.count_nonzero(m['active_bounds'])),numerical_failures=';'.join(reasons)or'NONE',physical_truth_accuracy='NOT_EVALUABLE',historical_measurement_fallback=0)
def fit_all():
    assert (R/'provenance/PREOPTIMIZATION_FREEZE.json').exists(),'Freeze protocol/code first'
    assert load(R/'metrics/S1_CONTROLS.json')['all_pass']
    rr=read_results('S2_ALL_STARTS.json')
    for scene,arm in jobs():
        for start in protocol()['optimization']['initializations']:
            if any(r['scene']==scene and r['arm']==arm and r['start']==start for r in rr):continue
            print('FIT',scene,arm,start,flush=True);p=Problem(scene,arm);result=p.solve(start)
            result['B_metrics']=[evaluate(result,cid)for cid in protocol()['scenes'][scene]['B']]
            rr.append(clean(result));save('metrics/S2_ALL_STARTS.json',rr)
            print('DONE',scene,arm,start,'cost',round(result['objective'],4),'B_IoU',round(result['B_metrics'][0]['head_IoU'],4),'sec',round(result['seconds'],2),flush=True)
    chosen=primaries();rows=[]
    for m in chosen:
        mod=asmodel(m);k=key(m['scene'],m['arm']);P,F=mesh(mod['p'],mod['R0'],m['family'],True)
        trimesh.Trimesh(P,F,process=False).export(R/'local_results'/(k+'.ply'))
        for cid in protocol()['scenes'][m['scene']]['B']:evaluate(mod,cid,R/'local_results'/(k+'__'+cid+'.npz'))
        m['A_metrics']=[evaluate(mod,cid)for cid in protocol()['scenes'][m['scene']]['A']]
        m['geometry'],m['numerical_failures']=numerical_gate(m,m['B_metrics'][0])
        for r in rr:
            if (r['scene'],r['arm'])==(m['scene'],m['arm']):rows.append(flatten(r,r['B_metrics'][0],r['start']==m['start']))
    for arm in ['A1-0','A1-1','A1-2','A1-3']:
        rows.append(dict(scene='G01_005',physical_group='G01',kind='Ip',arm=arm,tier='AUDIT_ONLY_SEPARATE_SPACE',A_only_selected=False,numerical_failures='NOT_EVALUABLE_NO_CURRENT_GATE_AND_CLEANUP',B_IoU=None,physical_truth_accuracy='NOT_EVALUABLE',historical_measurement_fallback=0))
    table('04_ABLATION_METRICS.csv',rows);save('metrics/S2_PRIMARY.json',chosen)

def jacobians():
    rr=read_results('S4_JACOBIANS.json')
    for m in load(R/'metrics/S2_PRIMARY.json'):
        k=key(m['scene'],m['arm'])
        if any(r['key']==k for r in rr):continue
        prob=Problem(m['scene'],m['arm']);p=np.array(m['p']);_,v=prob.parts(p);sc=np.r_[np.ones(3),np.full(3,.1),np.full(3,.2),np.full(len(p)-9,.1)]
        js=[]
        for h in [.001,.0005]:
            J=np.column_stack([(prob.residual(p+np.eye(len(p))[j]*sc[j]*h,white=True,observation_only=True,fixed_visibility=v)-prob.residual(p-np.eye(len(p))[j]*sc[j]*h,white=True,observation_only=True,fixed_visibility=v))/(2*h)for j in range(len(p))]);js.append(J)
        U,s,V=np.linalg.svd(js[1],full_matrices=False);ratio=float(s[-1]/max(s[0],1e-30));diff=float(np.linalg.norm(js[0]-js[1])/max(np.linalg.norm(js[1]),1e-30))
        record=dict(key=k,scene=m['scene'],arm=m['arm'],parameters=len(p),observational_rows=len(js[1]),parameter_scales=sc,noise_sigma=dict(C_px=3,D_mm=.25,H_mm=.25),priors_included=False,robustification=False,visibility='FROZEN_AT_SOLUTION_FOR_LOCAL_J; visibility discontinuities separately evaluated',singular_values=s,singular_ratio=ratio,condition_number=float(s[0]/s[-1])if s[-1]>1e-14 else None,effective_ranks={str(t):int((s>s[0]*t).sum())for t in [.01,.001,.0001,.000001]},weakest_normalized_parameter_direction=V[-1],relative_two_step_J_difference=diff,status='NUMERICALLY_UNSTABLE_J'if diff>.1 else'LOCALLY_UNIDENTIFIABLE'if ratio<.001 else'LOCALLY_FULL_RANK_CONDITIONAL')
        rr.append(clean(record));save('metrics/S4_JACOBIANS.json',rr);print('J',k,record['status'],'ratio',ratio,'diff',diff,flush=True)

def perturbations():
    rr=read_results('S4_PERTURBATIONS.json')
    # Predeclared stress analyses target C+D base and class model, without +H.
    cases=[('contour_plus_1px',dict(support_shift=1.)),('D_weight_0.9',dict(depth_weight=.9)),('D_weight_1.1',dict(depth_weight=1.1)),('last_A_removed',None),('camera_right_tx_0.05mm_ry_0.1deg',dict(camera_delta=True))]
    for m in load(R/'metrics/S2_PRIMARY.json'):
        if m['arm']not in ['A1-2','A1-3']:continue
        for name,kw in cases:
            k=key(m['scene'],m['arm'])+'__'+name
            if any(r['key']==k for r in rr):continue
            if kw is None:kw=dict(ids=protocol()['scenes'][m['scene']]['A'][:-1])
            prob=Problem(m['scene'],m['arm'],**kw);out=prob.solve(0,30,initial=np.array(m['p']));out['key']=k;out['perturbation']=name;out['B_metrics']=[evaluate(out,cid)for cid in protocol()['scenes'][m['scene']]['B']]
            a=geometry_diagnostics(np.array(m['p']),np.array(m['R0']),m['family']);g=geometry_diagnostics(out['p'],out['R0'],out['family']);out['geometry']=g;out['center_displacement_mm']=float(np.linalg.norm(g['center_mm']-a['center_mm']));out['axis_relative_change']=float(np.max(abs(g['axes_mm']/np.asarray(a['axes_mm'])-1)));out['B_IoU_change']=out['B_metrics'][0]['head_IoU']-m['B_metrics'][0]['head_IoU']
            rr.append(clean(out));save('metrics/S4_PERTURBATIONS.json',rr);print('PERTURB',k,'dc',round(out['center_displacement_mm'],3),'dIoU',round(out['B_IoU_change'],3),flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('stage',choices=['fit','jacobian','stability']);args=ap.parse_args()
    {'fit':fit_all,'jacobian':jacobians,'stability':perturbations}[args.stage]()
