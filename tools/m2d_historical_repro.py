#!/usr/bin/env python3
"""R0/R1 historical HERO reproduction with identical inputs."""
import json,os,sys,time,pathlib,hashlib
import numpy as np,pandas as pd,torch
WS=pathlib.Path('/home/liu/ring_first_3d_workspace'); O=WS/'runs/m2d_mvs_reproduction'; O.mkdir(parents=True,exist_ok=True); sys.path[:0]=[str(WS/'src')]
cfg=json.loads((WS/'mainline/configs/SITE.local.json').read_text()); sys.path[:0]=[str(x) for x in cfg.get('readonly_dependency_paths',[])]
from ring_first_3d.mainline.native.hero import load_official,infer
from ring_first_3d.mainline.native.io import save_json,sha256
R=WS/'experiments/TASK-E4-UNIFIED-RING-FIRST-HERO-DEPTH-001/runs/RF_ONLY_V1'
ids=['G01_004_ref03','G03_key00_raw00100','G05_key00_raw00097','G06_004_ref04']
model,receipt=load_official(cfg['mvs_root'],cfg['checkpoint'],cfg['dino_root'],json.loads((WS/'src/ring_first_3d/mainline/native/upstream_source_lock.json').read_text())); save_json(O/'MODEL_RECEIPT.json',receipt)
rows=[]
for hid in ids:
 g=hid.split('_')[0]; src=json.loads((R/g/'004'/'hero'/hid/'SOURCE.json').read_text()); out=O/'historical_reproduction'/'R1'/hid; out.mkdir(parents=True,exist_ok=True)
 frames=[]
 for k,(cid,ci) in enumerate(zip(src['frames'],src['input_caches'])):
  a=dict(np.load(ci['path'])); cam=json.loads(open(src['camera_results'][k]['path']).read()); frames.append(dict(id=cid,RGB=a['RGB'],labels=a['labels'],K=np.asarray(a['K'],float),c2w_mm=np.asarray(cam['c2w_mm'],float)))
 t0=time.time()
 try:
  rec=infer(model,frames,out); new=dict(np.load(out/'HERO_native.npz')); old=dict(np.load(R/g/'004'/'hero'/hid/'HERO_native.npz'))
  nd=np.asarray(new['depth_mm']); od=np.asarray(old['depth_mm']); finite=np.isfinite(nd)&np.isfinite(od); d=np.abs(nd[finite]-od[finite])
  nraw=dict(np.load(out/'RAW_NATIVE_MESH.npz')); oraw=dict(np.load(R/g/'004'/'hero'/hid/'RAW_NATIVE_MESH.npz'))
  rows.append(dict(historical_id=hid,group=g,status='PASS',seconds=rec.get('seconds'),peak_gpu_bytes=rec.get('peak_GPU_bytes'),native_shape=str(nd.shape),depth_finite_pixels=int(finite.sum()),depth_MAE_mm=float(d.mean()) if len(d) else None,depth_median_mm=float(np.median(d)) if len(d) else None,depth_p95_mm=float(np.percentile(d,95)) if len(d) else None,depth_max_mm=float(d.max()) if len(d) else None,depth_bitwise_equal=bool(np.array_equal(nd,od)),faces_equal=bool(np.array_equal(nraw['F'],oraw['F'])),vertices_max_abs_mm=float(np.max(np.abs(nraw['V']-oraw['V']))) if nraw['V'].shape==oraw['V'].shape else None,source_hash=sha256(src['input_caches'][0]['path']),old_sha256=sha256(R/g/'004'/'hero'/hid/'HERO_native.npz'),new_sha256=sha256(out/'HERO_native.npz')))
 except Exception as e:
  import traceback; rows.append(dict(historical_id=hid,group=g,status='FAIL',error=repr(e),traceback=traceback.format_exc())); print('FAIL',hid,e,flush=True)
 pd.DataFrame(rows).to_csv(O/'HISTORICAL_DEPTH_COMPARISON.csv',index=False)
print(pd.DataFrame(rows).to_string(index=False))
