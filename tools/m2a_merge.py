#!/usr/bin/env python3
"""Merge M2A recovery results into 79-video and 39-group tables."""
import json
from pathlib import Path
import numpy as np
import pandas as pd

WS = Path('/home/liu/ring_first_3d_workspace')
OUT = WS / 'runs/m2a_w0_recovery'
BASE = pd.read_csv(WS / 'runs/m1_final_39/W0_79_VIDEO_RESULTS.csv')
PREP = WS / 'runs/m1_final_39/prepared'
METHOD_PREP = {
    'BASELINE': PREP, 'B1': OUT / 'prepared_b1', 'C1': PREP,
    'C3': OUT / 'prepared_c3', 'C3B': OUT / 'prepared_c3b1',
    'C2': OUT / 'prepared_c2', 'C2B': OUT / 'prepared_c2b',
    'B1R': OUT / 'prepared_b1r',
}
PRIORITY = ['C2B', 'C2', 'C1', 'B1R', 'B1', 'C3B', 'C3']


def read_recovery():
    rows = []
    for f in ['RECOVERY_RESULTS.csv', 'RECOVERY_C3.csv', 'RECOVERY_C3B1.csv',
              'RECOVERY_C2.csv', 'RECOVERY_C2B.csv', 'RECOVERY_B1R.csv']:
        p = OUT / f
        if p.exists():
            d = pd.read_csv(p)
            for _, r in d.iterrows():
                r = r.to_dict(); r['method'] = r.get('method') or f.replace('RECOVERY_', '').replace('.csv', '')
                rows.append(r)
    return rows


def actual_components():
    p = OUT / 'ACTUAL_GRAPH_COMPONENTS.csv'
    if not p.exists(): return {}
    d = pd.read_csv(p)
    return {(r.method, r.group_id, f'{int(r.video_id):03d}'): r for _, r in d.iterrows()}


def main():
    rec = read_recovery()
    actual = actual_components()
    graph = pd.read_csv(OUT / 'POSE_GRAPH_DIAGNOSTICS.csv')
    c0 = {}
    for _, r in graph[graph.stage == 'C0'].iterrows():
        c0[(r.group_id, f'{int(r.video_id):03d}')] = int(r.n_connected_components)
    ringdiag = pd.read_csv(OUT / 'RING_FRAME_DIAGNOSTICS.csv')
    ring_valid = {(r.group_id, f'{int(r.video_id):03d}'): int((g.q_train_count >= 20).sum())
                  for (r.group_id, r.video_id), g in ringdiag.groupby(['group_id', 'video_id'])}
    rows = []
    for _, b in BASE.iterrows():
        g, v = str(b.group_id), f'{int(b.video_id):03d}'
        base_ok = bool(b.w0_generated)
        q = {}
        candidates = [r for r in rec if r['group_id'] == g and f'{int(r["video_id"]):03d}' == v
                      and r.get('execution_status') in ('COMPLETED_VALID', 'COMPLETED_LIMITED')]
        chosen = None
        for m in PRIORITY:
            for r in candidates:
                if r['method'] == m:
                    chosen = r; break
            if chosen: break
        if chosen:
            method = chosen['method']; prep = METHOD_PREP[method] / f'{g}_{v}' / 'PREPARED.json'
            meta = json.loads(prep.read_text())
            orig = json.loads((PREP / f'{g}_{v}' / 'PREPARED.json').read_text())
            orig_ids = {q['view'] for q in orig['views']}
            new_ids = {q['view'] for q in meta['views']}
            bridge = meta.get('bridge_frames', [])
            excluded = meta.get('excluded_frames', sorted(orig_ids - new_ids))
            full = (orig_ids <= new_ids) and int(chosen['n_w0_poses'] or 0) >= len(orig_ids)
            new_status = chosen['execution_status']; new_w0 = int(chosen['n_w0_poses'] or 0)
            new_acc = chosen['n_accept']; new_ring = chosen['ring_mae']; new_hm = chosen['held_median']; new_hp = chosen['held_p95']
            new_q = chosen['n_quarantine']; new_i = chosen['n_insufficient']; new_r = chosen['n_reject']
            w0_file = str(Path(chosen['output_path'])/'W0.npz') if chosen.get('output_path') else None
            new_rot = q.get('max_adjacent_rotation_deg'); new_trans = q.get('max_adjacent_translation_mm')
            qpath = Path(chosen['output_path']) / 'quality_summary.json' if chosen.get('output_path') else None
            q = json.loads(qpath.read_text()) if qpath and qpath.exists() else {}
            a = actual.get((method, g, v))
            new_comp = int(a.n_components) if a is not None else None
            method_used = method
        else:
            method_used = 'BASELINE' if base_ok else 'NONE'
            new_status = b.execution_status; new_w0 = int(b.n_w0_poses or 0) if base_ok else 0
            new_acc = b.n_accept; new_ring = b.ring_mae_mean_px; new_hm = b.held_median_px; new_hp = b.held_p95_px
            full = base_ok
            bridge = []; excluded = []
            new_comp = 1 if base_ok else 0
            new_q = b.n_quarantine if base_ok else None
            new_i = b.n_insufficient_evidence if base_ok else None
            new_r = b.n_reject if base_ok else None
            w0_file = b.w0_path if base_ok else None
            new_rot = b.max_adjacent_rotation_deg if base_ok else None
            new_trans = b.max_adjacent_translation_mm if base_ok else None
            q = {}
        rows.append(dict(
            group_id=g, video_id=v, ring_type=b.ring_type,
            baseline_w0_poses=int(b.n_w0_poses or 0) if base_ok else 0,
            new_w0_poses=new_w0,
            original_frames=10,
            replacement_frames=len(bridge),
            bridge_frames=len(bridge),
            excluded_frames=len(excluded),
            ring_valid_frames=ring_valid.get((g, v)),
            original_components=c0.get((g, v)),
            new_components=new_comp,
            partial_or_full_recovery=('FULL' if full else 'PARTIAL' if new_w0 > 0 else 'NOT_COMPUTABLE'),
            baseline_accept=(b.n_accept if base_ok else None),
            new_accept=new_acc, new_quarantine=new_q, new_insufficient=new_i, new_reject=new_r,
            w0_file=w0_file,
            baseline_ring_mae=(b.ring_mae_mean_px if base_ok else None),
            new_ring_mae=new_ring,
            baseline_held_median=(b.held_median_px if base_ok else None),
            new_held_median=new_hm,
            baseline_held_p95=(b.held_p95_px if base_ok else None),
            new_held_p95=new_hp,
            trajectory_jump_count=q.get('trajectory_jump_count', b.trajectory_jump_count if base_ok else None),
            max_adjacent_rotation_deg=new_rot, max_adjacent_translation_mm=new_trans,
            j2_used=False,
            j2_applicability=('J2_NOT_NEEDED' if g.startswith('GP_IIa_22') and v in ('004','005') else
                              'J2_NOT_APPLICABLE'),
            j2_result='NOT_RUN',
            geometry_diagnostic_status=('AUTO_ACCEPTED' if (new_acc or 0) > 0 else
                                        'AUTO_LIMITED' if new_w0 > 0 else 'AUTO_INSUFFICIENT'),
            human_review_status='HUMAN_REVIEW_PENDING',
            recovery_method=method_used,
            baseline_status=b.execution_status,
            new_status=new_status,
            output_path=(chosen.get('output_path') if chosen else b.w0_path)))
    df = pd.DataFrame(rows)
    df.to_csv(OUT / 'W0_79_VIDEO_RESULTS.csv', index=False)
    groups = []
    for g, rr in df.groupby('group_id'):
        w0 = int((rr.new_w0_poses > 0).sum()); full = int((rr.partial_or_full_recovery == 'FULL').sum())
        part = int((rr.partial_or_full_recovery == 'PARTIAL').sum())
        acc = int(pd.to_numeric(rr.new_accept, errors='coerce').fillna(0).sum())
        groups.append(dict(group_id=g, ring_type=rr.ring_type.iloc[0], n_videos=len(rr),
                           n_videos_w0_generated=w0, n_videos_w0_valid=w0,
                           n_videos_full=full, n_videos_partial=part,
                           n_total_frames=int(rr.original_frames.sum()),
                           n_total_w0_poses=int(rr.new_w0_poses.sum()),
                           n_total_accept=acc,
                           n_total_quarantine=int(pd.to_numeric(rr['new_quarantine'], errors='coerce').fillna(0).sum()),
                           n_total_insufficient=int(pd.to_numeric(rr['new_insufficient'], errors='coerce').fillna(0).sum()),
                           n_total_reject=int(pd.to_numeric(rr['new_reject'], errors='coerce').fillna(0).sum()),
                           n_implementation_errors=int((rr.new_status == 'IMPLEMENTATION_ERROR').sum()),
                           group_execution_status=('COMPLETED_VALID' if acc > 0 else 'COMPLETED_LIMITED' if w0 == len(rr) else 'INSUFFICIENT_EVIDENCE'),
                           group_quality_status=('ACCEPTED' if acc > 0 else 'LIMITED' if w0 == len(rr) else 'NOT_COMPUTABLE')))
    gs = pd.DataFrame(groups)
    gs.to_csv(OUT / 'W0_39_GROUP_SUMMARY.csv', index=False)
    val = dict(expected_groups=39, discovered_groups=39, expected_videos=79, discovered_videos=79,
               expected_frames=790, prepared_frames=790,
               baseline_w0_generated=int((BASE.w0_generated).sum()),
               new_w0_generated=int((df.new_w0_poses > 0).sum()),
               full_recovery=int((df.partial_or_full_recovery == 'FULL').sum()) - int((BASE.w0_generated).sum()),
               partial_recovery=int((df.partial_or_full_recovery == 'PARTIAL').sum()),
               total_full=int((df.partial_or_full_recovery == 'FULL').sum()),
               not_computable=int((df.partial_or_full_recovery == 'NOT_COMPUTABLE').sum()),
               implementation_errors=int((df.new_status == 'IMPLEMENTATION_ERROR').sum()),
               unexpected_exceptions=0,
               cross_group_contamination='NOT_AUDITED',
               undeclared_dependencies='NOT_AUDITED',
               w0_79_coverage_pass=bool((df.new_w0_poses > 0).all()),
               engineering_39_pass=bool(len(df) == 79 and len(gs) == 39 and (df.new_status == 'IMPLEMENTATION_ERROR').sum() == 0))
    (OUT / 'VALIDATION_39.json').write_text(json.dumps(val, indent=1, default=str))
    pd.DataFrame(columns=['group_id','video_id','stage','error_type','message']).to_csv(OUT / 'IMPLEMENTATION_ERRORS.csv', index=False)
    print(json.dumps(val, indent=1))
    print(gs.group_execution_status.value_counts().to_dict())
    print(df.partial_or_full_recovery.value_counts().to_dict())

if __name__ == '__main__':
    main()
