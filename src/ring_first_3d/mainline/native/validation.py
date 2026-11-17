"""Independent comparisons performed after outputs have been saved."""
from pathlib import Path
import numpy as np
from .io import save_json,read_json

def compare_history(data_root, output):
    data_root=Path(data_root);output=Path(output)
    pred=dict(np.load(output/'HERO_native.npz'));ref=dict(np.load(data_root/'historical/HERO_native.npz'))
    a=pred['depth_mm'];b=ref['depth_mm']
    if a.shape!=b.shape:raise ValueError('Native shape differs')
    d=abs(a.astype(float)-b.astype(float));valid=np.isfinite(a)&np.isfinite(b)
    m=dict(np.load(output/'RAW_NATIVE_MESH.npz'));r=dict(np.load(data_root/'historical/RAW_NATIVE_MESH.npz'))
    same_faces=np.array_equal(m['F'],r['F']);same_pixels=np.array_equal(m['native_pixel_id'],r['native_pixel_id'])
    rec=dict(N_pixels=int(a.size),N_common_finite=int(valid.sum()),depth_bitwise_equal=bool(np.array_equal(a,b)),depth_MAE_mm=float(d[valid].mean()),depth_p95_mm=float(np.quantile(d[valid],.95)),depth_max_mm=float(d[valid].max()),native_K_max_abs=float(abs(pred['K_index_native']-ref['K_index_native']).max()),c2w_max_abs=float(abs(pred['reference_pose_mm']-ref['reference_pose_mm']).max()),raw_faces_equal=same_faces,raw_pixel_ids_equal=same_pixels,raw_vertex_max_mm=float(abs(m['V']-r['V']).max()) if m['V'].shape==r['V'].shape else None,validity='historical-output reproducibility; not geometric truth',GT='NOT_EVALUABLE')
    rec['within_preregistered_tolerance']=bool(rec['depth_max_mm']<=.02 and same_faces and same_pixels and rec['native_K_max_abs']<1e-9)
    if (output/'FACE_EVIDENCE.npz').exists():
        f=dict(np.load(output/'FACE_EVIDENCE.npz'));g=dict(np.load(data_root/'historical/FACE_EVIDENCE.npz'))
        rec['cleaning_state_equal']=bool(np.array_equal(f['state'],g['state']))
        rec['cleaning_reason_bits_equal']=bool(np.array_equal(f['reason_bits'],g['reason_bits']))
    save_json(output/'HISTORICAL_COMPARISON.json',rec)
    return rec
