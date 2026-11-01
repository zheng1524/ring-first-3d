"""A single bounded robust SE(3) candidate, only when FIT evidence permits."""
from tests12 import *
SCALES=np.r_[np.full(3,np.deg2rad(cfg['rotation_scale_deg'])),np.full(3,cfg['translation_scale_mm'])]
def problem(cid):
    s=source(cid);r=np.load(R/f'runtime/ring/{short(cid)}_ORIGINAL.npz');p=r['observed_boundary'][r['observed_valid']]
    held=fit_partition(p,p);p=select_uniform(p[~held],cfg['ring_fit_boundary_max']);records=[];spec=[]
    for plan in load(R/'config/RGB_ONLY_METHOD_SELECTION.json'):
        if cid not in [plan['A'],plan['B']] or plan['selected_method'] is None:continue
        # ref13 is never used to fit a corrected pose. Its own rank is diagnostic only.
        if plan['extra_holdout'] and cid!=IDS[2]:continue
        a,b=plan['A'],plan['B'];d=match_data(a,b,plan['selected_method']);ids=np.flatnonzero(d['independent_good']&~d['held']);ii=select_uniform(ids,cfg['matching_fit_cap_per_relation'])
        records.append(dict(A=a,B=b,p=d['p'][ii],q=d['q'][ii],method=plan['selected_method'],raw_match_ids=ii));spec.append(dict(pair=plan['pair_id'],method=plan['selected_method'],raw_match_ids=ii,extra_holdout=plan['extra_holdout']))
    def residual(y,prior=False):
        T=local_pose(s['T'],np.asarray(y)*SCALES);curves=torus_contours(T[:3,3],T[:3,:3],s['K'],n=cfg['torus_curve_samples']).reshape(-1,2)
        ringr=cKDTree(curves).query(p)[0]/cfg['ring_max_MAE_px']/np.sqrt(max(1,len(p)))
        image=[]
        for rec in records:
            sa,sb=source(rec['A']),source(rec['B']);Ta=T if rec['A']==cid else sa['T'];Tb=T if rec['B']==cid else sb['T']
            image.append(sampson(fundamental(sa['K'],Ta,sb['K'],Tb),rec['p'],rec['q'],signed=True))
        ir=np.concatenate(image)/cfg['pose_inlier_px'] if image else np.array([])
        r=np.r_[ringr,ir/np.sqrt(max(1,len(ir)))]
        return np.r_[r,y] if prior else r
    return dict(camera=cid,ring_points=p,records=records,spec=spec,residual=residual,ring_residual_N=len(p),fit_match_N=sum(len(r['p']) for r in records),ref13_rank_is_diagnostic_only=cid==IDS[2])
def numerical_jac(fn,y):
    cols=[];eps=1e-3
    for i in range(6):
        d=np.zeros(6);d[i]=eps;cols.append((fn(y+d)-fn(y-d))/(2*eps))
    return np.asarray(cols).T
def observability(pr,y=None):
    y=np.zeros(6) if y is None else y;J=numerical_jac(pr['residual'],y);n=pr['ring_residual_N'];cid=pr['camera'];T=local_pose(source(cid)['T'],y*SCALES)
    # A sampled contour has spurious yaw derivatives. Enforce the known exact
    # circular-CAD null direction before reporting data-only rank, never a prior.
    g=np.r_[np.array([0.,0.,1.]),np.cross([0.,0.,1.],T[:3,3])]/SCALES;g/=np.linalg.norm(g)
    J[:n]-=(J[:n]@g)[:,None]*g[None,:]
    _,sing,V=np.linalg.svd(J,full_matrices=False);ring_sing=np.linalg.svd(J[:n],compute_uv=False)
    rank=int((sing>max(1e-10,sing[0]*cfg['observability_singular_ratio_min'])).sum()) if len(sing) else 0
    return dict(camera=cid,data_only_singular_values=sing,relative_min_singular_value=float(sing[-1]/sing[0]) if len(sing) and sing[0]>0 else 0.,rank=rank,full_local_numerical_rank=rank==6,weakest_normalized_direction=V[-1] if len(V) else [],physical_parameter_order=['world_rx_rad','world_ry_rad','world_rz_rad','world_Cx_mm','world_Cy_mm','world_Cz_mm'],scales=SCALES,ring_only_singular_values=ring_sing,ring_exact_yaw_null_direction_normalized=g,prior_included=False,geometry_truth=False,local_linear_rank_does_not_resolve_global_symmetry_or_matching_identity=True,fit_match_N=pr['fit_match_N'],ring_fit_N=n,fit_spec=pr['spec'],ref13_rank_is_diagnostic_only=pr['ref13_rank_is_diagnostic_only'])
def selected_relations(original,cid):return [r for r in original['pairs'] if r['selected_for_gate'] and cid in [r['A'],r['B']]]
def original_status(cid,original,obs):
    rr=next(r for r in original['Ring'] if r['camera']==cid);rel=selected_relations(original,cid);reasons=[]
    if rr['clear_contradiction']:reasons.append('RING_CLEAR_GEOMETRIC_CONTRADICTION')
    for p in rel:
        if p['clear_contradiction']:reasons.append('RELATIVE_RGB_GEOMETRY_CONTRADICTION:'+pair_id(p['A'],p['B']))
    if reasons:return 'UNQUALIFIED_GEOMETRY',reasons
    if not rr['Ring_pass']:reasons.append('RING_NOT_WITHIN_FROZEN_TOLERANCE_OR_INSUFFICIENT_BOUNDARY')
    required=set(BASE)-{cid}
    present={r['B'] if r['A']==cid else r['A'] for r in rel}
    for missing in sorted(required-present):reasons.append('INSUFFICIENT_REQUIRED_RGB_RELATION:'+short(missing))
    if any(not r['pair_pass'] for r in rel):reasons.append('RGB_GEOMETRY_OR_CHEIRALITY_PARALLAX_NOT_PASSED')
    if not obs['full_local_numerical_rank']:reasons.append('DATA_ONLY_LOCAL_POSE_UNOBSERVABLE_OR_ILL_CONDITIONED')
    return ('INSUFFICIENT_EVIDENCE',reasons) if reasons else ('CONDITIONAL_USABLE',['CONDITIONAL_ON_FROZEN_REFERENCE_FAMILY_AND_PINHOLE_K; NOT_ABSOLUTE_GT'])
def main():
    original=load(R/'config/ORIGINAL_TEST12.json');assert asset(R/'config/ORIGINAL_TEST12.json')['sha256']==load(R/'config/ORIGINAL_TEST12_FROZEN.json')['extra']['results']['sha256']
    P=ring().vertices;radial_error=np.max(abs(np.sqrt((np.linalg.norm(P[:,:2],axis=1)-5.6)**2+P[:,2]**2)-.6))
    assert radial_error<=cfg['torus_CAD_max_radial_error_mm'],'analytic Ring adapter not compatible with CAD'
    probs={c:problem(c) for c in IDS};observed={c:observability(probs[c]) for c in IDS};save('config/ORIGINAL_OBSERVABILITY.json',observed)
    decisions={c:dict(original_status=original_status(c,original,observed[c])[0],reasons=original_status(c,original,observed[c])[1]) for c in IDS}
    save('config/ORIGINAL_QUALIFICATION.json',decisions)
    freeze('BEFORE_BOUNDED_CORRECTION.json',dict(CAD_analytic_radial_max_error_mm=radial_error,original_statuses=decisions,observability=asset(R/'config/ORIGINAL_OBSERVABILITY.json'),holdout_not_used_for_trigger=True))
    results=[]
    for cid in NEW:
        pr=probs[cid];rr=next(r for r in original['Ring'] if r['camera']==cid);fit_rel=[r for r in selected_relations(original,cid) if not r['extra_holdout']]
        trigger=rr['clear_contradiction'] or any(r['fit_clear_contradiction'] for r in fit_rel)
        reason=[]
        if not trigger:reason.append('NO_CLEAR_FIT_LOCALISED_ERROR_TRIGGER')
        if len(fit_rel)<2 or pr['fit_match_N']<2*cfg['fit_min_matches']:reason.append('INSUFFICIENT_TWO_REFERENCE_FIT_RGB_CONSTRAINTS')
        if not observed[cid]['full_local_numerical_rank']:reason.append('UNREGULARIZED_FIT_POSE_RANK_INSUFFICIENT')
        if reason:
            results.append(dict(camera=cid,status='NOT_ATTEMPTED',reasons=reason,optimizer_calls=0));print('CORRECTION_SKIP',short(cid),reason,flush=True);continue
        marker=R/f'config/{short(cid)}_ONE_CORRECTION_ATTEMPT.json';assert not marker.exists(),'second correction forbidden'
        save(marker,dict(camera=cid,initial_c2w=source(cid)['T'],initial_parameters=np.zeros(6),trigger_uses_holdout=False,attempt=1))
        fn=pr['residual'];lo=np.full(6,-1/np.sqrt(3));hi=-lo
        opt=least_squares(lambda y:fn(y,prior=True),np.zeros(6),bounds=(lo,hi),loss='soft_l1',f_scale=1.,max_nfev=cfg['correction_max_nfev'])
        y=opt.x;T=local_pose(source(cid)['T'],y*SCALES);oldcost=float(np.sum(fn(np.zeros(6))**2));newcost=float(np.sum(fn(y)**2));improvement=1-newcost/max(oldcost,1e-20)
        ringr=ring_test(cid,T,True,'CORRECTED');rel=[]
        for p in load(R/'config/RGB_ONLY_METHOD_SELECTION.json'):
            if cid not in [p['A'],p['B']] or p['selected_method'] is None:continue
            r=pair_test(p['A'],p['B'],p['selected_method'],Ta=T if p['A']==cid else None,Tb=T if p['B']==cid else None);r['extra_holdout']=p['extra_holdout'];rel.append(r)
        ob=observability(pr,y);bound=bool(np.max(abs(y))/(1/np.sqrt(3))>=cfg['parameter_bound_contact_fraction'])
        good=bool(opt.success and improvement>=cfg['correction_min_relative_fit_improvement'] and ringr['Ring_pass'] and len(rel)>=3 and all(r['pair_pass'] for r in rel) and ob['full_local_numerical_rank'] and not bound)
        results.append(dict(camera=cid,status='CORRECTION_CANDIDATE' if good else 'BOUNDED_CORRECTION_NOT_QUALIFIED',optimizer_calls=1,optimizer_success=bool(opt.success),nfev=int(opt.nfev),normalized_parameters=y,corrected_c2w=T,original_c2w=source(cid)['T'],rotation_change_deg=float(np.degrees(np.linalg.norm(y[:3]*SCALES[:3]))),translation_change_mm=float(np.linalg.norm(y[3:]*SCALES[3:])),boundary_contact=bound,data_cost_before=oldcost,data_cost_after=newcost,relative_fit_improvement=improvement,Ring=ringr,relations=rel,observability=ob,formal_camera_overwritten=False,fit_reference_ids=cfg['fit_reference_ids'],extra_holdout_not_fitted=IDS[2]))
        save(f'config/{short(cid)}_CORRECTED_CANDIDATE.json',results[-1]);print('CORRECTION',short(cid),results[-1]['status'],'fit improvement',improvement,'bound',bound,flush=True)
    save('config/BOUNDED_CORRECTION_RESULTS.json',results)
    freeze('AFTER_BOUNDED_CORRECTION.json',dict(results=asset(R/'config/BOUNDED_CORRECTION_RESULTS.json')))
if __name__=='__main__':main()
