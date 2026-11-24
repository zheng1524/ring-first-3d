import importlib.util,json,sys
from pathlib import Path
import numpy as np
WS=Path('/home/liu/ring_first_3d_workspace'); OUT=WS/'runs/m2c_trajectory_admission'; CLEAN=OUT/'clean_labels'
spec=importlib.util.spec_from_file_location('dxy_ring_holes2','/home/liu/new-polyp-dxy/src/dxy_mid/_engine/ring_holes.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
roots=[WS/'runs/m2a_w0_recovery'/x for x in ['prepared_c2b','prepared_c2','prepared_b1r','prepared_c3b']]+[WS/'runs/m2b_ring_global_branch/prepared_c3b']
n=0; new=0
for root in roots:
 for p in root.glob('*/PREPARED.json'):
  meta=json.loads(p.read_text()); g=meta['group']; v=str(meta.get('video_id') or Path(meta['video']).stem).split('.')[0].zfill(3); d=CLEAN/f'{g}_{v}'; d.mkdir(parents=True,exist_ok=True)
  for q in meta['views']:
   cp=d/(q['view']+'.npz')
   if cp.exists(): continue
   a=np.load(q['cache']); clean,fill,info=mod.run(a['labels']); np.savez_compressed(cp,labels=clean); n+=1; new+=1
print('extra clean new',n)
