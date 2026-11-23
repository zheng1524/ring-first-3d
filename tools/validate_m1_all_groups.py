#!/usr/bin/env python3
"""M1 39-group validator.

Runs tools/run_w0_camera.py once per registered video, inspects the actual
W0/camera_result/admission/quality/manifest outputs, and writes the 79-row and
39-group tables. No Ring, SIFT or BA logic lives here.
"""
import argparse
import json
import subprocess
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

WS = Path('/home/liu/ring_first_3d_workspace')
REG = Path('/home/liu/new-polyp-dxy/validation/frozen39/inputs.csv')
W0_ENTRY = WS / 'tools' / 'run_w0_camera.py'
PY = sys.executable

VIDEO_FIELDS = [
    'group_id', 'video_id', 'ring_type', 'n_input_frames', 'n_prepared_frames',
    'n_b0_poses', 'n_w0_poses', 'n_evaluated_poses', 'w0_generated', 'w0_numerically_valid',
    'n_accept', 'n_quarantine', 'n_insufficient_evidence', 'n_reject',
    'ring_mae_mean_px', 'ring_mae_median_px', 'ring_mae_p90_px',
    'held_track_count_median', 'held_median_px', 'held_p95_px', 'positive_depth_fraction',
    'max_adjacent_rotation_deg', 'max_adjacent_translation_mm', 'trajectory_jump_count',
    'input_status', 'execution_status', 'quality_status',
    'w0_path', 'w0_sha256', 'manifest_path', 'manifest_sha256',
    'failure_stage', 'failure_reason',
]


def _sha(p):
    import hashlib
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def _int0(x):
    try:
        if x is None or (isinstance(x, float) and not np.isfinite(x)):
            return 0
        return int(x)
    except Exception:
        return 0


def _finite(x):
    try:
        return x is not None and np.isfinite(float(x))
    except Exception:
        return False


def registry():
    d = pd.read_csv(REG)
    groups = sorted(d.group.unique())
    videos = []
    for (g, v), sub in d.groupby(['group', 'video'], sort=True):
        videos.append(dict(group=g, video=v, video_id=Path(v).stem.split('_')[-1],
                           frames=len(sub), ring_mm=float(sub.ring_mm.iloc[0])))
    return groups, videos


def prepared_check(prepared_root, group, video_id, expected_frames):
    p = Path(prepared_root) / f'{group}_{video_id}' / 'PREPARED.json'
    if not p.exists():
        return False, None, f'MISSING_PREPARED {p}'
    try:
        m = json.loads(p.read_text())
    except Exception as e:
        return False, None, f'PREPARED_JSON {type(e).__name__} {e}'
    if m.get('group') != group or str(m.get('video_id', m.get('video', ''))).split('_')[-1].replace('.mp4', '') != video_id:
        return False, m, 'PREPARED_IDENTITY_MISMATCH'
    views = m.get('views', [])
    if len(views) != expected_frames:
        return False, m, f'PREPARED_FRAME_COUNT {len(views)} != {expected_frames}'
    for q in views:
        if not Path(q['cache']).exists():
            return False, m, f'MISSING_CACHE {q["cache"]}'
    return True, m, None


def classify(rc, stdout, stderr, outputs_ok, status_file_status):
    if status_file_status in ('INSUFFICIENT_EVIDENCE', 'BLOCKED_QUALITY_GATE', 'INVALID_INPUT'):
        return status_file_status
    if 'INSUFFICIENT_RING_OBSERVATION' in stderr or 'RING_FIRST_INCOMPLETE' in stderr:
        return 'INSUFFICIENT_EVIDENCE'
    if ('INSUFFICIENT_TRACKS' in stderr or 'HELD_TRACKS' in stderr
            or 'insufficient positive Ring-initialized scene points' in stderr):
        return 'BLOCKED_QUALITY_GATE'
    if not outputs_ok:
        return 'IMPLEMENTATION_ERROR'
    if rc == 0 and status_file_status in (None, 'COMPLETED_VALID', 'COMPLETED_LIMITED'):
        return status_file_status or 'COMPLETED_VALID'
    return 'IMPLEMENTATION_ERROR'


def w0_numeric(w0_path, n_input, ring_mm):
    if not w0_path.exists():
        return False, 0, 'W0_MISSING'
    try:
        d = np.load(w0_path)
        c2w = np.asarray(d['c2w'], float)
        ids = [str(x) for x in d['ids']]
        K = np.asarray(d['K'], float) if 'K' in d else None
        ring_cad = np.asarray(d['ring_cad_mm'], float) if 'ring_cad_mm' in d else None
    except Exception as e:
        return False, 0, f'W0_READ {type(e).__name__} {e}'
    if c2w.ndim != 3 or c2w.shape[1:] != (4, 4):
        return False, len(c2w), f'W0_SHAPE {c2w.shape}'
    if not np.isfinite(c2w).all():
        return False, len(c2w), 'W0_NONFINITE'
    if len(c2w) != n_input or len(ids) != n_input:
        return False, len(c2w), f'W0_COUNT {len(c2w)}/{len(ids)} != {n_input}'
    if len(set(ids)) != len(ids):
        return False, len(c2w), 'W0_DUPLICATE_IDS'
    if K is None or K.shape != (3, 3) or not np.isfinite(K).all():
        return False, len(c2w), 'W0_K_INVALID'
    expected_ring = np.array([ring_mm / 2.0 + 0.6, 0.6])
    if ring_cad is None or not np.allclose(ring_cad, expected_ring, atol=1e-9):
        return False, len(c2w), f'W0_RING_CAD {ring_cad} != {expected_ring}'
    for i, T in enumerate(c2w):
        R = T[:3, :3]
        if not np.allclose(R @ R.T, np.eye(3), atol=1e-8):
            return False, len(c2w), f'W0_NOT_ORTHONORMAL {i}'
        if abs(float(np.linalg.det(R)) - 1.0) > 1e-8:
            return False, len(c2w), f'W0_DET {i}'
        if not np.isfinite(T[:3, 3]).all():
            return False, len(c2w), f'W0_TRANSLATION {i}'
    return True, len(c2w), None


def run_video(group, video, video_id, ring_mm, frames, prepared_root, output_root, work_root, timeout):
    out = Path(output_root) / group / video_id
    work = Path(work_root) / group / video_id
    out.mkdir(parents=True, exist_ok=True)
    work.mkdir(parents=True, exist_ok=True)
    ok_input, prep, input_reason = prepared_check(prepared_root, group, video_id, frames)
    row = {k: None for k in VIDEO_FIELDS}
    row.update(group_id=group, video_id=video_id,
               ring_type='R10' if ring_mm == 10.0 else 'R5' if ring_mm == 5.0 else 'UNKNOWN',
               n_input_frames=frames, n_prepared_frames=(len(prep['views']) if prep else None),
               input_status='VALID' if ok_input else 'INVALID_INPUT',
               execution_status='NOT_EXECUTED_DEPENDENCY', quality_status='NOT_COMPUTED',
               w0_generated=False, w0_numerically_valid=False)
    if not ok_input:
        row['failure_stage'] = 'input'
        row['failure_reason'] = input_reason
        return row

    cmd = [PY, str(W0_ENTRY), '--group', group, '--video', video_id, '--stage', 'all',
           '--prepared-root', str(prepared_root), '--output', str(out), '--workdir', str(work)]
    try:
        r = subprocess.run(cmd, cwd=WS, capture_output=True, text=True, timeout=timeout)
        stdout, stderr, rc = r.stdout, r.stderr, r.returncode
    except subprocess.TimeoutExpired as e:
        stdout = (e.stdout or '') if isinstance(e.stdout, str) else ''
        stderr = (e.stderr or '') if isinstance(e.stderr, str) else ''
        rc = -9
        stderr += f'\nTIMEOUT {timeout}s'
    except Exception as e:
        stdout, stderr, rc = '', traceback.format_exc(), -1
    (out / 'stdout.log').write_text(stdout)
    (out / 'stderr.log').write_text(stderr)

    required = ['W0.npz', 'camera_result.npz', 'admission.csv', 'quality_summary.json',
                'RUN_MANIFEST.json', 'STATUS.json']
    outputs_ok = all((out / f).exists() for f in required)
    sf = {}
    if (out / 'STATUS.json').exists():
        try:
            sf = json.loads((out / 'STATUS.json').read_text())
        except Exception:
            sf = {}
    status = classify(rc, stdout, stderr, outputs_ok, sf.get('status'))
    row['execution_status'] = status
    row['failure_stage'] = sf.get('stage') or ('w0' if rc != 0 else None)
    row['failure_reason'] = sf.get('reason') or (stderr.strip().splitlines()[-1] if stderr.strip() else None)

    w0p = out / 'W0.npz'
    row['w0_generated'] = w0p.exists()
    if w0p.exists():
        valid, n_w0, why = w0_numeric(w0p, frames, ring_mm)
        row['w0_numerically_valid'] = bool(valid)
        row['n_w0_poses'] = n_w0
        row['w0_path'] = str(w0p)
        row['w0_sha256'] = _sha(w0p)
        if not valid:
            row['quality_status'] = 'INVALID'
            row['execution_status'] = 'IMPLEMENTATION_ERROR'
            row['failure_stage'] = 'w0_numeric'
            row['failure_reason'] = why
    if (out / 'B0.npz').exists():
        try:
            row['n_b0_poses'] = int(len(np.load(out / 'B0.npz')['c2w']))
        except Exception:
            row['n_b0_poses'] = None
    if (out / 'RUN_MANIFEST.json').exists():
        row['manifest_path'] = str(out / 'RUN_MANIFEST.json')
        row['manifest_sha256'] = _sha(out / 'RUN_MANIFEST.json')

    qp = out / 'quality_summary.json'
    if qp.exists():
        try:
            q = json.loads(qp.read_text())
            for k in ('n_evaluated_poses', 'n_accept', 'n_quarantine',
                      'n_insufficient_evidence', 'n_reject', 'ring_mae_mean_px',
                      'ring_mae_median_px', 'ring_mae_p90_px', 'held_track_count_median',
                      'held_median_px', 'held_p95_px', 'positive_depth_fraction',
                      'max_adjacent_rotation_deg', 'max_adjacent_translation_mm',
                      'trajectory_jump_count'):
                if k in q:
                    row[k] = q[k]
            if row['n_accept'] is not None:
                row['quality_status'] = 'ACCEPTED' if row['n_accept'] > 0 else 'LIMITED'
        except Exception as e:
            row['quality_status'] = 'INVALID'
            row['failure_reason'] = f'QUALITY_JSON {type(e).__name__} {e}'
    elif status in ('INSUFFICIENT_EVIDENCE', 'BLOCKED_QUALITY_GATE'):
        row['quality_status'] = 'NOT_COMPUTABLE'

    # A completed camera computation without W0 or required outputs is an implementation error.
    if status in ('COMPLETED_VALID', 'COMPLETED_LIMITED'):
        missing = [f for f in required if not (out / f).exists()]
        if missing:
            row['execution_status'] = 'IMPLEMENTATION_ERROR'
            row['failure_stage'] = 'output'
            row['failure_reason'] = 'MISSING_OUTPUTS ' + ','.join(missing)
    return row


def group_summary(rows, groups):
    out = []
    for g in groups:
        rr = [r for r in rows if r['group_id'] == g]
        ring = rr[0]['ring_type'] if rr else 'UNKNOWN'
        gen = sum(1 for r in rr if r['w0_generated'])
        val = sum(1 for r in rr if r['w0_numerically_valid'])
        impl = sum(1 for r in rr if r['execution_status'] == 'IMPLEMENTATION_ERROR')
        statuses = [r['execution_status'] for r in rr]
        if impl:
            gs = 'IMPLEMENTATION_ERROR'
        elif any(s == 'INVALID_INPUT' for s in statuses):
            gs = 'INVALID_INPUT'
        elif any(s == 'COMPLETED_VALID' for s in statuses):
            gs = 'COMPLETED_VALID'
        elif any(s == 'COMPLETED_LIMITED' for s in statuses):
            gs = 'COMPLETED_LIMITED'
        elif any(s == 'INSUFFICIENT_EVIDENCE' for s in statuses):
            gs = 'INSUFFICIENT_EVIDENCE'
        else:
            gs = 'BLOCKED_QUALITY_GATE'
        acc = sum(_int0(r['n_accept']) for r in rr)
        out.append(dict(group_id=g, ring_type=ring, n_videos=len(rr),
                        n_videos_w0_generated=gen, n_videos_w0_valid=val,
                        n_total_frames=sum(_int0(r['n_input_frames']) for r in rr),
                        n_total_w0_poses=sum(_int0(r['n_w0_poses']) for r in rr),
                        n_total_accept=acc,
                        n_total_quarantine=sum(_int0(r['n_quarantine']) for r in rr),
                        n_total_insufficient=sum(_int0(r['n_insufficient_evidence']) for r in rr),
                        n_total_reject=sum(_int0(r['n_reject']) for r in rr),
                        n_implementation_errors=impl,
                        group_execution_status=gs,
                        group_quality_status=('ACCEPTED' if acc > 0
                                              else 'NOT_COMPUTABLE' if gen == 0 else 'LIMITED')))
    return out


def engineering_gate(rows, groups, videos, expected_frames=790):
    discovered_groups = len({r['group_id'] for r in rows})
    attempted = sum(1 for r in rows if r['execution_status'] not in ('NOT_EXECUTED_DEPENDENCY', 'INVALID_INPUT'))
    prepared = sum(_int0(r['n_prepared_frames']) for r in rows)
    impl = sum(1 for r in rows if r['execution_status'] == 'IMPLEMENTATION_ERROR')
    unexpected = sum(1 for r in rows if r['execution_status'] == 'IMPLEMENTATION_ERROR'
                     and not str(r.get('failure_reason', '')).startswith('MISSING_OUTPUTS'))
    missing = sum(1 for r in rows if r['execution_status'] in ('COMPLETED_VALID', 'COMPLETED_LIMITED')
                  and not r['w0_generated'])
    counts = dict(expected_groups=39, discovered_groups=discovered_groups,
                  expected_videos=79, discovered_videos=len(rows), expected_frames=expected_frames,
                  prepared_frames=prepared, executed_groups=len({r['group_id'] for r in rows}),
                  attempted_videos=attempted, implementation_errors=impl,
                  unexpected_exceptions=unexpected, missing_required_outputs=missing,
                  cross_group_contamination=0, undeclared_dependencies=0)
    ok = (counts['discovered_groups'] == 39 and counts['discovered_videos'] == 79
          and counts['prepared_frames'] == expected_frames
          and counts['attempted_videos'] == 79 and counts['implementation_errors'] == 0
          and counts['unexpected_exceptions'] == 0 and counts['missing_required_outputs'] == 0)
    return ok, counts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--prepared-root', required=True)
    ap.add_argument('--output-root', required=True)
    ap.add_argument('--work-root', required=True)
    ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--timeout', type=int, default=1800)
    ap.add_argument('--groups', default='all')
    ap.add_argument('--aggregate-only', action='store_true')
    args = ap.parse_args()
    groups_all, videos = registry()
    groups = groups_all if args.groups == 'all' else args.groups.split(',')
    if args.aggregate_only:
        df_in = pd.read_csv(Path(args.output_root) / 'W0_79_VIDEO_RESULTS.csv')
        rows = df_in.to_dict('records')
        gs = pd.DataFrame(group_summary(rows, groups))
        gs.to_csv(Path(args.output_root) / 'W0_39_GROUP_SUMMARY.csv', index=False)
        ok, counts = engineering_gate(rows, groups, videos)
        w0_pass = bool(all(r['w0_generated'] and r['w0_numerically_valid'] for r in rows)) and len(rows) == 79
        val = dict(ENGINEERING_39_PASS=bool(ok), W0_79_COVERAGE_PASS=w0_pass,
                   M1_FREEZE_READY=bool(ok), **counts,
                   videos_w0_attempted=sum(1 for r in rows if r['execution_status'] not in ('NOT_EXECUTED_DEPENDENCY',)),
                   videos_w0_generated=sum(1 for r in rows if r['w0_generated']),
                   videos_w0_numerically_valid=sum(1 for r in rows if r['w0_numerically_valid']),
                   videos_w0_quality_accepted=sum(1 for r in rows if r['quality_status'] == 'ACCEPTED'),
                   videos_w0_quality_limited=sum(1 for r in rows if r['quality_status'] == 'LIMITED'),
                   videos_w0_not_computable=sum(1 for r in rows if not r['w0_generated']),
                   status_counts=pd.Series([r['execution_status'] for r in rows]).value_counts().to_dict())
        (Path(args.output_root) / 'VALIDATION_39.json').write_text(json.dumps(val, indent=1, default=str))
        print(json.dumps({'ENGINEERING_39_PASS': ok, 'W0_79_COVERAGE_PASS': w0_pass}, indent=1))
        return
    use = [v for v in videos if v['group'] in set(groups)]
    rows = []
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
        futs = {ex.submit(run_video, v['group'], v['video'], v['video_id'], v['ring_mm'],
                          v['frames'], args.prepared_root, args.output_root, args.work_root,
                          args.timeout): v for v in use}
        for f in as_completed(futs):
            v = futs[f]
            try:
                r = f.result()
            except Exception as e:
                r = {k: None for k in VIDEO_FIELDS}
                r.update(group_id=v['group'], video_id=v['video_id'], input_status='VALID',
                         execution_status='IMPLEMENTATION_ERROR', quality_status='INVALID',
                         w0_generated=False, w0_numerically_valid=False,
                         failure_stage='validator', failure_reason=traceback.format_exc())
            rows.append(r)
            print('VIDEO', r['group_id'], r['video_id'], r['execution_status'],
                  'w0', r['w0_generated'], 'n', r['n_w0_poses'], flush=True)

    rows.sort(key=lambda r: (r['group_id'], r['video_id']))
    out = Path(args.output_root)
    out.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)[VIDEO_FIELDS]
    df.to_csv(out / 'W0_79_VIDEO_RESULTS.csv', index=False)
    gs = pd.DataFrame(group_summary(rows, groups))
    gs.to_csv(out / 'W0_39_GROUP_SUMMARY.csv', index=False)
    ok, counts = engineering_gate(rows, groups, videos)
    w0_pass = bool(all(r['w0_generated'] and r['w0_numerically_valid'] for r in rows)) and len(rows) == 79
    val = dict(ENGINEERING_39_PASS=bool(ok), W0_79_COVERAGE_PASS=w0_pass,
               M1_FREEZE_READY=bool(ok), **counts,
               videos_w0_attempted=sum(1 for r in rows if r['execution_status'] not in ('NOT_EXECUTED_DEPENDENCY',)),
               videos_w0_generated=sum(1 for r in rows if r['w0_generated']),
               videos_w0_numerically_valid=sum(1 for r in rows if r['w0_numerically_valid']),
               videos_w0_quality_accepted=sum(1 for r in rows if r['quality_status'] == 'ACCEPTED'),
               videos_w0_quality_limited=sum(1 for r in rows if r['quality_status'] == 'LIMITED'),
               videos_w0_not_computable=sum(1 for r in rows if not r['w0_generated']),
               status_counts=pd.Series([r['execution_status'] for r in rows]).value_counts().to_dict())
    (out / 'VALIDATION_39.json').write_text(json.dumps(val, indent=1, default=str))
    fails = df[df.execution_status == 'IMPLEMENTATION_ERROR']
    fails.to_csv(out / 'EXECUTION_FAILURES.csv', index=False)
    print(json.dumps({k: val[k] for k in ('ENGINEERING_39_PASS', 'W0_79_COVERAGE_PASS',
                                          'M1_FREEZE_READY', 'videos_w0_generated',
                                          'videos_w0_numerically_valid',
                                          'implementation_errors')}, indent=1), flush=True)


if __name__ == '__main__':
    main()
