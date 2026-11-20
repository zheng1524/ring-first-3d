"""Opt-in Ring priors built on DXY fitted contours.

DESIGN CONTRACT (removable verification state):
  * Every prior is OFF by default. An empty `ENABLED` set reproduces the frozen
    A0 / TASK-...-005 behaviour exactly.
  * Each prior only *adds* a residual block (or rescales the existing q-block);
    it never mutates the Ring solver, BA, RGB, gates or the CAD model.
  * Deleting this file and `pilot_runner.py` restores A0 with zero residue.
  * No prior reads Body / GT / HERO. Only FIT data and DXY ellipses are used.

Priors
  P1 support    : down-weight raw boundary points that the DXY fit rejects.
  P2 shape      : normalised radial-shape prior (offset + scale projected out).
  P3 width      : tube-width profile prior (r_outer - r_inner), offset removed.
  P4 harmonic   : low-order harmonic descriptor instead of an ellipse.
  P5 offsetfree : polar conic residual with the per-view radial offset removed
                  ("fixed A1": keeps the DXY conics but not their biased offset).
"""
import numpy as np
import cv2

from ring_first_3d.mainline.native.camera import torus_contours
from ring_first_3d.mainline.native.geometry import project

TAU = 2.0          # px, support sigma
TH_N = 72          # angular bins for polar priors
HARMONIC_K = 3     # P4 keeps k = 1..3

ENABLED = {}       # name -> weight; empty == A0


# ----------------------------------------------------------------- helpers
def ellipse_pts(e, n=240):
    t = np.linspace(0, 2 * np.pi, n)
    c, s = np.cos(np.deg2rad(e['angle_deg'])), np.sin(np.deg2rad(e['angle_deg']))
    x = e['major_radius'] * np.cos(t); y = e['minor_radius'] * np.sin(t)
    return np.c_[c * x - s * y + e['cx'], s * x + c * y + e['cy']]


def theta_grid():
    return np.linspace(0, 2 * np.pi, TH_N, endpoint=False)


def polar(pts, center, th):
    q = np.asarray(pts, float) - np.asarray(center, float)
    r = np.linalg.norm(q, axis=1)
    a = np.mod(np.arctan2(q[:, 1], q[:, 0]), 2 * np.pi)
    idx = np.digitize(a, np.r_[th, 2 * np.pi]) - 1
    out = np.full(len(th), np.nan)
    for t in range(len(th)):
        s = idx == t
        if s.any():
            out[t] = r[s].mean()
    return out


def split_curves(curves):
    areas = [abs(cv2.contourArea(np.asarray(c, np.float32).reshape(-1, 1, 2))) for c in curves]
    i, j = int(np.argmin(areas)), int(np.argmax(areas))
    return curves[i], curves[j] if len(areas) > 1 else None


def center_of(pose, K):
    uv, _ = project(np.zeros((1, 3)), np.asarray(pose), np.asarray(K))
    return uv[0]


def _profiles(pose, K, obs):
    """CAD polar profiles at the current pose, plus the cached DXY ones."""
    th = theta_grid()
    c0 = center_of(pose, K)
    ci, co = split_curves(torus_contours(np.asarray(pose), np.asarray(K)))
    r_cad_in = polar(np.asarray(ci, float), c0, th)
    r_cad_out = polar(np.asarray(co, float), c0, th) if co is not None else np.full(len(th), np.nan)
    return th, c0, r_cad_in, r_cad_out


def cache_dxy(obs, rec):
    """Pose-independent cache: DXY polar profiles about the projected ring centre."""
    th = theta_grid()
    obs['dxy_inner_pts'] = ellipse_pts(rec['inner'])
    obs['dxy_outer_pts'] = ellipse_pts(rec['outer'])
    obs['dxy_theta'] = th
    return obs


# ----------------------------------------------------------------- P1
def q_trust(obs, rec, tau=TAU):
    """Pose-independent per-point trust for the raw boundary samples."""
    if rec.get('inner') is None or rec.get('outer') is None:
        return np.ones(len(obs['q_train']))
    C = [_conic(rec['inner']), _conic(rec['outer'])]
    q = np.asarray(obs['q_train'], float)
    d = np.minimum(_sampson(q, C[0]), _sampson(q, C[1]))
    return np.exp(-(d / tau) ** 2)


def _conic(e):
    c, s = np.cos(np.deg2rad(e['angle_deg'])), np.sin(np.deg2rad(e['angle_deg']))
    R = np.array([[c, -s], [s, c]])
    A = R @ np.diag([1 / e['major_radius'] ** 2, 1 / e['minor_radius'] ** 2]) @ R.T
    ctr = np.array([e['cx'], e['cy']])
    M = np.zeros((3, 3)); M[:2, :2] = A; M[:2, 2] = -A @ ctr; M[2, :2] = M[:2, 2]
    M[2, 2] = ctr @ A @ ctr - 1
    return M / np.linalg.norm(M)


def _sampson(p, M):
    h = np.c_[np.asarray(p, float), np.ones(len(p))]
    Ch = h @ M
    return np.abs(np.einsum('ni,ni->n', h, Ch)) / np.sqrt((2 * Ch[:, 0]) ** 2 + (2 * Ch[:, 1]) ** 2 + 1e-12)


# ----------------------------------------------------------------- P5
def residual_offsetfree_conic(pose, K, obs):
    """Polar conic residual with the per-view radial offset removed."""
    th, c0, r_ci, r_co = _profiles(pose, K, obs)
    vals = []
    for key, r_cad in (('inner', r_ci), ('outer', r_co)):
        if key == 'inner':
            pts = obs.get('dxy_inner_pts')
        else:
            pts = obs.get('dxy_outer_pts')
        if pts is None or not np.isfinite(r_cad).any():
            continue
        r_dxy = polar(pts, c0, th)
        ok = np.isfinite(r_cad) & np.isfinite(r_dxy)
        if ok.sum() < 12:
            continue
        d = r_cad[ok] - r_dxy[ok]
        d = d - d.mean()                      # <-- offset invariance
        vals.append(np.clip(d, -100, 100))
    return np.concatenate(vals) if vals else np.zeros(4)


# ----------------------------------------------------------------- P2 / P3 / P4
def residual_shape(pose, K, obs):
    """Normalised radial shape of both contours; scale and offset projected out."""
    th, c0, r_ci, r_co = _profiles(pose, K, obs)
    out = []
    for key, r_cad in (('inner', r_ci), ('outer', r_co)):
        pts = obs.get('dxy_' + key + '_pts')
        if pts is None or not np.isfinite(r_cad).any():
            continue
        r_dxy = polar(pts, c0, th)
        ok = np.isfinite(r_cad) & np.isfinite(r_dxy)
        if ok.sum() < 12:
            continue
        s = max(np.nanmean(r_dxy[ok]), 1e-6)
        d = (r_cad[ok] - r_dxy[ok]) / s
        d = d - d.mean()
        out.append(np.clip(d, -1, 1))
    return np.concatenate(out) if out else np.zeros(4)


def residual_width(pose, K, obs):
    """Tube-width profile w = r_out - r_in, offset removed, normalised."""
    th, c0, r_ci, r_co = _profiles(pose, K, obs)
    if not (np.isfinite(r_ci).any() and np.isfinite(r_co).any()):
        return np.zeros(4)
    pi, po = obs.get('dxy_inner_pts'), obs.get('dxy_outer_pts')
    if pi is None or po is None:
        return np.zeros(4)
    w_cad = r_co - r_ci
    w_dxy = polar(po, c0, th) - polar(pi, c0, th)
    ok = np.isfinite(w_cad) & np.isfinite(w_dxy)
    if ok.sum() < 12:
        return np.zeros(4)
    s = max(np.nanmean(w_dxy[ok]), 1e-6)
    d = (w_cad[ok] - w_dxy[ok]) / s
    d = d - d.mean()
    return np.clip(d, -1, 1)


def residual_harmonic(pose, K, obs):
    """Low-order harmonic descriptor (k=1..3) of both contours instead of an ellipse."""
    th, c0, r_ci, r_co = _profiles(pose, K, obs)
    out = []
    for key, r_cad in (('inner', r_ci), ('outer', r_co)):
        pts = obs.get('dxy_' + key + '_pts')
        if pts is None or not np.isfinite(r_cad).any():
            continue
        r_dxy = polar(pts, c0, th)
        ok = np.isfinite(r_cad) & np.isfinite(r_dxy)
        if ok.sum() < 12:
            continue
        a = r_cad[ok] - np.nanmean(r_cad[ok])
        b = r_dxy[ok] - np.nanmean(r_dxy[ok])
        s = max(np.nanmean(r_dxy[ok]), 1e-6)
        A = np.fft.rfft(a) / len(a); B = np.fft.rfft(b) / len(b)
        idx = [k for k in range(1, HARMONIC_K + 1) if k < len(A)]
        d = np.concatenate([2 * np.real(A[idx] - B[idx]) / s, 2 * np.imag(A[idx] - B[idx]) / s])
        out.append(np.clip(d, -1, 1))
    return np.concatenate(out) if out else np.zeros(4)


PRIOR_FUNCS = {
    'P2': residual_shape,
    'P3': residual_width,
    'P4': residual_harmonic,
    'P5': residual_offsetfree_conic,
}


def compose(pose, ob, K, base_residual, n_q, enabled):
    """Return the residual vector for the requested prior set.

    enabled is {name: weight}. Empty -> exactly base_residual (A0).
    P1 rescales the existing q-block; P2-P5 append a regulariser block.
    P5 replaces the q-block (it is the 'fixed A1' variant).
    """
    if not enabled:
        return base_residual
    q0 = np.asarray(base_residual[:n_q], float)
    tail = np.asarray(base_residual[n_q:], float)
    if 'P5' in enabled:                      # replacement variant
        q = np.sqrt(enabled['P5']) * residual_offsetfree_conic(pose, K, ob)
    else:
        if 'P1' in enabled:
            w = np.asarray(ob.get('q_trust', np.ones(n_q)), float)
            q = np.sqrt(w) * q0
        else:
            q = q0
    blocks = [q, tail]
    for name in ('P2', 'P3', 'P4'):
        if name in enabled:
            blocks.append(np.sqrt(enabled[name]) * PRIOR_FUNCS[name](pose, K, ob))
    return np.concatenate(blocks)
