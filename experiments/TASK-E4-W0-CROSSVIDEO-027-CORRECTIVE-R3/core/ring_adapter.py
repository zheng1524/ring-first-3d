"""Single place for Ring evaluation (027-CORRECTIVE D2 fix).

Historical RingRenderer.losses(H_in) computes C_actual = canonical(H_in @ T0).
To evaluate an ACTUAL camera C we must pass  H_in = C @ inv(T0)   (NOT inv(T0) @ C).
"""
import numpy as np, torch
from ring020_026 import tensor


def ring_increment_from_camera(C_actual, T_original):
    return np.asarray(C_actual, float) @ np.linalg.inv(np.asarray(T_original, float))


def evaluate_ring_at_camera(rr, C_actual, T_original, cid, with_aux=False):
    inc = ring_increment_from_camera(C_actual, T_original)
    L, aux, segs = rr.losses(tensor(inc, torch.float64), cid)
    out = dict(M=float(L['M']), I=float(L['I']), C=float(L['C']), O=float(L['O']))
    out['MIO'] = 0.25*out['M'] + 0.35*out['I'] + 0.35*out['O']
    out['MICO'] = 0.25*out['M'] + 0.35*out['I'] + 0.05*out['C'] + 0.35*out['O']
    if with_aux:
        out['aux'] = aux
    return out
