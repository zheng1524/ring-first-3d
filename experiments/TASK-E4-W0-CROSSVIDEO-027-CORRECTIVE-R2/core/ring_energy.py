"""Ring energy <-> least-squares residual mapping (027-CORRECTIVE D3/D4 fix).

Historical energies are weighted MEANS of per-point Huber(d/3) (plus the raster mask term M).
We build residuals r_i = sqrt(2 * lam * rho_i / N) so that 0.5 * sum_i r_i^2 == lam * E_k exactly,
and run scipy with loss='linear' (no second, unintended Huber).
"""
import numpy as np


def rho(x):
    x = np.abs(np.asarray(x, float))
    return np.where(x < 1.0, 0.5*x*x, x - 0.5)


def ring_residuals(dists, lam, block):
    """dists: per-point pixel distances; block in {'M','I','C','O'} weighting."""
    d = np.asarray(dists, float)
    if d.size == 0: return np.zeros(0)
    return np.sqrt(2.0*lam*block*rho(d/3.0)/d.size)


def mask_residual(M, lam, block=0.25):
    return np.array([np.sqrt(2.0*lam*block*max(float(M), 0.0))])


def energies(parts):
    """parts: dict block -> array. Returns per-block mean + weighted MICO/MIO energy."""
    E = {k: float(np.mean(v)) if np.size(v) else 0.0 for k, v in parts.items()}
    E['MIO'] = 0.25*E.get('M', 0) + 0.35*E.get('I', 0) + 0.35*E.get('O', 0)
    E['MICO'] = 0.25*E.get('M', 0) + 0.35*E.get('I', 0) + 0.05*E.get('C', 0) + 0.35*E.get('O', 0)
    return E
