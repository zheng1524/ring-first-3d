#!/usr/bin/env python3
"""THE single W0 camera entry point (stages: all|b0|w0|evaluate|admit|export).

Pipeline: prepared views -> Ring-First -> frozen tracks -> B0 -> W0 -> evaluate -> gate -> export.
No per-group branching: group/video only select inputs.
"""
import argparse, hashlib, json, sys
from pathlib import Path
import numpy as np

WS = Path('/home/liu/ring_first_3d_workspace')
T005 = WS/'experiments/TASK-E4-UNIFIED-RING-RGB-CAMERA-MAINLINE-005'
T006 = WS/'experiments/TASK-E4-UNIFIED-RING-CONTOUR-REFINEMENT-005'
T011 = WS/'experiments/TASK-E4-RING-RGB-JOINT-BA-011-REPAIR'
sys.path.insert(0, str(WS/'camera_mainline/code'))
sys.path.insert(0, str(T005/'code'))


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def load_prepared(g, v):
    p = T006/'runs/prepared'/f'{g}_{v}'/'PREPARED.json'
    if not p.exists():
        raise SystemExit(f'MISSING_PREPARED {p}')
    meta = json.loads(p.read_text())
    meta['views'] = sorted(meta['views'], key=lambda q: (q['raw_frame'], q['view']))
    return meta


def build_ns_and_views(g, v, meta, root):
    import unified_camera as U5
    views = meta['views']
    arrays, fit = {}, []
    for q in views:
        d = np.load(q['cache'])
        arrays[q['view']] = dict(RGB=d['RGB'], labels=d['labels'], K=d['K'])
        fit.append(dict(meta=dict(case=g, video=v, id=q['view'], raw_frame=q['raw_frame'], role='FIT',
                                  RGB_source=q['cache'], Mask_source=q['cache'], K=d['K'].tolist()),
                        cache=dict(path=q['cache'])))
    ns, ordered = U5.build_namespace(root, fit, arrays)
    return ns, ordered, arrays


def stage_tracks(ns, ordered, root, g, v):
    """Frozen tracks: reuse byte-identical 011 tracks when present, else fail (no silent regen)."""
    shared = T011/'runs'/f'{g}_{v}'/'B0'/'observations'
    tr = shared/'tracks005.npz'
    (root/'observations').mkdir(parents=True, exist_ok=True)
    if tr.exists():
        for f in ('tracks005.npz', 'pairs005.npz'):
            (root/'observations'/f).write_bytes((shared/f).read_bytes())
        src = 'frozen_011'
    else:
        ns['main']()                      # stage 'tracks' of this same pipeline (recorded, not silent)
        src = 'generated_by_pipeline'
    (root/'tracks_source.txt').write_text(src)
    actual = tr if tr.exists() else root/'observations/tracks005.npz'
    return dict(np.load(root/'observations/tracks005.npz')), dict(np.load(root/'observations/pairs005.npz')), actual


def stage_ring(ns, ordered, arrays, root):
    import unified_camera as U5
    rings = []
    for a in ordered:
        cid = a['meta']['id']
        ob = U5.observe(arrays[cid]['labels'])
        np.savez_compressed(root/'observations'/(cid+'_ring.npz'), **ob)
        raw = U5.recover(arrays[cid]['labels'], arrays[cid]['K'], rgb_geometry=None, initial_pose=None)
        cands = []
        for alt in raw['ring_alternatives']:
            Q = np.asarray(alt['Q'], float); C = np.eye(4)
            C[:3, :3] = Q.T; C[:3, 3] = -Q.T @ np.asarray(alt['center'], float)
            cands.append(dict(alt, c2r=C))
        rings.append(dict(id=cid, candidates=cands))
    return rings


def pick_ref(raw_frames):
    nums = [f for f in raw_frames if isinstance(f, (int, float))]
    if not nums:
        return len(raw_frames)//2
    return int(np.argmin([abs(f-459) for f in raw_frames]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--group', required=True); ap.add_argument('--video', required=True)
    ap.add_argument('--stage', default='all', choices=['all', 'b0', 'w0', 'evaluate', 'admit', 'export'])
    ap.add_argument('--output', default=None); ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--resume', action='store_true')
    a = ap.parse_args()
    g, v = a.group, a.video.zfill(3)
    out = Path(a.output) if a.output else WS/'camera_mainline'/g/f'video{v}'
    run = WS/'experiments/TASK-E4-W0-MAINLINE-CONSOLIDATION-015'/'runs'/f'{g}_{v}'
    meta = load_prepared(g, v)
    if a.dry_run:
        print(json.dumps(dict(group=g, video=v, n_views=len(meta['views']),
                              video_path=meta.get('video_path'), frames=[q['raw_frame'] for q in meta['views'][:5]]), indent=1))
        return
    import unified_camera as U5
    run.mkdir(parents=True, exist_ok=True)
    ns, ordered, arrays = build_ns_and_views(g, v, meta, run)
    tr, pack, trp = stage_tracks(ns, ordered, run, g, v)
    xy_tr = tr['xy']; held_mask = np.asarray(tr['held']).astype(bool)
    rings = stage_ring(ns, ordered, arrays, run)
    edges = ns['pair_data'](tr, pack)
    rf = [x['meta']['raw_frame'] for x in ordered]
    ref = pick_ref(rf)
    ini, _ = ns['initialize'](rings, tr, edges, ref, 0)
    if any(x is None for x in ini):
        raise SystemExit('RING_FIRST_INCOMPLETE')
    X, tids, support = ns['triangulate_training'](ini, tr)
    if a.stage in ('all', 'b0'):
        cur, P, ba = ns['BA'](ini, X, tids, support, tr, ref)
        np.savez_compressed(run/'B0.npz', c2w=cur, points=P, point_track_ids=tids, K=U5.K_CFG,
                            ids=[x['meta']['id'] for x in ordered], reference=ref, init_version=0)
        (run/'B0.json').write_text(json.dumps(dict(nfev=ba.get('nfev'), success=ba.get('success'),
                                                   objective=ba.get('training_soft_l1_objective')), indent=1))
        print('B0 done', ba.get('nfev'), flush=True)
    if a.stage in ('all', 'w0'):
        b0 = np.load(run/'B0.npz')
        X2, tids2, sup2 = ns['triangulate_training'](b0['c2w'], tr)
        ns['cfg'] = lambda: dict(U5.CFG, BA_max_nfev=30)
        cur, P, ba = ns['BA'](b0['c2w'], X2, tids2, sup2, tr, ref)
        np.savez_compressed(run/'W0.npz', c2w=cur, points=P, point_track_ids=tids2, K=U5.K_CFG,
                            ids=[x['meta']['id'] for x in ordered], reference=ref, init_version=0,
                            warm_start='B0')
        (run/'W0.json').write_text(json.dumps(dict(nfev=ba.get('nfev'), success=ba.get('success'),
                                                   objective=ba.get('training_soft_l1_objective')), indent=1))
        print('W0 done', ba.get('nfev'), flush=True)
    if a.stage in ('all', 'evaluate', 'admit', 'export'):
        import camera_admission as A, camera_rotation_metrics as RM, evaluate_held_geometry as EV
        import contour_metrics as CM
        POL = A.load_policy(WS/'camera_mainline/CAMERA_ADMISSION_POLICY.yaml')
        if (run/'W0.npz').exists():
            d = np.load(run/'W0.npz'); cams = d['c2w']
        else:
            d = np.load(run/'B0.npz'); cams = d['c2w']
        ids = [str(x) for x in d['ids']]
        order = sorted(range(len(ids)), key=lambda i: (rf[i], ids[i]))
        rows = []
        for i, cid in enumerate(ids):
            m = dict(arm=f'{g}/{v}', view=cid, raw_frame=rf[i],
                     pose_valid=bool(RM.check_so3(cams[i][:3, :3])[0]), cad_valid=True)
            qt = np.load(run/'observations'/(cid+'_ring.npz'))['q_train']
            try:
                m['ring_raw_mae'] = CM.ring_raw_mae(cams[i], qt, arrays[cid]['K'])
            except ValueError:
                m['cad_valid'] = False
            ev = EV.evaluate_view(xy_tr, held_mask, ids, cams, i, K=U5.K_CFG)
            vv = ev['valid_err']
            m.update(held_raw_n=len(ev['raw_err']), held_n=len(vv),
                     target_depth_fail=ev['target_depth_fail'],
                     triangulation_degenerate_n=ev['degenerate'])
            if len(vv):
                m.update(held_median=float(np.median(vv)), held_p95=float(np.percentile(vv, 95)),
                         held_p95_valid=float(np.percentile(vv, 95)),
                         held_median_valid=float(np.median(vv)),
                         held_mae=float(np.mean(vv)),
                         big_error_fraction=float((vv > POL['rgb']['big_error_px']).mean()))
            m['positive_depth'] = float(EV.project(np.zeros((1, 3)), cams[i])[1][0] > 0)
            pos = order.index(i)
            m['rotation_to_previous_deg'] = (None if pos == 0 else
                round(RM.relative_deg(cams[order[pos-1]], cams[i]), 3))
            m['center_to_previous_mm'] = (None if pos == 0 else
                round(RM.center_distance_mm(cams[order[pos-1]], cams[i]), 3))
            m['rotation_from_reference_deg'] = round(RM.relative_deg(cams[ref], cams[i]), 3)
            dec = A.decide(m, POL, artefact=('DEGENERATE_TRIANGULATION'
                           if m['triangulation_degenerate_n'] > 0 else None))
            m.update(admission_status=dec['status'], admission_reasons=';'.join(dec['reasons']))
            rows.append(m)
        import pandas as pd
        dfm = pd.DataFrame(rows)
        (run/'PER_VIEW.csv').parent.mkdir(parents=True, exist_ok=True)
        dfm.to_csv(run/'PER_VIEW.csv', index=False)
        out.mkdir(parents=True, exist_ok=True)
        dfm.to_csv(out/'admission.csv', index=False)
        acc = dfm[dfm.admission_status == 'ACCEPT'].view.tolist()
        idx = [ids.index(x) for x in acc]
        np.savez_compressed(out/'camera_result.npz', c2w=cams, K=U5.K_CFG, ids=np.array(ids),
                            raw_frames=np.array(rf), reference=ref, ring_cad_mm=np.array([5.6, 0.6]),
                            source_arm='W0', admission_status=np.array(dfm.admission_status.values),
                            pose_convention=np.array(['c2w']))
        np.savez_compressed(out/'accepted_cameras.npz', c2w=cams[idx], K=U5.K_CFG, ids=np.array(acc),
                            raw_frames=np.array([rf[i] for i in idx]), reference=ref,
                            ring_cad_mm=np.array([5.6, 0.6]), source_arm='W0', pose_convention=np.array(['c2w']))
        print('EVAL', {k: int(v) for k, v in dfm.admission_status.value_counts().items()},
              'ring=%.3f held=%.3f p95=%.3f' % (dfm.ring_raw_mae.mean(),
              dfm.held_median.median(), dfm.held_p95.median()), flush=True)
    man = dict(group=g, video=v, source_video=meta.get('video_path'), source_video_sha256=meta.get('video_sha256'),
               prepared=meta.get('n'), ids=[x['meta']['id'] for x in ordered], raw_frames=rf, ref=ref,
               tracks_sha256=sha(trp), gate='camera_mainline/CAMERA_ADMISSION_POLICY.yaml',
               code=dict(entry=sha(Path(__file__)), gate=sha(WS/'camera_mainline/code/camera_admission.py'),
                         held_eval=sha(WS/'camera_mainline/code/evaluate_held_geometry.py')),
               stages=a.stage)
    (out/'manifest.json').write_text(json.dumps(man, indent=1))
    for f in ('B0.npz', 'W0.npz'):
        if (run/f).exists():
            (out/f.replace('.npz', '.npz')).write_bytes((run/f).read_bytes())
    print('exported ->', out, flush=True)


if __name__ == '__main__':
    main()
