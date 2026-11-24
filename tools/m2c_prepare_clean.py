#!/usr/bin/env python3
"""M2C DXY ring_holes sidecar clean for all 79 prepared videos."""
import csv,importlib.util,json,sys,pathlib
from pathlib import Path
import numpy as np,cv2
WS=Path('/home/liu/ring_first_3d_workspace'); OUT=WS/'runs/m2c_trajectory_admission'; PREP=WS/'runs/m1_final_39/prepared'
DXY=Path('/home/liu/new-polyp-dxy/src/dxy_mid/_engine/ring_holes.py')
spec=importlib.util.spec_from_file_location('dxy_ring_holes',DXY); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
CLEAN=OUT/'clean_labels'; CLEAN.mkdir(parents=True,exist_ok=True)
rows=[]
for p in sorted(PREP.glob('*/PREPARED.json')):
 meta=json.loads(p.read_text()); g=meta['group']; v=str(meta.get('video_id') or pathlib.Path(meta['video']).stem).split('.')[0].zfill(3)
 d=CLEAN/f'{g}_{v}'; d.mkdir(parents=True,exist_ok=True)
 for q in meta['views']:
  a=np.load(q['cache']); raw=a['labels']; clean,fill,info=mod.run(raw)
  assert np.array_equal(clean==1,raw==1)
  assert np.array_equal(clean[~fill],raw[~fill])
  np.savez_compressed(d/(q['view']+'.npz'),labels=clean)
  rows.append(dict(group_id=g,video_id=v,frame_id=q['view'],raw_frame=int(q['raw_frame']),
   raw_ring_pixels=int((raw==2).sum()),clean_ring_pixels=int((clean==2).sum()),
   changed_pixels=int((clean!=raw).sum()),filled_pixels=int(fill.sum()),n_holes=len(info.get('holes',[])),
   filled_holes=sum(1 for h in info.get('holes',[]) if h.get('filled')),
   clean_operation='DXY ring_holes.run ring_enclosed_small_background_v1',clean_changed=bool(fill.any())))
with open(OUT/'MASK_CLEAN_PER_FRAME.csv','w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print('frames',len(rows),'changed',sum(r['clean_changed'] for r in rows),'pixels',sum(r['changed_pixels'] for r in rows))
