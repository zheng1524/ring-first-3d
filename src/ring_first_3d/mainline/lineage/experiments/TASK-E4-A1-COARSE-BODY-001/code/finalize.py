"""Final evidence index and acceptance state, preserving all earlier outcomes."""
from common import *
import re
def main():
    primary=load(R/'metrics/S2_PRIMARY.json');root=load(R/'metrics/ROOT_BRACKETING_FAILURE.json');j=load(R/'metrics/S4_JACOBIANS.json');v=load(R/'metrics/VALIDATION.json');q=[]
    for m in primary:
        x=next(x for x in j if(x['scene'],x['arm'])==(m['scene'],m['arm']));reasons=list(m['numerical_failures'])
        if(m['scene'],m['arm'])==(root['scene'],root['arm']):reasons.append('ROOT_BRACKETING_CONTRACT_FAIL')
        if x['status']!='LOCALLY_FULL_RANK_CONDITIONAL':reasons.append(x['status'])
        q.append(dict(scene=m['scene'],arm=m['arm'],start=m['start'],A_objective_selection_unchanged=True,postfit_model_contract_failures=reasons,numerically_eligible_on_fixed_tests=not reasons,strict_independent_qualified_real_case=False,G1='NOT_PASSED'))
    save('metrics/FINAL_ACCEPTANCE.json',dict(G0='AUDIT_COMPLETE_FORMAL_QUALIFICATION_INCOMPLETE',G1='NOT_PASSED',independent_non_degenerate_qualified_cases=0,formal_Is='NOT_EVALUABLE',S1_control_contracts_pass=True,source_freeze_export_integrity_checks_pass=v['all_pass'],source_freeze_export_integrity_checks_N=len(v['engineering_checks']),real_root_completeness_contract_all_pass=False,root_failure=root,models=q,A2_executions=0,B1_B2_executions=0,scientific_gate_override=False,stop='WAIT_FOR_RESEARCHER_PM_REVIEW'))
    # Attach final contract status to the all-start table without overwriting any
    # original objective, preliminary projection gate, prediction or model.
    with (R/'04_ABLATION_METRICS.csv').open()as f:rows=list(csv.DictReader(f))
    for row in rows:
        z=next((x for x in q if(x['scene'],x['arm'],str(x['start']))==(row['scene'],row['arm'],row.get('start',''))),None)
        row['final_primary_contract_status']=';'.join(z['postfit_model_contract_failures'])or'NO_FAILURE_DETECTED_ON_FIXED_TESTS_CONDITIONAL'if z else'NON_PRIMARY_OR_NOT_EVALUABLE'
        row['strict_G1_pass']=False
    table('04_ABLATION_METRICS.csv',rows)
    dependencies=[E1/'provenance/INPUT_ELIGIBILITY.json',N0/'code/common.py',OLD/'ring_first_v1/scripts/common.py',REPO/'visualization/real_p0_renderer.py',REPO/'visualization/pointcloud_audit_renderer.py',DXY/'v2.py']
    save('provenance/REUSED_IMPLEMENTATION_AND_METADATA.json',dict(recording_stage='POST_RUN_ADDITIONAL_REUSE_MANIFEST',files=[asset(p)for p in dependencies],not_retrospective_preoptimization_freeze=True))
    text=''
    for name in ['fit','jacobian','stability','audit','visualize','validation','refinement']:
        p=R/'runtime'/(name+'.log')
        if p.exists():text+='\n### '+name+'\n'+p.read_text()
    (R/'metrics/EXECUTION_TRACE.txt').write_text(text)
    code=list((R/'code').glob('*.py'));small=[p for d in ['metrics','config','provenance']for p in(R/d).glob('*')if p.is_file()and p.name!='FINAL_ARTIFACT_INDEX.json'];local=[p for p in(R/'local_results').rglob('*')if p.is_file()]
    save('provenance/FINAL_ARTIFACT_INDEX.json',dict(code=[asset(p)for p in sorted(code)],local_results=[asset(p)for p in sorted(local)],core_figures=[asset(p)for p in sorted((R/'figures').glob('Fig*.png'))],small_results=[asset(p)for p in sorted(small)],raw_assets_copied=False))
    links=[]
    for p in R.glob('*.md'):
        if p.name in ['TASK.md','RA_TASK_REFERENCE.md']:continue
        for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
            if target.startswith(('http:','https:','#')):continue
            clean_target=target.split('#')[0];links.append(dict(file=p.name,target=target,exists=(p.parent/clean_target).exists()))
    save('metrics/REPORT_LINK_CHECKS.json',dict(all_pass=all(x['exists']for x in links),checks=links))
    assert all(x['exists']for x in links),'Broken report link'
    print('FINALIZED',len(q),'models; G1 NOT_PASSED; real root contract FAIL; A2 executions 0')
if __name__=='__main__':main()
