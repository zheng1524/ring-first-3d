#!/usr/bin/env python3
"""THE single M1 W0 camera entry point.

Pipeline: prepared views -> Ring-First -> frozen track005 -> B0 -> W0 ->
held evaluation -> admission -> export. Core algorithms are reused unchanged.
Group/video select inputs only; no per-group algorithm branch.
"""
import argparse
import hashlib
import json
import sys
import traceback
from pathlib import Path

import numpy as np

WS = Path('/home/liu/ring_first_3d_workspace')
T005 = WS / 'experiments/TASK-E4-UNIFIED-RING-RGB-CAMERA-MAINLINE-005'
T006 = WS / 'experiments/TASK-E4-UNIFIED-RING-CONTOUR-REFINEMENT-005'
T011 = WS / 'experiments/TASK-E4-RING-RGB-JOINT-BA-011-REPAIR'
T002 = WS / 'experiments/TASK-E4-UNIFIED-PIPELINE-COMPLETION-002'
sys.path.insert(0, str(WS / 'camera_mainline/code'))
sys.path.insert(0, str(T005 / 'code'))


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def load_prepared(g, v, prepared_root):
    p = Path(prepared_root) / f'{g}_{v}' / 'PREPARED.json'
    if not p.exists():
        raise SystemExit(f'MISSING_PREPARED {p}')
    meta = json.loads(p.read_text())
    if not meta.get('views'):
        raise SystemExit(f'NO_PREPARED_VIEWS {p}')
    meta['views'] = sorted(meta['views'], key=lambda q: (q['raw_frame'], q['view']))
    meta['prepared_path'] = str(p)
    meta['prepared_sha256'] = sha(p)
    meta['views_sha256'] = {q['view']: sha(Path(q['cache'])) for q in meta['views']}
    return meta


def write_status(out, status, stage, reason, g, v, error_type=None):
    out.mkdir(parents=True, exist_ok=True)
    (out / 'STATUS.json').write_text(json.dumps(dict(
        status=status, stage=stage, reason=reason, error_type=error_type,
        group=g, video=v), indent=1))


def build_ns_and_views(g, v, meta, root, ring_radius, ring_wire, pair_offsets=None):
    import unified_camera as U5
    views = meta['views']
    arrays, fit = {}, []
    for q in views:
        d = np.load(q['cache'])
        arrays[q['view']] = dict(RGB=d['RGB'], labels=d['labels'], K=d['K'])
        fit.append(dict(meta=dict(case=g, video=v, id=q['view'], raw_frame=q['raw_frame'], role='FIT',
                                  RGB_source=q['cache'], Mask_source=q['cache'], K=d['K'].tolist()),
                        cache=dict(path=q['cache'])))
    ns, ordered = U5.build_namespace(root, fit, arrays, ring_radius, ring_wire, pair_offsets=pair_offsets)
    return ns, ordered, arrays


def stage_tracks(ns, ordered, root, g, v):
    """Reuse frozen 011 tracks when byte-identical; otherwise run frozen track005 once."""
    shared = T011 / 'runs' / f'{g}_{v}' / 'B0' / 'observations'
    tr = shared / 'tracks005.npz'
    (root / 'observations').mkdir(parents=True, exist_ok=True)
    if tr.exists():
        for f in ('tracks005.npz', 'pairs005.npz'):
            (root / 'observations' / f).write_bytes((shared / f).read_bytes())
        src = 'frozen_011'
    else:
        ns['main']()
        src = 'generated_by_pipeline'
    (root / 'tracks_source.txt').write_text(src)
    return (dict(np.load(root / 'observations/tracks005.npz')),
            dict(np.load(root / 'observations/pairs005.npz')),
            src)


def stage_ring(ns, ordered, arrays, root, ring_radius, ring_wire):
    import unified_camera as U5
    rings = []
    for a in ordered:
        cid = a['meta']['id']
        ob = U5.observe(arrays[cid]['labels'])
        np.savez_compressed(root / 'observations' / (cid + '_ring.npz'), **ob)
        raw = U5.recover(arrays[cid]['labels'], arrays[cid]['K'], rgb_geometry=None,
                         initial_pose=None, ring_radius=ring_radius, ring_wire=ring_wire)
        cands = []
        for alt in raw['ring_alternatives']:
            Q = np.asarray(alt['Q'], float)
            C = np.eye(4)
            C[:3, :3] = Q.T
            C[:3, 3] = -Q.T @ np.asarray(alt['center'], float)
            cands.append(dict(alt, c2r=C))
        rings.append(dict(id=cid, candidates=cands))
    return rings


def pick_ref(raw_frames):
    nums = [f for f in raw_frames if isinstance(f, (int, float))]
    if not nums:
        return len(raw_frames) // 2
    return int(np.argmin([abs(f - 459) for f in raw_frames]))


def _finite_metric(x):
    try:
        return float(x) if x is not None and np.isfinite(float(x)) else None
    except Exception:
        return None


def quality_summary(g, v, ring_mm, ring_radius, ring_wire, K, ids, rf, ref, dfm, n_input, n_b0, n_w0):
    sc = dfm.admission_status.value_counts().to_dict()
    def med(col):
        try:
            a = dfm[col].dropna().to_numpy(float)
            return float(np.median(a)) if len(a) else None
        except Exception:
            return None
    def pct(col, q):
        try:
            a = dfm[col].dropna().to_numpy(float)
            return float(np.percentile(a, q)) if len(a) else None
        except Exception:
            return None
    rot = dfm['rotation_to_previous_deg'].dropna().to_numpy(float) if 'rotation_to_previous_deg' in dfm else np.array([])
    tr = dfm['center_to_previous_mm'].dropna().to_numpy(float) if 'center_to_previous_mm' in dfm else np.array([])
    jumps = int(((rot > 10.0) | (tr > 5.0)).sum()) if len(rot) else 0
    return dict(
        group=g, video=v, ring_mm=float(ring_mm), ring_cad_mm=[float(ring_radius), float(ring_wire)],
        K=np.asarray(K, float).tolist(), n_input_frames=int(n_input),
        n_b0_poses=int(n_b0), n_w0_poses=int(n_w0), n_evaluated_poses=int(len(dfm)),
        n_accept=int(sc.get('ACCEPT', 0)), n_quarantine=int(sc.get('QUARANTINE', 0)),
        n_insufficient_evidence=int(sc.get('INSUFFICIENT_EVIDENCE', 0)),
        n_reject=int(sc.get('REJECT', 0)),
        ring_mae_mean_px=_finite_metric(dfm['ring_raw_mae'].mean()) if 'ring_raw_mae' in dfm else None,
        ring_mae_median_px=med('ring_raw_mae'), ring_mae_p90_px=pct('ring_raw_mae', 90),
        ring_projection_failures=int((~dfm['cad_valid'].astype(bool)).sum()) if 'cad_valid' in dfm else None,
        held_track_count_median=med('held_n'), held_median_px=med('held_median'),
        held_p95_px=med('held_p95'),
        positive_depth_fraction=_finite_metric(dfm['positive_depth'].mean()) if 'positive_depth' in dfm else None,
        big_error_fraction_max=_finite_metric(dfm['big_error_fraction'].max()) if 'big_error_fraction' in dfm else None,
        max_adjacent_rotation_deg=float(rot.max()) if len(rot) else None,
        max_adjacent_translation_mm=float(tr.max()) if len(tr) else None,
        trajectory_jump_count=jumps,
        reference=int(ref), ids=[str(x) for x in ids], raw_frames=[int(x) for x in rf])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--group', required=True)
    ap.add_argument('--video', required=True)
    ap.add_argument('--stage', default='all', choices=['all', 'b0', 'w0', 'evaluate', 'admit', 'export'])
    ap.add_argument('--output', default=None)
    ap.add_argument('--prepared-root', default=str(T006 / 'runs' / 'prepared'))
    ap.add_argument('--workdir', default=None)
    ap.add_argument('--ring-mm', type=float, default=None)
    ap.add_argument('--pair-offsets', default='')
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    g, v = args.group, args.video.zfill(3)
    out = Path(args.output) if args.output else WS / 'camera_mainline' / g / f'video{v}'
    run = (Path(args.workdir) if args.workdir
           else WS / 'experiments/TASK-E4-W0-MAINLINE-CONSOLIDATION-015' / 'runs' / f'{g}_{v}')
    meta = load_prepared(g, v, args.prepared_root)
    ring_mm = float(args.ring_mm if args.ring_mm is not None else meta.get('ring_mm', 10.0))
    ring_radius = ring_mm / 2.0 + 0.6
    ring_wire = 0.6
    pair_offsets = [int(x) for x in str(args.pair_offsets).split(',') if x.strip()] or None
    if args.dry_run:
        print(json.dumps(dict(group=g, video=v, n_views=len(meta['views']),
                              video_path=meta.get('video_path'), ring_mm=ring_mm,
                              ring_cad_mm=[ring_radius, ring_wire],
                              frames=[q['raw_frame'] for q in meta['views'][:5]]), indent=1))
        return

    import unified_camera as U5
    out.mkdir(parents=True, exist_ok=True)
    run.mkdir(parents=True, exist_ok=True)
    first = np.load(meta['views'][0]['cache'])
    if not np.allclose(np.asarray(first['K'], float), np.asarray(U5.K_CFG, float)):
        write_status(out, 'INVALID_INPUT', 'input', 'K_DIFFERS_FROM_FROZEN_640x360', g, v, 'K_MISMATCH')
        return 2

    try:
        ns, ordered, arrays = build_ns_and_views(g, v, meta, run, ring_radius, ring_wire, pair_offsets)
        tr, pack, tracks_source = stage_tracks(ns, ordered, run, g, v)
        xy_tr = tr['xy']
        held_mask = np.asarray(tr['held']).astype(bool)
        rings = stage_ring(ns, ordered, arrays, run, ring_radius, ring_wire)
        edges = ns['pair_data'](tr, pack)
        rf = [x['meta']['raw_frame'] for x in ordered]
        ref = pick_ref(rf)
        ini, _ = ns['initialize'](rings, tr, edges, ref, 0)
        if any(x is None for x in ini):
            write_status(out, 'INSUFFICIENT_EVIDENCE', 'ring_first', 'RING_FIRST_INCOMPLETE', g, v,
                         'RING_FIRST_INCOMPLETE')
            return 2
        X, tids, support = ns['triangulate_training'](ini, tr)
    except ValueError as e:
        if 'INSUFFICIENT_RING_OBSERVATION' in str(e):
            write_status(out, 'INSUFFICIENT_EVIDENCE', 'ring', str(e), g, v,
                         'INSUFFICIENT_RING_OBSERVATION')
            return 2
        raise
    except RuntimeError as e:
        msg = str(e)
        if 'insufficient positive Ring-initialized scene points' in msg:
            write_status(out, 'BLOCKED_QUALITY_GATE', 'triangulation', msg, g, v,
                         'INSUFFICIENT_SCENE_POINTS')
            return 2
        if 'Ring pose graph disconnected' in msg:
            write_status(out, 'BLOCKED_QUALITY_GATE', 'ring_first', msg, g, v,
                         'RING_POSE_GRAPH_DISCONNECTED')
            return 2
        raise

    n_b0 = n_w0 = 0
    if args.stage in ('all', 'b0'):
        cur, P, ba = ns['BA'](ini, X, tids, support, tr, ref)
        np.savez_compressed(run / 'B0.npz', c2w=cur, points=P, point_track_ids=tids, K=U5.K_CFG,
                            ids=[x['meta']['id'] for x in ordered], reference=ref, init_version=0,
                            ring_cad_mm=np.array([ring_radius, ring_wire]))
        n_b0 = len(cur)
        (run / 'B0.json').write_text(json.dumps(dict(nfev=ba.get('nfev'), success=ba.get('success'),
                                                     objective=ba.get('training_soft_l1_objective')), indent=1))
        print('B0 done', ba.get('nfev'), flush=True)
    if args.stage in ('all', 'w0'):
        b0 = np.load(run / 'B0.npz')
        X2, tids2, sup2 = ns['triangulate_training'](b0['c2w'], tr)
        ns['cfg'] = lambda: dict(U5.CFG, BA_max_nfev=30)
        cur, P, ba = ns['BA'](b0['c2w'], X2, tids2, sup2, tr, ref)
        np.savez_compressed(run / 'W0.npz', c2w=cur, points=P, point_track_ids=tids2, K=U5.K_CFG,
                            ids=[x['meta']['id'] for x in ordered], reference=ref, init_version=0,
                            warm_start='B0', ring_cad_mm=np.array([ring_radius, ring_wire]))
        n_w0 = len(cur)
        (run / 'W0.json').write_text(json.dumps(dict(nfev=ba.get('nfev'), success=ba.get('success'),
                                                     objective=ba.get('training_soft_l1_objective')), indent=1))
        print('W0 done', ba.get('nfev'), flush=True)

    quality = None
    if args.stage in ('all', 'evaluate', 'admit', 'export'):
        import camera_admission as A
        import camera_rotation_metrics as RM
        import contour_metrics as CM
        import evaluate_held_geometry as EV
        import pandas as pd
        POL = A.load_policy(WS / 'camera_mainline/CAMERA_ADMISSION_POLICY.yaml')
        if (run / 'W0.npz').exists():
            d = np.load(run / 'W0.npz')
            cams = d['c2w']
        else:
            d = np.load(run / 'B0.npz')
            cams = d['c2w']
        ids = [str(x) for x in d['ids']]
        order = sorted(range(len(ids)), key=lambda i: (rf[i], ids[i]))
        rows = []
        for i, cid in enumerate(ids):
            m = dict(arm=f'{g}/{v}', view=cid, raw_frame=rf[i],
                     pose_valid=bool(RM.check_so3(cams[i][:3, :3])[0]), cad_valid=True)
            qt = np.load(run / 'observations' / (cid + '_ring.npz'))['q_train']
            try:
                m['ring_raw_mae'] = CM.ring_raw_mae(cams[i], qt, arrays[cid]['K'],
                                                    ring_radius, ring_wire)
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
                round(RM.relative_deg(cams[order[pos - 1]], cams[i]), 3))
            m['center_to_previous_mm'] = (None if pos == 0 else
                round(RM.center_distance_mm(cams[order[pos - 1]], cams[i]), 3))
            m['rotation_from_reference_deg'] = round(RM.relative_deg(cams[ref], cams[i]), 3)
            dec = A.decide(m, POL, artefact=('DEGENERATE_TRIANGULATION'
                           if m['triangulation_degenerate_n'] > 0 else None))
            m.update(admission_status=dec['status'], admission_reasons=';'.join(dec['reasons']))
            rows.append(m)
        dfm = pd.DataFrame(rows)
        (run / 'PER_VIEW.csv').parent.mkdir(parents=True, exist_ok=True)
        dfm.to_csv(run / 'PER_VIEW.csv', index=False)
        dfm.to_csv(out / 'admission.csv', index=False)
        acc = dfm[dfm.admission_status == 'ACCEPT'].view.tolist()
        idx = [ids.index(x) for x in acc]
        np.savez_compressed(out / 'camera_result.npz', c2w=cams, K=U5.K_CFG, ids=np.array(ids),
                            raw_frames=np.array(rf), reference=ref,
                            ring_cad_mm=np.array([ring_radius, ring_wire]),
                            source_arm='W0', admission_status=np.array(dfm.admission_status.values),
                            pose_convention=np.array(['c2w']))
        np.savez_compressed(out / 'accepted_cameras.npz', c2w=cams[idx], K=U5.K_CFG, ids=np.array(acc),
                            raw_frames=np.array([rf[i] for i in idx]), reference=ref,
                            ring_cad_mm=np.array([ring_radius, ring_wire]), source_arm='W0',
                            pose_convention=np.array(['c2w']))
        quality = quality_summary(g, v, ring_mm, ring_radius, ring_wire, U5.K_CFG,
                                  ids, rf, ref, dfm, len(ordered), n_b0, n_w0)
        (out / 'quality_summary.json').write_text(json.dumps(quality, indent=1))
        status = 'COMPLETED_VALID' if quality['n_accept'] > 0 else 'COMPLETED_LIMITED'
        write_status(out, status, 'admission',
                     'ADMISSION_COMPLETE' if status == 'COMPLETED_VALID' else 'NO_ACCEPT_CAMERAS',
                     g, v)
        print('EVAL', quality['n_accept'], quality['n_quarantine'],
              quality['n_insufficient_evidence'], quality['n_reject'],
              'ring=%s held=%s p95=%s' % (quality['ring_mae_mean_px'],
              quality['held_median_px'], quality['held_p95_px']), flush=True)

    # Export all intermediate observations and pose artefacts into the output package.
    (out / 'observations').mkdir(parents=True, exist_ok=True)
    for p in sorted((run / 'observations').glob('*')):
        if p.is_file():
            (out / 'observations' / p.name).write_bytes(p.read_bytes())
    for f in ('B0.npz', 'W0.npz', 'B0.json', 'W0.json'):
        if (run / f).exists():
            (out / f).write_bytes((run / f).read_bytes())

    man = dict(
        group=g, video=v, ring_mm=ring_mm, ring_cad_mm=[ring_radius, ring_wire],
        K=np.asarray(U5.K_CFG, float).tolist(),
        source_video=meta.get('video_path'), source_video_sha256=meta.get('video_sha256'),
        prepared=dict(path=meta['prepared_path'], sha256=meta['prepared_sha256'],
                      views_sha256=meta['views_sha256']),
        ids=[x['meta']['id'] for x in ordered], raw_frames=rf, ref=ref,
        tracks=dict(source=tracks_source,
                    path=str(out / 'observations/tracks005.npz'),
                    sha256=sha(out / 'observations/tracks005.npz'),
                    observations=[p.name for p in sorted((out / 'observations').glob('*'))]),
        gate='camera_mainline/CAMERA_ADMISSION_POLICY.yaml',
        config=dict(policy_sha256=sha(WS / 'camera_mainline/CAMERA_ADMISSION_POLICY.yaml'),
                    frozen_config_sha256=sha(T002 / 'code/frozen_calibration/config.json')),
        code=dict(entry=sha(Path(__file__)),
                  gate=sha(WS / 'camera_mainline/code/camera_admission.py'),
                  held_eval=sha(WS / 'camera_mainline/code/evaluate_held_geometry.py'),
                  contour=sha(WS / 'camera_mainline/code/contour_metrics.py'),
                  unified=sha(T005 / 'code/unified_camera.py')),
        stages=args.stage,
        status=(quality and ('COMPLETED_VALID' if quality['n_accept'] > 0 else 'COMPLETED_LIMITED'))
               or None)
    for name in ('B0.npz', 'W0.npz', 'camera_result.npz', 'accepted_cameras.npz',
                 'admission.csv', 'quality_summary.json'):
        p = out / name
        if p.exists():
            man.setdefault('artifacts', {})[name] = dict(sha256=sha(p), bytes=p.stat().st_size)
    txt = json.dumps(man, indent=1)
    (out / 'manifest.json').write_text(txt)
    (out / 'RUN_MANIFEST.json').write_text(txt)
    print('exported ->', out, flush=True)


if __name__ == '__main__':
    sys.exit(main())
