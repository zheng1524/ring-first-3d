"""Unified camera solve on the newly prepared (raw-video -> INIT) caches.

Nested view sets V8 subset V16 subset V22, all from the same preparation pipeline.
Solver/BA/scoring/gates are the frozen 005 implementation (imported read-only).
"""
import json, sys, traceback
from pathlib import Path
import numpy as np, pandas as pd

WS = Path('/home/liu/ring_first_3d_workspace')
T005 = WS / 'experiments/TASK-E4-UNIFIED-RING-RGB-CAMERA-MAINLINE-005'
T = WS / 'experiments/TASK-E4-PREBODY-UNIFIED-CAMERA-READINESS-004'
sys.path.insert(0, str(T005 / 'code'))
import unified_camera as U5

K_CFG = U5.K_CFG
DENS = (8, 16, 22, 32)


def nested_idx(n, cap):
    return sorted(set(np.linspace(0, cap - 1, n).round().astype(int).tolist()))


def view_sets(n_avail):
    """Nested sets: V8 subset V16 subset V22 subset V32 (top capped by availability)."""
    idx = list(range(min(32, n_avail)))
    out = {}
    for L in (32, 22, 16, 8):
        if L <= len(idx):
            idx = [idx[i] for i in nested_idx(L, len(idx))]
        out[L] = list(idx)
    return out


def run(g, v, n):
    prep = json.loads((T / 'runs/prepared' / f'{g}_{v}' / 'PREPARED.json').read_text())
    views = prep['views']
    sets = view_sets(len(views))
    if n not in sets or len(sets[n]) < n:
        raise RuntimeError(f'INSUFFICIENT_VIEWS {len(views)}')
    chosen = [views[i] for i in sets[n]]
    root = T / 'runs' / f'N{len(chosen)}' / g / v
    for d in ('observations', 'predictions', 'metrics'):
        (root / d).mkdir(parents=True, exist_ok=True)
    arrays, fit = {}, []
    for q in chosen:
        d = np.load(q['cache'])
        arrays[q['view']] = dict(RGB=d['RGB'], labels=d['labels'], K=d['K'])
        fit.append(dict(meta=dict(case=g, video=v, id=q['view'], raw_frame=q['raw_frame'], role='FIT',
                                  RGB_source=q['cache'], Mask_source=q['cache'], K=d['K'].tolist()),
                        cache=dict(path=q['cache'])))
    ns, ordered = U5.build_namespace(root, fit, arrays)
    rings = []
    for a in ordered:
        cid = a['meta']['id']
        ob = U5.observe(arrays[cid]['labels'])
        if len(ob['q_train']) < 20:
            raise ValueError('INSUFFICIENT_RING ' + cid)
        np.savez_compressed(root / 'observations' / (cid + '_ring.npz'), **ob)
        raw = U5.recover(arrays[cid]['labels'], arrays[cid]['K'], rgb_geometry=None, initial_pose=None)
        cands = []
        for alt in raw['ring_alternatives']:
            Q = np.asarray(alt['Q'], float); C = np.eye(4)
            C[:3, :3] = Q.T; C[:3, 3] = -Q.T @ np.asarray(alt['center'], float)
            cands.append(dict(alt, c2r=C))
        rings.append(dict(id=cid, candidates=cands))
    (root / 'predictions/RING_CANDIDATES.json').write_text(json.dumps(rings, default=lambda o: o.tolist()))
    ns['main']()
    tr = dict(np.load(root / 'observations/tracks005.npz'))
    pack = dict(np.load(root / 'observations/pairs005.npz'))
    edges = ns['pair_data'](tr, pack)
    rf = [a['meta']['raw_frame'] for a in ordered]
    ref = int(np.argmin([abs(f - 459) for f in rf]))
    vers = {}
    for ver in range(U5.CFG['pose_initializations']):
        try:
            ini, _ = ns['initialize'](rings, tr, edges, ref, ver)
            X, tids, sup = ns['triangulate_training'](ini, tr)
            cur, P, ba = ns['BA'](ini, X, tids, sup, tr, ref)
            vers[ver] = dict(ok=True, c2w=cur, score=U5.version_score(ns, cur, tr, ref, ba))
        except Exception:
            vers[ver] = dict(ok=False, error=traceback.format_exc())
    ok = {k: x for k, x in vers.items() if x['ok']}
    if not ok:
        raise RuntimeError('NO_BA_VERSION')
    best = min(ok, key=lambda k: ok[k]['score']['score'])
    cur = ok[best]['c2w']
    from ring_first_3d.mainline.native.camera import torus_contours
    from scipy.spatial import cKDTree
    rows = []
    for i, a in enumerate(ordered):
        cid = a['meta']['id']; K = arrays[cid]['K']
        ob = dict(np.load(root / 'observations' / (cid + '_ring.npz')))
        d = cKDTree(torus_contours(cur[i], K).reshape(-1, 2)).query(ob['q_train'])[0]
        mae = float(np.mean(d))
        (root / 'camera' / cid).mkdir(parents=True, exist_ok=True)
        (root / 'camera' / cid / 'CAMERA_RESULT.json').write_text(json.dumps(dict(
            c2w_mm=cur[i].tolist(), candidate_source=f'UNIFIED_RAW_N{len(chosen)}', ba_version=int(best),
            ring_boundary_MAE_px=mae, GT_used=False, Body_used=False)))
        rows.append(dict(density=len(chosen), group=g, video=v, view=cid, ring_MAE_px=mae, ba_version=int(best)))
    held = U5.held_reprojection(cur, [a['meta']['id'] for a in ordered], tr, U5.K_CFG)
    for i, r in enumerate(rows):
        e = held[i]['errors']; pos = held[i]['positive']; nn = len(e)
        mae = float(np.mean(e)) if nn else float('nan'); p95 = float(np.percentile(e, 95)) if nn else float('nan')
        pf = float(np.mean(pos)) if pos else float('nan')
        adm = r['ring_MAE_px'] <= 3.0
        r.update(held_N=nn, held_MAE_px=mae, held_p95_px=p95, held_positive=pf, admission=bool(adm),
                 geometry_validated=bool(nn >= 8 and np.isfinite(mae) and mae <= 3 and p95 <= 6 and pf >= 0.95))
    (root / 'VALIDATION.json').write_text(json.dumps(dict(n=len(chosen), versions={str(k): ok[k]['score'] for k in ok}, rows=rows), indent=1))
    return rows


if __name__ == '__main__':
    g, v = sys.argv[1], sys.argv[2].zfill(3)
    dens = [int(x) for x in sys.argv[3].split(',')] if len(sys.argv) > 3 else list(DENS)
    allrows = []
    for n in dens:
        try:
            r = run(g, v, n); allrows += r
            print(f'OK {g}/{v} N={n} pass={sum(x["admission"] for x in r)} '
                  f'held={np.nanmedian([x["held_MAE_px"] for x in r]):.2f}', flush=True)
        except Exception:
            print(f'FAIL {g}/{v} N={n}\n{traceback.format_exc()[-500:]}', flush=True)
    df = pd.DataFrame(allrows)
    df.to_csv(T / f'metrics/CAMERA_DENSITY_{g}_{v}.csv', index=False)
    print('rows', len(allrows))
