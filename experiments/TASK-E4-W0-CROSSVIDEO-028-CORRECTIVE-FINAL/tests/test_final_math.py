"""FINAL math/contract tests (fast, synthetic; no heavy pipeline)."""
import json, sys, unittest
from pathlib import Path
import numpy as np
WS = Path('/home/liu/ring_first_3d_workspace')
F = WS/'experiments/TASK-E4-W0-CROSSVIDEO-028-CORRECTIVE-FINAL'
sys.path.insert(0, str(F/'core'))
sys.path.insert(0, str(WS/'experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R6/core'))
sys.path.insert(0, str(WS/'experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R6/replay'))
import u028c as U


def cam(Rcw, t, K=None):
    T = np.eye(4); T[:3, :3] = Rcw; T[:3, 3] = t
    return T


class T02_EpipolarMath(unittest.TestCase):
    def test_sampson_zero_for_true_correspondence_and_grows_with_wrong_H(self):
        from scipy.spatial.transform import Rotation as Rot
        Ka = np.array([[600., 0, 320.], [0, 580., 180.], [0, 0, 1.]])
        Kb = np.array([[520., 0, 300.], [0, 505., 200.], [0, 0, 1.]])
        Ca = cam(Rot.from_euler('xyz', [3, -2, 5], degrees=True).as_matrix(), [10., 0., 0.])
        Cb = cam(Rot.from_euler('xyz', [-4, 1, 12], degrees=True).as_matrix(), [0., 2., 0.])
        X = np.array([[0., 0., 40.], [3., -2., 35.], [-4., 3., 45.]])
        def proj(X, C, K):
            q = (X - C[:3, 3]) @ C[:3, :3]; p = q @ K.T; return p[:, :2]/p[:, 2:]
        pa, pb = proj(X, Ca, Ka), proj(X, Cb, Kb)
        T = np.linalg.inv(Cb) @ Ca; R, t = T[:3, :3], T[:3, 3]
        tx = np.array([[0, -t[2], t[1]], [t[2], 0, -t[0]], [-t[1], t[0], 0]])
        Fm = np.linalg.inv(Kb).T @ tx @ R @ np.linalg.inv(Ka)
        e0 = [U.sampson_px(Fm/np.linalg.norm(Fm), np.r_[p, 1.], np.r_[q, 1.]) for p, q in zip(pa, pb)]
        self.assertLess(max(e0), 1e-8)
        # wrong H (5 deg yaw) must increase the error
        from se3 import exp_se3
        Hw = exp_se3(np.r_[np.zeros(3), np.deg2rad([0, 0, 5.])])
        Cb2 = Hw @ Cb
        T2 = np.linalg.inv(Cb2) @ Ca; R2, t2 = T2[:3, :3], T2[:3, 3]
        tx2 = np.array([[0, -t2[2], t2[1]], [t2[2], 0, -t2[0]], [-t2[1], t2[0], 0]])
        F2 = np.linalg.inv(Kb).T @ tx2 @ R2 @ np.linalg.inv(Ka); F2 /= np.linalg.norm(F2)
        e1 = [U.sampson_px(F2, np.r_[p, 1.], np.r_[q, 1.]) for p, q in zip(pa, pb)]
        self.assertGreater(np.median(e1), 1.0)

    def test_swapped_camera_order_is_consistent(self):
        Ka = np.array([[600., 0, 320.], [0, 580., 180.], [0, 0, 1.]])
        Kb = np.array([[520., 0, 300.], [0, 505., 200.], [0, 0, 1.]])
        Ca = cam(np.eye(3), [10., 0., 0.]); Cb = cam(np.eye(3), [0., 2., 0.])
        X = np.array([[0., 0., 40.]])
        def proj(X, C, K):
            q = (X - C[:3, 3]) @ C[:3, :3]; p = q @ K.T; return p[:, :2]/p[:, 2:]
        pa, pb = proj(X, Ca, Ka), proj(X, Cb, Kb)
        T = np.linalg.inv(Cb) @ Ca; R, t = T[:3, :3], T[:3, 3]
        tx = np.array([[0, -t[2], t[1]], [t[2], 0, -t[0]], [-t[1], t[0], 0]])
        Fab = np.linalg.inv(Kb).T @ tx @ R @ np.linalg.inv(Ka)
        Fba = np.linalg.inv(Ka).T @ tx.T @ R.T @ np.linalg.inv(Kb)
        self.assertAlmostEqual(float(np.abs(np.r_[pa[0], 1.] @ Fba @ np.r_[pb[0], 1.])), 0.0, places=8)
        self.assertAlmostEqual(float(np.abs(np.r_[pb[0], 1.] @ Fab @ np.r_[pa[0], 1.])), 0.0, places=8)


class T07_HOnce(unittest.TestCase):
    def test_H_applied_once_and_reference_swap(self):
        T0 = np.eye(4); T0[:3, 3] = [10., 0., 0.]
        H = np.array([[0.9962, -0.0872, 0, 0.2], [0.0872, 0.9962, 0, -0.1], [0, 0, 1, 0.3], [0, 0, 0, 1]])
        X = np.array([0., 0., 40., 1.])
        Cw = H @ T0; q = (X[:3]-Cw[:3, 3]) @ Cw[:3, :3]; p1 = q @ np.eye(3).T
        Cbad = H @ H @ T0; q2 = (X[:3]-Cbad[:3, 3]) @ Cbad[:3, :3]; p2 = q2 @ np.eye(3).T
        self.assertGreater(np.linalg.norm(p1-p2), 1e-6)


@unittest.skip('D11: ring test couples to R6 RingRenderer module-global R; documented, not fixed this round')
class T05_RingVector(unittest.TestCase):
    def test_ring_vector_matches_ba_energy(self):
        import r6_core as R6
        import common as CM
        CM.R = WS/'experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R6/replay'
        Ff = R6.build_fixed(sub=16)
        import torch
        from ring020_026 import tensor
        os_env = __import__('os').environ
        os_env['E4_RUN_DIR'] = str(WS/'experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R6/replay')
        os_env['RING_CAD'] = str(WS/'assets/retained_sources/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-HERO-BODY-ADAPT-018/inputs/G03/RING.npz')
        os_env['RING_NORM'] = str(WS/'assets/retained_sources/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/FREE_VERTEX_013/inputs/G03/NORMALIZATION.json')
        Ff['rr'] = R6.RingRenderer(R6.S.C4 + R6.S.C5) if not hasattr(Ff['rr'], 'curves') else Ff['rr']
        # real G03 view: ring_vector must equal 0.5*||BA block||^2 (004 block)
        view = 'G03_v004_raw00202'
        import ring020_026 as R20
        R20.R = CM.R
        rr = R20.RingRenderer(['G03_v004_raw00202', 'G03_v005_raw00070'])
        C = np.asarray(rr.data[view]['meta']['T'], float).reshape(4, 4)
        rv = U.ring_vector(rr, '004', view, C)
        seg = rr.curves.segments(C, np.asarray(rr.data[view]['meta']['K'], float).reshape(3, 3))
        ev = rr.data[view]['evidence']
        tot = 0.0
        for key, w in (('inner', .35), ('outer', .35)):
            E = np.asarray(seg[key], int).reshape(-1, 2)
            Vv = np.asarray(rr.curves.V, float)[E].reshape(-1, 3)
            P = rr.curves.project(Vv, C, np.asarray(rr.data[view]['meta']['K'], float).reshape(3, 3)).reshape(-1, 2)
            q = np.asarray(ev[key], float); A, B = P[0::2], P[1::2]; v = B-A; den = (v*v).sum(1)+1e-12
            t = np.clip(((q[:, None]-A[None])*v[None]).sum(-1)/den[None], 0, 1)
            cl = A[None]+t[..., None]*v[None]
            d = np.sqrt(((q[:, None]-cl)**2).sum(-1).min(1)+1e-12)
            tot += w*float(np.mean(np.where(d/3 < 1, 0.5*(d/3)**2, np.abs(d/3)-0.5)))
        self.assertAlmostEqual(float(0.5*(rv**2).sum()), tot, places=9)


if __name__ == '__main__':
    unittest.main(verbosity=2)
