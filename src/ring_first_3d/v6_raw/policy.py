"""Explicit upstream policy; no predicted depth is accepted by this module."""
import hashlib,json
import numpy as np

def frame_indices(n):
 if n<16:raise ValueError('VIDEO_TOO_SHORT')
 return np.rint(np.linspace(0,n-1,16)).astype(int).tolist()

def admit_camera(row):
 checks=[('留出观测数',row['held_observations'],8,True),('RGB MAE px',row['held_reprojection']['MAE'],3,False),('RGB P95 px',row['held_reprojection']['p95'],6,False),('正深度比例',row['held_positive_fraction'],.95,True),('Ring边界 MAE px',row['ring_held_self_contour_px']['MAE'],3,False),('Ring边界 P95 px',row['ring_held_self_contour_px']['p95'],6,False)]
 reasons=[]
 for label,value,limit,lower in checks:
  if value is None or not np.isfinite(value)or(value<limit if lower else value>limit):reasons.append(f'{label} {value} '+('<'if lower else'>')+f' {limit}')
 primary_ok=not reasons;spread=row['initialization_center_spread_mm'];stable=spread is not None and np.isfinite(spread)and spread<=2
 if not stable:reasons.append(f'初始化中心分散 {spread:.3f} mm > 2 mm'if spread is not None else'初始化中心分散不可计算')
 return primary_ok and stable,primary_ok,reasons

def choose_sources(ranked,old_ok,new_ok):
 # V6 ordering is supplied by its original source selector, never re-scored here.
 eligible=lambda pool:[int(x['i'])for x in ranked if x['i']in pool and x['overlap']>=15][:3]
 original=eligible(old_ok)
 return (original,True)if len(original)==3 else(eligible(new_ok),False)

def tuple_identity(frames,raw_sha,model_sha):
 records=[]
 for f in frames:
  if not(np.isfinite(f['K']).all()and np.isfinite(f['c2w_mm']).all()):raise ValueError('NONFINITE_INPUT_CAMERA')
  record={k:hashlib.sha256(np.ascontiguousarray(f[k]).tobytes()).hexdigest()for k in ['RGB','labels','K','c2w_mm']}|dict(raw_frame=int(f['raw_frame']) if f['raw_frame'] is not None else None)
  if 'view_id' in f:record.update(view_id=f['view_id'],physical_view_id=f['physical_view_id'])
  records.append(record)
 return hashlib.sha256(json.dumps(dict(raw=raw_sha,model=model_sha,frames=records,protocol='V6-352x640-refine1-fp16-fastFalse-K+.5-mmToM'),sort_keys=True).encode()).hexdigest()
