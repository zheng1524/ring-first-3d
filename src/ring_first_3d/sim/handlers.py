"""Complete explicitly registered G0–G4 handlers and original regression suite."""
import io,unittest
from ..policy.contracts import ROOT
from ..synthetic.io import outputs


def regression(attempt):
    loader=unittest.defaultTestLoader
    base=unittest.TestSuite([loader.discover(str(ROOT/'tests'),pattern=p)for p in ['test_harness_contracts.py','test_policy_bootstrap.py']]);n=base.countTestCases()
    suite=unittest.TestSuite([base]+[loader.discover(str(ROOT/'tests'),pattern=p)for p in ['test_synthetic_correspondence.py','test_dualvideo_gate.py','test_sim_rev1.py']])
    stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite);(attempt/'regression_log.txt').write_text(stream.getvalue())
    return outputs(attempt,dict(status='PASS'if result.wasSuccessful()and n==35 else'FAIL',baseline_tests=n,tests=result.testsRun,failures=len(result.failures),errors=len(result.errors)))


def dispatch(stage,task,attempt):
    if stage=='sim_regression':return regression(attempt)
    if stage=='G0_simulate':
        from .scene import generate
        return generate(task,attempt)
    if stage=='G1_initialize':
        from .initialize import run
        return run(task,attempt)
    if stage=='G1_evaluate':
        from .evaluate import body
        return body(task,attempt)
    if stage=='G2_mapping':
        from .mapping import run
        return run(task,attempt)
    if stage=='G2_evaluate':
        from .evaluate import mapping
        return mapping(task,attempt)
    if stage in {'G3_smoke_predict','G3_matrix_predict'}:
        from .registration import run
        return run(task,attempt,stage=='G3_smoke_predict')
    if stage in {'G3_smoke_evaluate','G4_evaluate'}:
        from .evaluate import registration
        return registration(task,attempt,stage=='G3_smoke_evaluate')
    if stage=='G4_visualize':
        from .visualize import run
        return run(task,attempt)
    raise ValueError('Unregistered simulation handler: '+stage)
