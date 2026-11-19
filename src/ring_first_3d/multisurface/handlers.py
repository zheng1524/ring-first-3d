"""Registered G0–G4 multisurface handlers, using the existing Policy Runner."""
import io,unittest
from ..policy.contracts import ROOT
from ..synthetic.io import outputs


def regression(attempt):
    loader=unittest.defaultTestLoader;base=unittest.TestSuite([loader.discover(str(ROOT/'tests'),pattern=p)for p in ['test_harness_contracts.py','test_policy_bootstrap.py']]);n=base.countTestCases()
    suite=unittest.TestSuite([base]+[loader.discover(str(ROOT/'tests'),pattern=p)for p in ['test_synthetic_correspondence.py','test_dualvideo_gate.py','test_sim_rev1.py','test_multisurface.py']]);stream=io.StringIO();r=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite);(attempt/'regression_log.txt').write_text(stream.getvalue())
    return outputs(attempt,dict(status='PASS'if r.wasSuccessful()and n==35 else'FAIL',baseline_tests=n,tests=r.testsRun,failures=len(r.failures),errors=len(r.errors)))


def dispatch(stage,task,attempt):
    if stage=='fusion_regression':return regression(attempt)
    if stage in {'G0_views_noise','G1_body'}:
        from .scene import generate,body
        return generate(task,attempt)if stage=='G0_views_noise'else body(task,attempt)
    if stage in {'G2_candidates','G3_smoke_predict','G3_all_predict'}:
        from .registration import candidates_stage,run
        return candidates_stage(task,attempt)if stage=='G2_candidates'else run(task,attempt,stage=='G3_smoke_predict')
    if stage=='G3_smoke_evaluate':
        from .evaluate import smoke
        return smoke(task,attempt)
    if stage=='G4_fusion_predict':
        from .fusion import run
        return run(task,attempt)
    if stage=='G4_evaluate':
        from .evaluate import run
        return run(task,attempt)
    if stage=='G4_visualize':
        from .visualize import run
        return run(task,attempt)
    raise ValueError('Unregistered multisurface stage: '+stage)
