"""Additive policy stage dispatch; group failures remain independent evidence."""
import io,json,unittest
from pathlib import Path
import numpy as np
from ..policy.contracts import ROOT,require
from ..synthetic.io import save_json,outputs
from ..contracts.identities import sha256

def regression(attempt):
 loader=unittest.defaultTestLoader;base=unittest.TestSuite([loader.discover(str(ROOT/'tests'),pattern=p)for p in ['test_harness_contracts.py','test_policy_bootstrap.py']]);n=base.countTestCases();suite=unittest.TestSuite([base]+[loader.discover(str(ROOT/'tests'),pattern=p)for p in ['test_synthetic_correspondence.py','test_dualvideo_gate.py','test_sim_rev1.py','test_multisurface.py','test_stress.py','test_inita.py']]);stream=io.StringIO();r=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite);(attempt/'regression_log.txt').write_text(stream.getvalue());return outputs(attempt,dict(status='PASS'if r.wasSuccessful()and n==35 else'FAIL',baseline_tests=n,tests=r.testsRun,failures=len(r.failures),errors=len(r.errors)))

def audit(task,attempt):
 from .train import sources
 from ..stress.real import validate_view
 data=sources(task);cases=[];real=[]
 for r in data['cases']:
  a=np.load(r['initial']['path']);b=np.load(r['resolved013_initial']['path']);same=all(np.array_equal(a[k],b[k])for k in ['V','F','F_solid','inferred_base_faces']);require(same and'FREE_VERTEX_013/inputs/'in r['resolved013_initial']['path'],'INITIALIZATION_LINEAGE',r['case']);fit={v:[s['meta']['id']for s in r['FIT']if s['meta']['video']==v]for v in ['004','005']};held=[s['meta']['id']for s in r['HOLDOUT']];require(set(sum(fit.values(),[])).isdisjoint(held),'DATA_ISOLATION',r['case']);cases.append(dict(case=r['case'],status=r['status'],same_exact_013_mesh=True,vertices=len(a['V']),faces=len(a['F']),FIT=fit,HOLDOUT=held,initial_source=r['resolved013_initial'],A0_source=r['A0'],legacy_HERO_available_rows=len(r['legacy_HERO_inventory'])))
 for group in data['real_groups']:
  rows=[]
  for v in group['views']:
   try:rows.append(validate_view(v))
   except (ValueError,OSError,KeyError)as e:rows.append(dict(id=v['id'],status='NOT_EVALUABLE',reason=str(e)))
  ready=len([r for r in group['views']if r['role']=='FIT'])>=2 and all(r['status']=='PASS'for r in rows);real.append(dict(case=group['group'],status='READY'if ready else'NOT_EVALUABLE',views=rows,reason=None if ready else'No two source-bound complete native HERO Meshes; retained legacy depth-source inventory, no fabricated meshes'))
 save_json(attempt/'SOURCE_AUDIT.json',dict(cases=cases,HERO=real,source_review=data['Ip_source_review'],target_physical_cases=11,GT_shape_read=False));return outputs(attempt,dict(status='PASS',cases=11,ready_body=sum(c['status']=='READY'for c in cases),ready_HERO=sum(g['status']=='READY'for g in real),group_failures_retained=True))

def dispatch(stage,task,attempt):
 if stage=='inita_regression':return regression(attempt)
 if stage=='G0_sources':return audit(task,attempt)
 if stage in {'G1_smoke_train','G1_all_train'}:
  from .train import train
  return train(task,attempt,stage=='G1_smoke_train')
 if stage in {'G2_smoke_hero','G2_all_hero'}:
  from .hero import predict
  return predict(task,attempt,stage=='G2_smoke_hero')
 if stage in {'G3_smoke_evaluate','G3_all_evaluate'}:
  from .evaluate import run
  return run(task,attempt,stage=='G3_smoke_evaluate')
 if stage in {'G4_smoke_visualize','G4_visualize'}:
  from .visualize import run
  return run(task,attempt,stage=='G4_smoke_visualize')
 raise ValueError('Unregistered Init-A stage '+stage)
