"""TASK-E4-UNIFIED-RING-RGB-CAMERA-MAINLINE-005 : single unified Ring+RGB camera pipeline.

All ten (group, video) instances run through this file with the SAME code, SAME
config, SAME thresholds and SAME version-selection rule. There is no `if group ==`.

Reused (read-only) solver sources: the frozen V6 files captured by
TASK-E4-UNIFIED-PIPELINE-COMPLETION-002 under code/frozen_calibration/.
Only assembly/IO is new here.
"""
import argparse, hashlib, json, os, sys, traceback
from pathlib import Path
import numpy as np
import cv2
from scipy.optimize import least_squares, minimize_scalar
from scipy.sparse import lil_matrix
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation

WS = Path('/home/liu/ring_first_3d_workspace')
T002 = WS / 'experiments/TASK-E4-UNIFIED-PIPELINE-COMPLETION-002'
FROZEN = T002 / 'code/frozen_calibration'
TASK = WS / 'experiments/TASK-E4-UNIFIED-RING-RGB-CAMERA-MAINLINE-005'
RUNS = TASK / 'runs'
GROUPS = ['G01', 'G02', 'G03', 'G05', 'G06']
VIDEOS = ['004', '005']

sys.path.insert(0, str(WS / 'src'))
from ring_first_3d.mainline.native.camera import recover, observe, residual, torus_contours, RF_CONFIG
from ring_first_3d.mainline.native.geometry import project, validate_camera
from ring_first_3d.mainline.native.io import save_json, sha256

K_CFG = np.array(json.loads((FROZEN / 'config.json').read_text())['K'], float)
CFG = json.loads((FROZEN / 'config.json').read_text())


def stats(x):
    a = np.asarray(x, float); a = a[np.isfinite(a)]
    return dict(N=int(len(a)), MAE=float(np.abs(a).mean()) if len(a) else None,
                p95=float(np.percentile(np.abs(a), 95)) if len(a) else None,
                maximum=float(np.abs(a).max()) if len(a) else None)


# ---------------------------------------------------------------- views / IO
def all_views():
    return json.loads((T002 / 'audit/SELECTED_VIEWS.json').read_text())


def instance_views(g, v):
    return [x for x in all_views()
            if x['meta']['case'] == g and x['meta']['video'] == v and x['meta']['role'] == 'FIT']


def load_cache(x):
    d = np.load(x['cache']['path'])
    return dict(RGB=d['RGB'], labels=d['labels'], K=d['K'])


# ---------------------------------------------------------------- frozen namespace
def _extract(file, names, ns):
    import ast
    nodes = [n for n in ast.parse(Path(file).read_text()).body
             if isinstance(n, ast.FunctionDef) and n.name in names]
    assert len(nodes) == len(names), (file, names, len(nodes))
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(file), 'exec'), ns)


def build_namespace(root, fit, arrays, ring_radius=5.6, ring_wire=.6, pair_offsets=None):
    root = Path(root); (root / 'observations').mkdir(parents=True, exist_ok=True)
    (root / 'scripts').mkdir(exist_ok=True)
    import shutil
    shutil.copyfile(FROZEN / 'v6_common.py', root / 'scripts/v6_common.py')
    shutil.copyfile(FROZEN / 'config.json', root / 'config.json')
    (root / 'predictions').mkdir(exist_ok=True); (root / 'metrics').mkdir(exist_ok=True)
    def _rf(v):
        r = v['meta'].get('raw_frame')
        return (0, int(r)) if isinstance(r, (int, float)) else (1, 0)
    ordered = sorted(fit, key=lambda v: (_rf(v), v['meta']['id']))
    def _rfi(v):
        r = v['meta'].get('raw_frame')
        return int(r) if isinstance(r, (int, float)) else -1
    ledger = [dict(id=v['meta']['id'], raw_frame=_rfi(v),
                   RGB_path=v['meta']['RGB_source'], Mask_path=v['meta']['Mask_source']) for v in ordered]
    K = np.array(fit[0]['meta']['K'], float)
    assert np.allclose(K, K_CFG), 'K differs from frozen config'

    def obs(cid):
        return dict(np.load(root / 'observations' / (cid + '_ring.npz')))

    ns = dict(Path=Path, np=np, cv2=cv2, Rotation=Rotation, least_squares=least_squares,
              minimize_scalar=minimize_scalar, lil_matrix=lil_matrix, cKDTree=cKDTree,
              K=K, R=root, project=project, stats=stats,
              cfg=lambda: (dict(CFG, pair_offsets=list(pair_offsets)) if pair_offsets else CFG),
              ledger=lambda: ledger, image=lambda a: arrays[a['id']]['RGB'],
              labels=lambda a: arrays[a['id']]['labels'],
              save=lambda p, x: save_json(root / p, x),
              load=lambda p: json.loads((root / p).read_text()),
              obs=obs, ring_residual=lambda C, ob, part='train', K0=K: residual(C, ob, K0, ring_radius, ring_wire))

    def freeze(name, files):
        save_json(root / 'metrics' / ('freeze_' + name + '.json'),
                  dict(files=[dict(path=str(Path(p)), sha256=sha256(p)) for p in files],
                       GT_or_HERO_or_old_camera_read=False))

    def verify(name):
        if name == 'ring_inputs':
            return
        for r in json.loads((root / 'metrics' / ('freeze_' + name + '.json')).read_text())['files']:
            assert sha256(r['path']) == r['sha256']
    ns.update(freeze=freeze, verify=verify)
    _extract(FROZEN / 'background_registration.py', ['skew', 'fundamental', 'epi', 'vec', 'pose'], ns)
    _extract(FROZEN / 'v6_common.py', ['positive_gauge', 'spin', 'unit', 'triangle'], ns)
    _extract(FROZEN / 'local_ring_sfm.py',
             ['pair_data', 'canonical_reference', 'initialize', 'triangulate_training', 'BA'], ns)
    _extract(FROZEN / 'track005.py', ['main'], ns)
    ns['__file__'] = str(FROZEN / 'track005.py')
    return ns, ordered


# ---------------------------------------------------------------- ring observation
def ring_candidates(arrays, ordered, root, ring_radius=5.6, ring_wire=.6, ring_mode='all'):
    rings = []
    for v in ordered:
        cid = v['meta']['id']; a = arrays[cid]
        ob = observe(a['labels'], ring_mode)
        if len(ob['q_train']) < 20:
            raise ValueError(f'INSUFFICIENT_RING_OBSERVATION {cid}')
        np.savez_compressed(root / 'observations' / (cid + '_ring.npz'), **ob)
        rawpath = root / 'predictions' / (cid + '_RING_ONLY.json')
        if rawpath.exists():
            raw = json.loads(rawpath.read_text())
        else:
            raw = recover(a['labels'], a['K'], rgb_geometry=None, initial_pose=None,
                          ring_radius=ring_radius, ring_wire=ring_wire, ring_mode=ring_mode)
            save_json(rawpath, raw)
        cands = []
        for alt in raw['ring_alternatives']:
            Q = np.array(alt['Q'], float); C = np.eye(4)
            C[:3, :3] = Q.T; C[:3, 3] = -Q.T @ np.array(alt['center'], float)
            cands.append(dict(alt, c2r=C))
        rings.append(dict(id=cid, candidates=cands))
    save_json(root / 'predictions/RING_CANDIDATES.json', rings)
    return rings


# ---------------------------------------------------------------- scoring / selection
def version_score(ns, cur, tr, ref, ba):
    """Training-side only.  held tracks are excluded from every term."""
    n = len(cur); errs = []
    ob = [ns['obs'](a['id']) for a in ns['ledger']()]
    ring = []
    for i in range(n):
        r = ns['ring_residual'](cur[i], ob[i])
        ring.append(float(np.abs(np.asarray(r, float)).mean()))
    # training feature reprojection from tracks (held excluded inside pair_data already,
    # but xy still contains held; exclude them explicitly here)
    xy = tr['xy']; held = np.asarray(tr['held']).astype(bool)
    for i in range(n):
        for t in np.flatnonzero(~held):
            u = xy[t, i]
            if not np.isfinite(u[0]):
                continue
            others = [j for j in range(n) if j != i and np.isfinite(xy[t, j, 0])]
            if len(others) < 2:
                continue
            best, bd = None, -1
            for a in range(len(others)):
                for b in range(a + 1, len(others)):
                    j, k = others[a], others[b]
                    d = np.linalg.norm(cur[j][:3, 3] - cur[k][:3, 3])
                    if d > bd:
                        bd, best = d, (j, k)
            X = ns['triangle']([cur[best[0]], cur[best[1]]], [xy[t, best[0]], xy[t, best[1]]])
            uv, z = project(X[None], cur[i], K_CFG)
            if np.isfinite(uv).all() and z[0] > 0:
                errs.append(float(np.linalg.norm(uv[0] - u)))
    feat = float(np.mean(errs)) if errs else float('nan')
    ringm = float(np.mean(ring))
    conv = 0.0 if ba.get('success') else 1.0
    # positivity is already penalised inside BA (10*max(0,0.1-pc_z)); use the
    # training objective as its training-side proxy instead of recomputing depths.
    obj = float(ba.get('training_soft_l1_objective') or 0.0)
    score = 1.0 * ringm + 0.1 * (feat if np.isfinite(feat) else 50.0) + 0.02 * obj + 0.5 * conv
    return dict(score=float(score), ring_MAE_mean_px=ringm, feat_train_reproj_MAE_px=feat,
                ba_training_objective=obj, ba_success=bool(ba.get('success')),
                ba_nfev=ba.get('nfev'))


def run_instance(g, v):
    root = RUNS / g / v
    root.mkdir(parents=True, exist_ok=True)
    fit = instance_views(g, v)
    assert len(fit) == 8, f'{g}/{v}: expected 8 FIT, got {len(fit)}'
    arrays = {x['meta']['id']: load_cache(x) for x in fit}
    ns, ordered = build_namespace(root, fit, arrays)
    inp = dict(inputs=[dict(id=x['meta']['id'], cache=x['cache']['path'],
                            sha256=sha256(x['cache']['path'])) for x in ordered],
               roles=['FIT'] * len(ordered), GT_used=False, HERO_used=False, Body_used=False,
               config=dict(path=str(FROZEN / 'config.json'), sha256=sha256(FROZEN / 'config.json')),
               RF_CONFIG=RF_CONFIG)
    save_json(root / 'INPUT_FREEZE.json', inp)

    rings = ring_candidates(arrays, ordered, root)
    ns['main']()                      # V6 track005 -> tracks005.npz / pairs005.npz
    tr = dict(np.load(root / 'observations/tracks005.npz'))
    pack = dict(np.load(root / 'observations/pairs005.npz'))
    edges = ns['pair_data'](tr, pack)
    raw_frames = [a['meta']['raw_frame'] for a in ordered]
    numeric = [(i, f) for i, f in enumerate(raw_frames) if isinstance(f, (int, float))]
    # reference view: raw_frame closest to 459 when frame numbers exist (V6 convention),
    # otherwise the middle view. Identical rule for every instance.
    ref = int(min(numeric, key=lambda t: abs(t[1] - 459))[0]) if numeric else len(ordered) // 2
    versions = {}
    for ver in range(CFG['pose_initializations']):
        try:
            ini, info = ns['initialize'](rings, tr, edges, ref, ver)
            X, tids, support = ns['triangulate_training'](ini, tr)
            cur, P, ba = ns['BA'](ini, X, tids, support, tr, ref)
            np.savez_compressed(root / 'predictions' / f'BA_{ver}.npz', c2w=cur, K=K_CFG,
                                points=P, track_ids=tids, ids=[a['meta']['id'] for a in ordered],
                                reference=ref, reference_raw_frame=raw_frames[ref])
            sc = version_score(ns, cur, tr, ref, ba)
            versions[ver] = dict(score=sc, ba=ba, c2w=cur, ok=True)
        except Exception:
            versions[ver] = dict(ok=False, error=traceback.format_exc())
    save_json(root / 'VERSION_SCORES.json', {str(k): ({'ok': V['ok'], **({
        'score': V['score']} if V['ok'] else {'error': V.get('error')})}) for k, V in versions.items()})

    ok = {k: V for k, V in versions.items() if V['ok']}
    if not ok:
        for k, V in versions.items():
            print(f'VERSION {k} FAILED:', str(V.get('error'))[-800:], flush=True)
    assert ok, 'NO_BA_VERSION'
    best = min(ok, key=lambda k: ok[k]['score']['score'])
    second = [k for k in ok if k != best]
    ambiguous = bool(second) and abs(ok[best]['score']['score'] - ok[second[0]]['score']['score']) <= 0.05 * abs(ok[best]['score']['score'])
    cur = ok[best]['c2w']

    # ---- per-view gate + independent evaluation (evaluation never selects)
    prov, quality = [], []
    for i, x in enumerate(ordered):
        cid = x['meta']['id']; K = arrays[cid]['K']; ob = dict(np.load(root / 'observations' / (cid + '_ring.npz')))
        d = cKDTree(torus_contours(cur[i], K).reshape(-1, 2)).query(ob['q_train'])[0]
        mae = float(np.mean(d)); p95 = float(np.percentile(d, 95))
        adm = mae <= 3.0
        res = dict(c2w_mm=cur[i].tolist(), candidate_source='UNIFIED_MULTIVIEW_BA',
                   ba_version=int(best), ring_boundary_MAE_px=mae, ring_boundary_p95_px=p95,
                   GT_used=False, Body_used=False, PnP_used_as_final_camera=False)
        validate_camera(cur[i], K)
        (root / 'camera' / cid).mkdir(parents=True, exist_ok=True)
        save_json(root / 'camera' / cid / 'CAMERA_RESULT.json', res)
        save_json(root / 'camera' / cid / 'ADMISSION.json',
                  dict(status='PASS' if adm else 'FAIL', ring_MAE_px=mae, threshold_px=3.0,
                       reasons=[] if adm else ['RING_REPROJECTION_ABOVE_FROZEN_3PX']))
        prov.append(dict(group=g, video=v, view=cid, role='FIT', ba_version=int(best),
                         reference_view=ordered[ref]['meta']['id'], reference_raw_frame=raw_frames[ref],
                         ring_source='native.observe(labels)', ring_sha256=sha256(root / 'observations' / (cid + '_ring.npz')),
                         rgb_source=x['meta']['RGB_source'], rgb_sha256=sha256(x['meta']['RGB_source']),
                         gauge_definition='ring at origin; reference view positive_gauge and xy azimuth zero',
                         GT_used=False, Body_used=False, PnP_used_as_final=False))
        quality.append(dict(group=g, video=v, view=cid, role='FIT', ring_MAE_px=mae, ring_p95_px=p95,
                            admission=bool(adm), ba_version=int(best)))

    # held-out evaluation (independent; not used for selection)
    held_eval = held_reprojection(cur, [x['meta']['id'] for x in ordered], tr, K_CFG)
    for i, q in enumerate(quality):
        e = held_eval[i]['errors']; pos = held_eval[i]['positive']
        n = len(e); mae = float(np.mean(e)) if n else float('nan'); p95 = float(np.percentile(e, 95)) if n else float('nan')
        pf = float(np.mean(pos)) if pos else float('nan')
        validated = (n >= 8 and np.isfinite(mae) and mae <= 3 and p95 <= 6 and pf >= 0.95)
        if q['admission'] and validated:
            st = 'VALIDATED'
        elif q['admission'] and n < 8:
            st = 'USABLE_WITH_CAUTION'
        elif q['admission']:
            st = 'USABLE_WITH_CAUTION'
        elif n < 8:
            st = 'INSUFFICIENT_EVIDENCE'
        else:
            st = 'INVALID'
        q.update(held_N=n, held_MAE_px=mae, held_p95_px=p95, held_positive=pf,
                 camera_file_exists=True, camera_admission_pass=bool(q['admission']),
                 camera_geometry_validated=bool(validated),
                 camera_usable_for_downstream=bool(q['admission']),
                 per_view_status=st)
    save_json(root / 'VALIDATION.json', dict(version_selected=int(best), ambiguous_version=ambiguous,
                                             versions={str(k): ok[k]['score'] for k in ok},
                                             views=quality,
                                             held_tracks_total=int(np.asarray(tr['held']).sum())))
    save_json(root / 'CAMERA_FREEZE.json', dict(
        files=[dict(path=str(root / 'camera' / q['view'] / 'CAMERA_RESULT.json'),
                    sha256=sha256(root / 'camera' / q['view'] / 'CAMERA_RESULT.json')) for q in quality],
        selected_version=int(best), config_sha256=sha256(FROZEN / 'config.json'),
        source_lock=[dict(path=str(FROZEN / f), sha256=sha256(FROZEN / f))
                     for f in ['track005.py', 'local_ring_sfm.py', 'v6_common.py', 'background_registration.py', 'config.json']],
        GT_or_HERO_or_Body_read=False))
    return prov, quality, versions, best, ambiguous


def held_reprojection(cams, ids, tr, K):
    n = len(ids); xy = tr['xy']; held = np.asarray(tr['held']).astype(bool)
    out = []
    for i in range(n):
        errs, pos = [], []
        for t in np.flatnonzero(held):
            u = xy[t, i]
            if not np.isfinite(u[0]):
                continue
            others = [j for j in range(n) if j != i and np.isfinite(xy[t, j, 0])]
            if len(others) < 2:
                continue
            best, bd = None, -1
            for a in range(len(others)):
                for b in range(a + 1, len(others)):
                    j, k = others[a], others[b]
                    d = np.linalg.norm(cams[j][:3, 3] - cams[k][:3, 3])
                    if d > bd:
                        bd, best = d, (j, k)
            X = triangulate(xy[t, best[0]], xy[t, best[1]], cams[best[0]], cams[best[1]], K)
            if X is None:
                continue
            uv, z = project(X[None], cams[i], K)
            if not np.isfinite(uv).all():
                continue
            errs.append(float(np.linalg.norm(uv[0] - u))); pos.append(bool(z[0] > 0))
        out.append(dict(errors=errs, positive=pos))
    return out


def triangulate(x1, x2, C1, C2, K):
    def rows(uv, C):
        P = np.asarray(K) @ np.c_[C[:3, :3].T, -C[:3, :3].T @ C[:3, 3]]
        u, v = uv
        return np.r_[u * P[2] - P[0], v * P[2] - P[1]].reshape(2, 4)
    A = np.r_[rows(x1, C1), rows(x2, C2)]
    _, _, Vt = np.linalg.svd(A)
    Xh = Vt[-1]
    return None if abs(Xh[3]) < 1e-12 else Xh[:3] / Xh[3]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--group'); ap.add_argument('--video')
    a = ap.parse_args()
    import pandas as pd
    prov, quality, failures, coverage, inputs = [], [], [], [], []
    for g in GROUPS:
        if a.group and a.group != g:
            continue
        for v in VIDEOS:
            if a.video and a.video != v:
                continue
            fit = instance_views(g, v)
            for x in fit:
                inputs.append(dict(group=g, video=v, view=x['meta']['id'], role='FIT',
                                   cache=x['cache']['path'], cache_sha256=sha256(x['cache']['path']),
                                   rgb_source=x['meta']['RGB_source'], rgb_sha256=sha256(x['meta']['RGB_source'])))
            try:
                p, q, vers, best, amb = run_instance(g, v)
                prov += p; quality += q
                cov = dict(group=g, video=v, fit_expected=8,
                           camera_file_exists=sum(1 for r in q if r['camera_file_exists']),
                           admission_pass=sum(1 for r in q if r['camera_admission_pass']),
                           geometry_validated=sum(1 for r in q if r['camera_geometry_validated']),
                           usable_for_downstream=sum(1 for r in q if r['camera_usable_for_downstream']),
                           validated=sum(1 for r in q if r['per_view_status'] == 'VALIDATED'),
                           usable_with_caution=sum(1 for r in q if r['per_view_status'] == 'USABLE_WITH_CAUTION'),
                           insufficient_evidence=sum(1 for r in q if r['per_view_status'] == 'INSUFFICIENT_EVIDENCE'),
                           invalid=sum(1 for r in q if r['per_view_status'] == 'INVALID'),
                           selected_version=int(best), ambiguous_version=bool(amb),
                           holdout_cameras='NOT_SOLVED_THIS_ROUND')
                coverage.append(cov)
                print(f'OK {g}/{v} version={best} ambiguous={amb} '
                      f'pass={cov["admission_pass"]} validated={cov["validated"]}', flush=True)
            except Exception:
                err = traceback.format_exc()
                failures.append(dict(group=g, video=v, stage='UNIFIED_PIPELINE', error=err[-1500:]))
                coverage.append(dict(group=g, video=v, fit_expected=8, camera_file_exists=0,
                                     admission_pass=0, geometry_validated=0, usable_for_downstream=0,
                                     validated=0, usable_with_caution=0, insufficient_evidence=0,
                                     invalid=0, selected_version='', ambiguous_version='',
                                     holdout_cameras='NOT_SOLVED_THIS_ROUND'))
                print(f'FAIL {g}/{v}\n{err}', flush=True)
    def _norm(df):
        for c in ('video',):
            if c in df.columns:
                df[c] = df[c].astype(str).str.replace(r'\.0$', '', regex=True).str.zfill(3)
        for c in ('group', 'view'):
            if c in df.columns:
                df[c] = df[c].astype(str)
        return df

    def _merge(name, df, keys):
        path = TASK / name
        df = _norm(df)
        if path.exists():
            try:
                old = _norm(pd.read_csv(path))
                if set(keys) <= set(old.columns) and len(df) and set(keys) <= set(df.columns):
                    drop = set(map(tuple, df[keys].astype(str).values.tolist()))
                    keep = [i for i, r in old.iterrows()
                            if tuple(str(r[k]) for k in keys) not in drop]
                    df = pd.concat([old.loc[keep], df], ignore_index=True)
            except Exception:
                pass
        df.to_csv(path, index=False)
    _merge('CAMERA_PROVENANCE.csv', pd.DataFrame(prov), ['group', 'video', 'view'])
    _merge('CAMERA_QUALITY_MATRIX.csv', pd.DataFrame(quality), ['group', 'video', 'view'])
    _merge('VIEW_COVERAGE_MATRIX.csv', pd.DataFrame(coverage), ['group', 'video'])
    _merge('FAILURE_REGISTRY.csv', pd.DataFrame(failures, columns=['group', 'video', 'stage', 'error']), ['group', 'video'])
    _merge('INPUT_MANIFEST.csv', pd.DataFrame(inputs), ['group', 'video', 'view'])
    print('written:', len(prov), 'provenance rows,', len(coverage), 'instances')


if __name__ == '__main__':
    main()
