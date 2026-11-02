"""Incremental input validation, same pixel affine and common metric cube."""
from common import *

@lru_cache(None)
def final_native(cid):
    s=baseline(cid); d=np.load(R/'local_results/derived_inputs'/(cid+'.npz'));depth,valid=d['depth_mm'],d['valid'];v,u=np.nonzero(valid);uv=np.c_[u,v]
    return dict(s,depth=depth,valid=valid,native_uv=uv,native_id=v*640+u,X=unproject(depth[v,u].astype(float),s['T'],uv,s['Kn']))

def comparison(s,c):
    uv=s['native_uv']; q=affine_uv(uv,c['A']); p=np.floor(q+.5).astype(int)
    ok=(p[:,0]>=0)&(p[:,0]<320)&(p[:,1]>=0)&(p[:,1]<240); j=np.flatnonzero(ok); j=j[c['valid'][p[j,1],p[j,0]]]
    picked=np.full(len(uv),-1,np.int64);err=np.full(len(uv),np.nan);picked[j]=c['source_ids'][p[j,1],p[j,0]]
    X=unproject(c['depth_mm'][p[j,1],p[j,0]].astype(float),s['T'],p[j],c['K_crop']);err[j]=np.linalg.norm(X-s['X'][j],axis=1)
    return q,p,picked,err

def resampling_case(cid,s,c,stage,k):
    q,p,picked,err=comparison(s,c); a=s['native_uv'][k]; b=np.array([picked[k]%640,picked[k]//640]); native=s['depth']; za=float(native[a[1],a[0]]);zb=float(native[b[1],b[0]])
    # Exact actually-selected source pixel unprojected with original K, compared with output ray.
    xb=unproject(np.array([zb]),s['T'],b[None],s['Kn'])[0]; xo=unproject(np.array([float(c['depth_mm'][p[k,1],p[k,0]])]),s['T'],p[k,None],c['K_crop'])[0]
    discontinuity=abs(za-zb)>=1.
    return dict(source=cid,stage=stage,original_native_id=int(s['native_id'][k]),original_u=int(a[0]),original_v=int(a[1]),original_depth_mm=za,
        output_u=int(p[k,0]),output_v=int(p[k,1]),output_continuous_u=float(q[k,0]),output_continuous_v=float(q[k,1]),
        selected_native_id=int(picked[k]),selected_u=int(b[0]),selected_v=int(b[1]),selected_depth_mm=zb,native_pixel_displacement_px=float(np.linalg.norm(a-b)),
        forward_pair_XYZ_error_mm=float(err[k]),native_depth_difference_mm=abs(za-zb),crosses_1mm_depth_jump=discontinuity,
        original_ID_represented_elsewhere=bool(np.isin(s['native_id'][k],c['source_ids'][c['valid']])),
        chosen_original_XYZ_vs_actual_output_ray_mm=float(np.linalg.norm(xb-xo)),actual_inverse_NN_identity_correct=bool(picked[k]==c['source_ids'][p[k,1],p[k,0]]),
        blended_or_fabricated_depth=False,actual_depth_equals_original_selected_pixel=bool(c['depth_mm'][p[k,1],p[k,0]]==native[b[1],b[0]]),
        mechanism='DISCRETE_FORWARD_PAIR_CROSSES_DEPTH_JUMP; inverse sampler selects exact other legal native pixel' if discontinuity else 'CONTINUOUS_SAME_LAYER_QUANTIZATION',
        far_native_input_status='possible far/competing native surface; see projective decisions, not certified wrong',
        future_NF_risk='coarse lattice can represent the selected competing layer and omit adjacent layer; no fake averaged depth',
        bounded_revision_proposal='flag 4-neighbour>=1mm source footprints as uncertain, retain both native IDs; seek PM approval before any depth masking/resampling change' if discontinuity else 'none')

def diagnose_thin():
    cid=IDS[-1];s=final_native(cid);c=make_crop(s)
    context=load(BASE/'HUMAN_REVIEW_CONTEXT.json')['r14_candidate'];u,v=map(int,context['crop_uv'])
    nu,nv=c['nearest_source_uv'][v,u];dt,ridge=ridge_proxy(c['valid']);ndt,nridge=ridge_proxy(s['valid']);auv=archive_uv(s,np.array([[nu,nv]]))[0]
    assert [int(nu),int(nv)]==context['native_uv'], 'HISTORICAL_THIN_IDENTITY'
    sl=(slice(max(0,nv-4),nv+5),slice(max(0,nu-4),nu+5));cl=(slice(v-4,v+5),slice(u-4,u+5));zpatch=s['depth'][sl];vp=s['valid'][sl]
    thin=dict(source=cid,old_crop_uv=[u,v],mapped_native_uv=[int(nu),int(nv)],archive_uv=auv,old_output_width_proxy_px=2.,current_output_width_proxy_px=float(2*dt[v,u]),current_is_local_ridge=bool(ridge[v,u]),
        current_native_width_proxy_px=float(2*ndt[nv,nu]),current_native_is_local_ridge=bool(nridge[nv,nu]),native_depth_mm=float(s['depth'][nv,nu]),output_depth_mm=float(c['depth_mm'][v,u]),native_9x9_valid_N=int(vp.sum()),crop_9x9_valid_N=int(c['valid'][cl].sum()),native_9x9_depth_range_mm=[float(zpatch[vp].min()),float(zpatch[vp].max())],
        original_mask_unchanged=True,incremental_excluded_at_thin_pixel=bool(np.load(R/'local_results/derived_inputs'/(cid+'.npz'))['incremental_excluded'][nv,nu]),
        historical_report_coordinate_typo='prior narrative(99,143); actual prior stored pixel/context(99,144), native(282,215); numeric Gate A FAIL unchanged',
        status='THIN_STRUCTURE_UNRESOLVED_BY_CROP',anatomy='a crop medial-ridge corner proxy, not a certified stalk; inspect true RGB and native Mask; anatomy remains unconfirmed',
        old_3px_gate='FAIL_PRESERVED',proposed_v0_2='separate sampling topology/identity preservation from anatomical thinness; require source-traced native narrow region + RGB/human evidence before applying anatomical minimum width. PROPOSAL_ONLY, not accepted')
    save('R14_THIN_STRUCTURE_DIAGNOSIS.json',thin);print('A2_R14',thin,flush=True)

def main():
    assert not (R/'MODEL_DOMAIN_COMPARISON.json').exists(), 'VALIDATION_ALREADY_DONE'
    ss={cid:final_native(cid) for cid in IDS}; cohorts=[('ORIGINAL_ALL',native),('PREVIOUS_46_CLEANUP',baseline),('A2_INCREMENTAL',final_native)];domains=[]; bounds=[]
    decisions=read_csv(R/'PROJECTIVE_CLEANUP_DECISIONS.csv'); dmap={(d['source'],int(d['native_id'])):d for d in decisions}
    for name,loader in cohorts:
        sources={cid:loader(cid) for cid in IDS}; dom=make_domain(np.concatenate([s['X'] for s in sources.values()])); O=np.asarray(dom['O_mm']);L=dom['L_mm'];checks=[]
        for cid,s in sources.items():
            X=s['X'];m=(X-O)/L;outside=((m<0)|(m>=1)).any(1);T=s['T'].copy();T[:3,3]=(T[:3,3]-O)/L;uv=s['native_uv'];z=s['depth'][uv[:,1],uv[:,0]].astype(float)/L;mx=unproject(z,T,uv,s['Kn'])
            checks.append(dict(source=cid,retained_N=len(X),OUT_OF_GRID_N=int(outside.sum()),metric_inverse_max_mm=float(np.linalg.norm(m*L+O-X,axis=1).max()),camera_scale_max_mm=float(np.linalg.norm((mx-m)*L,axis=1).max())))
            if name=='A2_INCREMENTAL':
                for axis in range(3):
                    for side,k in [('min',X[:,axis].argmin()),('max',X[:,axis].argmax())]:
                        key=(cid,int(s['native_id'][k]));d=dmap.get(key,{})
                        bounds.append(dict(source=cid,axis='XYZ'[axis],side=side,native_id=key[1],native_u=int(uv[k,0]),native_v=int(uv[k,1]),X_mm=float(X[k,0]),Y_mm=float(X[k,1]),Z_mm=float(X[k,2]),review_category=d.get('category','NOT_IN_REVIEW_POOL_RETAINED'),review_reason=d.get('reason','UNREVIEWED_RETAINED')))
        ring=np.asarray(ringmesh().vertices);rb=((ring-O)/L)*L+O; dom.update(cohort=name,total_retained_N=sum(len(s['X']) for s in sources.values()),per_source=checks,all_points_enclosed=not any(c['OUT_OF_GRID_N'] for c in checks),ring_inverse_max_mm=float(np.linalg.norm(rb-ring,axis=1).max()),ring_inverse_outer_mm=float(np.ptp(rb,axis=0)[:2].max()))
        domains.append(dom)
    assert domains[0]['L_mm']==61.837 and domains[1]['L_mm']==29.641
    assert all(d['all_points_enclosed'] for d in domains)
    save('MODEL_DOMAIN_COMPARISON.json',dict(domain_builder=asset(BASE/'code/metric_domain.py'),cohorts=domains,current_candidate=domains[-1],formally_frozen_for_NF=False,smaller_is_not_quality_gate=True,diagnostic_25_735_is_not_target=True));table('FINAL_BOUNDARY_POINTS.csv',bounds)
    geometry=[]; cases=[]; output=R/'local_results/crops';output.mkdir(exist_ok=True)
    for cid,s in ss.items():
        c=make_crop(s); old=np.load(next(r['crop']['path'] for r in LINEAGE['sources'] if r['source']==cid));assert np.array_equal(c['A'],old['A']) and np.array_equal(c['K_crop'],old['K_crop'])
        np.savez_compressed(output/(cid+'.npz'),**{k:v for k,v in c.items() if isinstance(v,np.ndarray)})
        uv=s['native_uv'];z=s['depth'][uv[:,1],uv[:,0]].astype(float);q=affine_uv(uv,c['A']);xa=unproject(z,s['T'],q,c['K_crop']);err=np.linalg.norm(xa-s['X'],axis=1)
        qo,p,picked,pair_error=comparison(s,c);source_ids=c['source_ids'][c['valid']];depth_source=s['depth'].ravel()[source_ids]
        outuv=c['output_uv'];selected_uv=np.c_[source_ids%640,source_ids//640];xs=unproject(depth_source.astype(float),s['T'],selected_uv,s['Kn']);actual=np.linalg.norm(xs-c['output_X_mm'],axis=1)
        dt,ridge=ridge_proxy(c['valid']); narrow=ridge&(2*dt<3)
        geometry.append(dict(source=cid,original_N=len(native(cid)['native_id']),baseline_N=len(baseline(cid)['native_id']),final_N=len(uv),output_legal_N=int(c['valid'].sum()),analytic_max_mm=float(err.max()),analytic_PASS=bool(err.max()<=1e-5),crop_A_K_bitwise_unchanged=True,
            actual_NN_source_ID_and_depth_exact=bool(np.array_equal(depth_source,c['depth_mm'][c['valid']])),actual_NN_ray_shift_median_mm=float(np.median(actual)),actual_NN_ray_shift_max_mm=float(actual.max()),
            forward_pair_median_mm=stats(pair_error)['median'],forward_pair_p95_mm=stats(pair_error)['p95'],forward_pair_max_mm=stats(pair_error)['maximum'],output_sub3px_ridge_N=int(narrow.sum()),minimum_crop_ridge_px=float((2*dt[ridge]).min()),
            Ring_BG_Pad_depth_nonzero_N=int(((c['semantics']!=1)&(c['depth_mm']!=0)).sum()),source_ID_represented_N=len(np.unique(source_ids)),cameras_changed=False))
        if cid in IDS[2:5]:
            for stage,loader in [('PREVIOUS_46_CLEANUP',baseline),('A2_INCREMENTAL',final_native)]:
                a=loader(cid);ac=make_crop(a);_,_,_,e=comparison(a,ac);k=int(np.nanargmax(e));cases.append(resampling_case(cid,a,ac,stage,k))
    table('INCREMENTAL_GEOMETRY_VALIDATION.csv',geometry);table('RESAMPLING_FAILURE_DIAGNOSIS.csv',cases)
    diagnose_thin()
    save('config/VALIDATION_REUSE.json',dict(reused_functions=REUSE,previous_24_pairs=asset(BASE/'CROSS_VIEW_PROJECTION_VALIDATION.csv'),why_not_rerun_entire_Gate_A='unchanged A,K,c2w and subset of original point IDs; previous all-original24-pair algebra remains applicable; only changed inputs checked',GPU=0,neural_imports=sorted(n for n in sys.modules if n.startswith(('torch','tensorflow','training','graphics')))))
    print('A2_DOMAINS',[(d['cohort'],d['L_mm'],d['total_retained_N']) for d in domains],flush=True)
    print('A2_RESAMPLING',cases,flush=True)

if __name__=='__main__': main()
