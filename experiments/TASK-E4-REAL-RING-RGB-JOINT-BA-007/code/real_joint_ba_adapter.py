"""Real-data Ring-RGB joint BA adapter (A0 / A1 / A2) over the frozen 005 solver.

Only the Ring boundary block (r_q) is replaced; material (r_p) and background (r_b)
blocks and the whole BA machinery stay frozen.
"""
import json, shutil, sys, traceback
from pathlib import Path
import numpy as np

WS = Path('/home/liu/ring_first_3d_workspace')
T005 = WS/'experiments/TASK-E4-UNIFIED-RING-RGB-CAMERA-MAINLINE-005'
T006 = WS/'experiments/TASK-E4-UNIFIED-RING-CONTOUR-REFINEMENT-005'
T = WS/'experiments/TASK-E4-REAL-RING-RGB-JOINT-BA-007'
sys.path.insert(0, str(T005/'code')); sys.path.insert(0, str(T/'code'))
import unified_camera as U5
import joint_loss as JL
import cad_contour_correspondence as CC
import ring_contour_observation as RO

CFG = json.loads((T/'configs/real_joint_ba.json').read_text())


def prep_views(g, v):
    meta = json.loads((T006/'runs/prepared'/f'{g}_{v}'/'PREPARED.json').read_text())
    return meta


def build_obs(arrays, views):
    """Observation npz: native observe + DXY inner/outer polylines and their visibility."""
    out = {}
    for q in views:
        cid = q['view']; lab = arrays[cid]['labels']
        ob = U5.observe(lab)
        rec = RO.load(cid)                     # 006 export (new masks)
        if rec and rec.get('valid'):
            n = 360
            pin = RO.ellipse_points(rec['inner'], n); pout = RO.ellipse_points(rec['outer'], n)
            ob['dxy_inner_pts'] = pin; ob['dxy_outer_pts'] = pout
            ob['dxy_inner_vis'] = RO.visible_arc(rec, 'inner', ob['q_train'], tol=2.0, n=n)
            ob['dxy_outer_vis'] = RO.visible_arc(rec, 'outer', ob['q_train'], tol=2.0, n=n)
        out[cid] = ob
    return out


def make_residual(base, mode, lam_R, K_default):
    def f(C, ob, part='train', K0=None):
        b = base(C, ob, part, K0)
        if part != 'train':
            return b
        nq = len(ob['q_train'])
        if ob.get('dxy_inner_pts') is None:
            return b                            # recorded fallback (A0 behaviour for that view)
        K = K0 if K0 is not None else K_default
        obs = dict(inner=np.asarray(ob['dxy_inner_pts']), outer=np.asarray(ob['dxy_outer_pts']),
                   inner_vis=np.asarray(ob['dxy_inner_vis'], bool),
                   outer_vis=np.asarray(ob['dxy_outer_vis'], bool))
        rv = JL.ring_vector(C, K, obs, tau=CFG['tau_px'])
        if mode == 'A1':
            return np.r_[rv, b[nq:]]
        return np.r_[lam_R*rv, b[nq:]]
    return f


def run(g, v, arm):
    meta = prep_views(g, v)
    views = meta['views']
    root = T/'runs'/f'{g}_{v}'/arm
    for d in ('observations', 'predictions', 'metrics'):
        (root/d).mkdir(parents=True, exist_ok=True)
    arrays = {}
    fit = []
    for q in views:
        d = np.load(q['cache'])
        arrays[q['view']] = dict(RGB=d['RGB'], labels=d['labels'], K=d['K'])
        fit.append(dict(meta=dict(case=g, video=v, id=q['view'], raw_frame=q['raw_frame'], role='FIT',
                                  RGB_source=q['cache'], Mask_source=q['cache'], K=d['K'].tolist()),
                        cache=dict(path=q['cache'])))
    ns, ordered = U5.build_namespace(root, fit, arrays)
    obs = build_obs(arrays, views)
    for cid, ob in obs.items():
        np.savez_compressed(root/'observations'/(cid+'_ring.npz'), **ob)
    # shared tracks: compute once in a cache dir then reuse across arms
    shared = T/'runs'/f'{g}_{v}'/'_shared'
    (shared/'observations').mkdir(parents=True, exist_ok=True)
    if not (shared/'observations/tracks005.npz').exists():
        tmp_root = root
        ns['main']()
        shutil.copyfile(tmp_root/'observations/tracks005.npz', shared/'observations/tracks005.npz')
        shutil.copyfile(tmp_root/'observations/pairs005.npz', shared/'observations/pairs005.npz')
    else:
        shutil.copyfile(shared/'observations/tracks005.npz', root/'observations/tracks005.npz')
        shutil.copyfile(shared/'observations/pairs005.npz', root/'observations/pairs005.npz')
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
    ns['ring_residual'] = make_residual(base, CFG['arms'][arm]['ring'] if arm != 'A0' else 'A0',
                                        CFG['arms'][arm].get('lambda_R', 1.0), ns['K'])
    if arm == 'A0':
        ns['ring_residual'] = base
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
        raise RuntimeError('NO_BA_VERSION ' + json.dumps({k: x.get('error','')[-300:] for k,x in vers.items()}))
    best = min(ok, key=lambda k: ok[k]['score']['score'])
    cur = ok[best]['c2w']
    from ring_first_3d.mainline.native.camera import torus_contours
    from scipy.spatial import cKDTree
    rows = []
    for i, a in enumerate(ordered):
        cid = a['meta']['id']; K = arrays[cid]['K']; ob = obs[cid]
        ci, co = CC.split(torus_contours(cur[i], K))
        rows_i = dict(arm=arm, group=g, video=v, view=cid, ba_version=int(best))
        # unified evaluation on the FROZEN raw boundary (A0 metric) and on DXY contours
        d = cKDTree(torus_contours(cur[i], K).reshape(-1,2)).query(ob['q_train'])[0]
        rows_i['ring_mae_raw_px'] = float(np.mean(d)); rows_i['ring_p95_raw_px'] = float(np.percentile(d,95))
        if ob.get('dxy_inner_pts') is not None:
            din = CC.dist_to_polyline(CC.sampled(ci, 256), ob['dxy_inner_pts'])
            dout = CC.dist_to_polyline(CC.sampled(co, 256), ob['dxy_outer_pts'])
            rows_i['ring_inner_mae_px'] = float(np.mean(din)); rows_i['ring_outer_mae_px'] = float(np.mean(dout))
        rows.append(rows_i)
    held = U5.held_reprojection(cur, [a['meta']['id'] for a in ordered], tr, U5.K_CFG)
    for i, r in enumerate(rows):
        e = held[i]['errors']; pos = held[i]['positive']; n = len(e)
        r['held_N'] = n
        r['held_mae_px'] = float(np.mean(e)) if n else float('nan')
        r['held_p95_px'] = float(np.percentile(e,95)) if n else float('nan')
        r['positive'] = float(np.mean(pos)) if pos else float('nan')
        r['admission'] = bool(r['ring_mae_raw_px'] <= 3.0)
        r['version_score'] = float(ok[best]['score']['score'])
    (root/'VALIDATION.json').write_text(json.dumps(dict(arm=arm, n=len(ordered),
        versions={str(k): ok[k]['score'] for k in ok}, rows=rows), indent=1))
    return rows


if __name__ == '__main__':
    g, v = sys.argv[1], sys.argv[2].zfill(3)
    arms = sys.argv[3].split(',') if len(sys.argv) > 3 else list(CFG['arms'])
    import pandas as pd
    allr = []
    for arm in arms:
        try:
            r = run(g, v, arm); allr += r
            print(f'OK {g}/{v} {arm} pass={sum(x["admission"] for x in r)} '
                  f'held={np.nanmedian([x["held_mae_px"] for x in r]):.2f}', flush=True)
        except Exception:
            print(f'FAIL {g}/{v} {arm}\n{traceback.format_exc()[-800:]}', flush=True)
    if allr:
        p = T/f'metrics/BA_RESULTS_{g}_{v}.csv'
        pd.DataFrame(allr).to_csv(p, index=False)
    print('rows', len(allr))
