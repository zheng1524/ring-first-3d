import sys
import tempfile
import unittest
from pathlib import Path
import numpy as np

WS = Path('/home/liu/ring_first_3d_workspace')
sys.path.insert(0, str(WS / 'tools'))
import validate_m1_all_groups as V


class Status(unittest.TestCase):
    def test_success(self):
        self.assertEqual(V.classify(0, '', '', True, 'COMPLETED_VALID'), 'COMPLETED_VALID')

    def test_limited(self):
        self.assertEqual(V.classify(0, '', '', True, 'COMPLETED_LIMITED'), 'COMPLETED_LIMITED')

    def test_known_ring_insufficient(self):
        self.assertEqual(V.classify(2, '', 'INSUFFICIENT_RING_OBSERVATION', False, 'INSUFFICIENT_EVIDENCE'),
                         'INSUFFICIENT_EVIDENCE')

    def test_known_scene_points_blocked(self):
        self.assertEqual(V.classify(2, '', 'insufficient positive Ring-initialized scene points',
                                    False, 'BLOCKED_QUALITY_GATE'), 'BLOCKED_QUALITY_GATE')

    def test_keyerror_is_implementation(self):
        self.assertEqual(V.classify(1, '', 'KeyError: 3', False, None), 'IMPLEMENTATION_ERROR')

    def test_missing_output_is_implementation(self):
        self.assertEqual(V.classify(0, '', '', False, None), 'IMPLEMENTATION_ERROR')


class W0Numeric(unittest.TestCase):
    def _write(self, c2w, K, ids, ring):
        p = Path(tempfile.mkdtemp()) / 'W0.npz'
        np.savez_compressed(p, c2w=c2w, K=K, ids=np.array(ids), ring_cad_mm=np.array(ring))
        return p

    def test_valid(self):
        c2w = np.stack([np.eye(4), np.eye(4)])
        p = self._write(c2w, np.eye(3), ['a', 'b'], [5.6, 0.6])
        ok, n, why = V.w0_numeric(p, 2, 10.0)
        self.assertTrue(ok, why)
        self.assertEqual(n, 2)

    def test_bad_det(self):
        c2w = np.stack([np.eye(4), np.eye(4)])
        c2w[1, 0, 0] = 2.0
        p = self._write(c2w, np.eye(3), ['a', 'b'], [5.6, 0.6])
        ok, n, why = V.w0_numeric(p, 2, 10.0)
        self.assertFalse(ok)
        self.assertIn('ORTHONORMAL', why)

    def test_wrong_ring(self):
        c2w = np.stack([np.eye(4), np.eye(4)])
        p = self._write(c2w, np.eye(3), ['a', 'b'], [5.6, 0.6])
        ok, n, why = V.w0_numeric(p, 2, 5.0)
        self.assertFalse(ok)
        self.assertIn('RING_CAD', why)

    def test_count_mismatch(self):
        c2w = np.stack([np.eye(4)])
        p = self._write(c2w, np.eye(3), ['a'], [5.6, 0.6])
        ok, n, why = V.w0_numeric(p, 2, 10.0)
        self.assertFalse(ok)
        self.assertIn('COUNT', why)


class EngineeringGate(unittest.TestCase):
    def _rows(self):
        rows = []
        for i in range(39):
            nv = 3 if i == 0 else 2
            for j in range(nv):
                rows.append(dict(group_id=f'G{i:02d}', video_id=f'{j:03d}',
                                 execution_status='COMPLETED_VALID', n_prepared_frames=10,
                                 w0_generated=True, n_w0_poses=10, n_accept=1,
                                 n_quarantine=0, n_insufficient_evidence=0, n_reject=0,
                                 failure_reason=None))
        return rows

    def test_full_pass(self):
        rows = self._rows()
        groups = sorted({r['group_id'] for r in rows})
        ok, counts = V.engineering_gate(rows, groups, [], expected_frames=790)
        self.assertTrue(ok)
        self.assertEqual(counts['discovered_videos'], 79)
        self.assertEqual(counts['prepared_frames'], 790)

    def test_implementation_error_fails(self):
        rows = self._rows()
        rows[0]['execution_status'] = 'IMPLEMENTATION_ERROR'
        groups = sorted({r['group_id'] for r in rows})
        ok, counts = V.engineering_gate(rows, groups, [], expected_frames=790)
        self.assertFalse(ok)
        self.assertEqual(counts['implementation_errors'], 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
