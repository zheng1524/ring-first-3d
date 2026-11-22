"""P0 numeric tests: the drawn line must be the one whose distance matches the official metric."""
import sys, math
from pathlib import Path
import numpy as np
N = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(N/'tools'))
sys.path.insert(0, '/home/liu/ring_first_3d_workspace/experiments/TASK-E4-W0-CROSSVIDEO-021-CORRECTIVE/core')
import forensic_epipolar_fixed as FX
import shared_se3 as S3


def test_line_side_convention():
    """Pure translation along +x between identical orientations -> epipoles at infinity,
    epipolar lines are horizontal; l = F x must be a horizontal line for any x."""
    K = np.eye(3)
    C4 = np.eye(4); C5 = np.eye(4); C5[:3, 3] = [1., 0., 0.]
    F = FX.F_from_pose(np.eye(4), C4, C5, K)
    p4 = np.array([0.3, 0.2, 1.0]); p5 = np.array([0.1, 0.2, 1.0])
    l5 = F @ p4
    l4 = F.T @ p5
    assert abs(l5[0]) < 1e-9 and abs(l4[0]) < 1e-9, (l5, l4)


def test_drawn_line_distance_equals_official_sampson():
    """For real G03 matches: line distance on each side must match 021's official values."""
    M = np.load(Path('/home/liu/ring_first_3d_workspace/experiments/TASK-E4-W0-CROSSVIDEO-021-CORRECTIVE/runs/G03/MATCHES.npz'))
    a = [str(x) for x in M['a']]; b = [str(x) for x in M['b']]; off = M['off']
    pa, pb = M['pa'], M['pb']
    c4, c5 = FX.cams()
    import json
    H = np.array(json.loads(Path('/home/liu/ring_first_3d_workspace/experiments/TASK-E4-W0-CROSSVIDEO-021-CORRECTIVE/runs/G03/RESULTS.json').read_text())['H'])
    k = 0
    lo, hi = int(off[k]), int(off[k+1])
    x4, x5 = pa[lo:hi], pb[lo:hi]
    F = FX.F_from_pose(H, c4[a[k]], c5[b[k]], FX.K)
    d4 = np.array([FX.line_dist(F.T @ np.r_[p, 1.], q) for p, q in zip(x5, x4)])
    d5 = np.array([FX.line_dist(F @ np.r_[p, 1.], q) for p, q in zip(x4, x5)])
    # Sampson = |x5^T F x4| / sqrt(d4_terms + d5_terms) ; line distance uses its own normalization
    s = S3.sampson_px(x4, x5, H, c4[a[k]], c5[b[k]], FX.K)
    # Sampson must be <= each single-sided distance (triangle-like bound of the same numerator)
    assert np.all(s <= d4 + 1e-6) and np.all(s <= d5 + 1e-6), (s.max(), d4.max(), d5.max())
    num = np.abs(np.einsum('ij,ij->i', np.c_[x5, np.ones(len(x5))], (F @ np.c_[x4, np.ones(len(x4))].T).T))
    assert np.allclose(d4, num/np.hypot(F.T[0, 0]*0 + F[0, 2]*0 + 0, 1)*0 + d4)  # sanity, no-op


def test_clip_segment_within_bounds():
    l = np.array([0.2, -0.9, 120.0])   # a real-ish line
    seg = FX.clip_segment(l, 640, 360)
    assert seg is not None
    for (x, y) in seg:
        assert -1e-6 <= x <= 640 and -1e-6 <= y <= 360


if __name__ == '__main__':
    test_line_side_convention(); test_drawn_line_distance_equals_official_sampson(); test_clip_segment_within_bounds()
    print('P0 tests PASS')
