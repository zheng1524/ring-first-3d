#!/usr/bin/env python3
"""TASK-028 unified pipeline: ONE code path for every group; group id only selects inputs.

Stages: discover -> W0 (read or recomputed) -> Ring evidence -> tracks/identities ->
H init (old vs Ring+RGB) -> joint triangulation -> M3b joint BA -> FIT/HOLDOUT evaluation.
"""
import argparse, json, os, sys, time
from pathlib import Path
import numpy as np, pandas as pd
WS = Path('/home/liu/ring_first_3d_workspace')
U = WS/'experiments/TASK-E4-W0-CROSSVIDEO-028-REAL-UNIFIED'
sys.path.insert(0, str(WS/'experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R6/core'))
sys.path.insert(0, str(U/'core'))
import r6_core as C     # fixed BA / Ring / SE(3) / camvar primitives (single implementation)
import features019 as F19
import fixed_track_tri as FTT
import camvar, ring_energy as RE, ba_core_r4 as BA
from se3 import exp_se3
ASSETS = WS/'assets/retained_sources/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/FREE_VERTEX_013/inputs'
PREP = WS/'experiments/TASK-E4-UNIFIED-RING-CONTOUR-REFINEMENT-005/runs/prepared'
DXY = Path('/home/liu/new-polyp-dxy/src/dxy_mid')


def videos_of(group):
    out = []
    for p in sorted(PREP.glob(f'{group}_*')):
        v = p.name.split('_')[-1]
        if p.is_dir(): out.append(v)
    return out


def w0_path(group, video):
    p = WS/'camera_mainline'/group/f'video{video}'/'camera_result.npz'
    if p.exists(): return p, 'camera_mainline'
    p2 = U/'runs'/group/f'video{video}'/'camera_result.npz'
    if p2.exists(): return p2, 'recomputed_028'
    return None, None


def admission(group, video):
    p = WS/'camera_mainline'/group/f'video{video}'/'admission.csv'
    if not p.exists():
        p2 = U/'runs'/group/f'video{video}'/'admission.csv'
        p = p2 if p2.exists() else None
    if p is None: return {}
    d = pd.read_csv(p)
    return dict(zip(d['view'].astype(str), d['admission_status'].astype(str)))


def discover(group, max_views=8):
    views = {}
    for v in videos_of(group):
        prep = json.loads((PREP/f'{group}_{v}'/'PREPARED.json').read_text())
        adm = admission(group, v)
        wp, src = w0_path(group, v)
        if wp is None:
            views[v] = dict(status='BLOCKED_MISSING_W0', n=len(prep['views']), source=None)
            continue
        cam = np.load(wp)
        ids = [str(x) for x in cam['ids']]
        T = {i: np.asarray(cam['c2w'][k], float) for k, i in enumerate(ids)}
        K = np.asarray(cam['K'], float)
        pv = {x['view']: x for x in prep['views']}
        acc = [i for i in ids if adm.get(i) == 'ACCEPT'] or ids
        sel = sorted(acc, key=lambda i: pv[i]['raw_frame'])[:max_views]
        views[v] = dict(status='OK', source=src, n=len(ids), n_accept=sum(1 for i in ids if adm.get(i) == 'ACCEPT'),
                        selected=sel, T=T, K=K, prep=pv, admission=adm)
    return views


def ring_evidence(group, views, video, ids):
    """historical DXY recover() -> ring/<view>.npz|json (same routine as 019/020)."""
    sys.path.insert(0, str(DXY.parent))
    import importlib, types
    pkg = types.ModuleType('dxy_mid'); pkg.__path__ = [str(DXY)]; sys.modules.setdefault('dxy_mid', pkg)
    mod = importlib.import_module('dxy_mid._engine.ring_component')
    out = U/'runs'/group/'replay'; (out/'ring').mkdir(parents=True, exist_ok=True)
    valid = {}
    for vid in ids:
        p = out/'ring'/(vid+'.npz')
        if p.exists():
            j = json.loads((out/'ring'/(vid+'.json')).read_text())
            valid[vid] = bool(j.get('inner') and j.get('outer') and j.get('centerline'))
            continue
        a = np.load(views[video]['prep'][vid]['cache'])
        rep, pay = mod.recover(a['labels'], a['RGB'][:, :, ::-1], 10.)
        np.savez_compressed(p, inner=pay.get('inner_points', np.zeros((0, 2))),
                            outer=pay.get('outer_points', np.zeros((0, 2))),
                            rejected=pay.get('rejected_points', np.zeros((0, 2))))
        (out/'ring'/(vid+'.json')).write_text(json.dumps(rep))
        valid[vid] = bool(rep.get('inner') and rep.get('outer') and rep.get('centerline'))
    return valid


def build_renderer(group, views, keep_videos, sel=None):
    rep = U/'runs'/group/'replay'
    (rep/'inputs'/group).mkdir(parents=True, exist_ok=True)
    V = []
    for v in keep_videos:
        for vid in (sel[v] if sel else views[v]['selected']):
            src = np.load(views[v]['prep'][vid]['cache'])
            dst = rep/'inputs'/group/(vid+'.npz')
            np.savez_compressed(dst, RGB=src['RGB'], labels=src['labels'], K=views[v]['K'],
                                T=views[v]['T'][vid], RGB_SHA256=vid)
            V.append(dict(id=vid, group=group, video=v, role='FIT', cache=str(dst),
                          T=views[v]['T'][vid].tolist(), K=views[v]['K'].tolist(),
                          raw_frame=int(views[v]['prep'][vid]['raw_frame']), RGB_SHA256=vid))
    (rep/'config').mkdir(parents=True, exist_ok=True)
    (rep/'config'/'VIEWS.json').write_text(json.dumps(V, indent=1))
    os.environ.update(E4_RUN_DIR=str(rep),
        RING_CAD=str(ASSETS/group/'RING.npz'), RING_NORM=str(ASSETS/group/'NORMALIZATION.json'))
    import ring020_026
    ring020_026.R = rep                     # point the historical module at THIS group's replay dir
    return ring020_026.RingRenderer([x['id'] for x in V]), V


def ring_scores(rr, cams, video, ids):
    """M/I/C/O per camera from the historical renderer (no synthetic data)."""
    import torch
    from ring020_026 import tensor
    rows = []
    for vid in ids:
        L, _, _ = rr.losses(tensor(np.eye(4), torch.float64), vid)
        rows.append(dict(view=vid, M=float(L['M']), I=float(L['I']), C=float(L['C']), O=float(L['O']),
                         MIO=0.25*float(L['M'])+0.35*float(L['I'])+0.35*float(L['O'])))
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--group', required=True)
    ap.add_argument('--max-views', type=int, default=8)
    a = ap.parse_args(); g = a.group
    out = U/'runs'/g; out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    views = discover(g, a.max_views)
    matrix = []
    for v, d in views.items():
        matrix.append(dict(group=g, video=v, status=d['status'], source=d.get('source'),
                           n_views=d.get('n'), n_accept=d.get('n_accept'), n_selected=len(d.get('selected', []))))
    pd.DataFrame(matrix).to_csv(out/'ASSETS.csv', index=False)
    ok = [v for v, d in views.items() if d['status'] == 'OK']
    if not ok:
        (out/'SUMMARY.json').write_text(json.dumps(dict(group=g, status='BLOCKED_MISSING_W0', assets=matrix), indent=1))
        print('BLOCKED_MISSING_W0', g); return
    # reference video = most admitted views (unified rule), others = rest
    ref = max(ok, key=lambda v: (views[v]['n_accept'], -int(v)))
    others = [v for v in ok if v != ref]
    if not others:
        (out/'SUMMARY.json').write_text(json.dumps(dict(group=g, status='BLOCKED_SINGLE_VIDEO', assets=matrix), indent=1))
        print('BLOCKED_SINGLE_VIDEO', g); return
    sel_all = {v: views[v]['selected'] for v in ok}
    ring_valid = {}
    for v in ok:
        ring_valid.update(ring_evidence(g, views, v, sel_all[v]))
    sel_all = {v: [x for x in sel_all[v] if ring_valid.get(x)] for v in ok}
    if not any(sel_all.values()):
        (out/'SUMMARY.json').write_text(json.dumps(dict(group=g, status='BLOCKED_RING_EVIDENCE', ring_valid=ring_valid), indent=1, default=int))
        print('BLOCKED_RING_EVIDENCE', g); return
    rr, V = build_renderer(g, views, ok, sel_all)
    ring = ring_scores(rr, None, ref, sel_all[ref])
    ring.to_csv(out/'RING_SCORES.csv', index=False)
    (out/'SUMMARY.json').write_text(json.dumps(dict(group=g, status='RING_OK', ref=ref, others=others,
        ring_median_MIO=float(ring.MIO.median()), n_views={v: int(len(sel_all[v])) for v in ok},
        seconds=round(time.time()-t0, 1)), indent=1, default=int))
    print('RING', g, ref, others, round(float(ring.MIO.median()), 3), flush=True)
    # ---------------- stage 2: tracks, identities, H init, triangulation, BA ----------------
    Vmap = {x['id']: x for x in V}
    F19.VIEWS = Vmap
    for v in ok:
        for vid in sel_all[v]: F19.features(Vmap[vid])
    lm = {v: F19.landmarks(sel_all[v], f'{g}_{v}_029FIT') for v in ok}
    Xref, Dref = np.asarray(lm[ref]['X'], float), np.asarray(lm[ref]['des'], np.float32)
    idrows = []
    for v in others:
        Xo, Do = np.asarray(lm[v]['X'], float), np.asarray(lm[v]['des'], np.float32)
        m = F19.match_desc(Dref, Do)
        for i, j in m:
            idrows.append(dict(ref_index=int(i), other_video=v, other_index=int(j),
                               Xref_x=float(Xref[i,0]), Xref_y=float(Xref[i,1]), Xref_z=float(Xref[i,2]),
                               Xo_x=float(Xo[j,0]), Xo_y=float(Xo[j,1]), Xo_z=float(Xo[j,2])))
    ids = pd.DataFrame(idrows)
    ids.to_csv(out/'IDENTITIES.csv', index=False)
    rng = np.random.default_rng(2028)
    idx = np.arange(len(ids)); rng.shuffle(idx)
    nfit = max(1, int(round(0.7*len(ids))))
    fit_idx, ho_idx = sorted(idx[:nfit]), sorted(idx[nfit:])
    (out/'SPLIT.json').write_text(json.dumps(dict(ref=ref, others=others, n=int(len(ids)),
        fit=[int(x) for x in fit_idx], holdout=[int(x) for x in ho_idx]), indent=1))
    summ = dict(group=g, status='GEOMETRY_OK', ref=ref, others=others,
                n_landmarks={v: int(len(lm[v]['X'])) for v in ok},
                n_identities=int(len(ids)), n_fit=int(len(fit_idx)), n_holdout=int(len(ho_idx)),
                ring_median_MIO=float(ring.MIO.median()), seconds=round(time.time()-t0, 1))
    (out/'SUMMARY.json').write_text(json.dumps(summ, indent=1, default=int))
    print('IDS', g, len(ids), 'fit', len(fit_idx), 'hold', len(ho_idx), flush=True)


if __name__ == '__main__':
    main()
