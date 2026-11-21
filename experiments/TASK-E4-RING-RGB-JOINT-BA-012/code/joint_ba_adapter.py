"""W0 / W2 / W3 from a frozen B0 warm start (one process, shared init)."""
import argparse, hashlib, json, sys, time
from pathlib import Path
import numpy as np
WS = Path('/home/liu/ring_first_3d_workspace')
T005 = WS/'experiments/TASK-E4-UNIFIED-RING-RGB-CAMERA-MAINLINE-005'
T006 = WS/'experiments/TASK-E4-UNIFIED-RING-CONTOUR-REFINEMENT-005'
T011 = WS/'experiments/TASK-E4-RING-RGB-JOINT-BA-011-REPAIR'
T = WS/'experiments/TASK-E4-RING-RGB-JOINT-BA-012'
sys.path.insert(0, str(T/'code')); sys.path.insert(0, str(T005/'code'))
import unified_camera as U5
import j2_obs_correct as J

K = U5.K_CFG


def sha_arr(a):
    return hashlib.sha256(np.ascontiguousarray(a, dtype=np.float64).tobytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--arms', default='W0,W2,W3')
    ap.add_argument('--lam', type=float, default=1.0)
    ap.add_argument('--nfev', type=int, default=30)
    a = ap.parse_args()
    g, v = 'G03', '005'
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
    ns, ordered = U5.build_namespace(root/'W0', fit, arrays)
    # frozen tracks from 011 (never regenerate)
    src = T011/'runs'/f'{g}_{v}'/'B0'/'observations'
    for f in ('tracks005.npz', 'pairs005.npz'):
        (root/'W0'/'observations').mkdir(parents=True, exist_ok=True)
        (root/'W0'/'observations'/f).write_bytes((src/f).read_bytes())
    tr = dict(np.load(root/'W0'/'observations/tracks005.npz'))
    pack = dict(np.load(root/'W0'/'observations/pairs005.npz'))
    obs = {}
    for q in views:
        cid = q['view']; labels = arrays[cid]['labels']
        ob = U5.observe(labels)
        rec = json.loads((T011/'metrics/DXY_OBSERVATIONS'/(cid+'.json')).read_text())
        for key in ('inner', 'outer'):
            p = Path(T011/'metrics/DXY_OBSERVATIONS'/(cid+'.json'))
            pass
        from scipy.spatial import cKDTree
        import cv2
        for key in ('inner', 'outer'):
            e = rec.get(key)
            if e is None: continue
            t = np.linspace(0, 2*np.pi, 720, endpoint=False)
            c_, s_ = np.cos(np.deg2rad(e['angle_deg'])), np.sin(np.deg2rad(e['angle_deg']))
            xx = e['major_radius']*np.cos(t); yy = e['minor_radius']*np.sin(t)
            pts = np.c_[c_*xx - s_*yy + e['cx'], s_*xx + c_*yy + e['cy']]
            edge = cv2.Canny(((labels == 2).astype(np.uint8))*255, 50, 150)
            ys, xs = np.nonzero(edge)
            if len(ys):
                dd, _ = cKDTree(np.c_[xs, ys].astype(float)).query(pts, k=1); vis = dd <= 1.5
            else:
                vis = np.zeros(720, bool)
            ob[key+'_pts'] = pts; ob[key+'_vis'] = vis
        ob['_cid'] = np.array([cid])
        obs[cid] = ob
        np.savez_compressed(root/'W0'/'observations'/(cid+'_ring.npz'), **ob)
    edges = ns['pair_data'](tr, pack)
    cam0 = np.load(T011/'runs/G03_005/B0/cameras.npz')
    ini = cam0['c2w']
    X, tids, support = ns['triangulate_training'](ini, tr)   # support needed by the frozen BA
    ref = int(cam0['reference'])
    fair = dict(warm_start='011 B0 cameras; points re-triangulated from B0 cameras (shared by all arms)', ref=ref, n_points=int(len(X)),
                ini_sha=sha_arr(ini), X_sha=sha_arr(X), tids_sha=sha_arr(tids),
                tracks_sha=hashlib.sha256((src/'tracks005.npz').read_bytes()).hexdigest(),
                nfev_budget=a.nfev, lam=a.lam)
    (T/'metrics/INPUT_MANIFEST.json').write_text(json.dumps(fair, indent=1))
    print('FAIR', json.dumps({k: fair[k] for k in ('ref', 'n_points', 'nfev_budget')}), flush=True)
    ns['cfg'] = lambda: dict(U5.CFG, BA_max_nfev=a.nfev)
    base = ns['ring_residual']
    xy = tr['xy']; held = np.asarray(tr['held']).astype(bool)
    counts = {x['meta']['id']: int(np.isfinite(xy[~held, i, 0]).sum()) for i, x in enumerate(ordered)}
    for arm in a.arms.split(','):
        (root/arm/'observations').mkdir(parents=True, exist_ok=True)
        for f in ('tracks005.npz', 'pairs005.npz'):
            (root/arm/'observations'/f).write_bytes((src/f).read_bytes())
        if arm == 'W0':
            ns['ring_residual'] = base
        elif arm == 'W2':
            def rr2(C, ob, part='train', K0=None, _base=base):
                if part != 'train':
                    return _base(C, ob, part, K0)
                Kv = K0 if K0 is not None else ns['K']
                cb, _ = J.blocks(C, Kv, ob, which='both')
                nq = len(ob['q_train'])
                res = np.r_[cb, np.asarray(_base(C, ob, part, Kv), float)[nq:]]
                key = ob['_cid']; cid = str(key[0]) if hasattr(key, '__len__') else str(key)
                return res*np.sqrt(len(res)/max(1, counts[cid]))
            ns['ring_residual'] = rr2
        else:
            def rr3(C, ob, part='train', K0=None, _base=base, lam=a.lam):
                if part != 'train':
                    return _base(C, ob, part, K0)
                Kv = K0 if K0 is not None else ns['K']
                b = np.asarray(_base(C, ob, part, Kv), float)
                cb, _ = J.blocks(C, Kv, ob, which='both')
                k = np.sqrt((len(b)+len(cb))/max(len(b), 1))   # keep old-ring weight identical
                key = ob['_cid']; cid = str(key[0]) if hasattr(key, '__len__') else str(key)
                return k*np.r_[b, lam*cb]
            ns['ring_residual'] = rr3
        t0 = time.time()
        try:
            cur, P, ba = ns['BA'](ini, X, tids, support, tr, ref)
        except Exception as e:
            print(f'BA {arm} FAILED {e}', flush=True); continue
        np.savez_compressed(root/arm/'cameras.npz', c2w=cur, K=U5.K_CFG, points=P,
                            point_track_ids=tids, reference=ref, ids=[x['meta']['id'] for x in ordered])
        (root/arm/'ba_info.json').write_text(json.dumps(dict(arm=arm, seconds=time.time()-t0,
            success=ba.get('success'), nfev=ba.get('nfev'), objective=ba.get('training_soft_l1_objective'),
            fair=fair), indent=1))
        print(f'BA {arm} seconds={time.time()-t0:.0f} nfev={ba.get("nfev")} obj={ba.get("training_soft_l1_objective")}', flush=True)
    print('DONE', flush=True)


if __name__ == '__main__':
    main()
