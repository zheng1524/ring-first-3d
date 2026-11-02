"""A3 contracts. The user-revoked3px proxy is never an acceptance blocker."""
from analyze import *

def main():
    checks=[]
    def ck(name,ok,detail):checks.append(dict(test=name,status='PASS' if ok else 'FAIL',detail=detail))
    original=load(R/'config/BEFORE_RESULTS.json');amend=load(R/'config/AMENDMENT_BEFORE_RESULTS.json');ck('ORIGINAL_PROTOCOL_PRESERVED',sha(R/'config/A3_PREREGISTERED.json')==original['protocol']['sha256'],'original protocol not overwritten; explicit user amendment recorded separately')
    ck('AMENDMENT_FROZEN',sha(R/'config/USER_BACKGROUND_OVERRIDE.json')==amend['amendment']['sha256'],'BG orange removal authorized by user before amended run')
    for a in amend['code']:ck('FROZEN_CODE_'+Path(a['path']).name,sha(a['path'])==a['sha256'],'exact code frozen before amended result generation')
    audit=read_csv(R/'CANDIDATE_DISTANCE_AUDIT.csv');dec=read_csv(R/'CLEANUP_DECISIONS.csv');s=load(R/'CLEANUP_SUMMARY.json');coord=[]
    ck('ALL_1929_B_IDENTITIES',len(audit)==1929 and all(float(r['identity_XYZ_error_mm'])<=1e-8 and r['V1_legal']=='True' for r in audit),'all B original Pixel IDs and worldXYZ traced')
    ck('POLYP2_PLUS_EXPLICIT_BG',all((r['V2_new_suppress']=='True')==((r['original_mask_label']=='1' and float(r['distance_native_px'])<=2) or r['user_approved_BG']=='True') for r in audit),'native threshold2 unchanged; BG label0 is separate authorized rule')
    ck('V3_ALL_B',s['V3_ALL_B_COMPLETE'] and s['V3_new_excluded_N']==1929,'all exact B identities masked after explicit BG authorization')
    ck('RING_IDENTITY_EXCEPTIONS_PROTECTED',all(r['V2_new_suppress']=='False' and r['V3_new_suppress']=='False' for r in audit if r['original_mask_label']=='2' or r['identity_status'] not in ['QUALIFIED_INSIDE_ORIGINAL_MASK','BACKGROUND_NON_POLYP_NON_RING_USER_APPROVED']),'Ring and actual identity/mapping failures not automatically removed')
    ck('ORANGE_INTERIOR_RETAINED',all(r['V2_new_suppress']=='False' for r in audit if r['original_mask_label']=='1' and float(r['distance_native_px'])>2),'all1210 original-Mask interior B points retained in V2')
    ck('A_C_D_UNCHANGED',all(r['V1_valid']==r['V2_valid']==r['V3_valid'] for r in dec if r['A2_category']!='B_DEPTH_LAYER_RETAIN'),'red A remains masked; purple C and green D unchanged')
    # Independent original-mask integer EDT and brute BG-center checks, not a second threshold trial.
    for cid in IDS:
        a=[r for r in audit if r['source']==cid];q=np.array([[float(r['archive_continuous_u']),float(r['archive_continuous_v'])] for r in a]);m=mask_metric(cid);pix=np.floor(q+.5).astype(int);d,_=m['tree'].query(pix[:,::-1]*m['spacing']);edt=m['edt'][pix[:,1],pix[:,0]];err=float(np.max(abs(d-edt)))
        chosen=np.unique(np.linspace(0,len(a)-1,min(8,len(a)),dtype=int));brute=[]
        for k in chosen:
            independent=np.linalg.norm((m['bg']-q[k,::-1])*m['spacing'],axis=1).min();stored=float(a[k]['query_to_nearest_nonPolyp_center_native_px']);brute.append(abs(independent-stored))
        coord.append(dict(source=cid,original_Mask_WH=[640,360],native_WH=[640,352],native_units_per_archive_y_px=352/360,EDT_vs_KD_integer_max_px=err,independent_continuous_brute_max_px=max(brute),mapping_roundtrip_max_native_px=max(float(r['mapping_roundtrip_error_native_px']) for r in a),insidePolyp_primary_le2_N=sum(r['insidePolyp_edge_le2']=='True' for r in a),native_legacy_DT_le2_N=sum(float(r['legacy_native_DT_px'])<=2 for r in a),BG_authorized_N=sum(r['user_approved_BG']=='True' for r in a)))
        ck(cid+'_ORIGINAL_MASK_DISTANCE',err<1e-10 and max(brute)<1e-10,'exact original-mask metric; integer EDT and independent continuous brute checks')
        b=v1(cid)
        for version in VERSIONS:
            z=np.load(R/'local_results/inputs'/version/(cid+'.npz'));mask=z['new_excluded'];depth=z['depth_mm'];valid=z['valid'];back=depth.copy();back.flat[z['suppressed_native_ids']]=z['suppressed_original_depth_mm']
            ck(cid+'_'+version+'_BITWISE_AND_REVERSIBLE',np.array_equal(depth[~mask],b['depth'][~mask]) and np.array_equal(valid[~mask],b['valid'][~mask]) and np.array_equal(back,b['depth']),'only approved B pixels changed; original values recoverable')
            ck(cid+'_'+version+'_HISTORY_RETAINED',not np.any(valid&(b['historical_excluded']|b['A2_excluded'])),'46 original +223 A2 exclusions persist')
    synthetic=np.zeros((7,7),bool);synthetic[1:6,1:6]=True;dist=ndimage.distance_transform_edt(synthetic);ck('BOUNDARY_CENTER_CONVENTION',dist[1,3]==1 and dist[2,3]==2 and dist[3,3]==3,'center-to-nearest NON-Polyp center; no0.5 subtract; two-center rows inclusive')
    anis=ndimage.distance_transform_edt(synthetic,sampling=(352/360,1));ck('ANISOTROPIC_NATIVE_UNITS',abs(anis[2,3]-2*352/360)<1e-12,'original archive vertical spacing converted to native units')
    geo=read_csv(R/'GEOMETRY_VALIDATION.csv');ck('ALL18_GEOMETRY',len(geo)==18 and all(float(r['analytic_XYZ_max_mm'])<=1e-5 and float(r['camera_scale_max_mm'])<=1e-5 and r['out_of_grid_N']=='0' and r['exact_selected_depth']=='True' and r['nonPolyp_depth_nonzero_N']=='0' for r in geo),'same affine,K,c2w,sourceIDs and shared27.959mm domain; actual selected native depths only')
    reg=read_csv(R/'REGION_RETENTION.csv');ck('V2_BODY_INTERIOR_ALL_RETAINED',all(r['lost_N']=='0' for r in reg if r['version']=='V2' and r['region']=='body'),'fixed originalMask>2px interior retained across all six sources')
    ck('OLD3PX_REVOKED_NOT_BLOCKING',primary_protocol()['diagnostics']['historical_3px_gate'].startswith('REVOKED'),'old GateA/A2 files unchanged; no3px acceptance test')
    before=load(R/'config/PROTECTED_START.json');same=protected_state()==before['worktrees'];bad=[a['path'] for a in before['assets'] if sha(a['path'])!=a['sha256']];ck('HISTORY_SOURCE_SHA_PROTECTION',same and not bad,'all earlier branches, raw sources, Mask,K,c2w,CAD, A/A2 outcomes unchanged')
    table('A3_CONTRACT_TESTS.csv',checks);save('MASK_COORDINATE_AUDIT.json',dict(per_source=coord,boundary_definition=primary_protocol()['mask_coordinate_definition'],legacy_counts_are_diagnostic_not_decisions=True))
    save('config/FINAL_PROTECTION_CHECK.json',dict(worktree_N=len(before['worktrees']),worktrees_unchanged=same,old_SHA_check_N=len(before['assets']),all_old_SHA_unchanged=not bad,raw_mutations=0,model_imports=[n for n in sys.modules if n.startswith(('torch','tensorflow','training','graphics'))],GPU=0,NNforward=0,GT_read=False,old_3px_revoked_for_A3_only=True))
    save('GATE_A3_ACCEPTANCE.json',dict(status='A3_ENGINEERING_PASS_WITH_LIMITATIONS' if all(r['status']=='PASS' for r in checks) else 'A3_ENGINEERING_FAIL',execution_complete=True,scientific_improvement='PROXY_REDUCTION_WITH_COVERAGE_COST; physical truth NOT_EVALUABLE',versions=['V1','V2','V3'],orange_N=1929,insidePolyp_edge_le2_N=s['insidePolyp_edge_le2_N'],user_approved_BG_N=s['user_approved_BG_N'],V2_new_excluded_N=s['V2_new_excluded_N'],V3_new_excluded_N=s['V3_new_excluded_N'],V2_interior_B_retained_N=s['B_interior_retained_by_V2_N'],V3_all_B_complete=s['V3_ALL_B_COMPLETE'],old3px_blocker=False,old_Gate_A_A2_failed_results_unchanged=True,physical_valid_surface_loss_certified=False,GateB_recommendation='WORTH_CONTROLLED_V1_V2_INPUT_ABLATION_WITH_LIMITATIONS; V3 aggressive negative control only',GateB_authorized=False,automatic_promotion_to_baseline=False,tests_PASS=sum(r['status']=='PASS' for r in checks),tests_FAIL=sum(r['status']=='FAIL' for r in checks),failure_tests=[r for r in checks if r['status']=='FAIL']))
    print('A3_AUDIT',sum(r['status']=='PASS' for r in checks),'PASS',sum(r['status']=='FAIL' for r in checks),'FAIL',flush=True)

if __name__=='__main__':main()
