"""One additional5px variant explicitly requested by the researcher.
The original V1/V2/V3 outputs remain byte-for-byte unchanged.
"""
from analyze import *

def main():
    assert not (R/'V4_CLEANUP_DECISIONS.csv').exists(),'ONE_AUTHORIZED_V4_PASS_ONLY'
    before_files=[asset(p) for p in sorted(R.glob('*.csv'))]+[asset(R/'THREE_VERSION_COMPARISON.json'),asset(R/'DERIVED_INPUT_MANIFEST.json')]
    before_arrays=[a['file'] for a in load(R/'DERIVED_INPUT_MANIFEST.json')['sources']]
    save('config/USER_V4_AUTHORIZATION.json',dict(user_instruction='人工观察V2和V3还存在一些点没有清除干净，考虑将清除范围扩大至5px进行尝试，记为V4',date_Asia_Shanghai='2026-11-03',boundary_native_px=5.,candidate_pool='same frozen1929 B candidates; no new candidates or C/D changes',BG_rule='keep explicit61 BG suppression authorization',V1_V2_V3='unchanged; main V2 remains2px',relation='V2_suppressed subset V4_suppressed subset V3_suppressed; cannot remove V3 residual non-B points',parameter_search=False,reason='new human-requested ablation, not an autonomous threshold sweep',GPU=False,NNforward=False))
    save('config/V4_BEFORE_RESULTS.json',dict(protocol=asset(R/'config/USER_V4_AUTHORIZATION.json'),code=[asset(p) for p in sorted((R/'code').glob('*.py'))],protected_three_version_tables=before_files,protected_three_version_arrays=before_arrays,utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
    aa=read_csv(R/'CANDIDATE_DISTANCE_AUDIT.csv');dec=[];lineage=[]
    for cid in IDS:
        b=v1(cid);mask=np.zeros(b['valid'].shape,bool)
        for a in aa:
            if a['source']!=cid:continue
            remove=(a['original_mask_label']=='1' and a['identity_status']=='QUALIFIED_INSIDE_ORIGINAL_MASK' and float(a['distance_native_px'])<=5) or a['user_approved_BG']=='True'
            if remove:mask.flat[int(a['native_id'])]=True
            dec.append(dict(candidate_id=a['candidate_id'],source=cid,native_id=int(a['native_id']),original_mask_label=int(a['original_mask_label']),distance_native_px=float(a['distance_native_px']),V2_new_suppress=a['V2_new_suppress']=='True',V3_new_suppress=a['V3_new_suppress']=='True',V4_new_suppress=remove,user_approved_BG=a['user_approved_BG']=='True',fixed_boundary_native_px=5.))
        v2=np.load(R/'local_results/inputs/V2'/(cid+'.npz'))['new_excluded'];v3=np.load(R/'local_results/inputs/V3'/(cid+'.npz'))['new_excluded'];assert np.all(~v2|mask) and np.all(~mask|v3)
        depth=b['depth'].copy();valid=b['valid'].copy();values=depth[mask].copy();depth[mask]=0;valid[mask]=False;back=depth.copy();back[mask]=values;assert np.array_equal(back,b['depth'])
        out=R/'local_results/inputs/V4';out.mkdir(parents=True,exist_ok=True);np.savez_compressed(out/(cid+'.npz'),depth_mm=depth,valid=valid,new_excluded=mask,suppressed_native_ids=np.flatnonzero(mask),suppressed_original_depth_mm=values,historical_excluded=b['historical_excluded'],A2_excluded=b['A2_excluded'],original_native_id=np.arange(depth.size).reshape(depth.shape))
        lineage.append(dict(source=cid,version='V4',file=asset(out/(cid+'.npz')),V1_N=int(b['valid'].sum()),V4_N=int(valid.sum()),new_suppressed_N=int(mask.sum()),exact_same_B_pool=True,reversible=True))
    table('V4_CLEANUP_DECISIONS.csv',dec);save('V4_DERIVED_INPUT_MANIFEST.json',dict(sources=lineage,authorization=asset(R/'config/USER_V4_AUTHORIZATION.json'),original_ids_unchanged=True))
    # Exact existing analysis main, restricted to V4 and a fresh result namespace.
    target=R/'v4_validation';assert not (target/'THREE_VERSION_COMPARISON.json').exists()
    for d in ['local_results/crops','config']:(target/d).mkdir(parents=True,exist_ok=True)
    ns=dict(globals());ns.update(R=target,VERSIONS=['V4'],save=lambda p,data:save(target/p,data),table=lambda p,rows:table(target/p,rows));extract(R/'code/analyze.py',['main'],ns);ns['main']()
    new=load(target/'THREE_VERSION_COMPARISON.json')['versions'][0];old=load(R/'THREE_VERSION_COMPARISON.json');save('FOUR_VERSION_COMPARISON.json',dict(**old,versions=old['versions']+[new],V4_authorization=asset(R/'config/USER_V4_AUTHORIZATION.json'),visual_order=['V1','V2','V4','V3'],V4_scope='same orange pool only; remaining V3 points are outside that pool'))
    for name in ['SOURCE_VERSION_METRICS','GEOMETRY_VALIDATION','REGION_RETENTION','COMPONENT_RETENTION','NEW_GAP_STATISTICS','FIXED_DENOMINATOR_DEPTH_JUMPS','FIXED_DEPTH_CASES']:
        table('FOUR_VERSION_'+name+'.csv',read_csv(R/(name+'.csv'))+read_csv(target/(name+'.csv')))
    assert all(sha(a['path'])==a['sha256'] for a in before_files+before_arrays),'EARLIER3_VARIANTS_CHANGED'
    save('config/V4_PREVIOUS3_PROTECTION.json',dict(tables_and_arrays_unchanged=True,checks_N=len(before_files+before_arrays),V1_V2_V3_inputs_not_rerun=True,original_analyze_main=asset(R/'code/analyze.py'),exact_AST_execution=True))
    print('A3_V4',sum(r['V4_new_suppress'] for r in dec),'suppressed;',new['retained_N'],'retained; far proxy',new['retained_raw_far_gt1mm_N'],'L diagnostic',new['diagnostic_min_enclosing_L_mm'],flush=True)

if __name__=='__main__':main()
