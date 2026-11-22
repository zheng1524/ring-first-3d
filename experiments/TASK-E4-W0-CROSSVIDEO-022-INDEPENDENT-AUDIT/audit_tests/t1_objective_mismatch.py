"""P0-A: is torch_objective the same function as shared_se3.objective?
Read-only: imports the pinned 021 modules, computes both on the SAME observations and H."""
import sys, json
from pathlib import Path
import numpy as np
C21 = Path('/home/liu/ring_first_3d_workspace/experiments/TASK-E4-W0-CROSSVIDEO-021-CORRECTIVE')
sys.path.insert(0, str(C21/'core')); sys.path.insert(0, '/home/liu/ring_first_3d_workspace/src')
import torch, shared_se3 as S3, torch_objective as TO
K = np.array([[490., 0, 319.5], [0, 490., 179.5], [0, 0, 1.]])


def make():
    rng = np.random.default_rng(0)
    C4 = np.eye(4); C4[:3, :3] = np.diag([1., -1., -1.]); C4[:3, 3] = [15., 0., 40.]
    C5 = np.eye(4); C5[:3, :3] = np.diag([1., -1., -1.]); C5[:3, 3] = [-15., 4., 41.]
    X = np.c_[rng.uniform(-4, 4, 60), rng.uniform(-4, 4, 60), rng.uniform(-3, 3, 60)]
    def proj(C):
        q = (X - C[:3, 3]) @ C[:3, :3]; p = q @ K.T; return p[:, :2] / p[:, 2:]
    u4 = proj(C4) + rng.normal(0, 1.5, (60, 2)); u5 = proj(C5) + rng.normal(0, 1.5, (60, 2))
    return C4, C5, u4, u5


def main():
    C4, C5, u4, u5 = make()
    seed = np.eye(4)
    # formal objective (EPI + prior only: ring is empty)
    q0 = np.array([0.02, -0.01, 0.03, 0.01, 0.02, -0.01])
    L_formal, parts = S3.objective(q0, seed, {}, [(C4, C5, u4, u5)], K)
    t = lambda x: torch.tensor(x, dtype=torch.float64)
    L_torch = float(TO.epi_prior_loss(t(q0), t(seed), [(t(C4), t(C5), t(u4), t(u5))], t(K)))
    out = dict(formal_total=L_formal, formal_parts={k: (float(v) if isinstance(v, (int, float)) else v) for k, v in parts.items()},
               torch_total=L_torch, abs_diff=abs(L_formal - L_torch),
               formal_has_ring_term=('ring' in parts),
               formal_epi_weight=S3.W_EPI, torch_epi_weight=1.0,
               formal_prior_weight=S3.W_PRIOR, torch_prior_weight=0.01,
               verdict='MISMATCH' if abs(L_formal - L_torch) > 1e-9 else 'IDENTICAL')
    print(json.dumps(out, indent=1))
    Path('/home/liu/ring_first_3d_workspace/experiments/TASK-E4-W0-CROSSVIDEO-022-INDEPENDENT-AUDIT/results/T1_objective_mismatch.json').write_text(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
