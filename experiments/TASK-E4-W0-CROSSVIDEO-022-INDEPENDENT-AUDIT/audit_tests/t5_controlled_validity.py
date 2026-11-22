"""S3: do the 021 controlled experiments actually embed their ground truth?"""
import sys, json
from pathlib import Path
import numpy as np
C21 = Path('/home/liu/ring_first_3d_workspace/experiments/TASK-E4-W0-CROSSVIDEO-021-CORRECTIVE')
sys.path.insert(0, str(C21/'core')); sys.path.insert(0, '/home/liu/ring_first_3d_workspace/src')
import shared_se3 as S3, yaw_1dof as Y1
from ring_first_3d.mainline.native.camera import torus_contours
K = np.array([[490., 0, 319.5], [0, 490., 179.5], [0, 0, 1.]])


def main():
    # A2: observations are generated at the IDENTITY pose; H_true is only used in the metric
    C4 = np.eye(4); C4[:3, :3] = np.diag([1., -1., -1.]); C4[:3, 3] = [20., 0., 40.]
    pts = np.asarray(torus_contours(C4, K)[0], float)
    ring = {'v': dict(C=C4, pts=pts)}
    L0 = S3.ring_term(np.eye(4), ring, K)
    q, L, _, _ = S3.optimize(np.eye(4), ring, [], K, iters=150)
    H = S3.pose_from_q(q, np.eye(4))
    Htrue = np.eye(4); Htrue[:3, 3] = [0.25, -0.15, 0.1]
    t_mm, _ = S3.delta_size(H @ np.linalg.inv(Htrue))
    # A6: both the camera AND the observations are rotated by the same yaw
    yy = np.eye(4); th = np.deg2rad(40.); c, s = np.cos(th), np.sin(th)
    yy[:3, :3] = [[c, -s, 0], [s, c, 0], [0, 0, 1]]
    Cc = yy @ C4
    L_rot = S3.ring_term(np.eye(4), {'v': dict(C=Cc, pts=np.asarray(torus_contours(Cc, K)[0], float))}, K)
    out = dict(
        A2=dict(loss_at_identity=L0, loss_after_optimisation=L,
                estimated_correction_vs_Htrue_mm=t_mm,
                verdict='INVALID_TEST: observations are generated at the identity pose, so the optimum is q=0; '
                        'the reported 0.008 mm is ||H_true|| residual, not recovery. There is no signal for H_true '
                        'in the data.'),
        A6=dict(loss_identity=L0, loss_after_rotating_camera_and_observations=L_rot,
                verdict='INVALID_TEST: rotating the camera AND regenerating its observations makes invariance '
                        'true by construction (equivariance check), it does not test yaw identifiability. '
                        'A valid test must keep the observations fixed and vary only the model.'))
    print(json.dumps(out, indent=1))
    Path(C21.parent/'TASK-E4-W0-CROSSVIDEO-022-INDEPENDENT-AUDIT'/'results'/'T5_controlled_validity.json').write_text(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
