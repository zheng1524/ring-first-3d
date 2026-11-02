"""Proceed only with failure-mechanism baselines; do not manufacture gate PASS."""
from run_tsdf import *
def main():
    d=load(R/'config/SINGLE_DIAGNOSIS.json');first=load(R/'config/SINGLE_FIRST_ATTEMPT_FAILURE.json')
    assert first['checks']['raw_XYZ_roundtrip']and first['checks']['native_resize']and first['checks']['pixel_roundtrip']and first['checks']['unknown_zero']and first['checks']['empty_mask_empty_mesh']
    assert d['results']['SINGLE_RESOLUTION_CONTROL']['checks']['native_depth_error_full_denominator']
    assert d['results']['SINGLE_RESOLUTION_CONTROL']['checks']['point_retention']
    save('config/DIAGNOSTIC_CONTINUATION.json',dict(UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),formal_single_gate='FAIL_RETAINED',adapter_formally_frozen=False,thresholds_changed=False,
        reason='Source algebra/units/mask verified. Primary open-boundary/discretization loss localized by the only predeclared resolution control (89.56% ->96.01% rays); mm/m control has median 0.00000324 mm and a 0.00200267 mm worst surface discrepancy just above frozen 0.002 mm gate. No severe factor/pose error. User explicitly requires actual G0/G1 even if basic TSDF fails. Continue as diagnostic results, never scientific acceptance.',
        no_further_resolution_or_parameter_search=True,primary_G0_G1_voxel_mm=.1,adapter=asset(R/'code/hero_tsdf_adapter.py'),common=asset(R/'code/common.py')))
    for name in ['G0','G1']:
        assert not(R/'local_results'/name/'mesh_mm.ply').exists()
        integrate(name,cfg()[name])
    snapshot('AFTER_OFFICIAL_INTEGRATION')
if __name__=='__main__':main()
