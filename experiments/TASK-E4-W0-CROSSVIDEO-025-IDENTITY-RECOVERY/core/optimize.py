"""Adam with真 checkpoint/resume (q, m, v, step, best) and cumulative SE(3) bound."""
import numpy as np
from se3 import exp_se3

SCALE = np.array([0.6, 0.6, 0.6, np.deg2rad(5), np.deg2rad(5), np.deg2rad(5)])


def empty_state(q=None):
    return dict(q=np.zeros(6) if q is None else np.asarray(q, float).copy(),
                m=np.zeros(6), v=np.zeros(6), step=0, best=np.inf)


def state_to_npz(path, st, extra=None):
    d = dict(q=st['q'], m=st['m'], v=st['v'], step=st['step'], best=st['best'])
    if extra: d.update(extra)
    np.savez(path, **d)


def state_from_npz(path):
    z = np.load(path)
    return dict(q=np.asarray(z['q'], float), m=np.asarray(z['m'], float),
                v=np.asarray(z['v'], float), step=int(z['step']), best=float(z['best']))


def step_once(loss_fn, st, lr=0.01, b1=0.9, b2=0.999, eps=1e-8, h=1e-4,
              max_t=1.2, max_r=10.0, allowed=True):
    """One Adam step with FD gradient + backtracking + cumulative bound; deterministic given st."""
    q = st['q']
    g = np.zeros(6)
    for k in range(6):
        qp = q.copy(); qp[k] += h
        qm = q.copy(); qm[k] -= h
        g[k] = (loss_fn(qp) - loss_fn(qm)) / (2*h)
    st = dict(st); st['step'] = st['step'] + 1
    if not np.isfinite(g).all() or not allowed:
        st['reject_reason'] = 'NONFINITE_OR_FORCED'
        return st
    m = b1*st['m'] + (1-b1)*g
    v = b2*st['v'] + (1-b2)*g*g
    t = st['step']
    mh = m/(1-b1**t); vh = v/(1-b2**t)
    upd = lr*mh/(np.sqrt(vh)+eps)
    alpha = 1.0; cur = st['best']
    for _ in range(8):
        cand = q - alpha*upd
        dH = exp_se3(cand*SCALE)
        trans = float(np.linalg.norm(dH[:3, 3]))
        rot = float(np.degrees(np.arccos(np.clip((np.trace(dH[:3, :3])-1)/2, -1, 1))))
        if trans <= max_t and rot <= max_r:
            L = loss_fn(cand)
            if np.isfinite(L) and L < cur:
                st.update(q=cand, m=m, v=v, best=float(L)); st['reject_reason'] = None
                return st
        alpha *= .5
    st['reject_reason'] = 'REJECTED'
    return st            # q/m/v untouched -> exact rollback
