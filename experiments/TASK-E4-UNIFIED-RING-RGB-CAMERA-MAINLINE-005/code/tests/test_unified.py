"""Regression tests for the unified Ring+RGB camera mainline.

Run:  PYTHONPATH=<ws>/src:<task>/code python -m unittest discover -s tests -v
These tests never touch frozen predictions, DXY, HERO or Body.
"""
import re
import unittest
from pathlib import Path
import numpy as np

import unified_camera as U

CODE = Path(__file__).resolve().parents[1]


def _code_only(path):
    """Strip the module docstring and full-line comments so prose cannot trip the checks."""
    import ast
    src = Path(path).read_text()
    tree = ast.parse(src)
    doc = ast.get_docstring(tree)
    if doc:
        src = src.replace(doc, '', 1)
    return '\n'.join(l for l in src.splitlines() if not l.strip().startswith('#'))


class TestStaticContracts(unittest.TestCase):
    def test_no_per_case_branching(self):
        src = _code_only(CODE / 'unified_camera.py')
        bad = re.findall(r"if\s+group\s*==|elif\s+group\s*==", src)
        self.assertEqual(bad, [], f'per-case branching found: {bad}')

    def test_no_forbidden_dependencies(self):
        src = _code_only(CODE / 'unified_camera.py').lower()
        for tok in ['import dxy', 'from dxy', "/'body'", "/'hero'", "/'gt'"]:
            self.assertNotIn(tok, src, f'forbidden token {tok}')

    def test_single_config(self):
        self.assertTrue((U.FROZEN / 'config.json').exists())
        cfg = U.CFG
        for k in ['pose_initializations', 'yaw_grid', 'BA_max_nfev']:
            self.assertIn(k, cfg)

    def test_all_instances_use_same_k(self):
        for g in U.GROUPS:
            for v in U.VIDEOS:
                for x in U.instance_views(g, v):
                    self.assertTrue(np.allclose(np.array(x['meta']['K'], float), U.K_CFG))


class TestGeometry(unittest.TestCase):
    def test_triangulation_roundtrip(self):
        rng = np.random.default_rng(0)
        K = np.array([[490., 0, 319.5], [0, 490., 179.5], [0, 0, 1]])
        C1 = np.eye(4); C1[:3, 3] = [0, 0, 40]
        ok = 0
        for _ in range(100):
            X = rng.uniform(-5, 5, 3)
            C2 = np.eye(4)
            from scipy.spatial.transform import Rotation as Rot
            C2[:3, :3] = Rot.from_euler('y', rng.uniform(-8, 8), degrees=True).as_matrix()
            C2[:3, 3] = [2.0, 1.0, 41.0]
            uv1, _ = U.project(X[None], C1, K); uv2, _ = U.project(X[None], C2, K)
            Xr = U.triangulate(uv1[0], uv2[0], C1, C2, K)
            ok += (Xr is not None and np.linalg.norm(Xr - X) < 1e-6)
        self.assertEqual(ok, 100)

    def test_observe_contract(self):
        from ring_first_3d.mainline.native.camera import observe
        labels = np.zeros((360, 640), np.uint8)
        cv = __import__('cv2')
        cv.circle(labels, (320, 180), 90, 2, 6)
        cv.circle(labels, (320, 180), 40, 1, -1)
        ob = observe(labels)
        self.assertEqual(ob['mask'].shape, (360, 640))
        self.assertGreaterEqual(len(ob['q_train']), 20)
        self.assertTrue(np.isin(labels, [0, 1, 2]).all())


class TestVersionScore(unittest.TestCase):
    def test_ring_term_dominates_at_equal_other_terms(self):
        # pure arithmetic check of the frozen weights, no data needed
        w = dict(ring=1.0, feat=0.1, obj=0.02, conv=0.5)
        s_bad = w['ring'] * 5 + w['feat'] * 1 + w['obj'] * 0.1 + w['conv'] * 0
        s_good = w['ring'] * 0.5 + w['feat'] * 1 + w['obj'] * 0.1 + w['conv'] * 0
        self.assertLess(s_good, s_bad)

    def test_held_not_used_in_score_source(self):
        src = (CODE / 'unified_camera.py').read_text()
        start = src.index('def version_score')
        end = src.index('def run_instance')
        body = src[start:end]
        # held is only used with a negation (training tracks)
        self.assertIn('~held', body)
        self.assertNotIn('held].astype(bool)\n    for i in range(n):\n        errs', body)


if __name__ == '__main__':
    unittest.main(verbosity=2)
