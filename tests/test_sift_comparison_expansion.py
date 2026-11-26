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
