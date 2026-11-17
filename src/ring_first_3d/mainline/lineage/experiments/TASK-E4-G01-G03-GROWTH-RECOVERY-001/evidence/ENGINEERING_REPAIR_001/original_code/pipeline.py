"""Policy handlers: exact historical recovery → two fixed-Body pilots → GT only."""
import io,sys,unittest,json
from pathlib import Path
import numpy as np
from io_utils import TD,OLD,OLD_ROOT,body,load_inputs,read,dump,sha
from recover import restore
from embedded_sweep import prepare
from optimize import optimize
from ring_first_3d.synthetic.io import outputs

def regression(attempt):
    root=TD.parents[1];patterns=['test_harness_contracts.py','test_policy_bootstrap.py','test_synthetic_correspondence.py','test_dualvideo_gate.py','test_sim_rev1.py','test_multisurface.py','test_stress.py','test_inita.py','test_contour_guided.py','test_structural_update.py']
    loader=unittest.defaultTestLoader;suites=[loader.discover(str(root/'tests'),pattern=p)for p in patterns]
    baseline=sum(s.countTestCases()for s in suites[:2])
    suites.append(loader.discover(str(OLD/'tests')));suites.append(loader.discover(str(TD/'tests')))
    stream=io.StringIO();r=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.TestSuite(suites))
    (attempt/'regression_log.txt').write_text(stream.getvalue())
    return outputs(attempt,dict(status='PASS'if r.wasSuccessful()and baseline==35 else'FAIL',baseline_tests=baseline,tests=r.testsRun,failures=len(r.failures),errors=len(r.errors)))

def audit(t,attempt):
    frozen=read(t['recovery']['configuration']['path']);rows=[]
    for case in ['G01','G03']:
        current,rejected,info,C,A,chosen,report=restore(case);configuration=prepare(current,C,A,info)
        assert configuration==frozen[case], 'EMBED_CONFIGURATION_DRIFT'
        initial,views,ring,base,chart,row=load_inputs(case,'FIT')
        report.update(configuration=configuration,FIT=[v['id']for v in views],HOLDOUT=[v['meta']['id']for v in row['HOLDOUT']],weights=__import__('common').legacy.balanced_weights(views),GT_read=False,HERO_read=False)
        rows.append(report)
    dump(attempt/'RECOVERY_AUDIT.json',rows)
    return outputs(attempt,dict(status='PASS',cases=2,exact_historical_recovery=True,GT_read=False))

def predict(t,attempt,case):
    assert case in ['G01','G03']
    current,rejected,info,C,A,chosen,recovery=restore(case)
    initial,views,ring,base,chart,row=load_inputs(case,'FIT');configuration=read(t['recovery']['configuration']['path'])[case]
    folder=attempt/case;folder.mkdir()
    dump(folder/'EXACT_RECOVERY.json',recovery)
    np.savez_compressed(folder/'HISTORICAL_REJECTED_RESTORED.npz',**rejected)
    try:
        result=optimize(current,initial,views,ring,base,chart,configuration,chosen['support_views'],t['recovery']['update'],folder/'DEFORM_SWEEP_RECOVERY')
        path=folder/'DEFORM_SWEEP_RECOVERY'/result['mesh']
        record=dict(case=case,arm='DEFORM_SWEEP_RECOVERY',status='NUMERIC'if result['success']else'FAILED_NAN',
            mesh_relative=str(path.relative_to(attempt)),mesh_sha256=sha(path),scientific_growth_accepted=result['success'],
            failure_reasons=result['chosen']['reasons'],diagnostic_mesh_retained=not result['success'],
            chosen_gate_relative=str(Path(case)/'DEFORM_SWEEP_RECOVERY'/result['chosen']['folder']/'GATES.json'))
    except (ValueError,RuntimeError,np.linalg.LinAlgError)as e:
        from ring_first_3d.policy.contracts import PolicyError
        if isinstance(e,PolicyError):raise
        dump(folder/'ENGINEERING_FAILURE.json',dict(error=type(e).__name__,reason=str(e)))
        record=dict(case=case,arm='DEFORM_SWEEP_RECOVERY',status='FAILED_NAN',failure_reasons=[str(e)],scientific_growth_accepted=False)
    dump(attempt/'PREDICTIONS_FROZEN.json',dict(records=[record],GT_read=False,HERO_read=False,Body_fixed=True,camera_optimized=False,selection='FIT_ONLY_FULL_GATES_WITHIN_FROZEN_LOCAL_BUDGET'))
    return outputs(attempt,dict(status='PASS',records=[record],GT_read=False))

def dispatch(stage,t,attempt):
    if stage=='recovery_regression':return regression(attempt)
    if stage=='G0_recovery_audit':return audit(t,attempt)
    if stage in ['G1_G01','G1_G03']:return predict(t,attempt,stage[3:])
    if stage=='G2_evaluate':
        from evaluate import evaluate
        return evaluate(t,attempt)
    if stage=='G4_visualize':
        from visualize import visualize
        return visualize(t,attempt)
    raise ValueError(stage)

