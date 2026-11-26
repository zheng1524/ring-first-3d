import importlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from ring_first_3d.sift_comparison import run
from ring_first_3d.sift_comparison.core import transform_cameras


def camera(xyz=(0, 0, 0), angle=0):
    a = np.deg2rad(angle)
    out = np.eye(4)
    out[:3, :3] = [[np.cos(a), -np.sin(a), 0],
                    [np.sin(a), np.cos(a), 0], [0, 0, 1]]
    out[:3, 3] = xyz
    return out


class PoseMathTests(unittest.TestCase):
    def setUp(self):
        self.pose = importlib.import_module('ring_first_3d.sift_comparison.pose_metrics')

    def test_known_motion_and_identical_pose(self):
        result = self.pose.pose_delta(camera(), camera((3, 4, 0), 90))
        self.assertEqual(result['status'], 'OK')
        np.testing.assert_allclose(result['position_delta'], [3, 4, 0])
        self.assertAlmostEqual(result['position_norm'], 5)
        self.assertAlmostEqual(result['rotation_deg'], 90)
        same = self.pose.pose_delta(camera((2, 3, 4), 30), camera((2, 3, 4), 30))
        self.assertAlmostEqual(same['position_norm'], 0)
        self.assertAlmostEqual(same['rotation_deg'], 0, places=5)

    def test_relative_motion_uses_target_camera_coordinates(self):
        target = camera((10, 20, 30), 90)
        r = target @ camera((2, 0, 0))
        s = target @ camera((2, 1, 0), 30)
        result = self.pose.relative_pose_delta(target, r, target, s)
        np.testing.assert_allclose(result['position_delta'], [0, 1, 0], atol=1e-12)
        self.assertAlmostEqual(result['position_norm'], 1)
        self.assertAlmostEqual(result['rotation_deg'], 30)
        self.assertAlmostEqual(result['baseline_R'], 2)
        self.assertAlmostEqual(result['baseline_S'], np.sqrt(5))
        self.assertAlmostEqual(result['translation_error_percent'], 50)
        np.testing.assert_allclose(result['relative_R'], camera((2, 0, 0)), atol=1e-12)

    def test_relative_transform_invariant_to_common_world_rigid_transform(self):
        poses = [camera((1, 2, 3), 30), camera((2, 4, 5), 65),
                 camera((1, 3, 2), -20), camera((4, 2, 6), 75)]
        base = self.pose.relative_pose_delta(*poses)
        world = camera((200, -60, 17), 130)
        changed = self.pose.relative_pose_delta(*(world @ p for p in poses))
        for key in ['position_delta', 'position_norm', 'rotation_deg', 'baseline_R',
                    'baseline_S', 'translation_error_percent', 'relative_R', 'relative_S']:
            np.testing.assert_allclose(changed[key], base[key], atol=1e-11)

    def test_zero_baseline_keeps_finite_difference_but_not_percentage(self):
        result = self.pose.relative_pose_delta(camera(), camera(), camera(), camera((1, 0, 0)))
        self.assertEqual(result['status'], 'OK')
        self.assertEqual(result['position_norm'], 1)
        self.assertIsNone(result['translation_error_percent'])
        self.assertEqual(result['percentage_status'], 'NOT_EVALUABLE')
        self.assertEqual(result['percentage_reason'], 'ZERO_R_BASELINE')

    def test_missing_camera_is_not_zero_difference(self):
        missing = np.full((4, 4), np.nan)
        for result in [self.pose.pose_delta(camera(), missing),
                       self.pose.relative_pose_delta(camera(), camera(), missing, camera())]:
            self.assertEqual(result['status'], 'NOT_EVALUABLE')
            self.assertIsNone(result['position_norm'])
            self.assertIsNone(result['rotation_deg'])


class PoseArtifactTests(unittest.TestCase):
    def setUp(self):
        self.pose = importlib.import_module('ring_first_3d.sift_comparison.pose_metrics')
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.case = 'synthetic_frozen_case'
        self.root = self.base / self.case
        self.common = self.root / 'common'
        for path in [self.common, self.root / 'R', self.root / 'S']:
            path.mkdir(parents=True)
        self.patch = patch.object(run, 'BASE', self.base)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        run.save(self.common / 'meta.json', {'frames': [dict(id=f'frame_{i}', raw_frame=100 + 3*i) for i in range(5)]})
        run.save(self.common / 'TUPLES_FROZEN.json', {'tuples': [
            dict(tag='B_target_0', reference=0, sources=[1, 2, 3]),
            dict(tag='B_target_1', reference=1, sources=[0, 2, 3])]})
        run.save(self.common / 'INPUT_MANIFEST.json', {'frozen_inputs': {
            str(p): run.sha(p) for p in self.common.glob('*.json')}})
        for arm, passed in [('R', [0, 1, 2]), ('S', [1, 2, 4])]:
            run.save(self.root / arm / 'RGB_CHECKS.json', [dict(frame=i, passed=i in passed) for i in range(5)])
        self.r = np.array([camera((i, 0, 0)) for i in range(5)])
        self.s = self.r.copy()
        self.freeze()

    def freeze(self):
        sim = dict(status='FROZEN', scale=2, rotation=camera(angle=90)[:3, :3].tolist(),
                   translation=[10, 20, 30])
        # Nontrivial frozen alignment: raw S is not already in R coordinates.
        raw_s = self.s.copy()
        rot = np.array(sim['rotation'])
        raw_s[:, :3, :3] = rot.T @ self.s[:, :3, :3]
        raw_s[:, :3, 3] = (self.s[:, :3, 3] - sim['translation']) @ rot / sim['scale']
        np.savez(self.root / 'R/cameras.npz', c2w=self.r)
        np.savez(self.root / 'S/cameras.npz', c2w=raw_s)
        np.savez(self.root / 'S/cameras_normalized.npz', c2w=transform_cameras(raw_s, sim))
        sim['camera_hashes'] = {a: run.sha(self.root / a / 'cameras.npz') for a in ['R', 'S']}
        run.save(self.root / 'NORMALIZATION_FROZEN.json', sim)

    def test_frozen_alignment_subsets_raw_ids_and_six_directed_roles(self):
        self.s[:, 1, 3] = [0, 1, 2, 3, 4]
        self.freeze()
        result = self.pose.evaluate_pose(self.case)
        self.assertEqual(len(result['per_frame']), 5)
        self.assertEqual(result['per_frame'][2]['raw_frame'], 106)
        self.assertEqual(result['per_frame'][2]['frame_id'], 'frame_2')
        all_frames = result['summary']['all_common']
        self.assertEqual((all_frames['count'], all_frames['total']), (5, 5))
        self.assertEqual(all_frames['position_norm']['median'], 2)
        self.assertAlmostEqual(all_frames['position_norm']['P95'], 3.8)
        self.assertEqual(all_frames['position_norm']['max'], 4)
        self.assertEqual(result['summary']['common_rgb_pass']['frame_ids'], [1, 2])
        self.assertEqual(result['summary']['frozen_hero_union']['frame_ids'], [0, 1, 2, 3])
        roles = result['role_pose_differences']
        self.assertEqual((roles['count'], roles['total']), (6, 6))
        self.assertEqual(roles['per_role'][0]['target_raw_frame'], 100)
        self.assertEqual(roles['per_role'][3]['target_raw_frame'], 103)
        self.assertEqual(roles['per_role'][3]['support_raw_frame'], 100)
        self.assertEqual(json.loads((self.root / 'POSE_DIFFERENCES.json').read_text()), result)
        self.assertEqual(json.loads((self.root / 'ROLE_POSE_DIFFERENCES.json').read_text()), roles)

    def test_missing_poses_preserve_subset_and_role_denominators(self):
        self.s[2] = np.nan
        self.freeze()
        result = self.pose.evaluate_pose(self.case)
        self.assertEqual(result['per_frame'][2]['status'], 'NOT_EVALUABLE')
        self.assertEqual((result['summary']['all_common']['count'], result['summary']['all_common']['total']), (4, 5))
        self.assertEqual((result['summary']['frozen_hero_union']['count'], result['summary']['frozen_hero_union']['total']), (3, 4))
        self.assertEqual((result['role_pose_differences']['count'], result['role_pose_differences']['total']), (4, 6))

    def test_missing_alignment_or_camera_files_preserves_all_rows(self):
        for relative in ['NORMALIZATION_FROZEN.json', 'R/cameras.npz', 'S/cameras.npz', 'S/cameras_normalized.npz']:
            with self.subTest(relative=relative):
                self.freeze()
                (self.root / relative).unlink()
                result = self.pose.evaluate_pose(self.case)
                self.assertEqual(result['status'], 'NOT_EVALUABLE')
                self.assertEqual((result['summary']['all_common']['count'], result['summary']['all_common']['total']), (0, 5))
                self.assertEqual(len(result['role_pose_differences']['per_role']), 6)
                self.assertIsNone(result['summary']['all_common']['position_norm']['median'])

    def test_changed_camera_hash_or_normalized_transform_is_refused(self):
        self.r[0, 0, 3] = 99
        np.savez(self.root / 'R/cameras.npz', c2w=self.r)
        with self.assertRaisesRegex(ValueError, 'NORMALIZATION_CAMERA_DRIFT'):
            self.pose.evaluate_pose(self.case)
        self.freeze()
        changed = self.s.copy()
        changed[0, 0, 3] += 1
        np.savez(self.root / 'S/cameras_normalized.npz', c2w=changed)
        with self.assertRaisesRegex(ValueError, 'NORMALIZED_CAMERA_DRIFT'):
            self.pose.evaluate_pose(self.case)

