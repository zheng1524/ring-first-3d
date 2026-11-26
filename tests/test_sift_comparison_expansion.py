import tempfile
import unittest
from pathlib import Path
from ring_first_3d.sift_comparison.expansion import active_priority_jobs, authorized_cases, inference_limit

class ExpansionTests(unittest.TestCase):
    def test_expansion_is_ten_videos_five_physical_groups(self):
        allcases=authorized_cases('expanded')
        self.assertEqual(len(allcases),10)
        self.assertEqual(len({c.rsplit('_',1)[0] for c in allcases}),5)
        self.assertTrue(set(authorized_cases('pilot')).issubset(allcases))
        self.assertEqual(inference_limit('pilot'),8)
        self.assertEqual(inference_limit('expanded'),40)
        with self.assertRaises(ValueError):inference_limit('unbounded')

    def test_A_scheduler_has_priority_even_without_gpu_process(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'123';p.mkdir();(p/'cmdline').write_bytes(b'python\0-m\0ring_first_3d.v6_raw.full_run\0run\0--config\0a.json\0')
            self.assertEqual(active_priority_jobs(Path(tmp),own_pid=999)[0]['pid'],123)
            self.assertEqual(active_priority_jobs(Path(tmp),own_pid=123),[])
            (p/'cmdline').write_bytes(b'python\0tools/ring_sift_comparison.py\0--stage\0hero\0')
            self.assertEqual(active_priority_jobs(Path(tmp),own_pid=999),[])

class QueueSourceTests(unittest.TestCase):
    def test_queue_refuses_source_drift(self):
        import hashlib
        from ring_first_3d.sift_comparison.expansion import verify_queue_sources
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'code.py';p.write_text('fixed')
            hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest()}
            verify_queue_sources(hashes)
            p.write_text('changed')
            with self.assertRaises(RuntimeError):verify_queue_sources(hashes)

class ExpansionFailureTests(unittest.TestCase):
    def test_failure_dominates_gpu_wait(self):
        from ring_first_3d.sift_comparison.expansion import classify_hero_batch
        self.assertEqual(classify_hero_batch({'cases':{'a':{'status':'FAILED_STAGE'},'b':{'status':'QUEUED_A_PRIORITY'}}}),'FAILED_STAGE_NO_RETRY')
        self.assertEqual(classify_hero_batch({'cases':{'a':{'status':'FAILED_STAGE'}}}),'FAILED_STAGE_NO_RETRY')
        self.assertEqual(classify_hero_batch({'cases':{'a':{'status':'QUEUED_A_PRIORITY'}}}),'WAITING_FOR_GPU')

    def test_unavailable_case_preserves_both_arms_and_frame_denominators(self):
        from ring_first_3d.sift_comparison.expanded_report import unavailable_coverage
        rows=unavailable_coverage('physical_group_005',22,'FAILED_CAMERA_STAGE')
        self.assertEqual(len(rows),2)
        self.assertEqual([r['selected_frames'] for r in rows],[22,22])
        self.assertTrue(all(r['numeric_cameras'] is None and r['fixed_targets']==2 for r in rows))
        self.assertEqual({r['arm'] for r in rows},{'R','S'})
