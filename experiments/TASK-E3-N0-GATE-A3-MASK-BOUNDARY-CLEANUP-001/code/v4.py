"""Formal V4 = unchanged V3 minus exactly260 user-approved unreviewed proxies.
The withdrawn5px diagnostic is preserved separately and cannot define V4.
"""
from analyze import *

def freeze_targets():
    assert not (R/'config/V4_260_PREREGISTERED.json').exists(),'DO_NOT_REFREEZE_V4'
    reviewed={(r['source'],int(r['native_id'])):r['category'] for r in read_csv(A2/'PROJECTIVE_CLEANUP_DECISIONS.csv')};targets=[]
    for cid in IDS:
        s=cohort(cid,'V3');dist=raw_distances(cid,s['native_id'])
        for k,i in enumerate(s['native_id']):
            if dist[k]>1. and (cid,int(i)) not in reviewed:
                u,v=s['native_uv'][k];X=s['X'][k];targets.append(dict(candidate_id=f'V4U_{len(targets)+1:04d}',source=cid,native_id=int(i),native_u=int(u),native_v=int(v),X_mm=float(X[0]),Y_mm=float(X[1]),Z_mm=float(X[2]),depth_mm=float(s['depth'][v,u]),own_original_Raw_distance_mm=float(dist[k]),A2_category='NOT_IN_A2_REVIEW_POOL',action='USER_APPROVED_SUPPRESS_FROM_V3',physical_error_truth=False))
    assert len(targets)==260,('TARGET_IDENTITY_CHANGED',len(targets))
    table('V4_260_CANDIDATES.csv',targets)
    prior=[asset(p) for p in sorted(R.glob('*.csv')) if not p.name.startswith('V4_')]+[asset(R/'THREE_VERSION_COMPARISON.json'),asset(R/'DERIVED_INPUT_MANIFEST.json')]
    arrays=[a['file'] for a in load(R/'DERIVED_INPUT_MANIFEST.json')['sources']]
    save('config/V4_260_PREREGISTERED.json',dict(user_instruction='清除260个异常代理作为V4 。清理后提交报告',date_Asia_Shanghai='2026-11-03',definition='V3 minus exact260 existing V3-valid native IDs with own-original-Raw distance>1mm and absent from A2 review pool',targets=asset(R/'V4_260_CANDIDATES.csv'),target_N=260,
        V1_V2_V3='unchanged',C_D='all original A2 C/D remain untouched',old_5px='SUPERSEDED_NOT_FORMAL_V4',new_threshold_search=False,new_candidate_pool_search=False,
        geometry='same original Mask,K,c2w,CAD and fixed V1 common27.959mm model domain; original Raw distance is an authorized diagnostic proxy, not GT',
        audit_only_multiview='exact A2 observer projection loop on V3 observers; no new qualification and no result-driven target changes; conflicts/support reported, removal follows explicit user instruction',
        expected_denominators=dict(original=106144,pre_A2=106098,V1=105875,V2=105156,V3=103946,V4=103686),
        reversible=True,GPU=False,NNforward=False,TSDF=False,GT=False))
    save('config/V4_260_BEFORE_RESULTS.json',dict(protocol=asset(R/'config/V4_260_PREREGISTERED.json'),targets=asset(R/'V4_260_CANDIDATES.csv'),code=[asset(p) for p in sorted((R/'code').glob('*.py'))],protected_three_version_tables=prior,protected_three_version_arrays=arrays,utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
    return targets

def multiview_audit(targets):
    # Reuse the exact vectorized observer loop; do not execute its deletion reducer.
    path=A2/'code/cleanup.py';tree=ast.parse(path.read_text());main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main');loop=next(n for n in main.body if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='observer')
    ns=dict(globals());ns.update(cand=targets,p=load(A2/'config/A2_PREREGISTERED.json')['projection'],evidence=[],by={r['candidate_id']:[] for r in targets},baseline=lambda cid:cohort(cid,'V3'),blocks={r['source_id']:r['view_block'] for r in read_csv(D0/'VIEW_COVERAGE_SELECTION.csv')},qual={r['camera']:r['new_status'] for r in read_csv(REPO/'experiments/TASK-CAMERA-GATE-G01-004-PILOT-001/CAMERA_QUALIFICATION.csv')})
    exec(compile(ast.Module(body=[loop],type_ignores=[]),str(path),'exec'),ns)
    table('V4_260_MULTIVIEW_EVIDENCE.csv',ns['evidence']);summary=[]
    for row in targets:
        ee=ns['by'][row['candidate_id']];summary.append(dict(candidate_id=row['candidate_id'],source=row['source'],native_id=row['native_id'],near_support_observer_N=sum(e['near_support_veto'] for e in ee),depth_layer_observer_N=sum(e['depth_layer_veto'] for e in ee),CAD_occluded_observer_N=sum(e['CAD_occluded'] for e in ee),opposing_distinct_blocks=len({e['observer_block'] for e in ee if e['negative_vote']}),removal_basis='EXPLICIT_USER_TARGETED260_NOT_AUTOMATIC_CROSSVIEW_CERTIFICATION'))
    table('V4_260_MULTIVIEW_SUMMARY.csv',summary)
    save('config/V4_MULTIVIEW_REUSE.json',dict(source=asset(path),executed='exact main observer for-loop only; reducer not executed',loop_AST_SHA256=hashlib.sha256(ast.dump(loop,include_attributes=False).encode()).hexdigest(),rows=len(ns['evidence']),targets_with_near_support=sum(r['near_support_observer_N']>0 for r in summary),targets_with_layer_competition=sum(r['depth_layer_observer_N']>0 for r in summary),physical_truth=False))

def finish():
    target=R/'v4_validation';new=load(target/'THREE_VERSION_COMPARISON.json')['versions'][0];old=load(R/'THREE_VERSION_COMPARISON.json')
    save('FOUR_VERSION_COMPARISON.json',dict(old,versions=old['versions']+[new],V4_authorization=asset(R/'config/V4_260_PREREGISTERED.json'),visual_order=['V1','V2','V3','V4'],V4_scope='V3 plus exact260 user-approved previously unreviewed proxies; original C/D protected',formal_V4_is_not_5px=True))
    for name in ['SOURCE_VERSION_METRICS','GEOMETRY_VALIDATION','REGION_RETENTION','COMPONENT_RETENTION','NEW_GAP_STATISTICS','FIXED_DENOMINATOR_DEPTH_JUMPS','FIXED_DEPTH_CASES']:
        table('FOUR_VERSION_'+name+'.csv',read_csv(R/(name+'.csv'))+read_csv(target/(name+'.csv')))
    before=load(R/'config/V4_260_BEFORE_RESULTS.json');assert all(sha(a['path'])==a['sha256'] for a in before['protected_three_version_tables']+before['protected_three_version_arrays'])
    # Trace remaining proxies without treating raw/native discrepancy as physical GT.
    cls={(r['source'],int(r['native_id'])):r['category'] for r in read_csv(A2/'PROJECTIVE_CLEANUP_DECISIONS.csv')};remaining=[]
    for cid in IDS:
        s=cohort(cid,'V4');d=raw_distances(cid,s['native_id'])
        for k in np.flatnonzero(d>1):
            i=int(s['native_id'][k]);remaining.append(dict(source=cid,native_id=i,native_u=i%640,native_v=i//640,own_original_Raw_distance_mm=float(d[k]),A2_category=cls.get((cid,i),'NOT_IN_A2_REVIEW_POOL'),retained=True,physical_error_truth=False))
    table('V4_REMAINING_ANOMALY_PROXIES.csv',remaining);counts={k:sum(r['A2_category']==k for r in remaining) for k in sorted({r['A2_category'] for r in remaining})}
    save('config/V4_PREVIOUS3_PROTECTION.json',dict(tables_and_arrays_unchanged=True,checks_N=len(before['protected_three_version_tables'])+len(before['protected_three_version_arrays']),V1_V2_V3_inputs_not_rerun=True,original_analyze_main=asset(R/'code/analyze.py'),exact_AST_execution=True,remaining_raw_proxy_N=len(remaining),remaining_classes=counts))
    print('FORMAL_V4',new['retained_N'],'retained; incremental_from_V3=260; remaining proxy',counts,flush=True)

def main():
    assert not (R/'V4_DERIVED_INPUT_MANIFEST.json').exists(),'FORMAL_V4_ONCE_ONLY'
    targets=freeze_targets();multiview_audit(targets);lineage=[]
    for cid in IDS:
        base=v1(cid);v3=cohort(cid,'V3');mask=np.zeros(base['valid'].shape,bool);ids=np.array([r['native_id'] for r in targets if r['source']==cid],np.int64);mask.flat[ids]=True;assert np.all(v3['valid'][mask])
        depth=v3['depth'].copy();valid=v3['valid'].copy();values=depth[mask].copy();depth[mask]=0;valid[mask]=False
        prior=np.load(R/'local_results/inputs/V3'/(cid+'.npz'))['new_excluded'];all_new=prior|mask;back=depth.copy();back[mask]=values;assert np.array_equal(back,v3['depth'])
        out=R/'local_results/inputs/V4';out.mkdir(parents=True,exist_ok=True);np.savez_compressed(out/(cid+'.npz'),depth_mm=depth,valid=valid,new_excluded=all_new,V4_from_V3_excluded=mask,inherited_V3_excluded=prior,suppressed_native_ids=np.flatnonzero(all_new),suppressed_original_depth_mm=base['depth'][all_new],incremental_native_ids=ids,incremental_original_depth_mm=values,historical_excluded=base['historical_excluded'],A2_excluded=base['A2_excluded'],original_native_id=np.arange(depth.size).reshape(depth.shape))
        lineage.append(dict(source=cid,version='V4',file=asset(out/(cid+'.npz')),V1_N=int(base['valid'].sum()),V3_N=int(v3['valid'].sum()),V4_N=int(valid.sum()),incremental_from_V3_N=int(mask.sum()),cumulative_from_V1_N=int(all_new.sum()),reversible=True))
    table('V4_CLEANUP_DECISIONS.csv',targets);save('V4_DERIVED_INPUT_MANIFEST.json',dict(sources=lineage,authorization=asset(R/'config/V4_260_PREREGISTERED.json'),incremental_target_N=260,original_ids_unchanged=True,formal_V4_is_not_5px=True))
    target=R/'v4_validation'
    for d in ['local_results/crops','config']:(target/d).mkdir(parents=True,exist_ok=True)
    ns=dict(globals());ns.update(R=target,VERSIONS=['V4'],save=lambda p,data:save(target/p,data),table=lambda p,rows:table(target/p,rows));extract(R/'code/analyze.py',['main'],ns);ns['main']();finish()

if __name__=='__main__':main()
