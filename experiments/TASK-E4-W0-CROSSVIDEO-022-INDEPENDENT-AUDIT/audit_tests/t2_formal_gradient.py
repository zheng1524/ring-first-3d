"""M2: finite-difference gradient of the FORMAL objective, and whether any autograd validates it."""
import sys, json
from pathlib import Path
import numpy as np
C21 = Path('/home/liu/ring_first_3d_workspace/experiments/TASK-E4-W0-CROSSVIDEO-021-CORRECTIVE')
sys.path.insert(0, str(C21/'core')); sys.path.insert(0, '/home/liu/ring_first_3d_workspace/src')
import shared_se3 as S3
K = np.array([[490., 0, 319.5], [0, 490., 179.5], [0, 0, 1.]])


def make():
    rng = np.random.default_rng(1)
    C4 = np.eye(4); C4[:3, :3] = np.diag([1., -1., -1.]); C4[:3, 3] = [15., 0., 40.]
    C5 = np.eye(4); C5[:3, :3] = np.diag([1., -1., -1.]); C5[:3, 3] = [-15., 4., 41.]
    X = np.c_[rng.uniform(-4, 4, 60), rng.uniform(-4, 4, 60), rng.uniform(-3, 3, 60)]
    def proj(C):
        q = (X - C[:3, 3]) @ C[:3, :3]; p = q @ K.T; return p[:, :2] / p[:, 2:]
    return C4, C5, proj(C4), proj(C5)


def main():
    C4, C5, u4, u5 = make()
    pairs = [(C4, C5, u4, u5)]
    q0 = np.array([0.02, -0.01, 0.03, 0.01, 0.02, -0.01])
    h = 1e-6
    g = np.zeros(6)
    for k in range(6):
        qp = q0.copy(); qp[k] += h
        qm = q0.copy(); qm[k] -= h
        g[k] = (S3.objective(qp, np.eye(4), {}, pairs, K)[0] - S3.objective(qm, np.eye(4), {}, pairs, K)[0]) / (2 * h)
    Ld = S3.objective(q0 - 1e-4 * g, np.eye(4), {}, pairs, K)[0]
    L0 = S3.objective(q0, np.eye(4), {}, pairs, K)[0]
    out = dict(fd_gradient=g.tolist(), grad_norm=float(np.linalg.norm(g)),
               L_at_q0=L0, L_after_descent_step=Ld, descent=bool(Ld < L0),
               validated_by_autograd=False,
               note='the shipped torch_objective.py is a DIFFERENT function (no Ring term, no 0.02 EPI weight); '
                    'no autograd validates this formal objective. The optimizer itself uses the same FD stencil, '
                    'so a "gradient check" that compares FD with FD is circular.')
    print(json.dumps(out, indent=1))
    Path('/home/liu/ring_first_3d_workspace/experiments/TASK-E4-W0-CROSSVIDEO-022-INDEPENDENT-AUDIT/results/T2_formal_gradient.json').write_text(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
