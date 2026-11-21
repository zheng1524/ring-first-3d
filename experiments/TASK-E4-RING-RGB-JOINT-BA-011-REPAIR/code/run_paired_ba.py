"""Paired B0-v0 / J2-v0 run: one process, one tracks set, one initialisation.

Fairness is guaranteed by construction: both arms receive the *same* ini/X/tids/support
arrays (their SHA256 are recorded), the same reference frame and the same BA budget.
"""
import argparse, hashlib, json, sys
from pathlib import Path
import numpy as np
WS = Path('/home/liu/ring_first_3d_workspace')
T005 = WS/'experiments/TASK-E4-UNIFIED-RING-RGB-CAMERA-MAINLINE-005'
T006 = WS/'experiments/TASK-E4-UNIFIED-RING-CONTOUR-REFINEMENT-005'
T011 = WS/'experiments/TASK-E4-RING-RGB-JOINT-BA-011'
T = WS/'experiments/TASK-E4-RING-RGB-JOINT-BA-011-REPAIR'
sys.path.insert(0, str(T/'code'))
sys.path.insert(0, str(T005/'code'))

EXPECTED = {
 'unified_camera': str(T005/'code/unified_camera.py'),
 'joint_ring_observation': str(T/'code/joint_ring_observation.py'),
 'contour_geometry': str(T/'code/contour_geometry.py'),
}


def sha_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def sha_arr(a):
    return hashlib.sha256(np.ascontiguousarray(a, dtype=np.float64).tobytes()).hexdigest()


def check_modules(strict=True):
    import importlib
    assert str(T/'code') in sys.path, 'REPAIR code dir missing from sys.path'
    assert not any(str(T011/'code') in p for p in sys.path), 'old 011 code dir must not be on sys.path'
    for m in ('joint_ring_observation', 'contour_geometry'):
        importlib.import_module(m)
    rows, bad = [], []
    for name in ('unified_camera', 'joint_ring_observation', 'contour_geometry',
                 'local_ring_sfm', 'ring_first_3d.mainline.native.camera'):
        mod = sys.modules.get(name) or sys.modules.get(name.split('.')[0])
        f = getattr(mod, '__file__', None)
        rec = dict(module=name, file=str(f), sha256=sha_file(f) if f else None,
                   expected=EXPECTED.get(name))
        rows.append(rec)
        if strict and name in EXPECTED and str(f) != EXPECTED[name]:
            bad.append(rec)
    (T/'metrics/MODULE_PROVENANCE.json').write_text(json.dumps(dict(modules=rows, violations=bad), indent=1))
    if bad:
        raise RuntimeError('MODULE_PROVENANCE_VIOLATION ' + json.dumps(bad))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--group', default='G03'); ap.add_argument('--video', default='005')
    ap.add_argument('--version', type=int, required=True)
    ap.add_argument('--arms', default='B0,J2')
    a = ap.parse_args()
    import unified_camera as U5
    check_modules()
    g, v = a.group, a.video
    meta = json.loads((T006/'runs/prepared'/f'{g}_{v}'/'PREPARED.json').read_text())
    views = meta['views']
    root = T/'runs'/f'{g}_{v}'
    for arm in a.arms.split(','):
        (root/arm).mkdir(parents=True, exist_ok=True)
    arrays, fit = {}, []
    for q in views:
        d = np.load(q['cache'])
        arrays[q['view']] = dict(RGB=d['RGB'], labels=d['labels'], K=d['K'])
        fit.append(dict(meta=dict(case=g, video=v, id=q['view'], raw_frame=q['raw_frame'], role='FIT',
                                  RGB_source=q['cache'], Mask_source=q['cache'], K=d['K'].tolist()),
                        cache=dict(path=q['cache'])))
    ns, ordered = U5.build_namespace(root/'B0', fit, arrays)
    # ---- frozen tracks: no silent regeneration
    src = T011/'runs'/f'{g}_{v}'/'B0'/'observations'
    tr_p, pa_p = src/'tracks005.npz', src/'pairs005.npz'
    if not (tr_p.exists() and pa_p.exists()):
        raise RuntimeError('FROZEN_TRACKS_MISSING: refusing to regenerate')
    for arm in a.arms.split(','):
        for f in (tr_p, pa_p):
            (root/arm/'observations').mkdir(parents=True, exist_ok=True)
            (root/arm/'observations'/f.name).write_bytes(f.read_bytes())
    tr = dict(np.load(root/'B0'/'observations/tracks005.npz'))
    pack = dict(np.load(root/'B0'/'observations/pairs005.npz'))
    import joint_ring_observation as JO
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
        ob['_cid'] = np.array([cid])
        obs[cid] = ob
        np.savez_compressed(root/'B0'/'observations'/(cid+'_ring.npz'), **ob)
    edges = ns['pair_data'](tr, pack)
    rings = []
    for q in views:
        cid = q['view']
        raw = U5.recover(arrays[cid]['labels'], arrays[cid]['K'], rgb_geometry=None, initial_pose=None)
        cands = []
        for alt in raw['ring_alternatives']:
            Q = np.asarray(alt['Q'], float); C = np.eye(4)
            C[:3,:3] = Q.T; C[:3,3] = -Q.T @ np.asarray(alt['center'], float)
            cands.append(dict(alt, c2r=C))
        rings.append(dict(id=cid, candidates=cands))
    rf = [x['meta']['raw_frame'] for x in ordered]
    ref = int(np.argmin([abs(f-459) for f in rf]))
    ini, _ = ns['initialize'](rings, tr, edges, ref, a.version)
    if any(x is None for x in ini):
        raise RuntimeError(f'VERSION {a.version} FAILED: unconnected cameras')
    X, tids, support = ns['triangulate_training'](ini, tr)
    # recorded fairness identity
    fair = dict(version=a.version, ref=ref, ref_raw_frame=rf[ref],
                ini_sha=sha_arr(np.array(ini)), X_sha=sha_arr(X),
                tids_sha=sha_arr(np.asarray(tids)), n_points=int(len(X)),
                tracks_sha=sha_file(tr_p), pairs_sha=sha_file(pa_p),
                budgets=dict(BA_max_nfev=U5.CFG['BA_max_nfev'], initializations=U5.CFG['pose_initializations']),
                ref_in_input=bool(459 in rf))
    (T/'metrics/PRE_RUN_FAIRNESS_CHECK.json').write_text(json.dumps(fair, indent=1))
    print('FAIR', json.dumps({k: fair[k] for k in ('version', 'ref', 'ref_raw_frame', 'n_points', 'tracks_sha')}), flush=True)
    base = ns['ring_residual']
    xy = tr['xy']; held = np.asarray(tr['held']).astype(bool)
    counts = {x['meta']['id']: int(np.isfinite(xy[~held, i, 0]).sum()) for i, x in enumerate(ordered)}
    out = {}
    for arm in a.arms.split(','):
        if arm == 'J2':
            def rr(C, ob, part='train', K0=None):
                if part != 'train':
                    return base(C, ob, part, K0)
                Kv = K0 if K0 is not None else ns['K']
                cb, _ = JO.blocks(C, Kv, ob, which='both', m=256)
                nq = len(ob['q_train'])
                res = np.r_[cb, np.asarray(base(C, ob, part, Kv), float)[nq:]]
                key = ob['_cid']; cid = str(key[0]) if hasattr(key, '__len__') else str(key)
                return res * np.sqrt(len(res)/max(1, counts[cid]))
            ns['ring_residual'] = rr
        else:
            ns['ring_residual'] = base
        try:
            import time; t0 = time.time()
            cur, P, ba = ns['BA'](ini, X, tids, support, tr, ref)
            print(f'BA {arm} seconds={time.time()-t0:.1f}', flush=True)
        except Exception as e:
            print(f'BA {arm} FAILED: {e}', flush=True)
            out[arm] = dict(cams=None, P=None, ba=dict(success=False, nfev=0, obj=None))
            continue
        out[arm] = dict(cams=cur, P=P, ba=dict(success=ba.get('success'), nfev=ba.get('nfev'),
                                               obj=ba.get('training_soft_l1_objective')))
        (root/arm/'ba_info.json').write_text(json.dumps(dict(arm=arm, version=a.version, ref=ref,
            ref_raw_frame=rf[ref], success=ba.get('success'), nfev=ba.get('nfev'),
            objective=ba.get('training_soft_l1_objective'), fair=fair), indent=1))
        np.savez_compressed(root/arm/'cameras.npz', c2w=cur, K=U5.K_CFG,
                            ids=[x['meta']['id'] for x in ordered], points=P, point_track_ids=tids,
                            reference=ref, initialization_version=a.version)
        print(f'BA {arm} nfev={ba.get("nfev")} success={ba.get("success")}', flush=True)
    # ---- shared evaluation
    from ring_first_3d.mainline.native.camera import torus_contours
    from scipy.spatial import cKDTree
    def split(cs):
        import cv2
        ar = [abs(cv2.contourArea(np.asarray(c, np.float32).reshape(-1,1,2))) for c in cs]
        i, j = int(np.argmin(ar)), int(np.argmax(ar))
        return cs[i], cs[j]
    rows = []
    for arm in a.arms.split(','):
        if out[arm]['cams'] is None: continue
        cur = out[arm]['cams']
        for i, x in enumerate(ordered):
            cid = x['meta']['id']; K = arrays[cid]['K']; ob = obs[cid]
            ci, co = split(torus_contours(cur[i], K))
            cs = torus_contours(cur[i], K)
            d_raw = min(cKDTree(np.asarray(c, float)).query(ob['q_train'])[0].mean() for c in cs)
            r = dict(arm=arm, version=a.version, view=cid, ring_raw_mae=float(d_raw))
            if 'inner_pts' in ob:
                r['inner_mae'] = float(cKDTree(ob['inner_pts']).query(ci)[0].mean())
                r['outer_mae'] = float(cKDTree(ob['outer_pts']).query(co)[0].mean())
            rows.append(r)
    first = [x for x in a.arms.split(',') if out[x]['cams'] is not None][0]
    held_r = U5.held_reprojection(out[first]['cams'], [x['meta']['id'] for x in ordered], tr, U5.K_CFG)
    for arm in a.arms.split(','):
        if out[arm]['cams'] is None: continue
        cur = out[arm]['cams']
        hr = U5.held_reprojection(cur, [x['meta']['id'] for x in ordered], tr, U5.K_CFG)
        for i, r in enumerate([x for x in rows if x['arm'] == arm]):
            e = hr[i]['errors']; pos = hr[i]['positive']; n = len(e)
            r.update(held_mae=float(np.mean(e)) if n else float('nan'),
                     held_p95=float(np.percentile(e, 95)) if n else float('nan'),
                     positive=float(np.mean(pos)) if pos else float('nan'), held_n=n)
    import pandas as pd
    df = pd.DataFrame(rows); df.to_csv(T/'metrics/PAIRED_BA_RESULTS.csv', index=False)
    summary = df.groupby('arm').agg(n=('view','size'), inner=('inner_mae','mean'), outer=('outer_mae','mean'),
                                    raw=('ring_raw_mae','mean'), held=('held_mae','median'),
                                    p95=('held_p95','median'), pos=('positive','mean')).round(3)
    print(summary.to_string())
    summary.to_csv(T/'metrics/PAIRED_SUMMARY.csv')


if __name__ == '__main__':
    main()
