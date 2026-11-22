"""Before/after tests for the four confirmed 026 defects (non-trivial numeric assertions)."""
import json, os, sys, unittest
from pathlib import Path
import numpy as np, torch
WS = Path('/home/liu/ring_first_3d_workspace')
K = WS/'experiments/TASK-E4-W0-CROSSVIDEO-026-CORRECTIVE'
R26 = WS/'experiments/TASK-E4-W0-CROSSVIDEO-026-RING-GEOMETRY-AND-UNCERTAINTY/replay_020/runs'
sys.path.insert(0, str(K/'replay')); sys.path.insert(0, str(K/'core'))
os.environ.update(E4_RUN_DIR=str(K/'replay'),
    RING_CAD=str(WS/'assets/retained_sources/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-HERO-BODY-ADAPT-018/inputs/G03/RING.npz'),
    RING_NORM=str(WS/'assets/retained_sources/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/FREE_VERTEX_013/inputs/G03/NORMALIZATION.json'))
views = {v['id']: v for v in json.loads((K/'replay'/'config'/'VIEWS.json').read_text())}
V5 = sorted(k for k in views if views[k]['video'] == '005')[0]


class TestCenterline(unittest.TestCase):
    def test_old_adapter_is_wrong_and_new_is_distinct(self):
        old = json.loads((R26/'ring'/(V5+'.json')).read_text())
        new = json.loads((K/'replay'/'ring_corrective'/(V5+'.json')).read_text())
        self.assertEqual(old['centerline'], old['inner'])          # reproduces the defect
        self.assertNotEqual(new['centerline'], new['inner'])       # fixed source
        d = abs(new['centerline']['major_radius']-new['inner']['major_radius'])
        self.assertGreater(d, 0.5, 'real centerline must differ materially from inner')


class TestSE3Composition(unittest.TestCase):
    def test_increment_equals_direct_camera(self):
        from ring020_026 import RingRenderer, tensor
        rr = RingRenderer([V5]); d = rr.data[V5]; T = np.asarray(d['meta']['T'], float)
        inc = np.eye(4); inc[:3, 3] = [0.4, -0.2, 0.1]; inc[:3, :3] = np.array([[1, 0, 0], [0, np.cos(.01), -np.sin(.01)], [0, np.sin(.01), np.cos(.01)]])
        d['T'] = tensor(T, torch.float64); La = rr.losses(tensor(inc, torch.float64), V5)[0]
        d['T'] = tensor(inc @ T, torch.float64); Lb = rr.losses(tensor(np.eye(4), torch.float64), V5)[0]
        d['T'] = tensor(T, torch.float64)
        delta = max(abs(float(La[k])-float(Lb[k])) for k in ('M', 'I', 'O'))
        self.assertLess(delta, 1e-3, f'increment semantics broken: {delta}')
        # the OLD bug passed H@T as the increment -> camera H@T@T, materially different
        d['T'] = tensor(inc @ T, torch.float64); Lc = rr.losses(tensor(inc, torch.float64), V5)[0]
        d['T'] = tensor(T, torch.float64)
        self.assertGreater(abs(float(Lc['I'])-float(La['I'])), 0.05, 'old double-application not detectable')


class TestPerturbationDirection(unittest.TestCase):
    def test_world_ring_axis_rotation_is_symmetric(self):
        from ring020_026 import RingRenderer, tensor
        from se3 import exp_se3
        rr = RingRenderer([V5]); T = np.asarray(rr.data[V5]['meta']['T'], float)
        base = float(rr.losses(tensor(np.eye(4), torch.float64), V5)[0]['I'])
        w = np.zeros(6); w[5] = np.deg2rad(15.0)
        correct = float(rr.losses(tensor(exp_se3(w), torch.float64), V5)[0]['I'])
        old = float(rr.losses(tensor(np.linalg.inv(T) @ exp_se3(w) @ T, torch.float64), V5)[0]['I'])
        self.assertLess(abs(correct-base)/base, 1e-3, 'world Ring-axis rotation must be symmetric')
        self.assertGreater(abs(old-base), 0.5, 'old conjugated increment is materially wrong')


class TestTrackIdentity(unittest.TestCase):
    def test_stable_keys_vs_row_index(self):
        L = R26/'landmarks'
        Xb = np.load(L/'REL_BASE_005.npz')['X']; Xp = np.load(L/'REL_005_independent_0.5_0.0.npz')['X']
        Ob = json.loads((L/'REL_BASE_005_OBSERVATIONS.json').read_text()); Op = json.loads((L/'REL_005_independent_0.5_0.0_OBSERVATIONS.json').read_text())
        kb = {tuple(sorted((x['view'], int(x['feature_id'])) for x in o['observations'])): i for i, o in enumerate(Ob)}
        kp = {tuple(sorted((x['view'], int(x['feature_id'])) for x in o['observations'])): i for i, o in enumerate(Op)}
        common = sorted(set(kb) & set(kp))
        dk = np.median([np.linalg.norm(Xp[kp[k]]-Xb[kb[k]]) for k in common])
        n = min(len(Xp), len(Xb)); dr = np.median(np.linalg.norm(Xp[:n]-Xb[:n], axis=1))
        self.assertLess(dk, 5.0); self.assertGreater(dr, 2.0)
        self.assertGreater(abs(dr-dk), 1.0, 'row-index and stable-key results must differ')


if __name__ == '__main__':
    unittest.main(verbosity=2)
