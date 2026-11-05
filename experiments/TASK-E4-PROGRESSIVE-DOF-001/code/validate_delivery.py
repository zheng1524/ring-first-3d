"""Validate identities, phase inheritance and frozen evidence without refitting."""
from pathlib import Path
import json,hashlib,ast,re
import numpy as np
R=Path(__file__).resolve().parents[1]
def load(p):
    def reject(x):raise ValueError((str(p),x))
    return json.loads(Path(p).read_text(),parse_constant=reject)
def verify(records):
    for x in records:assert hashlib.sha256(Path(x['path']).read_bytes()).hexdigest()==x['sha256'],x['path']
    return len(records)
def main():
    out={}
    for name in ['PARENT_PROTECTION','PREOPT_FREEZE','S2_DYNAMIC_FREEZE']:out[name+'_N']=verify(load(R/'assets_index'/(name+'.json'))['files'])
    f=load(R/'metrics/ALL_OPTIMIZED_PREDICTIONS_FREEZE.json');out['prediction_files_N']=verify(f['files']);verify(f['configs']);assert f['before_first_native_GT_read']and not f['GT_selection']
    out['local_assets_N']=verify(load(R/'assets_index/LOCAL_RESULTS.json')['files'])
    ref=np.load(R/'inputs/BASE_SOURCE_MESH.npz');zero=np.load(R/'local_results/P0/MODEL.npz');start=np.load(R/'local_results/S1/START/MODEL.npz');a=np.load(R/'local_results/S1/FINAL/MODEL.npz');b=np.load(R/'local_results/S2/START/MODEL.npz')
    for key in ['V','F']:assert np.array_equal(ref[key],zero[key])and np.array_equal(ref[key],start[key]);assert np.array_equal(a[key],b[key])
    assert load(R/'metrics/P0_ZERO_AND_FIREWALL.json')['passed'];assert load(R/'metrics/LOCAL_ZERO_CONTRACT.json')['passed'];assert load(R/'metrics/DATA_AND_OBJECTIVE_REUSE.json')['passed']
    for s in ['S1','S2']:
        run=load(R/'metrics'/(s+'_FINISHED.json'));assert run['finished']and run['nfev']<=500 and run['iterations']<=12
        for row in load(R/'metrics'/(s+'_HISTORY.json')):
            assert row['physical']['quality']['closed']and row['physical']['quality']['components']==1 and not row['physical']['collision']
            for v in row['per_view']:assert v['foreground_denominator']+v['background_denominator']==v['known_N']
    assert not load(R/'metrics/CENTER_RELEASE_GATE.json')['released'];assert load(R/'metrics/S3_STATUS.json')['status']=='NOT_TRIGGERED';assert not(R/'metrics/S3_START.json').exists()
    post=load(R/'metrics/POSTERIOR.json');assert post['all_predictions_frozen_before_GT']and post['GT_vertices_outside_fixed_metric_domain']==0
    assert all(c['Ring']['EXACT_intersection_volume_mm3']<1e-8 and c['self']['nonadjacent_intersecting_triangle_pairs_N']==0 for c in post['Blender_checks'])
    assert load(R/'metrics/RESULT.json')['stopped']and not load(R/'metrics/RESULT.json')['mainline_promoted']
    for p in(R/'code').rglob('*.py'):ast.parse(p.read_text(),filename=str(p))
    files=[p for p in R.rglob('*.json')if 'runtime'not in p.relative_to(R).parts]
    for p in files:load(p)
    for p in R.glob('*.md'):
        for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
            if '://'not in target and not target.startswith('#'):assert(p.parent/target.split('#')[0]).exists(),(p,target)
    images=list((R/'figures').glob('Fig*.png'));assert len(images)==4
    for p in images:assert p.stat().st_size<4*1024*1024 and p.read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
    out.update(passed=True,strict_JSON_N=len(files),P0_exact=True,S2_inherits_S1_exact=True,S3_not_triggered=True,Gate_B_C_D_not_run=True,predictions_unchanged=True,scientific_result='MIXED_GLOBAL_CORRECTION_LOCAL_NO_EFFECTIVE_SIGNAL')
    (R/'assets_index/DELIVERY_VALIDATION.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
if __name__=='__main__':main()
