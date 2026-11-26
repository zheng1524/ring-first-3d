import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pycolmap

from ring_first_3d.sift_comparison import colmap_arm as arm


class ColmapInterfaceTests(unittest.TestCase):
    def fixture(self, root):
        xy = np.array([[[100, 80], [90, 80], [85, 80]],
                       [[200, 90], [190, 90], [180, 90]],
                       [[300, 70], [295, 70], [290, 70]]], float)
        np.savez(root / 'tracks.npz', xy=xy, held=[False, True, False],
                 category=[0, 1, 0], frame_raw=[10, 30, 50])
        np.savez(root / 'pairs.npz', ij=[[0, 1], [1, 2]],
                 pair0=[[0, 100, 80, 90, 80], [1, 200, 90, 190, 90]],
                 pair1=[[2, 295, 70, 290, 70]])
        (root / 'split.json').write_text(json.dumps(dict(train=[0, 2], validation=[1], test=[])))
        (root / 'ledger.json').write_text(json.dumps([
            dict(id=f'raw_{i:06}', raw_frame=i, RGB_path=str(root/f'{i}.png'),
                 K=[[490, 0, 319.5], [0, 490, 179.5], [0, 0, 1]])
            for i in [10, 30, 50]]))
        return xy

    def test_fixed_intrinsics_in_all_optimization_options(self):
        o = arm.fixed_options()
        self.assertFalse(o.ba_refine_focal_length)
        self.assertFalse(o.ba_refine_principal_point)
        self.assertFalse(o.ba_refine_extra_params)
        self.assertFalse(o.ba_refine_sensor_from_rig)
        self.assertFalse(o.mapper.abs_pose_refine_focal_length)
        self.assertFalse(o.mapper.abs_pose_refine_extra_params)
        self.assertFalse(o.ba_use_gpu)
        self.assertFalse(o.structure_less_registration_fallback)
        self.assertEqual(o.random_seed, 20261126)

    def test_import_keeps_original_edges_and_excludes_held(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            xy = self.fixture(root)
            receipt, maps = arm.import_database(root, root/'database.db')
            self.assertEqual(receipt['training_matches'], 2)
            self.assertEqual([x.tolist() for x in maps], [[0, 2]]*3)
            with sqlite3.connect(root/'database.db') as db:
                rows = db.execute('select image_id, rows, cols, data from keypoints order by image_id').fetchall()
                for i, row in enumerate(rows):
                    points = np.frombuffer(row[3], np.float32).reshape(row[1], row[2])
                    np.testing.assert_allclose(points, xy[[0, 2], i] + .5)
                self.assertEqual(db.execute('select count(*) from matches').fetchone()[0], 2)
                raw = db.execute('select data from matches order by pair_id').fetchall()
                np.testing.assert_array_equal(np.frombuffer(raw[0][0], np.uint32), [0, 0])
                np.testing.assert_array_equal(np.frombuffer(raw[1][0], np.uint32), [1, 1])
                self.assertEqual(db.execute('select count(*) from two_view_geometries').fetchone()[0], 2)

    def test_pixel_center_and_inverse_pose_roundtrip(self):
        rotation = pycolmap.Rotation3d(np.array([.1, -.2, .04]))
        w2c = pycolmap.Rigid3d(rotation, np.array([1., 2., 3.]))
        c2w = arm.c2w_from_cam_from_world(w2c)
        point = np.array([2., 1., 10., 1.])
        cam_point = (np.linalg.inv(c2w) @ point)[:3]
        camera = pycolmap.Camera(model='PINHOLE', width=640, height=360,
                                params=[490, 490, 320, 180])
        colmap_uv = camera.img_from_cam(cam_point)
        opencv_uv = (arm.K @ cam_point)[:2] / cam_point[2]
        np.testing.assert_allclose(colmap_uv-.5, opencv_uv, atol=1e-10)
        np.testing.assert_allclose(c2w[:3, 3], -w2c.rotation.matrix().T @ w2c.translation)
        self.assertAlmostEqual(np.linalg.det(c2w[:3, :3]), 1.)

    def test_import_rejects_changed_track_coordinate(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.fixture(root)
            np.savez(root/'pairs.npz', ij=[[0, 1]], pair0=[[0, 123, 80, 90, 80]])
            with self.assertRaisesRegex(ValueError, 'PAIR_COORDINATE'):
                arm.import_database(root, root/'database.db')

    def test_real_mapper_recovers_fixture_without_images_or_ring_inputs(self):
        # Small interface fixture: known c2w is used only to synthesize observations,
        # never passed to solve(). This is not a scientific accuracy experiment.
        with tempfile.TemporaryDirectory() as td:
            common = Path(td)/'common'
            common.mkdir()
            rng = np.random.default_rng(42)
            points = rng.uniform([-1.5, -1., 8.], [1.5, 1., 12.], (180, 3))
            centers = np.column_stack([np.linspace(-3, 3, 12), np.zeros((12, 2))])
            xyz = points[:, None] - centers[None]
            pixels = xyz @ arm.K.T
            xy = pixels[:, :, :2]/pixels[:, :, 2:]
            np.savez(common/'tracks.npz', xy=xy, category=np.zeros(180, int),
                     held=np.zeros(180, bool), frame_raw=np.arange(12)*10)
            edges, packs = [], {}
            for i in range(12):
                for j in range(i+1, 12):
                    packs[f'pair{len(edges)}'] = np.column_stack([np.arange(180), xy[:,i], xy[:,j]])
                    edges.append([i, j])
            np.savez(common/'pairs.npz', ij=edges, **packs)
            (common/'split.json').write_text(json.dumps(dict(train=list(range(180)), validation=[], test=[])))
            (common/'ledger.json').write_text(json.dumps([
                dict(id=f'raw_{i*10:06}', raw_frame=i*10, RGB_path='NOT_READ', K=arm.K.tolist())
                for i in range(12)]))
            receipt = arm.solve(common, Path(td)/'S')
            self.assertEqual(receipt['status'], 'COMPLETED')
            self.assertEqual(receipt['registered_union_count'], 12)
            self.assertTrue(receipt['components'][0]['fixed_intrinsics_verified'])
            self.assertGreater(receipt['components'][0]['positive_fraction'], .99)
            camera = np.load(Path(td)/'S/cameras.npz')
            np.testing.assert_array_equal(camera['K'], arm.K)
            self.assertEqual(len(camera['point_track_ids']), 180)
            self.assertTrue(np.isfinite(camera['c2w']).all())
            with self.assertRaisesRegex(FileExistsError, 'ALREADY_STARTED'):
                arm.solve(common, Path(td)/'S')


if __name__ == '__main__':
    unittest.main()
