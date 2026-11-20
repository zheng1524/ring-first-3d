"""Pilot runner for opt-in Ring priors. P0 (no priors) must reproduce A0/005 exactly.

Usage:
  python pilot_runner.py --tag P0
  python pilot_runner.py --tag P1 --priors P1:1.0 --groups G01/004,G03/004,G03/005
  python pilot_runner.py --tag P5 --priors P5:1.0 --groups ...
  python pilot_runner.py --tag P2 --priors P1:1.0,P2:0.1 --groups ...
"""
import argparse, json, shutil, sys, traceback
from pathlib import Path
import numpy as np
import pandas as pd

WS = Path('/home/liu/ring_first_3d_workspace')
T005 = WS / 'experiments/TASK-E4-UNIFIED-RING-RGB-CAMERA-MAINLINE-005'
T001 = WS / 'experiments/TASK-E4-DXY-CONIC-RING-OBSERVATION-REUSE-001'
TASK = WS / 'experiments/TASK-E4-DXY-CONIC-PRIOR-PILOT-002'
RUNS = TASK / 'runs'
DXY = T001 / 'metrics/DXY_OBSERVATIONS'

sys.path.insert(0, str(T005 / 'code')); sys.path.insert(0, str(TASK / 'code'))
import unified_camera as U5     # frozen 005 assembly (read-only)
import priors as P              # opt-in priors


def parse_priors(s):
    out = {}
    if not s:
        return out
    for part in s.split(','):
        k, _, w = part.partition(':')
        out[k.strip()] = float(w) if w else 1.0
    return out


def prepare(g, v, tag, enabled):
    root = RUNS / tag / g / v
    for d in ('observations', 'predictions', 'metrics'):
        (root / d).mkdir(parents=True, exist_ok=True)
    src = T005 / 'runs' / g / v
    for f in ('tracks005.npz', 'pairs005.npz'):
        shutil.copyfile(src / 'observations' / f, root / 'observations' / f)
    shutil.copyfile(src / 'predictions/RING_CANDIDATES.json', root / 'predictions/RING_CANDIDATES.json')
    for x in U5.instance_views(g, v):
        cid = x['meta']['id']
        ob = dict(np.load(src / 'observations' / (cid + '_ring.npz')))
        rec = json.loads((DXY / (cid + '.json')).read_text()) if (DXY / (cid + '.json')).exists() else {}
        if rec.get('valid'):
            ob = P.cache_dxy(ob, rec)
            ob['dxy_inner_conic'] = P._conic(rec['inner'])
            ob['dxy_outer_conic'] = P._conic(rec['outer'])
            if 'P1' in enabled:
                ob['q_trust'] = P.q_trust(ob, rec)
        np.savez_compressed(root / 'observations' / (cid + '_ring.npz'), **ob)
    return root


def run_instance(g, v, tag, enabled):
    root = prepare(g, v, tag, enabled)
    fit = U5.instance_views(g, v)
    arrays = {x['meta']['id']: U5.load_cache(x) for x in fit}
    ns, ordered = U5.build_namespace(root, fit, arrays)
    base = ns['ring_residual']

    def ring_residual(C, ob, part='train', K0=None):
        K = K0 if K0 is not None else ns['K']
        nq = len(ob.get('q_' + part, []))
        b = base(C, ob, part, K) if part == 'train' else np.zeros(0)
        if not enabled:
            return b
        return P.compose(C, ob, K, b, nq, enabled)
    ns['ring_residual'] = ring_residual

    tr = dict(np.load(root / 'observations/tracks005.npz'))
    pack = dict(np.load(root / 'observations/pairs005.npz'))
    edges = ns['pair_data'](tr, pack)
    rings = json.loads((root / 'predictions/RING_CANDIDATES.json').read_text())
    for r in rings:
        for c in r['candidates']:
            c['c2r'] = np.asarray(c['c2r'], float)
    rf = [a['meta']['raw_frame'] for a in ordered]
    numeric = [(i, f) for i, f in enumerate(rf) if isinstance(f, (int, float))]
    ref = int(min(numeric, key=lambda t: abs(t[1] - 459))[0]) if numeric else len(ordered) // 2

    versions = {}
    for ver in range(U5.CFG['pose_initializations']):
        try:
            ini, info = ns['initialize'](rings, tr, edges, ref, ver)
            X, tids, support = ns['triangulate_training'](ini, tr)
            cur, Pm, ba = ns['BA'](ini, X, tids, support, tr, ref)
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
        mae = float(np.mean(d)); p95 = float(np.percentile(d, 95))
        (root / 'camera' / cid).mkdir(parents=True, exist_ok=True)
        (root / 'camera' / cid / 'CAMERA_RESULT.json').write_text(json.dumps(dict(
            c2w_mm=cur[i].tolist(), candidate_source=f'PILOT_{tag}', ba_version=int(best),
            ring_boundary_MAE_px=mae, ring_boundary_p95_px=p95,
            priors=enabled, GT_used=False, Body_used=False)))
        rows.append(dict(tag=tag, priors=json.dumps(enabled), group=g, video=v, view=cid,
                         ring_MAE_px=mae, ring_p95_px=p95, ba_version=int(best)))
    held = U5.held_reprojection(cur, [x['meta']['id'] for x in ordered], tr, U5.K_CFG)
    for i, r in enumerate(rows):
        e = held[i]['errors']; pos = held[i]['positive']
        n = len(e); mae = float(np.mean(e)) if n else float('nan')
        p95 = float(np.percentile(e, 95)) if n else float('nan')
        pf = float(np.mean(pos)) if pos else float('nan')
        adm = r['ring_MAE_px'] <= 3.0
        r.update(held_N=n, held_MAE_px=mae, held_p95_px=p95, held_positive=pf, admission=bool(adm),
                 geometry_validated=bool(n >= 8 and np.isfinite(mae) and mae <= 3 and p95 <= 6 and pf >= 0.95))
    (root / 'VALIDATION.json').write_text(json.dumps(dict(tag=tag, priors=enabled,
                                                          versions={str(k): ok[k]['score'] for k in ok},
                                                          rows=rows), indent=1))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tag', required=True)
    ap.add_argument('--priors', default='')
    ap.add_argument('--groups', default='', help='comma list like G01/004,G03/005')
    a = ap.parse_args()
    enabled = parse_priors(a.priors)
    targets = []
    if a.groups:
        for p in a.groups.split(','):
            g, v = p.split('/'); targets.append((g, v.zfill(3)))
    else:
        targets = [(g, v) for g in U5.GROUPS for v in U5.VIDEOS]
    rows = []
    for g, v in targets:
        try:
            r = run_instance(g, v, a.tag, enabled); rows += r
            print(f'OK {a.tag} {g}/{v} pass={sum(x["admission"] for x in r)} valid={sum(x["geometry_validated"] for x in r)}', flush=True)
        except Exception:
            print(f'FAIL {a.tag} {g}/{v}\n{traceback.format_exc()}', flush=True)
    out = TASK / f'PILOT_{a.tag}_VIEW_METRICS.csv'
    pd.DataFrame(rows).to_csv(out, index=False)
    print('rows', len(rows), '->', out.name)


if __name__ == '__main__':
    main()
