import unittest,tempfile,json
from pathlib import Path
from ring_first_3d.v6_raw import full_run as f
class R1RunnerTests(unittest.TestCase):
 def test_clean_is_mandatory_before_render(self):
  self.assertEqual(f.stages_for(dict(fixed_clean=True),{'origin':'NEW'}),['prepare','camera','schedule','hero','clean','render'])
 def test_no_output_keeps_full_denominator(self):
  manifest=dict(videos=[dict(case='a',group='g',selected_targets=21),dict(case='b',group='g',selected_targets=20)])
  rows=[dict(case='a',group='g',status='CAMERA_FAILED',renderable=0),dict(case='b',group='g',status='DONE',renderable=5)]
  f.freeze_denominators(rows,manifest)
  self.assertEqual(f.coverage(rows)['target_denominator_known'],41)
 def test_exception_categories_preserve_engineering_failure(self):
  self.assertEqual(f.failure_category(1,'Traceback KeyError: x'),'ENGINEERING_ERROR')
  self.assertEqual(f.failure_category(1,'RuntimeError: CUDA out of memory'),'RESOURCE_ERROR')
  self.assertEqual(f.failure_category(-9,''),'RESOURCE_ERROR')
  self.assertEqual(f.failure_category(1,'OSError: [Errno 28] No space left on device'),'LOW_DISK')
  self.assertEqual(f.failure_category(1,'FROZEN_RAW_MANIFEST_DRIFT'),'DATA_ERROR')
 def test_space_reserves_current_stage_peak(self):
  cfg=dict(minimum_free_bytes=1073741824,stage_peak_bytes={'hero':500000000})
  self.assertEqual(f.required_free(cfg,'hero'),1573741824)
class ResumeIdentityTests(unittest.TestCase):
 def test_completed_receipt_rejects_corrupted_output(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);out=p/'mesh';out.write_bytes(b'mesh')
   receipt=p/'HERO_COMPLETE.json';f.atomic_json(receipt,dict(outputs={str(out):f.hash_file(out)}))
   f.verify_outputs(receipt)
   out.write_bytes(b'bad')
   with self.assertRaises(ValueError):f.verify_outputs(receipt)
if __name__=='__main__':unittest.main()

class HeroFailureTests(unittest.TestCase):
 def test_resource_retry_never_selects_success_or_engineering_failure(self):
  rows=[dict(tag='ok',success=True),dict(tag='oom',success=False,failure='CUDA out of memory'),dict(tag='bad',success=False,failure='KeyError: x')]
  self.assertEqual(f.retryable_hero_tags(rows,[]),['oom'])
  self.assertEqual(f.retryable_hero_tags(rows,[dict(tags=['oom'])]),[])
 def test_partial_hero_is_not_successful_terminal(self):
  rows=[dict(success=True),dict(success=False,failure='CUDA out of memory')]
  self.assertEqual(f.hero_outcome(rows),'RESOURCE_ERROR')
  self.assertEqual(f.hero_outcome([dict(success=False,failure='KeyError')]),'ENGINEERING_ERROR')

class HeroLedgerOrderTests(unittest.TestCase):
 def test_retry_completion_restores_original_case_order(self):
  plan=dict(legal=[dict(tag='a'),dict(tag='b'),dict(tag='c')])
  rows=[dict(tag='a',success=True),dict(tag='c',success=True),dict(tag='b',success=True)]
  self.assertEqual([x['tag'] for x in f.ordered_hero_results(rows,plan)],['a','b','c'])

class HeroRetryTransactionTests(unittest.TestCase):
 def test_interrupted_retry_intent_recovers_without_hiding_failed_tag(self):
  from types import SimpleNamespace
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);R=root/'HIST'/'case';(R/'metrics').mkdir(parents=True)
   ledger=R/'metrics/MVS005_supported_runs.json';complete=R/'HERO_COMPLETE.json'
   f.atomic_json(R/'PLAN_FROZEN.json',dict(legal=[dict(tag='a',input_sha256='aa'),dict(tag='b',input_sha256='bb')]))
   f.atomic_json(ledger,[dict(tag='a',success=True),dict(tag='b',success=False,failure='CUDA out of memory')]);f.atomic_json(complete,{})
   calls=[]
   def hero(case,variant):
    calls.append(1)
    if len(calls)==1:return {}
    self.assertFalse(complete.exists())
    self.assertEqual([x['tag'] for x in f.read(ledger)],['a'])
    if len(calls)==2:raise SystemExit('simulate kill after ledger update')
    f.atomic_json(ledger,[dict(tag='a',success=True),dict(tag='b',success=True)]);f.atomic_json(complete,{})
    return {}
   r=SimpleNamespace(B=root,hero=hero)
   with self.assertRaises(SystemExit):f.hero_with_resource_retry(r,'case',R)
   self.assertEqual(f.read(R/'HERO_RESOURCE_RETRIES.json')[0]['status'],'PENDING')
   f.hero_with_resource_retry(r,'case',R)
   self.assertEqual(f.read(R/'HERO_RESOURCE_RETRIES.json')[0]['status'],'COMPLETE')
   self.assertEqual([x['tag'] for x in f.read(ledger)],['a','b'])

class HistoricalImportTests(unittest.TestCase):
 def test_bootstrap_replaces_only_retired_import_time_camera_reads(self):
  import ast
  from ring_first_3d.v6_raw.frontend_kernels import bootstrap_tree
  source="import numpy as np\nK=prev.cam('real','0')['K'];OLDPOSE=prev.cam('real','0')['c2w']\ndef compute(x):return x+K[0,0]\n"
  before=ast.parse(source);after=bootstrap_tree(source)
  self.assertEqual(ast.dump(before.body[-1]),ast.dump(after.body[-1]))
  self.assertNotIn('prev.cam',ast.unparse(after))
