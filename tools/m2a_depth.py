#!/usr/bin/env python3
"""Correct positive-depth diagnostics from actual W0 3D points and cameras."""
import json
from pathlib import Path
import numpy as np
import pandas as pd

OUT = Path('/home/liu/ring_first_3d_workspace/runs/m2a_w0_recovery')
df = pd.read_csv(OUT / 'W0_79_VIDEO_RESULTS.csv')
rows = []
for _, r in df.iterrows():
    p = r.get('w0_file')
    old = np.nan
    od = r.get('output_path')
    if isinstance(od, str):
        qp = Path(od) / 'quality_summary.json' if Path(od).is_dir() else Path(od).parent / 'quality_summary.json'
        if qp.exists():
            try: old = json.loads(qp.read_text()).get('positive_depth_fraction', np.nan)
            except Exception: pass
    if not isinstance(p, str) or not Path(p).exists():
        rows.append(dict(group_id=r.group_id, video_id=r.video_id, w0_file=None,
                         positive_depth_points_fraction=None, positive_depth_source_fraction=None,
                         positive_depth_target_fraction=None, positive_depth_old_world_origin=old,
                         max_positive_depth_gap=None)); continue
    d = np.load(p); X = np.asarray(d['points'], float); C = np.asarray(d['c2w'], float)
    def frac(cam):
        q = (X - cam[:3, 3]) @ cam[:3, :3]
        return float((q[:, 2] > 0).mean()) if len(q) else None
    fr = [frac(c) for c in C]
    rows.append(dict(group_id=r.group_id, video_id=r.video_id, w0_file=p,
                     positive_depth_points_fraction=float((np.asarray(fr) > 0).mean()) if fr else None,
                     positive_depth_source_fraction=fr[0] if fr else None,
                     positive_depth_target_fraction=fr[-1] if fr else None,
                     positive_depth_old_world_origin=old,
                     max_positive_depth_gap=float(np.nanmax(np.abs(np.asarray(fr)-old))) if fr and np.isfinite(old) else None))
pd.DataFrame(rows).to_csv(OUT / 'POSITIVE_DEPTH_DIAGNOSTICS.csv', index=False)
df = df.merge(pd.DataFrame(rows)[['group_id','video_id','positive_depth_points_fraction',
                                  'positive_depth_source_fraction','positive_depth_target_fraction',
                                  'positive_depth_old_world_origin','max_positive_depth_gap']],
              on=['group_id','video_id'], how='left')
df.to_csv(OUT / 'W0_79_VIDEO_RESULTS.csv', index=False)
print(pd.DataFrame(rows).describe().to_string())
print('n', len(rows), 'valid', sum(1 for r in rows if r['positive_depth_points_fraction'] is not None))
