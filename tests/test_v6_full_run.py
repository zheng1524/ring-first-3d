import unittest,tempfile,json
from pathlib import Path
import ring_first_3d.v6_raw.full_run as f
class FullRunTests(unittest.TestCase):
 def test_manifest_denominators_keep_zero_failed_and_pending(self):
  rows=[dict(case='a',group='g',status='DONE',renderable=2,selected_targets=17,native_success=2,q0=1,q1=1,origin='NEW'),dict(case='b',group='g',status='DONE',renderable=0,selected_targets=15,origin='REUSED'),dict(case='c',group='h',status='PREPARE_FAILED',renderable=0,selected_targets=None),dict(case='d',group='h',status='PENDING',renderable=0,selected_targets=None)]
  x=f.coverage(rows);self.assertEqual((x['groups_total'],x['videos_total'],x['videos_with_output']), (2,4,1));self.assertEqual((x['target_denominator_known'],x['target_denominator_unknown_videos']),(32,2));self.assertEqual(x['groups_all_videos_output'],0)
 def test_budget_rejects_unfrozen_or_changed_tuple(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'plan.json';p.write_text(json.dumps(dict(legal=[dict(tag='t',input_sha256='x')],budget=1)))
   self.assertEqual(f.authorize_tuple(p,'t','x'),1)
   with self.assertRaises(ValueError): f.authorize_tuple(p,'t','y')
   with self.assertRaises(ValueError): f.authorize_tuple(p,'u','x')
 def test_resume_success_requires_native_hash(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'x';p.write_bytes(b'real result')
   self.assertTrue(f.valid_cached_native(p,dict(success=True,raw_SHA256=f.hash_file(p))))
   p.write_bytes(b'truncated');self.assertFalse(f.valid_cached_native(p,dict(success=True,raw_SHA256='old')))
 def test_atomic_json_replaces_without_tmp(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'state.json';f.atomic_json(p,dict(status='RUNNING'));f.atomic_json(p,dict(status='DONE'));self.assertEqual(json.loads(p.read_text())['status'],'DONE');self.assertEqual(len(list(Path(td).iterdir())),1)

 def test_cli_runner_creates_new_state_before_stage(self):
  from unittest.mock import patch
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);manifest=root/'manifest.json';manifest.write_text(json.dumps(dict(videos=[dict(case='fresh',group='g',status='READY')],groups=['g'])))
   cfg=root/'config.json';cfg.write_text(json.dumps(dict(run_root=str(root),manifest=str(manifest),minimum_free_bytes=0)))
   def child(cmd,**kwargs):
    self.assertEqual(cmd[2],'ring_first_3d.v6_raw.full_run')
    state=f.read(root/'states/fresh.json');self.assertEqual(state['status'],'PREPARE_RUNNING')
    return 3
   with patch.object(f.subprocess,'call',side_effect=child):f.run(cfg)
   self.assertEqual(f.read(root/'states/fresh.json')['status'],'PREPARE_FAILED')
   self.assertEqual(f.read(root/'PROGRESS.json')['status'],'COMPLETE_WITH_FAILURES')
