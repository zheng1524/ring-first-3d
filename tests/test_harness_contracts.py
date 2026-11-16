import unittest
import numpy as np
from ring_first_3d.contracts.coordinates import (ellipse_coordinates, resize_intrinsics, w2c,
    convert_units, validate_ring, project, unproject, z_to_range)
from ring_first_3d.contracts.identities import validate_split, verify_assets
from ring_first_3d.views.selection import select_views


class CoordinateTests(unittest.TestCase):
    def test_dxy_rotated_basis(self):
        center = [17, 23];basis = np.array([[0, -3], [7, 0]])
        local = np.array([[1, 0], [0, 1], [.3, .4]])
        uv = local @ basis.T + center
        np.testing.assert_allclose(ellipse_coordinates(uv, center, basis), local, atol=1e-14)
        with self.assertRaises(ValueError):
            ellipse_coordinates(uv, center, np.zeros((2, 2)))

    def test_half_pixel_intrinsics(self):
        K = np.array([[800., 0, 319.5], [0, 810, 179.5], [0, 0, 1]])
        scaled = resize_intrinsics(K, (640, 360), (320, 180))
        self.assertEqual(scaled[0, 2], 159.5)
        ray = np.array([.1, -.2, 1.]);p = K @ ray;ps = scaled @ ray
        np.testing.assert_allclose(ps[:2], (p[:2]+.5)*.5-.5)

    def test_c2w_and_roundtrip(self):
        T = np.array([[0., -1, 0, 12], [1, 0, 0, -9], [0, 0, 1, 5], [0, 0, 0, 1]])
        np.testing.assert_allclose(w2c(T) @ T, np.eye(4))
        K = np.array([[800., 0, 319.5], [0, 800, 179.5], [0, 0, 1]])
        uv = np.array([[0., 0], [319.5, 179.5], [639, 359]])
        X = unproject(uv, np.array([10., 20, 30]), K, T)
        out, z = project(X, K, T)
        np.testing.assert_allclose(out, uv, atol=1e-12)
        np.testing.assert_allclose(z, [10, 20, 30])
        bad = T.copy();bad[0, 0] = 2
        with self.assertRaises(ValueError):w2c(bad)

    def test_mm_m(self):
        np.testing.assert_allclose(convert_units([1, 20, 1000], "mm", "m"), [.001, .02, 1])
        with self.assertRaises(ValueError):convert_units([1], "unknown", "mm")

    def test_ring_units(self):
        V = np.array([[5, 0, 0], [6.2, 0, 0], [5.6, 0, .6], [5.6, 0, -.6]])
        validate_ring(V, 10)
        with self.assertRaises(ValueError):validate_ring(V/1000, 10)

    def test_axial_z_not_range(self):
        K = np.eye(3);uv = np.array([[0., 0], [3, 4]])
        np.testing.assert_allclose(z_to_range(uv, [2, 2], K), [2, 2*np.sqrt(26)])


class BoundaryTests(unittest.TestCase):
    def test_fit_holdout_and_duplicate_rejection(self):
        with self.assertRaises(ValueError):validate_split([dict(id="a", role="FIT")], ["a"])
        with self.assertRaises(ValueError):validate_split([dict(id="a", role="HOLDOUT")])
        with self.assertRaises(ValueError):validate_split([dict(id="a", role="FIT")]*2)

    def test_missing_and_hash_mismatch(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        with TemporaryDirectory() as d:
            p = Path(d)/"asset";p.write_text("changed")
            with self.assertRaises(ValueError):verify_assets({str(p):dict(bytes=7, sha256="0"*64)})

    def test_strategy_identity_and_partitions(self):
        views = [dict(id="a", role="FIT", video="004", direction=[1, 0, 0])]
        with self.assertRaises(ValueError):select_views(views, strategy="mixed")
        with self.assertRaises(ValueError):select_views(views, strategy="direction_quota")
        with self.assertRaises(ValueError):select_views(views, max_views=9)

    def test_historical_source_tampering(self):
        import os
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        from ring_first_3d._legacy import LOCK, source
        with TemporaryDirectory() as d:
            p = Path(d)/LOCK["sources"]["T24"]["path"];p.parent.mkdir(parents=True);p.write_text("altered core")
            with patch.dict(os.environ, RING_FIRST_SOURCE_ROOT=d):
                with self.assertRaises(ValueError):source("T24")

    def test_explicit_duplicate_migration_rejects_conflicts(self):
        from ring_first_3d.views.selection import collapse_exact_duplicates
        v=dict(id="a",role="FIT",video="004")
        _,_,audit=collapse_exact_duplicates([v,v],np.array([[True],[True]]))
        self.assertEqual(len(audit),1)
        with self.assertRaises(ValueError):collapse_exact_duplicates([v,v],np.array([[True],[False]]))
        with self.assertRaises(ValueError):collapse_exact_duplicates([v,dict(v,video="005")],np.array([[True],[True]]))


if __name__ == "__main__":
    unittest.main()
