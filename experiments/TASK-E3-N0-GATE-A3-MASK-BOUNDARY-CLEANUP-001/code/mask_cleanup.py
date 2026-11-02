from common import *

def main():
    assert not (R/'CANDIDATE_DISTANCE_AUDIT.csv').exists(),'ONE_PASS_ONLY'
    assert sha(R/'config/A3_PREREGISTERED.json')==load(R/'config/BEFORE_RESULTS.json')['protocol']['sha256']
    amendment=load(R/'config/USER_BACKGROUND_OVERRIDE.json');assert amendment['threshold_native_px']==2.
    old=read_csv(A2/'PROJECTIVE_CLEANUP_DECISIONS.csv');orange=[r for r in old if r['category']=='B_DEPTH_LAYER_RETAIN'];audit=[];audit_by={};summary=[];lineage=[];decisions=[]
    for cid in IDS:
        s=v1(cid);o=native(cid);cand=[r for r in orange if r['source']==cid];ids=np.array([int(r['native_id']) for r in cand]);uv=np.c_[ids%640,ids//640];q=mask_query(cid,uv)
        dt=cv2.distanceTransform((o['native_labels']==1).astype(np.uint8),cv2.DIST_L2,5);X=unproject(o['depth'][uv[:,1],uv[:,0]].astype(float),s['T'],uv,s['Kn'])
        for k,r in enumerate(cand):
            u,v=map(int,uv[k]);valid_id=int(r['native_u'])==u and int(r['native_v'])==v and 0<=u<640 and 0<=v<352 and bool(o['valid'][v,u]) and bool(s['valid'][v,u]);err=float(np.linalg.norm(X[k]-np.array([float(r[n]) for n in ['X_mm','Y_mm','Z_mm']])));roundtrip=affine_uv(q['archive_uv'][k,None],s['Kn']@np.linalg.inv(s['K']))[0];maperr=float(np.linalg.norm(roundtrip-uv[k]));label=int(q['label'][k]);native_lab=int(o['native_labels'][v,u]);qualified=valid_id and err<=1e-8 and q['inside'][k] and label==1 and native_lab==1 and maperr<=1e-8
            if not valid_id or err>1e-8:status='IDENTITY_ERROR_RETAIN'
            elif not q['inside'][k] or label!=1:status='OUTSIDE_ORIGINAL_MASK_RETAIN'
            elif native_lab!=label or maperr>1e-8:status='MAPPING_UNCERTAIN_RETAIN'
            else:status='QUALIFIED_INSIDE_ORIGINAL_MASK'
            approved_BG=valid_id and err<=1e-8 and q['inside'][k] and label==0 and native_lab==1 and maperr<=1e-8
            if approved_BG:status='BACKGROUND_NON_POLYP_NON_RING_USER_APPROVED'
            edge=qualified and q['distance_native_px'][k]<=2.
            row=dict(candidate_id=r['candidate_id'],source=cid,native_id=int(ids[k]),native_u=u,native_v=v,archive_continuous_u=float(q['archive_uv'][k,0]),archive_continuous_v=float(q['archive_uv'][k,1]),archive_pixel_u=int(q['archive_pixel'][k,0]),archive_pixel_v=int(q['archive_pixel'][k,1]),original_mask_label=label,legacy_native_label=native_lab,identity_status=status,identity_XYZ_error_mm=err,mapping_roundtrip_error_native_px=maperr,
                distance_native_px=float(q['distance_native_px'][k]) if label==1 else np.nan,query_to_nearest_nonPolyp_center_native_px=float(q['distance_native_px'][k]),original_integer_EDT_native_px=float(q['nearest_original_raster_EDT_native_px'][k]),legacy_native_DT_px=float(dt[v,u]),nearest_BG_archive_u=float(q['nearest_BG_archive_uv'][k,0]),nearest_BG_archive_v=float(q['nearest_BG_archive_uv'][k,1]),V1_legal=bool(s['valid'][v,u]),V2_new_suppress=edge or approved_BG,V3_new_suppress=qualified or approved_BG,insidePolyp_edge_le2=edge,user_approved_BG=approved_BG,rule='Polyp metric<=2 native px OR explicitly user-approved nonPolyp/nonRing BG; no effect-driven selection',original_depth_mm=float(o['depth'][v,u]),X_mm=float(X[k,0]),Y_mm=float(X[k,1]),Z_mm=float(X[k,2]),previous_review_id=r['previous_review_id'])
            audit.append(row);audit_by[(cid,int(ids[k]))]=row
        for version in VERSIONS:
            mask=np.zeros(s['depth'].shape,bool)
            if version!='V1':
                for r in audit:
                    if r['source']==cid and r[version+'_new_suppress']:mask.flat[r['native_id']]=True
            depth=s['depth'].copy();valid=s['valid'].copy();removed_values=depth[mask].copy();depth[mask]=0;valid[mask]=False
            assert not np.any(mask&(s['historical_excluded']|s['A2_excluded']))
            restore=depth.copy();restore[mask]=removed_values;assert np.array_equal(restore,s['depth'])
            out=R/'local_results/inputs'/version;out.mkdir(parents=True,exist_ok=True)
            np.savez_compressed(out/(cid+'.npz'),depth_mm=depth,valid=valid,new_excluded=mask,suppressed_native_ids=np.flatnonzero(mask),suppressed_original_depth_mm=removed_values,historical_excluded=s['historical_excluded'],A2_excluded=s['A2_excluded'],original_native_id=np.arange(depth.size).reshape(depth.shape))
            area=s['depth'].astype(float)**2/(s['Kn'][0,0]*s['Kn'][1,1]);summary.append(dict(source=cid,version=version,V1_N=int(s['valid'].sum()),new_excluded_N=int(mask.sum()),retained_N=int(valid.sum()),retained_fraction_vs_V1=float(valid.sum()/s['valid'].sum()),ray_area_proxy_loss_mm2=float(area[mask].sum()),ray_area_proxy_loss_fraction=float(area[mask].sum()/area[s['valid']].sum()),reversible=True))
            lineage.append(dict(source=cid,version=version,file=asset(out/(cid+'.npz')),baseline=next(r['incremental'] for r in A2_LINEAGE['sources'] if r['source']==cid)))
    for r in old:
        a=audit_by.get((r['source'],int(r['native_id'])));cid=r['source'];u,v=int(r['native_u']),int(r['native_v']);base=v1(cid);legal=bool(base['valid'][v,u])
        decisions.append(dict(candidate_id=r['candidate_id'],source=cid,native_id=int(r['native_id']),A2_category=r['category'],A2_action=r['action'],V1_valid=legal,V2_valid=legal and not(a and a['V2_new_suppress']),V3_valid=legal and not(a and a['V3_new_suppress']),V2_new_suppress=bool(a and a['V2_new_suppress']),V3_new_suppress=bool(a and a['V3_new_suppress']),distance_native_px=a['distance_native_px'] if a else np.nan,identity_status=a['identity_status'] if a else 'NON_B_UNCHANGED',purple_green_unchanged=r['category'].startswith(('C_','D_'))))
    table('CANDIDATE_DISTANCE_AUDIT.csv',audit);table('CLEANUP_DECISIONS.csv',decisions);table('SOURCE_VERSION_RETENTION.csv',summary)
    save('DERIVED_INPUT_MANIFEST.json',dict(sources=lineage,original_N=106144,preA2_N=106098,V1_N=105875,versions=VERSIONS,all_originals_unchanged=True,depth_zero_means_unknown=True))
    save('CLEANUP_SUMMARY.json',dict(B_N=len(audit),qualified_inside_originalPolyp_N=sum(r['identity_status']=='QUALIFIED_INSIDE_ORIGINAL_MASK' for r in audit),user_approved_BG_N=sum(r['user_approved_BG'] for r in audit),protected_exception_N=sum(r['identity_status'] not in ['QUALIFIED_INSIDE_ORIGINAL_MASK','BACKGROUND_NON_POLYP_NON_RING_USER_APPROVED'] for r in audit),insidePolyp_edge_le2_N=sum(r['insidePolyp_edge_le2'] for r in audit),V2_new_excluded_N=sum(r['V2_new_suppress'] for r in audit),V3_new_excluded_N=sum(r['V3_new_suppress'] for r in audit),B_interior_retained_by_V2_N=sum(r['identity_status']=='QUALIFIED_INSIDE_ORIGINAL_MASK' and r['distance_native_px']>2 for r in audit),V3_ALL_B_COMPLETE=all(r['V3_new_suppress'] for r in audit),per_source=summary,protocol=asset(R/'config/A3_PREREGISTERED.json'),explicit_user_amendment=asset(R/'config/USER_BACKGROUND_OVERRIDE.json')))
    print('A3_CLEANUP', {k:v for k,v in load(R/'CLEANUP_SUMMARY.json').items() if k not in ['per_source','protocol']},flush=True)

if __name__=='__main__':main()
