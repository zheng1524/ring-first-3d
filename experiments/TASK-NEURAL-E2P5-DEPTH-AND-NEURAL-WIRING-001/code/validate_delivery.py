"""Integrity validation; preserve empirical research failures, no model/audit rerun."""
from common import *
import re

def readrows(name):return list(csv.DictReader((R/'metrics'/name).open()))
def main():
    checks=[]
    def check(name,ok,detail=None):
        checks.append(dict(test=name,pass_=bool(ok),detail=detail))
        if not ok:
            save('metrics/DELIVERY_VALIDATION.json',dict(status='FAIL_INTEGRITY',checks=checks));raise AssertionError((name,detail))
    check('P1 completed before real network',load(R/'provenance/P2_BEFORE_FIRST_OFFICIAL_MODEL.json')['extra']['P1_complete'])
    check('historical worktrees HEAD/status/dirty hashes unchanged',protected_state()==load(R/'provenance/PROTECTED_START.json'))
    check('source official revision unchanged',git(SDF,'rev-parse','HEAD')=='12513009cd20a08b35ddc2c55a7e42da2c7baf43')
    model=load(R/'provenance/P2_BEFORE_FIRST_OFFICIAL_MODEL.json')['extra']['official_network']
    check('official network source unchanged',sha(model['path'])==model['sha256'])
    C={x['id']:x for x in registry()['references']};inputs={}
    for refs in selected().values():
        for ref in refs:
            c=C[ref]
            for a in [c['files']['RGB'],c['files']['Mask'],c['files']['pack'],c['files']['camera_file'],c['E1_actual_native'],c['Ring_CAD']]:
                if a['path'] in inputs:continue
                check('source hash '+ref+' '+Path(a['path']).name,sha(a['path'])==a['sha256'])
                inputs[a['path']]=a['sha256']
    save('provenance/READONLY_INPUT_HASHES.json',dict(files=[dict(path=p,sha256=h) for p,h in inputs.items()],
        source='existing E1/E2 eligibility reused; only actual task inputs hash checked',E1_audit_rerun=False))
    cfg=load(R/'config/PREREGISTERED.json');actual=load(R/'config/ACTUAL_OFFICIAL_NEURAL_CANDIDATES.json')
    check('only2 unique initialization/sampling candidates',len(actual)==4 and len({x['candidate'] for x in actual})==2)
    check('pre-registered16 rays per source and128 finite cells',sum(cfg['per_reference_CPU_quota'])==16 and cfg['sample_cells']==128)
    # Check exact reused renderer code and actual CPU class instrumentation,
    # independent of the main orchestration amended for reproducibility.
    archived=ast.parse((R/'provenance/official_sdf_cpu_adapter_EXECUTED_ATTEMPT001.py.txt').read_text())
    now=ast.parse((R/'code/official_sdf_cpu_adapter.py').read_text())
    for name in ['AuthorizedFiniteCPU','construct_official','model_config','gradient','per_view_terms','run_candidate']:
        before=next(x for x in archived.body if isinstance(x,(ast.ClassDef,ast.FunctionDef))and x.name==name)
        after=next(x for x in now.body if isinstance(x,(ast.ClassDef,ast.FunctionDef))and x.name==name)
        check('executed neural core AST preserved '+name,ast.dump(before,include_attributes=False)==ast.dump(after,include_attributes=False))
    # Recompute small subsets of THIS task's world->target diagnostic equation.
    flows=readrows('PAIRWISE_QUALIFICATION_FLOW.csv');pair=readrows('HERO_PAIRWISE_DEPTH_CONFLICTS.csv')
    check('12 directed pairs and120 region/tier rows',len(flows)==12 and len(pair)==120)
    for f in flows:
        A,B=f['A'],f['B'];ca,pa,ra=source(A);cb,pb,rb=source(B)
        z=np.load(R/'local_results/depth_pairs'/(A+'__'+B+'.npz'));pix=z['source_pixel'][:64];tar=z['target_index'][:64]
        P=unproject(pa['depth_mm'].ravel()[pix],pa['pose'],np.c_[pix%640,pix//640],pa['K']);xy,Z=vis.project_camera(P,pb['K'],pb['pose'])
        expected=Z-pb['depth_mm'].ravel()[tar]
        check('directed axial residual equation '+A+' -> '+B,np.max(abs(expected-z['residual'][:64]))<1e-8)
        check('projected target pixel identity '+A+' -> '+B,np.array_equal(np.floor(xy+.5).astype(int),np.c_[tar%640,tar//640]))
        count=sum(int(f[k]) for k in ['outside_projection_N','target_invalid_or_identity_N','known_Ring_occluded_N','projected_A_self_occluded_N','loose_candidate_N'])
        check('all source candidates accounted '+A+' -> '+B,count==int(f['source_visible_depth_N']) and int(f['conditional_candidate_N'])<=int(f['loose_candidate_N']))
    rr=readrows('RING_DEPTH_RESIDUALS.csv');reliable=[x for x in rr if x['tier']=='RING_INTERIOR_INCIDENCE']
    check('native Ring independently evaluable for all6',len(reliable)==6 and all(int(x['N'])>0 for x in reliable))
    check('Ring selection has no agreement-residual trimming',all('NO Z-residual filter' in x['selection'] for x in reliable))
    for row in reliable:
        z=np.load(R/f'local_results/ring/{row["source"]}.npz');use=z['reliable_Ring'];res=z['native_Ring_Z_mm'][use]-z['CAD_Z_mm'][use]
        check('native Ring residual '+row['source'],len(res)==int(row['N']) and abs(float(np.median(res))-float(row['median_signed']))<1e-10)
    runs=load(R/'metrics/OFFICIAL_SDF_CPU_RUNS.json');gate=load(R/'metrics/OFFICIAL_SDF_CPU_GATE.json')
    check('four real official models670395 parameters',len(runs)==4 and all(x['actual_class']=='model.network.MonoSDFNetwork' and x['parameter_N']==670395 for x in runs))
    check('all parameters immutable; all allocations CPU',all(x['parameters_unchanged'] and x['parameter_SHA_before']==x['parameter_SHA_after'] and not x['GPU_initialized'] and x['optimizer_step_N']==0 and len(x['constructor_CPU_ports'])==2 for x in runs))
    replay=load(R/'provenance/IDENTICAL_NETWORK_DIAGNOSTIC_REPLAY.json')
    check('2 identical diagnostic replays, not new candidates',len(replay['replays'])==2 and replay['initialization_candidate_N']==2 and all(x['parameters_unchanged'] and not x['new_candidate'] for x in replay['replays']))
    init=readrows('NEURAL_INITIALIZATION_AND_HITS.csv');grads=readrows('NEURAL_PER_REFERENCE_GRADIENTS.csv')
    for row in init:
        z=np.load(R/f'local_results/neural/{row["scene"]}_{row["candidate"]}_{row["source"]}.npz')
        check('unhit depth NaN '+row['candidate']+' '+row['source'],np.isnan(z['depth_mm'][~z['render_hit']]).all())
        check('source fixed observed denominator '+row['candidate']+' '+row['source'],int(row['qualified_HERO_N'])==int(row['observed_hit_N'])+int(row['observed_miss_N'])==6)
    pass004=[x for x in grads if x['scene']=='G01_004' and x['candidate']=='A_LEGACY_INIT_CONTROL' and x['source']!='SHARED_FIELD']
    check('004A each source actual three losses has finite nonzero true gradients',len(pass004)==9 and all(x['gradient_finite']=='True' and float(x['gradient_norm'])>0 for x in pass004))
    fail005=[x for x in init if x['scene']=='G01_005'];check('005 both candidates failure preserved',len(fail005)==6 and all(int(x['observed_hit_N'])==0 for x in fail005))
    check('research three-reference Gate remains failed',gate['THREE_REFERENCE_GRADIENT']=='FAIL_OR_INCOMPLETE' and not gate['candidateB_joint_pass'])
    stable=readrows('STABLE_MASK_NUMERICAL_CHECKS.csv');check('corrected stable BCE equivalence nonvacuous',len(stable)==3 and all(x['pass_']=='True' and float(x['BCE_equivalence_abs_error'])<1e-5 for x in stable))
    dg=load(R/'metrics/DEGENERACY_EXPLICIT_CONCLUSION.json');d=dg['selection_control']
    check('partial coverage failure not hidden',d['reduced_coverage']<d['baseline_coverage'] and d['reduced_joint_total']<d['baseline_joint_total'] and dg['not_eliminated_by_current_joint_gate'])
    empty=dg['actual_neural_empty_field'];check('current clamp loses recovery gradient; candidate diagnostic retains it',empty['old_clamped_Mask_offset_gradient']==0 and empty['stable_log_Mask_offset_gradient']>0)
    check('invalid negative BCE attempt retained separately',(R/'provenance/ATTEMPT001_DEGENERACY_TESTS.csv').is_file() and load(R/'provenance/STABLE_MASK_ATTEMPT001_FAILURE.json')['status']=='FAILED_NUMERICAL_CANDIDATE')
    proposal=load(R/'config/GPU_MVP_PROPOSED.json')
    check('MVP is blocked, not authorized',proposal['execute'] is False and proposal['GPU']=='NOT_AUTHORIZED' and 'BLOCKED' in proposal['status'])
    check('D0 current robust weights preserved; duplicate S2 not fabricated',proposal['arms']['E2P5_S0']['conflict_weight']==.25 and 'DUPLICATE' in proposal['arms']['E2P5_S2'] and proposal['budget']['planned_runs']==4)
    check('D2 not silently applied',load(R/'metrics/P1_GATE.json')['D2']=='NOT_RECOMMENDED_FOR_FIRST_MVP')
    bad=[]
    for p in (R/'code').glob('*.py'):
        t=ast.parse(p.read_text())
        for n in ast.walk(t):
            if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ['step','infer','from_pretrained','load_state_dict']:
                bad.append((p.name,n.lineno,n.func.attr))
    check('no optimizer update/Map inference/checkpoint loading calls',not bad,bad)
    text=(R/'TECHNICAL_REPORT.md').read_text();summary=text.split('\n\n')[1]
    check('summary200–350 characters',200<=len(summary)<=350,len(summary))
    check('required fixed audit table present',all(k in text for k in ['目标组数','本算法独立成功','本算法失败','历史测量值回退','失败组及具体原因','最终统计样本','是否使用GT选择算法']))
    images=list((R/'figures').glob('Fig*.png'));check('all4 core figures under2MB each',len(images)==4 and all(p.stat().st_size<2000000 for p in images))
    # Public manifest excludes self and validation to avoid cyclic hashes. Never
    # record an active validation logfile before its writer closes.
    save('metrics/DELIVERY_VALIDATION.json',dict(status='RUNNING'))
    public=[];local=[]
    for p in sorted(R.rglob('*')):
        if not p.is_file() or '__pycache__' in str(p)or p.suffix=='.pyc':continue
        rel=p.relative_to(R).as_posix()
        if rel in ['provenance/DELIVERY_MANIFEST.json','metrics/DELIVERY_VALIDATION.json']:continue
        if rel.startswith('runtime/'):
            if p.suffix=='.log' and p.name!='DELIVERY_VALIDATION.log':local.append(dict(path=rel,bytes=p.stat().st_size,sha256=sha(p)))
            continue
        if rel.startswith('local_results/'):
            if p.suffix=='.npz':local.append(dict(path=rel,bytes=p.stat().st_size,sha256=sha(p)))
            continue
        public.append(dict(path=rel,bytes=p.stat().st_size,sha256=sha(p)))
    save('provenance/DELIVERY_MANIFEST.json',dict(task=R.name,files=public,LOCAL_ONLY=local,
        source_inputs='READONLY_INPUT_HASHES.json',self_exclusions=['manifest','validation JSON','active validation logfile','final git receipt'],
        research_gate='THREE_REFERENCE_GRADIENT failed; integrity does not change it',GPU='NOT_AUTHORIZED'))
    links=[]
    for p in [R/'TECHNICAL_REPORT.md',R/'FAILURE_LEDGER.md',R/'REPRODUCE.md',R/'RESULT_INDEX.md',R/'docs/DEPTH_CORRECTION_DECISION.md',R/'docs/GPU_MVP_PREREGISTRATION.md']:
        for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
            if '://' in target:continue
            links.append(dict(document=str(p.relative_to(R)),target=target,exists=(p.parent/target.split('#')[0]).is_file()))
    for target in re.findall(r'<img src="([^"]+)"',(R/'visualizations/index.html').read_text()):
        links.append(dict(document='visualizations/index.html',target=target,exists=(R/'visualizations'/target).is_file()))
    check('all document/figure links resolve',all(x['exists'] for x in links),dict(N=len(links),broken=[x for x in links if not x['exists']]))
    check('public and closed local file SHA readback',all(sha(R/x['path'])==x['sha256'] for x in public+local))
    check('all local artifacts persistent',not (R/'local_results').is_symlink() and not (R/'runtime').is_symlink())
    save('metrics/DELIVERY_VALIDATION.json',dict(status='PASS_INTEGRITY_WITH_RESEARCH_GATES_FAILED',check_N=len(checks),checks=checks,
        links_N=len(links),public_files_N=len(public),local_files_N=len(local),read_only_inputs_N=len(inputs),old_audits_rerun=False,
        model_forward='CPU_DIAGNOSTIC_ONLY',model_training='NOT_RUN',optimizer_step_N=0,GPU='NOT_AUTHORIZED',
        three_reference_scope='FAIL_OR_INCOMPLETE',formal_GPU_ready=False))
    print('DELIVERY_VALIDATION_COMPLETE',len(checks),'integrity checks;',len(links),'links; failed research Gate preserved')

if __name__=='__main__':main()
