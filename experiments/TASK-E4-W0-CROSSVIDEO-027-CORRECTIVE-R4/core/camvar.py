"""Explicit camera variable management (027-CORRECTIVE D1 fix).

Three disjoint sets, keyed by REAL camera ids:
  FROZEN   : never touched by the optimizer (all 005 FIT + the 004 anchor)
  ANCHOR   : the single 004 FIT camera whose local delta is fixed at zero (H carries the video placement)
  RELEASED : the remaining 004 FIT cameras (small local correction)
"""
import numpy as np


class CameraVariables:
    def __init__(self, cams, anchor_id, released_ids):
        assert anchor_id in cams, f'anchor {anchor_id} not a camera id'
        released = sorted(set(released_ids) - {anchor_id})
        for c in released:
            assert c in cams, f'released {c} not a camera id'
        frozen = sorted(set(cams) - set(released))
        assert anchor_id in frozen, 'anchor must be frozen'
        assert not (set(released) & set(frozen))
        self.cams = cams
        self.anchor = anchor_id
        self.released = released
        self.frozen = frozen
        self.index = {c: 6 + 6*i for i, c in enumerate(released)}
        self.n = 6 + 6*len(released)

    def dim(self, n_lm):
        return self.n + 3*n_lm

    def unpack(self, theta, H0, n_lm):
        from se3 import exp_se3
        theta = np.asarray(theta, float)
        assert len(theta) == self.dim(n_lm), f'theta {len(theta)} != dim {self.dim(n_lm)}'
        H = exp_se3(theta[:6]) @ H0
        dx = {c: np.zeros(6) for c in self.cams}
        for c in self.released:
            dx[c] = theta[self.index[c]:self.index[c]+6]
        X = theta[self.n:].reshape(-1, 3)
        return H, dx, X
