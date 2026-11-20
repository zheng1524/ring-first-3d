"""P3/P4: fixed-pose Inner/Outer audit + CAD joint feasibility on B0 cameras."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation as Rot
T = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(T/'code')); sys.path.insert(0, '/home/liu/ring_first_3d_workspace/src')
import contour_geometry as CG, cad_contour_geometry as G
from ring_first_3d.mainline.native.camera import torus_contours
K = np.array([[490., 0, 319.5], [0, 490., 179.5], [0, 0, 1]])
R8 = Path('/home/liu/ring_first_3d_workspace/experiments/TASK-E4-REAL-JOINT-BA-008/runs/G03_005')
T006 = Path('/home/liu/ring_first_3d_workspace/experiments/TASK-E4-UNIFIED-RING-CONTOUR-REFINEMENT-005')
views = json.loads((T006/'runs/prepared/G03_005/PREPARED.json').read_text())['views']
cams = dict(np.load(R8/'B0'/'cameras.npz'))
ids = [str(s) for s in cams['ids']]


def signed_residual(curve, poly, vis):
    """Signed offset of DXY support points relative to the CAD curve (outward positive)."""
    p = np.asarray(poly, float)[np.asarray(vis, bool)]
    if len(p) == 0:
        return None
    from scipy.spatial import cKDTree
    dense = CG.resample_closed(curve, 720)
    d, idx = cKDTree(dense).query(p, k=1)
    c = dense[idx]
    # local outward normal of the CAD curve
    nxt = dense[(idx+4) % len(dense)]
    prv = dense[(idx-4) % len(dense)]
    tg = nxt-prv; tg /= np.maximum(np.linalg.norm(tg, axis=1, keepdims=True), 1e-9)
    nrm = np.c_[-tg[:, 1], tg[:, 0]]
    ctr = dense.mean(0)
    out = nrm.copy()
    for i in range(len(out)):
        if np.dot(p[i]-ctr, out[i]) < 0:
            out[i] = -out[i]
    s = ((p-c)*out).sum(1)
    return s


def audit():
    rows, feas = [], []
    for i, cid in enumerate(ids):
        q = [v for v in views if v['view'] == cid][0]
        c = np.load(q['cache']); labels = c['labels']
        ob, rec = G.build_obs(cid, labels, {'q_train': np.zeros((0, 2))})
        if 'inner_pts' not in ob:
            rows.append(dict(view=cid, status='NO_DXY')); continue
        ci, co = CG.split_by_area(torus_contours(cams['c2w'][i], K))
        r = dict(view=cid, inner_vis=int(ob['inner_vis'].sum()), outer_vis=int(ob['outer_vis'].sum()),
                 inner_cov=float(ob['inner_vis'].mean()), outer_cov=float(ob['outer_vis'].mean()),
                 inner_perim=float(ob['inner_perim']), outer_perim=float(ob['outer_perim']))
        din = CG.dist_to_polyline(CG.resample_closed(ci, 256), ob['inner_pts'])
        dout = CG.dist_to_polyline(CG.resample_closed(co, 256), ob['outer_pts'])
        r['inner_mae'] = float(din.mean()); r['outer_mae'] = float(dout.mean())
        si = signed_residual(ci, ob['inner_pts'], ob['inner_vis'])
        so = signed_residual(co, ob['outer_pts'], ob['outer_vis'])
        r['inner_signed_mean'] = float(np.mean(si)) if si is not None else np.nan
        r['outer_signed_mean'] = float(so is not None and np.mean(so) or np.nan) if so is not None else np.nan
        r['class'] = ('A_COMMON_SHIFT' if (si is not None and so is not None and
                                           np.sign(np.mean(si)) == np.sign(np.mean(so)) and
                                           abs(np.mean(si)) > 1.0 and abs(np.mean(so)) > 1.0)
                      else 'B_RELATIVE' if (abs(r['inner_mae']-r['outer_mae']) > 1.0) else 'CONSISTENT')
        rows.append(r)
    return pd.DataFrame(rows)


def feasibility(frame_idx, which):
    """Local Ring-only pose search from the B0 camera: can one pose explain both curves?"""
    cid = ids[frame_idx]
    q = [v for v in views if v['view'] == cid][0]
    labels = np.load(q['cache'])['labels']
    ob, _ = G.build_obs(cid, labels, {'q_train': np.zeros((0, 2))})
    C0 = cams['c2w'][frame_idx]

    def res(p):
        M = np.eye(4); M[:3, :3] = Rot.from_rotvec(p[:3]).as_matrix(); M[:3, 3] = p[3:]
        cb, _ = G.cad_blocks(M, K, ob, which=which)
        return cb
    p0 = np.r_[Rot.from_matrix(C0[:3, :3]).as_rotvec(), C0[:3, 3]]
    out = least_squares(res, p0, loss='soft_l1', f_scale=1.0, max_nfev=300)
    M = np.eye(4); M[:3, :3] = Rot.from_rotvec(out.x[:3]).as_matrix(); M[:3, 3] = out.x[3:]
    ci, co = CG.split_by_area(torus_contours(M, K))
    din = float(CG.dist_to_polyline(CG.resample_closed(ci, 256), ob['inner_pts']).mean())
    dout = float(CG.dist_to_polyline(CG.resample_closed(co, 256), ob['outer_pts']).mean())
    return dict(view=cid, which=which, status=('CONVERGED' if out.success else 'NUMERIC_FAILURE'),
                inner_mae=din, outer_mae=dout, nfev=int(out.nfev),
                trans_mm=float(np.linalg.norm(M[:3, 3]-C0[:3, 3])),
                rot_deg=float(np.degrees(np.linalg.norm(Rot.from_matrix(M[:3, :3]@C0[:3, :3].T).as_rotvec()))))


if __name__ == '__main__':
    a = audit(); a.to_csv(T/'metrics/FIXED_POSE_GEOMETRY.csv', index=False)
    print(a[['view', 'inner_mae', 'outer_mae', 'inner_signed_mean', 'outer_signed_mean', 'class']].round(2).to_string(index=False))
    F = []
    for i in (0, 5, 10):
        for w in ('inner', 'outer', 'both'):
            try:
                F.append(feasibility(i, w))
            except Exception as e:
                F.append(dict(view=ids[i], which=w, status='ERROR:'+str(e)[:60]))
    fd = pd.DataFrame(F); fd.to_csv(T/'metrics/CAD_FEASIBILITY.csv', index=False)
    print(); print(fd.round(2).to_string(index=False))
