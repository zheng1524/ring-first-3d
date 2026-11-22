"""P0-C: is the Adam rollback test non-vacuous, and can the optimizer resume?"""
import sys, json, inspect
from pathlib import Path
import numpy as np
C21 = Path('/home/liu/ring_first_3d_workspace/experiments/TASK-E4-W0-CROSSVIDEO-021-CORRECTIVE')
sys.path.insert(0, str(C21/'core')); sys.path.insert(0, '/home/liu/ring_first_3d_workspace/src')
import shared_se3 as S3
K = np.array([[490., 0, 319.5], [0, 490., 179.5], [0, 0, 1.]])


def bad_pairs():
    rng = np.random.default_rng(1)
    return [(np.eye(4), np.eye(4), rng.uniform(0, 640, (40, 2)), rng.uniform(0, 360, (40, 2)))]


def main():
    sig = inspect.signature(S3.optimize)
    q, L, hist, acc = S3.optimize(np.eye(4), {}, bad_pairs(), K, iters=5)
    reasons = sorted({h.get('reason') for h in hist if not h['accepted']})
    out = dict(
        optimize_signature=str(sig),
        has_checkpoint_parameter=('state' in sig.parameters or 'checkpoint' in sig.parameters),
        accepted_steps=acc,
        rollback_assertion_triggered=(acc == 0),
        rejection_reasons=reasons,
        note='test_adam_rejection_restores_state only asserts when accepted_steps==0; here that is %s. '
             'q/m/v are local to optimize() and are never exposed or checkpointed, so resume==uninterrupted '
             'cannot be tested at all (test_resume_equals_uninterrupted runs the same call twice instead).' % (acc == 0),
        resume_test_is_real=False)
    print(json.dumps(out, indent=1))
    Path('/home/liu/ring_first_3d_workspace/experiments/TASK-E4-W0-CROSSVIDEO-022-INDEPENDENT-AUDIT/results/T3_optimizer_state.json').write_text(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
