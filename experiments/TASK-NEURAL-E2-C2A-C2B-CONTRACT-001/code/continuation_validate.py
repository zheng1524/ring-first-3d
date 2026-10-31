"""Final continuation integrity checks; previous scientific tests are not rerun."""
from continuation_context import *
import re


def main():
    checks=[]
    def check(name,ok,detail=None):
        checks.append(dict(test=name,pass_=bool(ok),detail=detail))
        if not ok:
            csave('metrics/FINAL_CONTINUATION_VALIDATION.json',dict(status='FAIL',checks=checks));raise AssertionError((name,detail))
    freeze=load(CROOT/'provenance/AUTHORIZATION_AND_FREEZE.json');a=load(CROOT/'metrics/JOINT_WIRING_GATE.json');b=load(CROOT/'metrics/CONTINUATION_INPUT_GATE.json')
    check('new joint wiring72 and input70 passed',a['status']=='PASS_ANALYTIC_CPU_WIRING_ONLY' and a['check_N']==72 and b['status']=='PASS_CPU_INPUT_CONTRACT' and b['check_N']==70)
    check('official neural/sampler/weights remain unexecuted',a['official_neural_forward_N']==a['official_sampler_execution_N']==a['weights_loaded_N']==a['weight_update_N']==0)
    check('old E2 worktree remains frozen5d4bcbb',git(BASE.parents[1],'rev-parse','HEAD')=='5d4bcbbee444d8db9a479ed256417fb7cfd9a83b')
    check('old E1 head remains frozen',git(E1.parents[1],'rev-parse','HEAD')=='af71a6f85328f487b4a319d47e429c3606f5ca33')
    check('all historical HEAD/status/dirty file hashes preserved',protected_state()==freeze['source_protection'])
    for name in ['continuation_context.py','finite_joint_adapter.py','continuation_tests.py','continuation_inputs.py']:
        old=next(x for x in freeze['code'] if Path(x['path']).name==name)
        check('tested new source hash '+name,sha(R/'code'/name)==old['sha256'])
    old_public=load(BASE/'provenance/DELIVERY_MANIFEST.json')['files']
    check('previous E2 public artifacts unchanged',all(sha(BASE/x['path'])==x['sha256'] for x in old_public))
    check('old E2 code remains unchanged in continuation',all(sha(p)==sha(R/'code'/p.name) for p in (BASE/'code').glob('*.py')))
    check('old numerical metrics not overwritten',all(sha(p)==sha(R/'metrics'/p.name) for p in (BASE/'metrics').glob('*') if p.is_file()))
    # Eight targeted API method bindings, not a repetition of E1 source audit.
    api=load(CROOT/'provenance/OFFICIAL_API_BINDING.json')
    for f in api['methods']:
        node,now=official_method(f['path'],f['class_name'],f['method'])
        check('new API binding exact '+f['class_name']+'.'+f['method'],now['file_SHA256']==f['file_SHA256'] and now['AST_SHA256']==f['AST_SHA256'])
    response=[]
    for name in ['ANALYTIC_RESPONSE_ARTIFACTS.json','COMMON_HERO_ARTIFACTS.json']:
        for f in load(CROOT/'provenance'/name):
            check('new local artifact '+Path(f['path']).name,sha(f['path'])==f['sha256']);response.append(f)
    manifests=load(CROOT/'provenance/COMMON_HERO_GEOMETRY_MANIFEST.json')
    total=0
    for m in manifests:
        check('three source ids preserved '+m['scene'],m['view_ids']==selected()[m['scene']] and len(m['view_ids'])==3)
        check('comparison limitations disclosed '+m['scene'],m['SDF_RGB_role']!=m['Map_RGB_role'] and 'not a claim' in m['comparison_status'] and m['strict_holdout_N']==0)
        for f in m['views']:
            ref=f['source'];p=np.load(f['payload']['path']);z=np.load(baseline_asset('local_results/rays/'+ref+'.npz'))
            check('qualified native support exact '+ref,np.array_equal(p['SDF_eligibility'].ravel(),z['depth_weight']>0))
            check('frozen source camera exact '+ref,np.array_equal(p['source_K'],z['K']) and np.array_equal(p['source_c2w_mm'],z['c2w_mm']))
            check('no hidden invented dense depth '+ref,np.all(p['depth_z_m'][~p['SDF_eligibility']]==0))
            total+=int(p['SDF_eligibility'].sum())
    check('matched qualified depth denominator86789',total==86789)
    cats=list(csv.DictReader((CROOT/'metrics/HERO_CONFLICT_CATEGORIES.csv').open()))
    check('visibility conflict categories2759+4',sum(int(x['BEHIND_FIRST_RING_HIT']) for x in cats)==2759 and sum(int(x['RING_FRONT_MARGIN']) for x in cats)==4 and sum(int(x['UNRESOLVED']) for x in cats)==0)
    ev=list(csv.DictReader((CROOT/'metrics/SOURCE_EVIDENCE_DENOMINATORS.csv').open()))
    check('5457 single-view observations preserved',sum(int(x['single_view_no_comparison_N']) for x in ev)==5457 and all(x['single_view_weight_remains_1']=='True' for x in ev))
    check('all evidence bins keep86789 denominator',sum(sum(int(x[k]) for k in ['single_view_no_comparison_N','co_visible_agree_all_N','co_visible_some_conflict_N','co_visible_all_compared_conflict_N']) for x in ev)==86789)
    violations=[]
    for p in [*(R/'code').glob('*continuation*.py'),R/'code/finite_joint_adapter.py']:
        tree=ast.parse(p.read_text())
        for node in ast.walk(tree):
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr in ['cuda','infer','step','from_pretrained','load_state_dict']:
                violations.append((p.name,node.lineno,node.func.attr))
    check('new code contains no model inference GPU optimizer execution',not violations,violations)
    check('GPU remains NOT_GRANTED and not science-ready',load(CROOT/'metrics/GPU_READINESS.json')['GPU']=='NOT_GRANTED' and load(CROOT/'metrics/GPU_READINESS.json')['formal_GPU_ready'] is False)
    check('two new figures under2MB',len(list((CROOT/'figures').glob('*.png')))==2 and all(p.stat().st_size<2000000 for p in (CROOT/'figures').glob('*.png')))
    report=(R/'TECHNICAL_REPORT.md').read_text();summary=report.split('\n\n')[1]
    check('opening Chinese summary length200–350',200<=len(summary)<=350)
    check('new audit table and NaN output explicit','目标组数' in report and '共同成功配对N=0' in report and '0/1新测量' in report)
    check('local artifacts persist on disk',not (R/'local_results').is_symlink() and not (R/'runtime').is_symlink())
    # Manifest self/final validation are excluded to avoid cyclic hashes.
    csave('metrics/FINAL_CONTINUATION_VALIDATION.json',dict(status='RUNNING'))
    public=[];local=[]
    for p in sorted(R.rglob('*')):
        if not p.is_file() or '__pycache__' in str(p) or p.suffix=='.pyc':continue
        rel=p.relative_to(R).as_posix()
        if rel in ['continuation_cpu/provenance/CONTINUATION_MANIFEST.json','continuation_cpu/metrics/FINAL_CONTINUATION_VALIDATION.json']:continue
        if rel.startswith(('runtime/','local_results/')):
            if rel=='runtime/CONTINUATION_VALIDATION.log':continue  # own active writer: hash only after it closes
            if rel.startswith('local_results/continuation_cpu/')or (rel.startswith('runtime/CONTINUATION')and p.suffix=='.log'):
                local.append(dict(path=rel,sha256=sha(p),bytes=p.stat().st_size))
            continue
        public.append(dict(path=rel,sha256=sha(p),bytes=p.stat().st_size))
    csave('provenance/CONTINUATION_MANIFEST.json',dict(task=R.name,base_commit='5d4bcbbee444d8db9a479ed256417fb7cfd9a83b',
        files=public,LOCAL_ONLY=local,previous_E2_local_assets='read-only at '+str(BASE),GPU='NOT_GRANTED',
        self_exclusions=['continuation manifest','final continuation validation','active validation logfile','final git receipt in ignored runtime']))
    links=[]
    for p in [R/'TECHNICAL_REPORT.md',R/'FAILURE_LEDGER.md',R/'RESULT_INDEX.md',R/'REPRODUCE.md',CROOT/'README.md']:
        for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
            if '://' in target:continue
            links.append(dict(document=str(p.relative_to(R)),target=target,exists=(p.parent/target.split('#')[0]).is_file()))
    for target in re.findall(r'<img src="([^"]+)"',(CROOT/'visualizations/index.html').read_text()):
        links.append(dict(document='continuation_cpu/visualizations/index.html',target=target,exists=(CROOT/'visualizations'/target).is_file()))
    check('all report and figure links resolve',all(x['exists'] for x in links),dict(link_N=len(links),broken=[x for x in links if not x['exists']]))
    check('public/local manifest hash readback',all(sha(R/x['path'])==x['sha256'] for x in public+local))
    csave('metrics/FINAL_CONTINUATION_VALIDATION.json',dict(status='PASS_NEW_CPU_ENGINEERING_ONLY',check_N=len(checks),checks=checks,
        new_wiring_check_N=72,new_input_check_N=70,old_scientific_audits_rerun=False,source_protection=True,
        manifest_public_file_N=len(public),manifest_local_file_N=len(local),link_N=len(links),
        official_neural_forward_N=0,official_sampler_execution_N=0,weight_update_N=0,GPU='NOT_GRANTED',formal_GPU_ready=False))
    print('CONTINUATION_FINAL_VALIDATION',len(checks),'checks;',len(links),'links; prior E1/E2 tests not rerun')


if __name__=='__main__':main()
