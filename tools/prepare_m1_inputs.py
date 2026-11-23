#!/usr/bin/env python3
"""M1 39-group prepared-input glue.

Reads the frozen39 frame registry, resolves local raw videos, and calls the
existing 005 `prepare_view` (frozen INIT math) once per registered frame.
No segmentation, resize, label or interpolation logic is reimplemented here.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import cv2
import numpy as np
import pandas as pd

WS = Path('/home/liu/ring_first_3d_workspace')
RAW = WS / 'smart_endoscope_20260805 (1)' / 'raw'
REG = Path('/home/liu/new-polyp-dxy/validation/frozen39/inputs.csv')
T005 = WS / 'experiments/TASK-E4-UNIFIED-RING-CONTOUR-REFINEMENT-005'
INIT = Path('/home/liu/polyp_research/experiments/dxy_remeasurement_20260917/02_segmentation/model/model.safetensors')
INIT_SHA = '981aa596e8906edc4457219581c606d4a5a22bfc6f7e4924d3d9a4b9aff64464'

sys.path.insert(0, str(T005 / 'code'))
from prepare import K, prepare_view, sha  # noqa: E402


def vid_of(name):
    return Path(name).stem.split('_')[-1]


def reference_photos(group):
    return sorted(p.name for p in RAW.glob(f'{group}_*.jpg'))


def _video_meta(path):
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise RuntimeError(f'VIDEO_OPEN_FAILED {path}')
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    return dict(frames=n, width=w, height=h)


def build_registry():
    d = pd.read_csv(REG)
    required = {'group', 'video', 'frame_index', 'stem', 'ring_mm'}
    missing = required - set(d.columns)
    if missing:
        raise ValueError(f'frozen39 missing columns: {sorted(missing)}')
    groups = sorted(d['group'].unique().tolist())
    if len(groups) != 39:
        raise ValueError(f'expected 39 groups, found {len(groups)}')
    rows, photos = [], {}
    for (g, v), sub in d.groupby(['group', 'video'], sort=True):
        raw = RAW / v
        if not raw.exists():
            raise FileNotFoundError(raw)
        meta = _video_meta(raw)
        if int(sub['frame_index'].max()) >= meta['frames']:
            raise ValueError(f'FRAME_OUT_OF_RANGE {g} {v} {sub["frame_index"].max()} >= {meta["frames"]}')
        rings = sorted({float(x) for x in sub['ring_mm'].tolist()})
        if len(rings) != 1:
            raise ValueError(f'MIXED_RING {g} {v} {rings}')
        rows.append(dict(group=g, video=v, video_id=vid_of(v), frames=len(sub),
                         raw_path=str(raw), ring_mm=rings[0], max_frame=int(sub['frame_index'].max()),
                         n_video_frames=meta['frames'], width=meta['width'], height=meta['height']))
        photos[g] = reference_photos(g)
    if sum(r['frames'] for r in rows) != 790:
        raise ValueError(f'expected 790 frames, found {sum(r["frames"] for r in rows)}')
    if len(rows) != 79:
        raise ValueError(f'expected 79 videos, found {len(rows)}')
    return groups, rows, photos


def prepare_one(group, video, frames, out_root, force=False):
    out = Path(out_root) / f'{group}_{vid_of(video)}'
    out.mkdir(parents=True, exist_ok=True)
    views = []
    for _, r in frames.sort_values('frame_index').iterrows():
        cache = out / f'{r.stem}.npz'
        if force or not cache.exists():
            res = prepare_view(RAW / video, int(r.frame_index), cache)
        else:
            res = dict(rgb_sha256=None, label_counts=None)
        d = np.load(cache)
        if d['labels'].shape != (360, 640):
            raise ValueError(f'MASK_SHAPE {cache} {d["labels"].shape}')
        if not np.isin(d['labels'], [0, 1, 2]).all():
            raise ValueError(f'MASK_LABELS {cache}')
        if not np.allclose(np.asarray(d['K'], float), np.asarray(K, float)):
            raise ValueError(f'K_MISMATCH {cache}')
        views.append(dict(view=str(r.stem), raw_frame=int(r.frame_index), cache=str(cache),
                          rgb_sha256=res.get('rgb_sha256'),
                          label_counts=res.get('label_counts')))
    meta = dict(group=group, video=video, video_id=vid_of(video),
                video_path=str(RAW / video), video_sha256=sha(RAW / video),
                init_weights=str(INIT), init_weight_sha256=INIT_SHA,
                math='PIL bilinear 256 /255; bilinear logits upsample; argmax',
                ring_mm=float(frames['ring_mm'].iloc[0]), K=np.asarray(K).tolist(),
                views=views)
    (out / 'PREPARED.json').write_text(json.dumps(meta, indent=1))
    return meta


def coverage_row(group, rows, photos, prepared_root):
    g_rows = [r for r in rows if r['group'] == group]
    rings = sorted({r['ring_mm'] for r in g_rows})
    prepared = all((Path(prepared_root) / f"{r['group']}_{r['video_id']}" / 'PREPARED.json').exists()
                   for r in g_rows)
    return dict(group_id=group,
                video_ids=';'.join(r['video_id'] for r in g_rows),
                reference_photo_ids=';'.join(photos[group]),
                reference_photos_used=False,
                ring_type=('R10' if rings == [10.0] else 'R5' if rings == [5.0] else 'MIXED'),
                ring_dimensions=f'inner={rings[0]}mm;centerline={rings[0]/2+0.6}mm;wire=0.6mm',
                raw_input_exists=all(Path(r['raw_path']).exists() for r in g_rows),
                prepared_input_exists=prepared,
                input_status='VALID' if prepared else 'PREPARED_MISSING')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--output-root', required=True)
    ap.add_argument('--coverage', required=True)
    ap.add_argument('--groups', default='all')
    ap.add_argument('--force', action='store_true')
    a = ap.parse_args()
    groups, rows, photos = build_registry()
    use = groups if a.groups == 'all' else a.groups.split(',')
    unknown = sorted(set(use) - set(groups))
    if unknown:
        raise SystemExit(f'UNKNOWN_GROUPS {unknown}')
    out_root = Path(a.output_root)
    for g in use:
        for r in [x for x in rows if x['group'] == g]:
            sub = pd.read_csv(REG)
            sub = sub[(sub.group == g) & (sub.video == r['video'])]
            meta = prepare_one(g, r['video'], sub, out_root, force=a.force)
            print('PREPARED', g, r['video_id'], len(meta['views']), flush=True)
    cov = [coverage_row(g, rows, photos, out_root) for g in groups]
    Path(a.coverage).parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(cov).to_csv(a.coverage, index=False)
    print(json.dumps(pd.DataFrame(cov).input_status.value_counts().to_dict()), flush=True)


if __name__ == '__main__':
    main()
