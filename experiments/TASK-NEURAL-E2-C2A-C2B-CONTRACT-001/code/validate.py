"""Independent E2 artifact/integrity checks; reuses E1 evidence, no audit rerun."""
from context import *

def main():
    freeze('DELIVERY_BEFORE_VALIDATION.json')
    checks=[]
    def check(name,ok,detail=None):
        checks.append(dict(test=name,pass_=bool(ok),detail=detail))
        if not ok:save('metrics/FINAL_VALIDATION.json',dict(status='FAIL',checks=checks));raise AssertionError((name,detail))
    a=load(R/'metrics/C2A_GATE.json');b=load(R/'metrics/C2B_DATA_GATE.json');m=load(R/'metrics/C2B_MAP_GATE.json')
    check('C2a precedes C2b',a['mandatory_CPU_tests_passed']and b['CPU_contract_pass']and m['CPU_contract_pass'])
    check('GPU/model/weight update remain unauthorized and zero',a['GPU']=='NOT_GRANTED'and b['official_model_forward_N']==0 and m['official_model_forward_N']==0 and b['weight_update_N']==0)
    # C2b extended only the depth reducer. All C2a-tested adapter function ASTs
    # must remain exactly equal to the source already committed in stage1.
    frozen=load(R/'provenance/C2A_BEFORE_TEST.json')['code']
    for name in ['context.py','opacity.py','test_c2a.py']:
        f=next(f for f in frozen if Path(f['path']).name==name)
        check('final RA-aligned C2a tested source '+name,sha(R/'code'/name)==f['sha256'])
    check('E1 historical branch unchanged',git(E1.parents[1],'rev-parse','HEAD')=='af71a6f85328f487b4a319d47e429c3606f5ca33')
    C={x['id']:x for x in registry()['references']};inputs={}
    def expect(path,h):
        p=str(path);inputs[p]=h
        check('read-only source '+Path(p).name,Path(p).is_file()and sha(p)==h)
    for r in load(R/'provenance/E1_REUSED_ASSETS.json'):expect(r['path'],r['sha256'])
    for r in load(R/'provenance/C2A_REAL_INPUTS_FROZEN.json'):expect(r['path'],r['sha256'])
    e1cache={str(E1/f['path']):f['sha256']for f in load(E1/'provenance/DELIVERY_MANIFEST.json')['files']}
    dag={n['id']:n for n in load(E1/'provenance/E1_SOURCE_DAG.json')['nodes']}
    f3={x['scene']:x for x in load(E1/'provenance/F3_SOURCE_AUDIT.json')}
    conversions=list(csv.DictReader((R/'metrics/MAP_DERIVED_DEPTH_CONVERSIONS.csv').open()))
    audited=set()
    for r in conversions:
        parents=json.loads(r['parents']);family=r['family']
        for parent in parents:
            key=(parent,family)
            if key in audited:continue
            audited.add(key);c=C[parent]
            for role in ['source_points','mesh','RGB','pack']:
                info=c['files'][role]
                if info['path']not in inputs:expect(info['path'],info['sha256'])
            if family in ['Cleaned','F1']:
                f=c['cleaned_flags']
                if f['path']not in inputs:expect(f['path'],f['sha256'])
            if family=='F2':
                f=dag['F2:'+parent]
                if f['path']not in inputs:expect(f['path'],f['sha256'])
        if family=='F3':
            for f in [f3[r['scene']],f3[r['scene']]['scene_faces']]:
                if f['path']not in inputs:expect(f['path'],f['sha256'])
        if r['E1_projection_reused']=='True':
            f=json.loads(r['projection_input']);expect(f['path'],e1cache[f['path']])
        artifact=json.loads(r['input_depth']);z=np.load(artifact['path']);ref=r['source_view'];src=np.load(C[ref]['pack']);rays=np.load(R/f'local_results/rays/{ref}.npz')
        check('Map condition frozen camera '+ref+' '+family,np.array_equal(z['source_K'],src['K'])and np.array_equal(z['source_c2w_mm'],src['pose']))
        valid=z['validity'].ravel();t=z['depth_z_m'].ravel()*1000*rays['ray_length_factor']
        check('Map conditions respect finite visible prefix '+ref+' '+family,np.all(t[valid]>=rays['ROI_start_t_mm'][valid]-.002)and np.all(t[valid]<=rays['ROI_end_t_mm'][valid]+.002)and np.all(z['depth_z_m'].ravel()[~valid]==0))
    for scene,refs in selected().items():
        pre=load(R/f'provenance/{scene}_BEFORE_ANALYTIC_PROBE.json')
        check('three-view weights frozen before probe '+scene,pre['no_prediction_or_GT_used']and len(pre['reliability'])==3)
        for f in pre['reliability']:check('frozen source reliability artifact '+Path(f['path']).name,sha(f['path'])==f['sha256'])
        for ref in refs:
            z=np.load(R/f'local_results/rays/{ref}.npz');p=np.load(C[ref]['pack'])
            check('source native depth never replaced '+ref,np.array_equal(z['native_axial_Z_mm'],p['depth_mm'].ravel(),equal_nan=True))
            check('hidden/unknown depth weights zero '+ref,np.all(z['depth_weight'][z['ray_class']!=0]==0))
            check('HERO depth only in P_INTERIOR '+ref,np.all(z['depth_weight'][z['sampling_class']!=0]==0))
            check('positive Mask not overridden by conflicting HERO '+ref,np.all(z['mask_weight'][z['HERO_visibility_conflict']]>0)and np.all(z['depth_weight'][z['HERO_visibility_conflict']]==0))
            packet=np.load(R/f'local_results/{ref}_batch.npz')
            check('render misses are explicit NaN rather than zero depth '+ref,np.all(np.isnan(packet['analytic_depth_mm'][~packet['render_hit']])))
    configs=load(R/'provenance/MAP_M0_M4_DATA_MANIFEST.json')
    check('RA M0-M4 profiles and bounded raw diagnostics',len(configs)==16 and sum(x['primary']for x in configs)==14 and all(x['real_view_N']==3 and x['legal_input']for x in configs))
    for cfg in configs:
        if cfg['mode']=='M3':
            for v in cfg['views']:
                cad=v['CAD_condition'];z=np.load(cad['source_condition']['path']);p=np.load(C[v['id']]['pack'])
                check('CAD-conditioned Ring never replaces Polyp '+v['id'],cad['qualified_CAD_pixel_N']>0 and not z['CAD_condition_mask'][p['labels']==1].any())
    evals=load(R/'provenance/EVALUATION_IDENTITIES_FROZEN.json')
    check('strict holdout not invented',evals['strict_holdout_N']==0 and all(not t['strict_holdout']for t in evals['targets']))
    check('no cross-video camera/geometry ancestry in manifests',all(all(C[x]['scene_id']==c['scene']for x in c['geometry_parent_refs'])for c in configs))
    # Inspect only own new entrypoints: no neural constructors, optimizer steps
    # or infer calls are allowed in this engineering task.
    forbidden=[]
    for p in (R/'code').glob('*.py'):
        for n in ast.walk(ast.parse(p.read_text())):
            if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr in ['infer','step','from_pretrained','cuda']:
                forbidden.append((p.name,n.lineno,n.func.attr))
    check('own entrypoints contain no model/optimizer/CUDA execution',not forbidden,forbidden)
    for p in ['/home/liu/private_gt/E2_probe.blend','/home/liu/model_probe.safetensors']:
        try:sys.audit('open',p,'r',0);denied=False
        except PermissionError:denied=True
        check('protected input denied '+Path(p).name,denied)
    end=protected_state();save('provenance/PROTECTED_END.json',end)
    check('historical HEAD/status/modified files unchanged',end==load(R/'provenance/PROTECTED_START.json'))
    save('provenance/E2_READONLY_INPUTS_AND_SHAS.json',dict(files=[dict(path=p,sha256=h)for p,h in sorted(inputs.items())],N=len(inputs),all_verified=True,E1_audit_rerun=False))
    check('four core figures exist',len(list((R/'figures').glob('Fig*.png')))==4)
    ready=load(R/'metrics/GPU_READINESS.json');check('formal GPU science remains gated',not ready['formal_GPU_scientific_experiment_ready']and ready['GPU_authorization']=='NOT_GRANTED')
    save('metrics/FINAL_VALIDATION.json',dict(status='PASS_CPU_ENGINEERING_ONLY',check_N=len(checks),checks=checks,
        stage_CPU_checks=dict(C2a=a['synthetic_check_N']+a['real_link_check_N'],C2b_data=b['check_N'],C2b_Map=m['check_N']),source_input_SHA_N=len(inputs),
        model_forward_N=0,weight_update_N=0,GPU='NOT_GRANTED',formal_GPU_ready=False))
    print('E2_VALIDATION_COMPLETE',len(checks),'assertions;',len(inputs),'frozen inputs; E1 audit not rerun',flush=True)

if __name__=='__main__':main()
