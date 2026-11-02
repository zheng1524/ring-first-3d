"""Bounded projective evidence using unchanged real camera/CAD routines."""
from common import *

def main():
    assert not (R/'PROJECTIVE_CLEANUP_DECISIONS.csv').exists(), 'ONE_ROUND_ONLY'
    p=load(R/'config/A2_PREREGISTERED.json')['projection']; cand=read_csv(R/'CLEANUP_CANDIDATES.csv'); evidence=[]; by={r['candidate_id']:[] for r in cand}
    blocks={r['source_id']:r['view_block'] for r in read_csv(D0/'VIEW_COVERAGE_SELECTION.csv')}
    qual={r['camera']:r['new_status'] for r in read_csv(REPO/'experiments/TASK-CAMERA-GATE-G01-004-PILOT-001/CAMERA_QUALIFICATION.csv')}
    for observer in IDS:
        t=baseline(observer); cc=[r for r in cand if r['source']!=observer]; X=np.array([[float(r[k]) for k in ['X_mm','Y_mm','Z_mm']] for r in cc]); uv,z=vis.project_camera(X,t['K'],t['T']); nuv,_=vis.project_camera(X,t['Kn'],t['T'])
        inside=np.isfinite(uv).all(1)&np.isfinite(z)&(z>0)&(uv[:,0]>=-.5)&(uv[:,0]<639.5)&(uv[:,1]>=-.5)&(uv[:,1]<359.5)
        ni=(nuv[:,0]>=-.5)&(nuv[:,0]<639.5)&(nuv[:,1]>=-.5)&(nuv[:,1]<351.5); inside &= ni
        j=np.flatnonzero(inside); pix=np.floor(uv[j]+.5).astype(int); npix=np.floor(nuv[j]+.5).astype(int); lab=np.full(len(cc),-1,int); dist=np.full(len(cc),np.nan); cad=np.full(len(cc),np.inf); zd=np.full(len(cc),np.nan); zn=np.full(len(cc),np.nan); legal=np.zeros(len(cc),bool)
        dm=cv2.distanceTransform((t['labels']!=1).astype(np.uint8),cv2.DIST_L2,5); pack=np.load(t['c']['pack'])
        lab[j]=t['labels'][pix[:,1],pix[:,0]]; dist[j]=dm[pix[:,1],pix[:,0]]; cad[j],_=cast(ringscene(),uv[j],t['K'],t['T']); zd[j]=pack['depth_mm'][pix[:,1],pix[:,0]]; zn[j]=t['depth'][npix[:,1],npix[:,0]]; legal[j]=t['valid'][npix[:,1],npix[:,0]]
        hidden=np.isfinite(cad)&(z>cad+p['CAD_epsilon_mm']); qualified=observer in p['negative_voters']
        for k,row in enumerate(cc):
            near=False; oppose=False; layer=False
            if not inside[k]: status='C_OUTSIDE_FIELD'
            elif hidden[k]: status='C_CAD_OCCLUDED'
            elif lab[k]==2: status='C_RING_MASK'
            elif lab[k]==1 and legal[k] and ((np.isfinite(zd[k]) and zd[k]>0 and abs(z[k]-zd[k])<=p['support_tolerance_mm']) or abs(z[k]-zn[k])<=p['support_tolerance_mm']):
                near=True; status='D_NEAR_SUPPORT_CONDITIONAL' if qualified else 'C_UNCERTIFIED_R14_NEAR_VETO'
            elif lab[k]==1 and legal[k]:
                layer=qualified; status='B_DEPTH_LAYER_COMPETITION' if qualified else 'C_UNCERTIFIED_R14_LAYER'
            elif lab[k]==1: status='C_INVALID_OR_EXCLUDED_POLYP_DEPTH'
            elif lab[k]==0 and dist[k]>p['silhouette_margin_archived_px']:
                oppose=qualified; status='A_CONDITIONAL_SILHOUETTE_CONTRADICTION' if qualified else 'C_R14_NOT_NEGATIVE_VOTER'
            else: status='C_BOUNDARY_UNCERTAIN'
            ev=dict(candidate_id=row['candidate_id'],source=row['source'],native_id=int(row['native_id']),observer=observer,observer_block=blocks[observer],
                target_archive_u=float(uv[k,0]),target_archive_v=float(uv[k,1]),target_axial_Z_mm=float(z[k]),target_native_u=float(nuv[k,0]),target_native_v=float(nuv[k,1]),inside_field=bool(inside[k]),
                target_Mask_label=int(lab[k]),outside_Polyp_distance_px=float(dist[k]),CAD_first_hit_mm=float(cad[k]),CAD_occluded=bool(hidden[k]),observer_ARCH_HERO_mm=float(zd[k]),observer_NATIVE_HERO_mm=float(zn[k]),observer_baseline_depth_legal=bool(legal[k]),
                camera_gate_status=qual.get(observer,'NOT_IN_CAMERA_GATE_PILOT'),inherited_use='CONDITIONAL_GEOMETRY_PROXY' if qualified else 'UNQUALIFIED_NEGATIVE_VOTE',
                evidence=status,negative_vote=oppose,near_support_veto=near,depth_layer_veto=layer,background_geometry='NOT_INDEPENDENTLY_CERTIFIED',physical_truth=False)
            evidence.append(ev); by[row['candidate_id']].append(ev)
    decisions=[]; excluded={cid:[] for cid in IDS}
    for row in cand:
        ev=by[row['candidate_id']]; blocks_opp=sorted({r['observer_block'] for r in ev if r['negative_vote']}); near=[r['observer'] for r in ev if r['near_support_veto']]; layer=[r['observer'] for r in ev if r['depth_layer_veto']]
        core_protect=row['source'] in CORE and float(row['source_mask_interior_px'])>2 and float(row['distance_to_own_original_Raw_mm'])<=1
        if near:
            category='D_SUPPORTED_RETAIN' if any(o in p['negative_voters'] for o in near) else 'C_UNKNOWN_RETAIN'; reason='NEAR_SUPPORT_VETO'
        elif layer: category='B_DEPTH_LAYER_RETAIN'; reason='POLYP_LAYER_COMPETITION_NOT_A_DELETION_TRUTH'
        elif core_protect: category='C_UNKNOWN_RETAIN'; reason='PROTECTED_CORE_CONTINUOUS_INTERIOR'
        elif len(blocks_opp)>=p['independent_opposing_blocks']: category='A_STRONG_CONTOUR_PROXY_EXCLUDE'; reason='AT_LEAST_TWO_DISTINCT_CONDITIONAL_BLOCKS_NO_SUPPORT_OR_LAYER_VETO'
        else: category='C_UNKNOWN_RETAIN'; reason='INSUFFICIENT_UNOCCLUDED_DISTINCT_CONTOUR_OPPOSITION'
        remove=category.startswith('A_')
        if remove: excluded[row['source']].append(int(row['native_id']))
        decisions.append(dict(**row,category=category,action='DERIVED_EXCLUDE' if remove else 'RETAIN',reason=reason,opposing_blocks=blocks_opp,near_sources=near,layer_sources=layer,CORE_interior_protection=core_protect,unknown_observer_N=sum(r['evidence'].startswith('C_') for r in ev),conditional_proxy_only=True,original_input_modified=False))
    out=R/'local_results/derived_inputs';out.mkdir(parents=True,exist_ok=True);summary=[]
    for cid in IDS:
        s=baseline(cid); orig=native(cid); depth=s['depth'].copy(); valid=s['valid'].copy(); mask=np.zeros(depth.shape,bool); mask.flat[np.array(excluded[cid],np.int64)]=True
        assert not np.any(mask&s['historical_excluded']); assert np.all(s['valid'][mask]); depth[mask]=0;valid[mask]=False
        assert np.array_equal(depth[~mask],s['depth'][~mask]); assert np.array_equal(valid[~mask],s['valid'][~mask])
        np.savez_compressed(out/(cid+'.npz'),depth_mm=depth,valid=valid,incremental_excluded=mask,historical_excluded=s['historical_excluded'],original_native_id=np.arange(depth.size).reshape(depth.shape))
        # Local camera-ray area footprint is only a coverage proxy, not surface area.
        area=(s['depth'].astype(float)**2)/(s['Kn'][0,0]*s['Kn'][1,1]); denom=float(area[s['valid']].sum())
        summary.append(dict(source=cid,original_N=len(orig['native_id']),baseline_N=int(s['valid'].sum()),incremental_excluded_N=int(mask.sum()),incremental_fraction_of_baseline=float(mask.sum()/s['valid'].sum()),final_N=int(valid.sum()),historical_excluded_N=int(s['historical_excluded'].sum()),
            projected_ray_area_proxy_excluded_mm2=float(area[mask].sum()),projected_ray_area_proxy_fraction=float(area[mask].sum()/denom),not_a_surface_area=True,all_other_values_bitwise_unchanged=True,derived_file=asset(out/(cid+'.npz'))))
    table('PROJECTIVE_CLEANUP_EVIDENCE.csv',evidence); table('PROJECTIVE_CLEANUP_DECISIONS.csv',decisions)
    save('CLEANUP_SUMMARY.json',dict(protocol=asset(R/'config/A2_PREREGISTERED.json'),candidate_N=len(cand),per_source=summary,category_counts={cat:sum(r['category']==cat for r in decisions) for cat in sorted({r['category'] for r in decisions})},original_N=106144,baseline_N=106098,final_N=sum(r['final_N'] for r in summary),incremental_excluded_N=sum(r['incremental_excluded_N'] for r in summary),cleanup_rounds=1,all_previous_9_retained=all(r['action']=='RETAIN' for r in decisions if r['previous_review_id']),main_surface_anatomical_truth='NOT_CERTIFIED'))
    print('A2_CLEANUP',load(R/'CLEANUP_SUMMARY.json'),flush=True)

if __name__=='__main__': main()
