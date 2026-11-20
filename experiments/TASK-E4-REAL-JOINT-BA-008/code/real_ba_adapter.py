"""A0/A1/A2 real BA with the corrected blocks (008)."""
import json, shutil, sys, traceback
from pathlib import Path
import numpy as np
WS = Path('/home/liu/ring_first_3d_workspace')
T005 = WS/'experiments/TASK-E4-UNIFIED-RING-RGB-CAMERA-MAINLINE-005'
T006 = WS/'experiments/TASK-E4-UNIFIED-RING-CONTOUR-REFINEMENT-005'
T007 = WS/'experiments/TASK-E4-REAL-RING-RGB-JOINT-BA-007'
T = WS/'experiments/TASK-E4-REAL-JOINT-BA-008'
for p in (T005/'code', T/'code', T007/'code'):
    sys.path.insert(0, str(p))
import unified_camera as U5
import joint_residual_blocks as JB
import contour_geometry as CG
import ring_contour_observation as RO

CFG = json.loads((T/'configs/real_joint_ba.json').read_text())


def obs_for(cid, lab, ob):
    rec = RO.load(cid)
    ob = dict(ob)
    if rec and rec.get('valid'):
        n = 360
        ob['dxy_inner_pts'] = RO.ellipse_points(rec['inner'], n)
        ob['dxy_outer_pts'] = RO.ellipse_points(rec['outer'], n)
        ob['inner_vis'] = RO.visible_arc(rec, 'inner', ob['q_train'], tol=2.0, n=n)
        ob['outer_vis'] = RO.visible_arc(rec, 'outer', ob['q_train'], tol=2.0, n=n)
        ob['inner'] = ob['dxy_inner_pts']; ob['outer'] = ob['dxy_outer_pts']
    return ob


def run(g, v, arm, lam_C=1.0):
    meta = json.loads((T006/'runs/prepared'/f'{g}_{v}'/'PREPARED.json').read_text())
    views = meta['views']
    root = T/'runs'/f'{g}_{v}'/f'{arm}_lamC{lam_C}'
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
        cid = q['view']
        obs[cid] = obs_for(cid, arrays[cid]['labels'], U5.observe(arrays[cid]['labels']))
        np.savez_compressed(root/'observations'/(cid+'_ring.npz'), **obs[cid])
    shared = T/'runs'/f'{g}_{v}'/'_shared'
    (shared/'observations').mkdir(parents=True, exist_ok=True)
    src = T007/'runs'/f'{g}_{v}'/'_shared'/'observations'
    if (src/'tracks005.npz').exists():
        shutil.copyfile(src/'tracks005.npz', root/'observations/tracks005.npz')
        shutil.copyfile(src/'pairs005.npz', root/'observations/pairs005.npz')
    else:
        ns['main']()
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
            C[:3,:3] = Q.T; C[:3,3] = -Q.T @ np.asarray(alt['center'], float)
            cands.append(dict(alt, c2r=C))
        rings.append(dict(id=cid, candidates=cands))
    (root/'predictions/RING_CANDIDATES.json').write_text(json.dumps(rings, default=lambda o: o.tolist()))
    rf = [a['meta']['raw_frame'] for a in ordered]
    ref = int(np.argmin([abs(f-459) for f in rf]))
    base = ns['ring_residual']
    if arm != 'A0':
        def rr(C, ob, part='train', K0=None):
            if part != 'train':
                return base(C, ob, part, K0)
            K = K0 if K0 is not None else ns['K']
            out, _ = JB.ring_residual(arm, base, C, ob, K, lam_C=lam_C)
            return out
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
        raise RuntimeError('NO_BA ' + json.dumps({k: x.get('error','')[-200:] for k,x in vers.items()}))
    best = min(ok, key=lambda k: ok[k]['score']['score'])
    cur = ok[best]['c2w']
    from ring_first_3d.mainline.native.camera import torus_contours
    rows = []
    for i, a in enumerate(ordered):
        cid = a['meta']['id']; K = arrays[cid]['K']; ob = obs[cid]
        ci, co = CG.split_by_area(torus_contours(cur[i], K))
        d_raw = CG.dist_to_polyline(np.asarray(ob['q_train'], float),
                                    np.asarray(torus_contours(cur[i], K)[0], float))
        r = dict(arm=arm, lam_C=lam_C, group=g, video=v, view=cid, ba_version=int(best))
        if 'dxy_inner_pts' in ob:
            r['ring_inner_mae_px'] = float(CG.boundary_distance(ci, ob['dxy_inner_pts']).mean())
            r['ring_outer_mae_px'] = float(CG.boundary_distance(co, ob['dxy_outer_pts']).mean())
        rows.append(r)
    held = U5.held_reprojection(cur, [a['meta']['id'] for a in ordered], tr, U5.K_CFG)
    for i, r in enumerate(rows):
        e = held[i]['errors']; pos = held[i]['positive']; n = len(e)
        r.update(held_mae_px=float(np.mean(e)) if n else float('nan'),
                 held_p95_px=float(np.percentile(e, 95)) if n else float('nan'),
                 positive=float(np.mean(pos)) if pos else float('nan'), held_N=n)
    np.savez_compressed(root/'cameras.npz', c2w=cur, ids=[a['meta']['id'] for a in ordered], K=U5.K_CFG)
    (root/'VALIDATION.json').write_text(json.dumps(dict(arm=arm, lam_C=lam_C, rows=rows,
                                        versions={str(k): ok[k]['score'] for k in ok}), indent=1))
    return rows


if __name__ == '__main__':
    import pandas as pd
    g, v = sys.argv[1], sys.argv[2].zfill(3)
    arms = sys.argv[3].split(',') if len(sys.argv) > 3 else ['A0', 'A1', 'A2']
    lam = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
    allr = []
    for arm in arms:
        try:
            r = run(g, v, arm, lam); allr += r
            print(f'OK {g}/{v} {arm} lamC={lam} inner={np.nanmean([x.get("ring_inner_mae_px",np.nan) for x in r]):.2f} '
                  f'outer={np.nanmean([x.get("ring_outer_mae_px",np.nan) for x in r]):.2f} '
                  f'held={np.nanmedian([x["held_mae_px"] for x in r]):.2f}', flush=True)
        except Exception:
            print(f'FAIL {g}/{v} {arm}\n{traceback.format_exc()[-500:]}', flush=True)
    pd.DataFrame(allr).to_csv(T/f'metrics/A0_A1_A2_{g}_{v}.csv', index=False)
