"""View-density sweep 8 -> 16 -> 22 with the frozen unified Ring+RGB pipeline.

Only the *calibration view set size* changes. The solver, BA, scoring and gates are
byte-identical to TASK-...-005 (unified_camera.py is imported, not copied/modified).

N=8 must reproduce the 005 frozen cameras exactly (same 8 caches, same code path).

View pool sources (all read-only):
  baseline : SELECTED_VIEWS.json role=FIT  (the 8 views used by 005)
  extras   : <002>/runs/RF_ONLY_V1/<g>/<v>/reference_build/REV*/inputs/*.npz
             (surviving caches; the original source images were retired in cleanup)

Selection rule (identical for every instance):
  pool = baseline8 + extras (dedup by view id), ordered by (raw_frame, id)
  N=8  -> exactly the baseline 8
  N>8  -> baseline 8 first, then the remaining ordered extras by uniform stride
  if pool < N -> use the whole pool and record actual_N
"""
import argparse, json, shutil, sys, traceback
from pathlib import Path
import numpy as np
import pandas as pd

WS = Path('/home/liu/ring_first_3d_workspace')
T005 = WS / 'experiments/TASK-E4-UNIFIED-RING-RGB-CAMERA-MAINLINE-005'
T002 = WS / 'experiments/TASK-E4-UNIFIED-PIPELINE-COMPLETION-002'
TASK = WS / 'experiments/TASK-E4-VIEW-DENSITY-SWEEP-003'
RUNS = TASK / 'runs'

sys.path.insert(0, str(T005 / 'code'))
import unified_camera as U5  # frozen assembly layer, read-only

DENSITIES = (8, 16, 22)


def _clean(o):
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, dict):
        return {k: _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    return o


def _rf(cid):
    tail = cid.rsplit('_raw', 1)
    if len(tail) == 2 and tail[1].isdigit():
        return int(tail[1])
    tail = cid.rsplit('ref', 1)
    if len(tail) == 2 and tail[1].isdigit():
        return int(tail[1])
    return None


def pool(g, v):
    base = [dict(id=x['meta']['id'], cache=x['cache']['path'], meta=x['meta'], baseline=True)
            for x in U5.instance_views(g, v)]
    have = {b['id'] for b in base}
    extra = []
    for p in sorted((T002 / 'runs/RF_ONLY_V1' / g / v).glob('reference_build/*/inputs/*.npz')):
        cid = p.stem
        if cid in have:
            continue
        have.add(cid)
        extra.append(dict(id=cid, cache=str(p), meta=dict(
            case=g, video=v, id=cid, raw_frame=_rf(cid), role='FIT',
            RGB_source=str(p), Mask_source=str(p),
            K=json.loads((T002 / 'code/frozen_calibration/config.json').read_text())['K']),
            baseline=False))
    extra.sort(key=lambda x: (x['meta'].get('raw_frame') is None, x['meta'].get('raw_frame') or 0, x['id']))
    return base, extra


def select(g, v, n):
    base, extra = pool(g, v)
    if n <= len(base):
        chosen = base[:n]
    else:
        need = n - len(base)
        if need >= len(extra):
            chosen = base + extra
        else:
            idx = np.linspace(0, len(extra) - 1, need).round().astype(int)
            chosen = base + [extra[i] for i in sorted(set(idx.tolist()))]
    return chosen


def run(g, v, n):
    chosen = select(g, v, n)
    tag = f'N{len(chosen)}'
    root = RUNS / tag / g / v
    for d in ('observations', 'predictions', 'metrics'):
        (root / d).mkdir(parents=True, exist_ok=True)
    arrays = {c['id']: U5.load_cache(dict(cache=dict(path=c['cache']))) for c in chosen}
    fit = [dict(meta=c['meta'], cache=dict(path=c['cache'])) for c in chosen]
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
            Q = np.asarray(alt['Q'], float)
            C = np.eye(4); C[:3, :3] = Q.T; C[:3, 3] = -Q.T @ np.asarray(alt['center'], float)
            cands.append(dict(alt, c2r=C))
        rings.append(dict(id=cid, candidates=cands))
    (root / 'predictions/RING_CANDIDATES.json').write_text(json.dumps(_clean(rings)))
    ns['main']()

    tr = dict(np.load(root / 'observations/tracks005.npz'))
    pack = dict(np.load(root / 'observations/pairs005.npz'))
    edges = ns['pair_data'](tr, pack)
    rf = [a['meta']['raw_frame'] for a in ordered]
    num = [(i, f) for i, f in enumerate(rf) if isinstance(f, (int, float))]
    ref = int(min(num, key=lambda t: abs(t[1] - 459))[0]) if num else len(ordered) // 2

    versions = {}
    for ver in range(U5.CFG['pose_initializations']):
        try:
            ini, info = ns['initialize'](rings, tr, edges, ref, ver)
            X, tids, sup = ns['triangulate_training'](ini, tr)
            cur, P, ba = ns['BA'](ini, X, tids, sup, tr, ref)
            versions[ver] = dict(ok=True, c2w=cur, score=U5.version_score(ns, cur, tr, ref, ba))
        except Exception:
            versions[ver] = dict(ok=False, error=traceback.format_exc())
    ok = {k: V for k, V in versions.items() if V['ok']}
    if not ok:
        raise RuntimeError('NO_BA_VERSION')
    best = min(ok, key=lambda k: ok[k]['score']['score'])
    cur = ok[best]['c2w']

    from ring_first_3d.mainline.native.camera import torus_contours
    from scipy.spatial import cKDTree
    rows = []
    for i, x in enumerate(ordered):
        cid = x['meta']['id']; K = arrays[cid]['K']
        ob = dict(np.load(root / 'observations' / (cid + '_ring.npz')))
        d = cKDTree(torus_contours(cur[i], K).reshape(-1, 2)).query(ob['q_train'])[0]
        mae = float(np.mean(d)); (root / 'camera' / cid).mkdir(parents=True, exist_ok=True)
        (root / 'camera' / cid / 'CAMERA_RESULT.json').write_text(json.dumps(dict(
            c2w_mm=cur[i].tolist(), candidate_source=f'DENSITY_{tag}', ba_version=int(best),
            ring_boundary_MAE_px=mae, GT_used=False, Body_used=False)))
        rows.append(dict(density=len(chosen), tag=tag, group=g, video=v, view=cid,
                         baseline=bool(x['meta']['id'] in {b['id'] for b in pool(g, v)[0]}),
                         ring_MAE_px=mae, ba_version=int(best)))
    held = U5.held_reprojection(cur, [x['meta']['id'] for x in ordered], tr, U5.K_CFG)
    for i, r in enumerate(rows):
        e = held[i]['errors']; pos = held[i]['positive']; nn = len(e)
        mae = float(np.mean(e)) if nn else float('nan')
        p95 = float(np.percentile(e, 95)) if nn else float('nan')
        pf = float(np.mean(pos)) if pos else float('nan')
        adm = r['ring_MAE_px'] <= 3.0
        r.update(held_N=nn, held_MAE_px=mae, held_p95_px=p95, held_positive=pf, admission=bool(adm),
                 geometry_validated=bool(nn >= 8 and np.isfinite(mae) and mae <= 3 and p95 <= 6 and pf >= 0.95))
    (root / 'VALIDATION.json').write_text(json.dumps(dict(tag=tag, n_views=len(chosen),
                                                          versions={str(k): ok[k]['score'] for k in ok},
                                                          rows=rows), indent=1))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--groups', default='G02/005,G05/005')
    ap.add_argument('--densities', default='8,16,22')
    a = ap.parse_args()
    rows = []
    for spec in a.groups.split(','):
        g, v = spec.split('/'); v = v.zfill(3)
        for n in [int(x) for x in a.densities.split(',')]:
            try:
                r = run(g, v, n); rows += r
                print(f'OK {g}/{v} N={len({x["view"] for x in r})} pass={sum(x["admission"] for x in r)} '
                      f'valid={sum(x["geometry_validated"] for x in r)} '
                      f'held={np.nanmedian([x["held_MAE_px"] for x in r]):.3f}', flush=True)
                pd.DataFrame(rows).to_csv(TASK / 'DENSITY_VIEW_METRICS.csv', index=False)
            except Exception:
                print(f'FAIL {g}/{v} N={n}\n{traceback.format_exc()}', flush=True)
    pd.DataFrame(rows).to_csv(TASK / 'DENSITY_VIEW_METRICS.csv', index=False)
    print('rows', len(rows))


if __name__ == '__main__':
    main()
