"""Read-only delivery checks; never optimize, render, or alter predictions."""
from pathlib import Path
import hashlib,json,ast,re
import numpy as np
R=Path(__file__).resolve().parents[1]
def load(p):
    def reject(s):raise ValueError((str(p),s))
    return json.loads(Path(p).read_text(),parse_constant=reject)
def verify(files):
    for f in files:assert hashlib.sha256(Path(f['path']).read_bytes()).hexdigest()==f['sha256'],f['path']
    return len(files)
def main():
    out={}
    for label in ['PRIOR_FREEZE','PREOPT_FREEZE']:
        out[label+'_N']=verify(load(R/'assets_index'/(label+'.json'))['files'])
    out['frozen_prediction_N']=verify(load(R/'metrics/ALL_PREDICTIONS_FREEZE.json')['files'])
    out['local_data_N']=verify(load(R/'assets_index/LOCAL_RESULTS.json')['files'])
    assert load(R/'metrics/PROJECTION_GATE.json')['passed']
    assert load(R/'metrics/FIREWALL.json')['passed']
    starts=[]
    for arm in ['ORIGINAL','SUBPIXEL_TARGET']:
        run=load(R/'metrics'/(arm+'_FINISHED.json'));assert run['finished'] and run['optimizer_nfev']<=500 and run['iterations']<=12
        starts.append(load(R/'metrics'/(arm+'_START.json'))['seed'])
        history=load(R/'metrics'/(arm+'_HISTORY.json'))
        for h in history:
            assert h['physical']['quality']['closed'] and h['physical']['quality']['components']==1
            assert not h['physical']['collision']
            for row in h['per_view']:
                assert row['foreground_denominator']==row['fixed_known_Mask_N']
                assert row['foreground_denominator']+row['background_denominator']==row['known_N']
        fixed=[[(x['view'],x['Mask_N'],x['known_N'],x['unknown_N'])for x in h['per_view']]for h in history]
        assert all(x==fixed[0]for x in fixed)
    assert starts[0]==starts[1]
    final=load(R/'metrics/NATIVE_POSTERIOR.json');assert final['GT_never_used_for_selection']
    assert final['representation']['GT_q']=='DOES_NOT_EXIST'
    assert final['representation']['GT_requires_both_signs']
    assert all(x['EXACT_intersection_volume_mm3']<=1e-8 for x in final['Blender_checks'])
    assert all(x['nonadjacent_intersecting_triangle_pairs_N']==0 for x in load(R/'metrics/SELF_INTERSECTION_AUDIT.json')['rows'])
    for row in load(R/'metrics/STRICT_NORMAL_RAY_VALIDATION.json')['rows']:
        a=np.load(R/'audit_only'/(row['arm']+'_STRICT_NORMAL_RAYS.npz'));valid=a['valid']
        assert row['fixed_N']==len(valid)and row['valid_N']==int(valid.sum())
        assert row['valid_N']+row['missing_N']==row['fixed_N']
        assert not np.any(valid&~a['GT_origin_outside'])
        assert np.isnan(a['error'][~valid]).all()
    gate=load(R/'metrics/GATE_A_ACCEPTANCE.json');assert gate['Gate_A_completed']and not gate['scientific_correct_3D_recovery_certified']and gate['stopped']
    for key in ['Gate_B','Gate_C','Gate_D']:assert gate[key]=='NOT_RUN_HUMAN_HOLD'
    for p in (R/'code').rglob('*.py'):ast.parse(p.read_text(),filename=str(p))
    jsons=[p for p in R.rglob('*.json')if 'runtime'not in p.relative_to(R).parts]
    for p in jsons:load(p)
    out['strict_json_N']=len(jsons)
    for p in R.glob('*.md'):
        if p.name=='00_AUTHORIZED_TASK.md':continue
        for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
            if '://'not in target and not target.startswith('#'):assert (p.parent/target.split('#')[0]).exists(),(p,target)
    images=sorted((R/'figures').glob('Fig*.png'));assert len(images)==4
    for p in images:assert p.stat().st_size<4*1024*1024 and p.read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
    out.update(passed=True,predictions_unchanged=True,Gate_B_C_D_not_run=True,scientific_recovery_not_certified=True)
    (R/'assets_index/DELIVERY_VALIDATION.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
if __name__=='__main__':main()
