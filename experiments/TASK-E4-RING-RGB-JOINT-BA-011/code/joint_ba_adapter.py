"""J2: Inner+Outer joint Ring-RGB BA on the frozen solver.

Cancels the frozen sqrt(counts/rglen) scaling so each block keeps its designed weight:
  residual_scaled = frozen_scale * (sqrt(rglen/counts) * normalised_block)
"""
import json, sys, traceback
from pathlib import Path
import numpy as np
WS = Path('/home/liu/ring_first_3d_workspace')
T005 = WS/'experiments/TASK-E4-UNIFIED-RING-RGB-CAMERA-MAINLINE-005'
T006 = WS/'experiments/TASK-E4-UNIFIED-RING-CONTOUR-REFINEMENT-005'
T008 = WS/'experiments/TASK-E4-REAL-JOINT-BA-008'
T = WS/'experiments/TASK-E4-RING-RGB-JOINT-BA-011'
sys.path.insert(0, str(T005/'code')); sys.path.insert(0, str(T/'code'))
import unified_camera as U5
import joint_ring_observation as JO

M = 256
K = np.array([[490., 0, 319.5], [0, 490., 179.5], [0, 0, 1]])


def run(g, v, arm):
    meta = json.loads((T006/'runs/prepared'/f'{g}_{v}'/'PREPARED.json').read_text())
    views = meta['views']
    root = T/'runs'/f'{g}_{v}'/arm
    for d in ('observations', 'predictions', 'metrics'):
        (root/d).mkdir(parents=True, exist_ok=True)
    arrays, fit = {}, []
    for q in views:
        d = np.load(q['cache'])
        arrays[q['view']] = dict(RGB=d['RGB'], labels=d['labels'], K=d['K'])
        fit.append(dict(meta=dict(case=g, video=v, id=q['view'], raw_frame=q['raw_frame'], role='FIT',
                                  RGB_source=q['cache'], Mask_source=q['cache'], K=d['K'].tolist()),
                        cache=dict(path=q['cache'])))
    ns, ordered = U5.build_namespace(root, fit, arrays)
    obs = {}
    for q in views:
        cid = q['view']; labels = arrays[cid]['labels']
        ob = U5.observe(labels)
        rec = JO.load(cid)
        if rec and rec.get('valid'):
            for key in ('inner', 'outer'):
                pts, vis = JO.trusted_support(rec, key, labels)
                if pts is not None:
                    ob[key+'_pts'] = pts; ob[key+'_vis'] = vis
        ob['_cid'] = np.array([cid]); obs[cid] = ob
        np.savez_compressed(root/'observations'/(cid+'_ring.npz'), **ob)
    src = T008/'runs'/f'{g}_{v}'/'_shared'/'observations'
    for f in ('tracks005.npz', 'pairs005.npz'):
        s = src/f
        if not s.exists():
            ns['main'](); break
        (root/'observations'/f).write_bytes(s.read_bytes())
    tr = dict(np.load(root/'observations/tracks005.npz'))
    pack = dict(np.load(root/'observations/pairs005.npz'))
    edges = ns['pair_data'](tr, pack)
    rings = []
    for q in views:
        cid = q['view']
        raw = U5.recover(arrays[cid]['labels'], arrays[cid]['K'], rgb_geometry=None, initial_pose=None)
        cands = []
        for alt in raw['ring_alternatives']:
            Q = np.asarray(alt['Q'], float); C = np.eye(4)
            C[:3, :3] = Q.T; C[:3, 3] = -Q.T @ np.asarray(alt['center'], float)
            cands.append(dict(alt, c2r=C))
        rings.append(dict(id=cid, candidates=cands))
    (root/'predictions/RING_CANDIDATES.json').write_text(json.dumps(rings, default=lambda o: o.tolist()))
    xy = tr['xy']; held = np.asarray(tr['held']).astype(bool)
    counts = {a['meta']['id']: int(np.isfinite(xy[~held, i, 0]).sum()) for i, a in enumerate(ordered)}
    rf = [a['meta']['raw_frame'] for a in ordered]
    ref = int(np.argmin([abs(f-459) for f in rf]))
    base = ns['ring_residual']
    if arm == 'J2':
        def rr(C, ob, part='train', K0=None):
            if part != 'train':
                return base(C, ob, part, K0)
            Kv = K0 if K0 is not None else ns['K']
            cb, _ = JO.blocks(C, Kv, ob, which='both', m=M)
            nq = len(ob['q_train'])
            out = np.r_[cb, np.asarray(base(C, ob, part, Kv), float)[nq:]]
            key = ob['_cid']
            cid = str(key[0]) if hasattr(key, '__len__') else str(key)
            n_r = len(out); c = max(1, counts[cid])
            return out * np.sqrt(n_r/c)          # cancels frozen sqrt(counts/rglen)
        ns['ring_residual'] = rr
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
        raise RuntimeError('NO_BA ' + json.dumps({k: x.get('error', '')[-200:] for k, x in vers.items()}))
    forced = None
    if len(sys.argv) > 4 and sys.argv[4].isdigit():
        forced = int(sys.argv[4])
    if forced is not None and forced in ok:
        best = forced
        print(f'FORCED version {best} (comparable-version experiment)', flush=True)
    else:
        best = min(ok, key=lambda k: ok[k]['score']['score'])
    cur = ok[best]['c2w']
    from ring_first_3d.mainline.native.camera import torus_contours
    from scipy.spatial import cKDTree
    rows = []
    for i, a in enumerate(ordered):
        cid = a['meta']['id']; Kv = arrays[cid]['K']; ob = obs[cid]
        ci, co = CG_split(torus_contours(cur[i], Kv))
        r = dict(arm=arm, group=g, video=v, view=cid, ba_version=int(best))
        if 'inner_pts' in ob:
            r['inner_mae'] = float(cKDTree(ob['inner_pts']).query(ci)[0].mean())
            r['outer_mae'] = float(cKDTree(ob['outer_pts']).query(co)[0].mean())
        r['ring_raw_mae'] = float(cKDTree(torus_contours(cur[i], Kv)[0]).query(ob['q_train'])[0].mean())
        rows.append(r)
    held_r = U5.held_reprojection(cur, [a['meta']['id'] for a in ordered], tr, U5.K_CFG)
    for i, r in enumerate(rows):
        e = held_r[i]['errors']; pos = held_r[i]['positive']; n = len(e)
        r.update(held_mae=float(np.mean(e)) if n else float('nan'),
                 held_p95=float(np.percentile(e, 95)) if n else float('nan'),
                 positive=float(np.mean(pos)) if pos else float('nan'))
    np.savez_compressed(root/'cameras.npz', c2w=cur, ids=[a['meta']['id'] for a in ordered], K=U5.K_CFG)
    (root/'VALIDATION.json').write_text(json.dumps(dict(arm=arm, rows=rows), indent=1))
    return rows


def CG_split(curves):
    import cv2
    a = [abs(cv2.contourArea(np.asarray(c, np.float32).reshape(-1, 1, 2))) for c in curves]
    i, j = int(np.argmin(a)), int(np.argmax(a))
    return curves[i], curves[j]


if __name__ == '__main__':
    import pandas as pd
    g, v = sys.argv[1], sys.argv[2]
    arms = sys.argv[3].split(',') if len(sys.argv) > 3 else ['B0', 'J2']
    allr = []
    for arm in arms:
        try:
            r = run(g, v, arm); allr += r
            print(f"OK {g}/{v} {arm} inner={np.nanmean([x.get('inner_mae',np.nan) for x in r]):.2f} "
                  f"outer={np.nanmean([x.get('outer_mae',np.nan) for x in r]):.2f} "
                  f"held={np.nanmedian([x['held_mae'] for x in r]):.2f}", flush=True)
        except Exception:
            print(f'FAIL {arm}\n{traceback.format_exc()[-600:]}', flush=True)
    pd.DataFrame(allr).to_csv(T/f'metrics/REAL_BA_RESULTS_{g}_{v}.csv', index=False)
