"""A0/A1/A2 controlled arms: only the Ring observation term changes.

A0 = frozen TASK-...-005 result (read, never recomputed).
A1 = DXY inner/outer conics as the Ring term.
A2 = DXY conics + weak raw-boundary contour term.

Everything else (tracks, ring candidates, RGB PnP seeds, BA optimiser/budget,
version scoring, gates, view set) is reused verbatim from the 005 frozen run.
"""
import argparse, json, shutil, sys, traceback
from pathlib import Path
import numpy as np
import pandas as pd

WS = Path('/home/liu/ring_first_3d_workspace')
T005 = WS / 'experiments/TASK-E4-UNIFIED-RING-RGB-CAMERA-MAINLINE-005'
TASK = WS / 'experiments/TASK-E4-DXY-CONIC-RING-OBSERVATION-REUSE-001'
RUNS = TASK / 'runs'
DXY = TASK / 'metrics/DXY_OBSERVATIONS'

sys.path.insert(0, str(T005 / 'code'))
sys.path.insert(0, str(TASK / 'code'))
import unified_camera as U5          # noqa: E402  (frozen 005 assembly layer, read-only use)
import conic as CON                  # noqa: E402

ARMS = {'A1': dict(mode='A1'), 'A2': dict(mode='A2', aux_weight=0.2)}


def dxy_rec(cid):
    p = DXY / (cid + '.json')
    return json.loads(p.read_text()) if p.exists() else None


def prepare_root(g, v, arm):
    root = RUNS / arm / g / v
    (root / 'observations').mkdir(parents=True, exist_ok=True)
    (root / 'predictions').mkdir(parents=True, exist_ok=True)
    (root / 'metrics').mkdir(exist_ok=True)
    src = T005 / 'runs' / g / v
    for f in ['tracks005.npz', 'pairs005.npz']:
        shutil.copyfile(src / 'observations' / f, root / 'observations' / f)
    shutil.copyfile(src / 'predictions/RING_CANDIDATES.json', root / 'predictions/RING_CANDIDATES.json')
    fit = U5.instance_views(g, v)
    for x in fit:
        cid = x['meta']['id']
        ob = dict(np.load(src / 'observations' / (cid + '_ring.npz')))
        rec = dxy_rec(cid)
        if rec and rec.get('valid'):
            if rec.get('inner'):
                ob['dxy_inner_conic'] = CON.conic_from_ellipse(rec['inner'])
                ob['dxy_inner_weight'] = CON.quality_weight(rec)
            if rec.get('outer'):
                ob['dxy_outer_conic'] = CON.conic_from_ellipse(rec['outer'])
                ob['dxy_outer_weight'] = CON.quality_weight(rec)
        np.savez_compressed(root / 'observations' / (cid + '_ring.npz'), **ob)
    return root, fit


def run_arm(g, v, arm):
    root, fit = prepare_root(g, v, arm)
    arrays = {x['meta']['id']: U5.load_cache(x) for x in fit}
    ns, ordered = U5.build_namespace(root, fit, arrays)
    base_res = ns['ring_residual']
    mode = ARMS[arm]['mode']; aux = ARMS[arm].get('aux_weight', 0.2)

    def ring_residual(C, ob, part='train', K0=None):
        K = K0 if K0 is not None else ns['K']
        nq = len(ob.get('q_' + part, []))
        base = base_res(C, ob, part, K) if part == 'train' else np.zeros(0)
        return CON.conic_residual(C, ob, K, mode=mode, aux_weight=aux,
                                  base_residual=base, n_q=nq)
    ns['ring_residual'] = ring_residual

    tr = dict(np.load(root / 'observations/tracks005.npz'))
    pack = dict(np.load(root / 'observations/pairs005.npz'))
    edges = ns['pair_data'](tr, pack)
    rings = json.loads((root / 'predictions/RING_CANDIDATES.json').read_text())
    for r in rings:
        for c in r['candidates']:
            c['c2r'] = np.asarray(c['c2r'], float)
    raw_frames = [a['meta']['raw_frame'] for a in ordered]
    numeric = [(i, f) for i, f in enumerate(raw_frames) if isinstance(f, (int, float))]
    ref = int(min(numeric, key=lambda t: abs(t[1] - 459))[0]) if numeric else len(ordered) // 2

    versions = {}
    for ver in range(U5.CFG['pose_initializations']):
        try:
            ini, info = ns['initialize'](rings, tr, edges, ref, ver)
            X, tids, support = ns['triangulate_training'](ini, tr)
            cur, P, ba = ns['BA'](ini, X, tids, support, tr, ref)
            np.savez_compressed(root / 'predictions' / f'BA_{ver}.npz', c2w=cur, K=U5.K_CFG,
                                points=P, track_ids=tids, ids=[a['meta']['id'] for a in ordered],
                                reference=ref)
            versions[ver] = dict(ok=True, c2w=cur,
                                 score=U5.version_score(ns, cur, tr, ref, ba), ba=ba)
        except Exception:
            versions[ver] = dict(ok=False, error=traceback.format_exc())
    ok = {k: V for k, V in versions.items() if V['ok']}
    if not ok:
        raise RuntimeError('NO_BA_VERSION ' + json.dumps({k: v.get('error', '')[-300:] for k, v in versions.items()}))
    best = min(ok, key=lambda k: ok[k]['score']['score'])
    cur = ok[best]['c2w']
    save = {}
    for i, x in enumerate(ordered):
        cid = x['meta']['id']; K = arrays[cid]['K']
        ob = dict(np.load(root / 'observations' / (cid + '_ring.npz')))
        from ring_first_3d.mainline.native.camera import torus_contours
        from scipy.spatial import cKDTree
        d = cKDTree(torus_contours(cur[i], K).reshape(-1, 2)).query(ob['q_train'])[0]
        mae = float(np.mean(d)); p95 = float(np.percentile(d, 95))
        # conic-level diagnostics (reporting only)
        crec = dxy_rec(cid) or {}
        cvals = {}
        if crec.get('inner') and crec.get('outer'):
            for key in ('inner', 'outer'):
                cvals[key] = float(np.mean(CON.conic_residual(cur[i], ob, K, mode='A1'))) if key == 'inner' else None
        rec = dict(c2w_mm=cur[i].tolist(), candidate_source=f'{arm}_CONIC_FIRST',
                   ba_version=int(best), ring_boundary_MAE_px=mae, ring_boundary_p95_px=p95,
                   GT_used=False, Body_used=False)
        save[cid] = rec
        (root / 'camera' / cid).mkdir(parents=True, exist_ok=True)
        (root / 'camera' / cid / 'CAMERA_RESULT.json').write_text(json.dumps(rec))
    held = U5.held_reprojection(cur, [x['meta']['id'] for x in ordered], tr, U5.K_CFG)
    rows = []
    for i, x in enumerate(ordered):
        cid = x['meta']['id']
        e = held[i]['errors']; pos = held[i]['positive']
        n = len(e); mae = float(np.mean(e)) if n else float('nan')
        p95 = float(np.percentile(e, 95)) if n else float('nan')
        pf = float(np.mean(pos)) if pos else float('nan')
        adm = save[cid]['ring_boundary_MAE_px'] <= 3.0
        validated = (n >= 8 and np.isfinite(mae) and mae <= 3 and p95 <= 6 and pf >= 0.95)
        status = ('VALIDATED' if (adm and validated) else
                  'USABLE_WITH_CAUTION' if adm else
                  'INSUFFICIENT_EVIDENCE' if n < 8 else 'INVALID')
        rows.append(dict(arm=arm, group=g, video=v, view=cid,
                         ring_MAE_px=save[cid]['ring_boundary_MAE_px'],
                         ring_p95_px=save[cid]['ring_boundary_p95_px'],
                         held_N=n, held_MAE_px=mae, held_p95_px=p95, held_positive=pf,
                         admission=bool(adm), geometry_validated=bool(validated),
                         status=status, ba_version=int(best),
                         score=float(ok[best]['score']['score']),
                         dxy_valid=bool((dxy_rec(cid) or {}).get('valid'))))
    (root / 'VALIDATION.json').write_text(json.dumps(dict(rows=rows, versions={str(k): ok[k]['score'] for k in ok}), indent=1))
    return rows


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--arm', choices=['A1', 'A2'], required=True)
    ap.add_argument('--group'); ap.add_argument('--video'); a = ap.parse_args()
    rows = []
    for g in U5.GROUPS:
        if a.group and g != a.group: continue
        for v in U5.VIDEOS:
            if a.video and v != a.video: continue
            try:
                r = run_arm(g, v, a.arm); rows += r
                print(f'OK {a.arm} {g}/{v} pass={sum(x["admission"] for x in r)} valid={sum(x["geometry_validated"] for x in r)}', flush=True)
            except Exception:
                print(f'FAIL {a.arm} {g}/{v}\n{traceback.format_exc()}', flush=True)
    out = TASK / f'ARM_{a.arm}_VIEW_METRICS.csv'
    if out.exists():
        old = pd.read_csv(out); old = old[~old.set_index(['group', 'video']).index.isin(
            [(r['group'], r['video']) for r in rows])]
        rows = pd.concat([old, pd.DataFrame(rows)], ignore_index=True)
    pd.DataFrame(rows).to_csv(out, index=False)
    print('rows', len(rows))


if __name__ == '__main__':
    main()
