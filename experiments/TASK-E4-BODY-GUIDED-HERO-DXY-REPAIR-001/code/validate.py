"""A1 validate-style integrity, exact source ASTs, fairness and failure retention."""
from common import *
def main():
    checks=[]
    def ck(name,p,**extra):checks.append(dict(name=name,passed=bool(p),**extra))
    guard('evaluation')
    for x in load(R/'provenance/INPUT_SHA.json'):ck('input:'+x['path'],sha(x['path'])==x['sha256'])
    for x in load(R/'provenance/DXY_RUNTIME_SOURCE_INDEX.json'):ck('official_dxy_code:'+x['path'],sha(x['path'])==x['sha256'])
    for x in load(R/'provenance/SOLVER_CODE_FREEZE.json')['code']:ck('frozen_solver:'+x['path'],sha(x['path'])==x['sha256'])
    for x in load(R/'provenance/ALL_PREDICTIONS_FROZEN.json')['files']:ck('frozen_prediction:'+x['path'],sha(x['path'])==x['sha256'])
    ck('numerical_contracts',load(R/'metrics/NUMERICAL_CONTRACTS.json')['all_pass'])
    plan=load(R/'config/BODY_FIT_VIEWS.json');selected=[]
    for name,sc in plan.items():
        for arm in ['E1','E2']:
            root=R/'local_results'/name/arm;m=load(root/'SELECTION.json');fits=[load(p) for p in root.glob('START_*.json')];eligible=[r for r in fits if r['eligible']]
            if sc['FIT']:ck(name+arm+':three_starts_retained',len(fits)==3)
            if m['available']:
                selected.append(m);ck(name+arm+':eligible_success_only',m['eligible'] and m['optimizer_success']);ck(name+arm+':minimum_fit_among_eligible',m['objective']==min(r['objective'] for r in eligible))
            else:ck(name+arm+':failure_null',m['p'] is None and not eligible)
        if sc['FIT'] and sc['E1_available']:
            for start in range(3):
                a,b=[load(R/'local_results'/name/arm/f'START_{start}.json') for arm in ['E1','E2']]
                ck(name+str(start)+':same_initial_R0_views_weights',a['initial']==b['initial'] and a['R0']==b['R0'] and a['source_ids']==b['source_ids'] and a['weights']==b['weights'])
                ck(name+str(start)+':same_budget',a['nfev']<=60 and b['nfev']<=60)
    met=load(R/'metrics/ALL_VIEW_EVALUATION.json')
    for r in met:
        if r['available']:ck(r['pool']+r['arm']+r['source']+':fixed_mask_denominator',r['intersection_N']+r['FN']==r['full_mask_N'])
    for rec in load(R/'provenance/CODE_REUSE_FUNCTIONS.json'):
        ck('reused_file:'+rec['function'],sha(rec['file']['path'])==rec['file']['sha256'] and rec['mathematics_modified'] is False)
    text=(R/'code/fitting.py').read_text();ck('no_depth_parts_called','depth_parts(' not in text);ck('no_class_conditioned_model',not any(x in text for x in ["'Ip'","'Is'","'IIa'",'fitEllipse','distanceTransform']))
    ck('4_physical_groups',len({s['group'] for s in load(R/'config/SOURCE_BINDING.json')})==4)
    ck('DXY_75_sources',len(load(R/'provenance/DXY_GENERATED.json'))==75)
    jj=load(R/'metrics/JACOBIAN_IDENTIFIABILITY.json')
    ck('single_view_conic_at_most_five',all(v['conic_only_rank']<=5 for j in jj for v in j['single_view_at_same_solution']))
    ck('all_multiview_conic_diagnostics_present',len(jj)==12 and all('conic_only_singular_values' in j for j in jj))
    save('metrics/VALIDATION.json',dict(all_pass=all(x['passed'] for x in checks),checks=checks,GT_read=False,history_prediction_fallback=0))
    save('provenance/ENVIRONMENT.json',dict(Python=sys.version,numpy=np.__version__,scipy=__import__('scipy').__version__,opencv=cv2.__version__,open3d=o3d.__version__,trimesh=trimesh.__version__,DXY_Python='/home/liu/new-polyp-dxy/.venv/bin/python',CPU_only=True))
    print('VALIDATED',sum(x['passed'] for x in checks),'/',len(checks),flush=True)
    assert all(x['passed'] for x in checks)
if __name__=='__main__':main()
