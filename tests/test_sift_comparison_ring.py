import importlib
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np


def pinhole(points, pose, K):
    camera = (points - pose[:3, 3]) @ pose[:3, :3]
    homogeneous = camera @ K.T
    return homogeneous[:, :2] / homogeneous[:, 2:3], camera[:, 2]


class RingDiagnosticTests(unittest.TestCase):
    def module(self):
        try:
            return importlib.import_module('ring_first_3d.sift_comparison.ring_diagnostic')
        except ModuleNotFoundError:
            self.fail('Ring diagnostic module is not implemented')

    def test_whole_world_similarity_preserves_same_observation_projection(self):
        ring = self.module()
        poses = np.repeat(np.eye(4)[None], 2, axis=0)
        poses[1, :3, 3] = [1., 2., -.5]
        points = np.array([[0., 0., 4.], [1., -1., 6.], [3., 2., 8.]])
        K = np.array([[490., 0., 320.], [0., 490., 180.], [0., 0., 1.]])
        angle = np.deg2rad(30)
        rotation = np.array([[np.cos(angle), -np.sin(angle), 0.],
                             [np.sin(angle), np.cos(angle), 0.], [0., 0., 1.]])
        for scale in [.5, .75, 1., 1.25, 1.5]:
            changed, shifted = ring.transform_global_similarity(poses, points, scale, rotation)
            result = ring.projection_invariance(poses, points, changed, shifted,
                                                np.arange(3), np.zeros((3, 2, 2)), K, pinhole)
            self.assertEqual(result['evaluable_observations'], 6)
            self.assertLess(result['max_change_px'], 1e-10)
            np.testing.assert_allclose(changed[:, :3, :3], rotation @ poses[:, :3, :3])
        np.testing.assert_array_equal(points[0], [0., 0., 4.])

    def test_invalid_camera_and_empty_ring_are_retained(self):
        ring = self.module()
        contour = lambda pose, n: np.array([[[0., 0.], [1., 0.]]])
        malformed = np.eye(4); malformed[:3, :3] = 0
        invalid = ring.ring_frame(malformed, np.zeros((2, 2)), contour)
        self.assertEqual(invalid['status'], 'NOT_EVALUABLE')
        self.assertEqual(invalid['reason'], 'INVALID_CAMERA_ROTATION')
        empty = ring.ring_frame(np.eye(4), np.empty((0, 2)), contour)
        self.assertEqual(empty['reason'], 'EMPTY_HELD_RING')
        partial = ring.ring_frame(np.eye(4), np.array([[0., 3.], [np.nan, 0.]]), contour)
        self.assertEqual(partial['held_points'], 2)
        self.assertEqual(partial['finite_held_points'], 1)
        self.assertEqual(partial['MAE_px'], 3.)
        summary = ring.ring_summary([invalid, empty, partial])
        self.assertEqual(summary['total_frames'], 3)
        self.assertEqual(summary['evaluable_frames'], 1)
        self.assertEqual(summary['median_frame_MAE_px'], 3.)

    def test_projection_failures_keep_frozen_denominator(self):
        ring = self.module()
        poses = np.repeat(np.eye(4)[None], 2, axis=0); poses[1] = np.nan
        points = np.array([[0., 0., 1.], [0., 0., -1.]])
        xy = np.zeros((2, 2, 2)); xy[1, 1] = np.nan
        result = ring.projection_invariance(poses, points, poses, points,
                                           np.arange(2), xy, np.eye(3), pinhole)
        self.assertEqual(result['total_observed_pairs'], 3)
        self.assertEqual(result['evaluable_observations'], 1)
        self.assertEqual(sum(result['reasons'].values()), 2)

    def test_no_saved_points_has_explicit_nonevaluable_reason(self):
        ring = self.module()
        poses = np.eye(4)[None]
        result = ring.projection_invariance(poses, np.empty((0, 3)), poses, np.empty((0, 3)),
                                           [], np.empty((0, 1, 2)), np.eye(3), pinhole)
        self.assertEqual(result.get('reason'), 'NO_SAVED_TRAIN_POINTS')
        self.assertEqual(result['total_observed_pairs'], 0)
        self.assertIsNone(result['max_change_px'])

    def test_nonfinite_contour_is_not_a_large_fabricated_residual(self):
        ring = self.module()
        result = ring.ring_frame(np.eye(4), np.zeros((5, 2)),
                                 lambda pose, n: np.full((2, n, 2), np.nan))
        self.assertEqual(result['reason'], 'NONFINITE_RING_CONTOUR')
        self.assertIsNone(result['MAE_px'])
        self.assertEqual(result['finite_held_points'], 5)

    def test_diagnose_preserves_failed_normalization_and_common_rgb_denominator(self):
        ring = self.module()
        from ring_first_3d.sift_comparison import run
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory); root = base / 'case'; common = root / 'common'
            common.mkdir(parents=True)
            (root / 'R/observations').mkdir(parents=True); (root / 'S').mkdir()
            run.save(common / 'meta.json', {'frames': [{'id': 'one'}, {'id': 'missing'}], 'ring_inner_mm': 5})
            np.savez(common / 'tracks.npz', xy=np.zeros((1, 2, 2)))
            run.save(common / 'split.json', {'train': [0]})
            poses = np.repeat(np.eye(4)[None], 2, axis=0)
            for arm in ['R', 'S']:
                np.savez(root / arm / 'cameras.npz', c2w=poses, points=np.array([[0., 0., 4.]]),
                         point_track_ids=np.array([0]), K=np.eye(3))
                run.save(root / arm / 'RGB_CHECKS.json', [{'frame': i, 'passed': True} for i in range(2)])
            np.savez(root / 'R/observations/one_ring.npz', q_held=np.array([[0., 4.]]))
            run.save(root / 'NORMALIZATION_FROZEN.json', {'status': 'NOT_EVALUABLE', 'reason': 'DEGENERATE_COMMON_TRAIN_POINTS'})
            kernel = SimpleNamespace(contours=lambda pose, n: np.array([[[0., 0.], [1., 0.]]]), project=pinhole)
            with patch.object(run, 'BASE', base), patch.object(run, 'verify_common', return_value=common), \
                    patch.object(run, 'kernels', return_value=(None, {'v6': kernel})):
                self.assertTrue(hasattr(ring, 'diagnose_ring'), 'diagnose_ring adapter missing')
                result = ring.diagnose_ring('case')
            self.assertEqual(result['arms']['R']['nominal']['total_frames'], 2)
            self.assertEqual(result['arms']['R']['nominal']['evaluable_frames'], 1)
            self.assertEqual(result['arms']['S']['nominal']['evaluable_frames'], 0)
            self.assertEqual(result['arms']['S']['reason'], 'DEGENERATE_COMMON_TRAIN_POINTS')
            conflict = result['arms']['R']['common_rgb_ring_conflict']
            self.assertEqual(conflict['common_rgb_pass_frames'], 2)
            self.assertEqual(conflict['conflict_frames'], 1)
            self.assertEqual(conflict['not_evaluable_frames'], 1)
            self.assertEqual([row['scale'] for row in result['arms']['R']['scale_sweep']], [.5,.75,1.,1.25,1.5])
            json.loads((root / 'RING_DIAGNOSTIC.json').read_text())

            sim = dict(status='FROZEN', scale=1., rotation=np.eye(3).tolist(), translation=[0.,0.,0.],
                       camera_hashes={a:run.sha(root / a / 'cameras.npz') for a in ['R','S']})
            run.save(root / 'NORMALIZATION_FROZEN.json', sim)
            with np.load(root / 'S/cameras.npz') as archive:
                normalized = dict(archive)
            np.savez(root / 'S/cameras_normalized.npz', **normalized)
            with patch.object(run, 'BASE', base), patch.object(run, 'verify_common', return_value=common), \
                    patch.object(run, 'kernels', return_value=(None, {'v6': kernel})):
                result = ring.diagnose_ring('case')
                self.assertEqual(result['arms']['S']['nominal']['evaluable_frames'], 1)
                normalized['points'][0, 0] += 1
                np.savez(root / 'S/cameras_normalized.npz', **normalized)
                result = ring.diagnose_ring('case')
                self.assertEqual(result['arms']['S']['reason'], 'NORMALIZED_POINTS_DRIFT')
                self.assertEqual(result['arms']['S']['nominal']['evaluable_frames'], 0)

    def test_authoritative_contour_has_yaw_symmetry_but_fixed_size_rejects_scaling(self):
        ring = self.module()
        source = Path('/home/liu/polyp_research/ring_anchor_3d/scripts/geometry.py')
        if not source.exists():
            self.skipTest('Read-only authoritative scientific kernel unavailable')
        spec = importlib.util.spec_from_file_location('ring_test_geometry', source)
        geometry = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(geometry)
        pose = np.eye(4); pose[:3, :3] = np.diag([1., -1., -1.]); pose[:3, 3] = [3., 2., 40.]
        K = np.array([[490., 0., 320.], [0., 490., 180.], [0., 0., 1.]])
        angle = np.deg2rad(30.)
        rotation = np.array([[np.cos(angle), -np.sin(angle), 0.],
                             [np.sin(angle), np.cos(angle), 0.], [0., 0., 1.]])
        for major_radius in [3.1, 5.6]:
            def contour(p, n):
                return geometry.torus_contours(p[:3,3], p[:3,:3], K, R=major_radius, r=.6, n=n)
            held = contour(pose, 2048).reshape(-1, 2)
            rotated, _ = ring.transform_global_similarity(pose[None], np.empty((0, 3)), rotation=rotation)
            yaw = ring.ring_frame(rotated[0], held, contour)
            self.assertLess(yaw['P95_px'], .1)
            scaled, _ = ring.transform_global_similarity(pose[None], np.empty((0, 3)), scale=1.5)
            self.assertGreater(ring.ring_frame(scaled[0], held, contour)['MAE_px'], 5.)


if __name__ == '__main__':
    unittest.main()
