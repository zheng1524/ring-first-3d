"""Original 247-test set, executed against copied canonical code with an audit guard."""
import io,json,sys,unittest,traceback
from pathlib import Path
from ring_first_3d.mainline.paths import ROOT,LINEAGE,activate
from ring_first_3d.mainline.execution_guard import install,EXECUTED
install()
patterns=['test_harness_contracts.py','test_policy_bootstrap.py','test_synthetic_correspondence.py','test_dualvideo_gate.py','test_sim_rev1.py','test_multisurface.py','test_stress.py','test_inita.py','test_contour_guided.py','test_structural_update.py']
loader=unittest.defaultTestLoader;suites=[loader.discover(str(ROOT/'tests'),pattern=p)for p in patterns]
activate('TASK-E4-STRUCTURED-BODY-UPDATE-002')
suites.append(loader.discover(str(LINEAGE/'experiments/TASK-E4-STRUCTURED-BODY-UPDATE-002/tests')))
suites.append(loader.discover(str(LINEAGE/'experiments/TASK-E4-G01-G03-GROWTH-RECOVERY-001/tests')))
out=ROOT/'mainline/validation/regression';out.mkdir(parents=True,exist_ok=True)
stream=io.StringIO();r=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.TestSuite(suites));(out/'LOG.txt').write_text(stream.getvalue())
result=dict(status='PASS'if r.wasSuccessful()and r.testsRun==247 else'FAIL',tests=r.testsRun,errors=len(r.errors),failures=len(r.failures),skipped=len(r.skipped),old_experiment_execution_guard=True,canonical_executed_sources=sorted(EXECUTED))
(out/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));print(stream.getvalue()[-5000:]);sys.exit(0 if result['status']=='PASS'else 1)
