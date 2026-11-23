#!/usr/bin/env python3
"""M2A diagnostics: Ring frame observability and RGB pose-graph connectivity.

Reads existing M1 prepared caches/W0 work dirs only. No frozen algorithm is edited.
"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np
import pandas as pd

WS = Path('/home/liu/ring_first_3d_workspace')
M1 = WS / 'runs/m1_final_39'
PREP = M1 / 'prepared'
WORK = M1 / 'work'
OUT = WS / 'runs/m2a_w0_recovery'
FROZEN = WS / 'experiments/TASK-E4-UNIFIED-PIPELINE-COMPLETION-002/code/frozen_calibration'
R6 = WS / 'experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R6/replay'
DXY = Path('/home/liu/new-polyp-dxy/src/dxy_mid')

sys.path.insert(0, str(WS / 'src'))
sys.path.insert(0, str(FROZEN))
sys.path.insert(0, str(R6))
sys.path.insert(0, str(WS / 'camera_mainline/code'))

RING_FAIL = [
    ('GP_IIa_14.0mm_closed_R5_single_refY', '005'),
    ('GP_IIa_22.0mm_closed_R5_single_refY', '004'),
    ('GP_IIa_22.0mm_closed_R5_single_refY', '005'),
    ('GP_Is_18.0mm_closed_R5_single_refY', '005'),
]
GRAPH_FAIL = [
    ('GP_IIa_14.0mm_closed_R5_single_refY', '004'),
    ('GP_Ip_2.9mm_closed_R10_single_refY', '005'),
    ('GP_Ip_2.9mm_closed_R5_single_refY', '005'),
    ('GP_Ip_4.0mm_closed_R5_single_refY', '006'),
    ('GP_Ip_6.2mm_closed_R5_single_refY', '005'),
    ('GP_Is_10.5mm_closed_R5_single_refY', '005'),
    ('GP_Is_18.0mm_closed_R10_single_refY', '005'),
    ('GP_Is_4.8mm_closed_R5_single_refY', '004'),
    ('GP_Is_4.8mm_closed_R5_single_refY', '005'),
    ('GP_Is_7.0mm_closed_R5_single_refY', '005'),
    ('GP_Is_9.79mm_closed_R10_single_refY', '004'),
]


def ring_module():
    import importlib
    import types
    sys.path.insert(0, str(DXY.parent))
    pkg = types.ModuleType('dxy_mid')
    pkg.__path__ = [str(DXY)]
    sys.modules.setdefault('dxy_mid', pkg)
    return importlib.import_module('dxy_mid._engine.ring_component')


def ring_diagnostics():
    from ring_first_3d.mainline.native.camera import observe, edge
    mod = ring_module()
    rows = []
    for g, v in RING_FAIL:
        p = PREP / f'{g}_{v}' / 'PREPARED.json'
        meta = json.loads(p.read_text())
        for q in meta['views']:
            a = np.load(q['cache'])
            labels = a['labels']
            ob = observe(labels)
            rm = labels == 2
            try:
                rep, pay = mod.recover(labels, a['RGB'][:, :, ::-1], 10.)
                inner = len(pay.get('inner_points', []))
                outer = len(pay.get('outer_points', []))
                center = 1 if rep.get('centerline') else 0
                conf = min(inner, outer) / max(1, max(inner, outer))
            except Exception as e:
                inner = outer = center = 0
                conf = 0.0
            qn = len(ob['q_train'])
            rows.append(dict(
                group_id=g, video_id=v, frame_id=q['view'], raw_frame=q['raw_frame'],
                ring_mask_pixels=int(rm.sum()),
                ring_boundary_pixels=int(len(edge(rm))),
                boundary_near_polyp=int(len(ob['unknown_boundary'])),
                boundary_after_filter=int(qn),
                q_train_count=int(qn), q_train_threshold=20,
                inner_visible_count=int(inner), outer_visible_count=int(outer),
                centerline_visible=int(center), inner_outer_confidence=float(conf),
                observation_status='OK' if qn >= 20 else 'INSUFFICIENT',
                failure_reason='' if qn >= 20 else 'QTRAIN_LT20',
                ring_type='R10' if float(meta.get('ring_mm', 10.0)) == 10.0 else 'R5'))
    pd.DataFrame(rows).to_csv(OUT / 'RING_FRAME_DIAGNOSTICS.csv', index=False)
    return rows


def _components(n, edges):
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for e in edges:
        a, b = find(int(e['i'])), find(int(e['j']))
        if a != b:
            parent[b] = a
    comp = {}
    for i in range(n):
        comp.setdefault(find(i), []).append(i)
    members = sorted(comp.values(), key=len, reverse=True)
    membership = {}
    for k, mem in enumerate(members):
        for i in mem:
            membership[i] = k
    return members, membership


def c0_edges(g, v):
    import ast
    tr = dict(np.load(WORK / g / v / 'observations/tracks005.npz'))
    pack = dict(np.load(WORK / g / v / 'observations/pairs005.npz'))
    cfgp = WORK / g / v / 'config.json'
    cfg = json.loads(cfgp.read_text()) if cfgp.exists() else {}
    src = (FROZEN / 'local_ring_sfm.py').read_text()
    node = next(n for n in ast.parse(src).body
                if isinstance(n, ast.FunctionDef) and n.name == 'pair_data')
    ns = dict(np=np, cv2=cv2, cfg=lambda: cfg)
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(FROZEN / 'local_ring_sfm.py'), 'exec'), ns)
    edges = ns['pair_data'](tr, pack)
    return tr, pack, cfg, edges


def pose_graph_diagnostics():
    import features019 as F19
    F19.R = OUT / 'features019'
    F19.R.mkdir(parents=True, exist_ok=True)
    out_diag, out_edges = [], []
    for g, v in GRAPH_FAIL:
        meta = json.loads((PREP / f'{g}_{v}' / 'PREPARED.json').read_text())
        tr, pack, cfg, edges0 = c0_edges(g, v)
        n = len(tr['frame_raw'])
        views = []
        for q in meta['views']:
            a = np.load(q['cache'])
            views.append(dict(id=q['view'], cache=str(q['cache']), raw_frame=q['raw_frame'],
                              T=np.eye(4).tolist(), K=np.asarray(a['K']).tolist(),
                              RGB_SHA256=q.get('rgb_sha256') or ''))
        F19.VIEWS = {x['id']: x for x in views}
        metrics = json.loads((WORK / g / v / 'metrics/track005.json').read_text())
        raw_pairs = metrics.get('pairs', [])
        # C0 pair rows
        pair_metrics = {k: raw_pairs[k] for k in range(len(raw_pairs))} if raw_pairs else {}
        c0_accept = {(int(e['i']), int(e['j'])): e for e in edges0}
        for k, (i, j) in enumerate(pack['ij']):
            i, j = int(i), int(j)
            pm = pair_metrics.get(k, {})
            rows = pack.get(f'pair{k}', np.zeros((0, 5)))
            e = c0_accept.get((i, j))
            out_edges.append(dict(
                stage='C0', group_id=g, video_id=v, frame_i=int(i), frame_j=int(j),
                raw_frame_i=int(tr['frame_raw'][i]), raw_frame_j=int(tr['frame_raw'][j]),
                temporal_gap=int(abs(int(tr['frame_raw'][j]) - int(tr['frame_raw'][i]))),
                raw_sift_matches=pm.get('appearance_matches'), mutual_matches=pm.get('union_consistent'),
                track_supported_matches=int(len(rows)), ransac_inliers=(int(len(e['rows'])) if e else 0),
                inlier_ratio=(float(len(e['rows']) / max(1, len(rows))) if e and len(rows) else None),
                edge_accepted=bool(e), edge_rejection_reason=('' if e else 'LT12_OR_NO_F'),
                ring_type='R10' if float(meta.get('ring_mm', 10.0)) == 10.0 else 'R5'))
        # C1 all pairs via features019 matches
        c1_edges = []
        for i in range(n):
            for j in range(i + 1, n):
                try:
                    m = F19.matches(views[i], views[j])
                    good = int(np.asarray(m['RGB_RANSAC']).sum())
                    raw = int(len(m['index_pairs']))
                    acc = good >= 12
                    if acc:
                        c1_edges.append(dict(i=i, j=j, rows=np.zeros((good, 5))))
                    out_edges.append(dict(
                        stage='C1', group_id=g, video_id=v, frame_i=i, frame_j=j,
                        raw_frame_i=int(tr['frame_raw'][i]), raw_frame_j=int(tr['frame_raw'][j]),
                        temporal_gap=int(abs(int(tr['frame_raw'][j]) - int(tr['frame_raw'][i]))),
                        raw_sift_matches=raw, mutual_matches=raw,
                        track_supported_matches=good, ransac_inliers=good,
                        inlier_ratio=(float(good / raw) if raw else None),
                        edge_accepted=bool(acc), edge_rejection_reason=('' if acc else 'LT12_INLIERS'),
                        ring_type='R10' if float(meta.get('ring_mm', 10.0)) == 10.0 else 'R5'))
                except Exception as e:
                    out_edges.append(dict(stage='C1', group_id=g, video_id=v, frame_i=i, frame_j=j,
                                          raw_frame_i=int(tr['frame_raw'][i]), raw_frame_j=int(tr['frame_raw'][j]),
                                          temporal_gap=None, raw_sift_matches=None, mutual_matches=None,
                                          track_supported_matches=None, ransac_inliers=None,
                                          inlier_ratio=None, edge_accepted=False,
                                          edge_rejection_reason=f'MATCH_ERROR {type(e).__name__}',
                                          ring_type='R10' if float(meta.get('ring_mm', 10.0)) == 10.0 else 'R5'))
        for stage, ee in (('C0', edges0), ('C1', c1_edges)):
            members, membership = _components(n, ee)
            out_diag.append(dict(
                group_id=g, video_id=v, stage=stage,
                ring_type='R10' if float(meta.get('ring_mm', 10.0)) == 10.0 else 'R5',
                n_frames=n, n_candidate_pairs=(len(pack['ij']) if stage == 'C0' else n * (n - 1) // 2),
                n_valid_edges=len(ee), n_connected_components=len(members),
                largest_component_size=max((len(x) for x in members), default=0),
                isolated_frames=sum(1 for x in members if len(x) == 1),
                component_membership=json.dumps({str(i): membership[i] for i in range(n)}),
                component_sizes=json.dumps([len(x) for x in members]),
                failure_reason='' if len(members) == 1 else 'MULTIPLE_COMPONENTS',
                pair_offsets=json.dumps(cfg.get('pair_offsets'))))
    pd.DataFrame(out_diag).to_csv(OUT / 'POSE_GRAPH_DIAGNOSTICS.csv', index=False)
    pd.DataFrame(out_edges).to_csv(OUT / 'POSE_GRAPH_EDGES.csv', index=False)
    return out_diag, out_edges


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    print('RING start', flush=True)
    rr = ring_diagnostics()
    print('ring rows', len(rr), flush=True)
    print('GRAPH start', flush=True)
    dd, ee = pose_graph_diagnostics()
    print('graph rows', len(dd), 'edge rows', len(ee), flush=True)
    print(pd.DataFrame(dd)[['group_id', 'video_id', 'stage', 'n_connected_components', 'n_valid_edges']].to_string(index=False))


if __name__ == '__main__':
    main()
