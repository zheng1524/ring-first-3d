"""P2/P3: real loss blocks, gradients and corrected evaluators at the frozen B0 cameras."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
from scipy.spatial import cKDTree
from scipy.optimize import approx_fprime
T = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(T/'code')); sys.path.insert(0, '/home/liu/ring_first_3d_workspace/src')
import j2_obs_correct as J
from ring_first_3d.mainline.native.camera import torus_contours
from ring_first_3d.mainline.native.geometry import project
from scipy.spatial.transform import Rotation as Rot
K = np.array([[490., 0, 319.5], [0, 490., 179.5], [0, 0, 1]])
T006 = Path('/home/liu/ring_first_3d_workspace/experiments/TASK-E4-UNIFIED-RING-CONTOUR-REFINEMENT-005')
T011 = Path('/home/liu/ring_first_3d_workspace/experiments/TASK-E4-RING-RGB-JOINT-BA-011-REPAIR')
views = json.loads((T006/'runs/prepared/G03_005/PREPARED.json').read_text())['views']
ids = [v['view'] for v in views]
tr = dict(np.load(T011/'runs/G03_005/B0/observations/tracks005.npz'))
xy = tr['xy']; held = np.asarray(tr['held']).astype(bool)
cams = np.load(T011/'runs/G03_005/B0/cameras.npz')['c2w']
pts = np.load(T011/'runs/G03_005/B0/cameras.npz')['points']
pids = np.load(T011/'runs/G03_005/B0/cameras.npz')['point_track_ids'].astype(int)


def obs_for(cid):
    q = [v for v in views if v['view'] == cid][0]
    labels = np.load(q['cache'])['labels']
    rec = json.loads((T/'code'/'..'/'..'/'..'/'..'/ 'x' if False else
                      Path('/home/liu/ring_first_3d_workspace/experiments/TASK-E4-RING-RGB-JOINT-BA-011-REPAIR/metrics/DXY_OBSERVATIONS')/(cid+'.json')).read_text()) if False else None
    return labels


def dxy(cid):
    p = Path('/home/liu/ring_first_3d_workspace/experiments/TASK-E4-RING-RGB-JOINT-BA-011-REPAIR/metrics/DXY_OBSERVATIONS')/(cid+'.json')
    return json.loads(p.read_text())


def ellipse_pts(e, n=720):
    t = np.linspace(0, 2*np.pi, n, endpoint=False)
    c, s = np.cos(np.deg2rad(e['angle_deg'])), np.sin(np.deg2rad(e['angle_deg']))
    x = e['major_radius']*np.cos(t); y = e['minor_radius']*np.sin(t)
    return np.c_[c*x - s*y + e['cx'], s*x + c*y + e['cy']]


def trusted(rec, key, labels, tol=1.5, n=720):
    import cv2
    e = rec.get(key)
    if e is None: return None, None
    p = ellipse_pts(e, n)
    edge = cv2.Canny(((labels == 2).astype(np.uint8))*255, 50, 150)
    ys, xs = np.nonzero(edge)
    if len(ys) == 0: return p, np.zeros(n, bool)
    d, _ = cKDTree(np.c_[xs, ys].astype(float)).query(p, k=1)
    return p, d <= tol


rows, grad_rows = [], []
for i, cid in enumerate(ids):
    q = [v for v in views if v['view'] == cid][0]
    labels = np.load(q['cache'])['labels']; rec = dxy(cid)
    ob = {}
    for key in ('inner', 'outer'):
        p_, v_ = trusted(rec, key, labels); ob[key+'_pts'], ob[key+'_vis'] = p_, v_
    ob['q_train'] = np.load(T011/'runs/G03_005/B0/observations'/(cid+'_ring.npz'))['q_train']
    # --- real loss blocks at B0 camera
    cs = torus_contours(cams[i], K)
    ci, co = J.split_by_area(cs)
    cb, st = J.blocks(cams[i], K, ob, which='both')
    inner_r, outer_r, bar = cb[:256], cb[256:512], cb[512:]
    d_in = J.dist_pts_to_poly(J.resample_closed(ci, 256), ob['inner_pts'])
    d_out = J.dist_pts_to_poly(J.resample_closed(co, 256), ob['outer_pts'])
    # corrected raw metric: per-observation min over the two CAD curves
    rmin = np.minimum(J.dist_pts_to_poly(ob['q_train'], ci), J.dist_pts_to_poly(ob['q_train'], co))
    # RGB train reprojection
    errs = []
    for j, tid in enumerate(pids):
        if held[tid]: continue
        u = xy[tid, i]
        if not np.isfinite(u[0]): continue
        uv, z = project(pts[j][None], cams[i], K)
        if np.isfinite(uv).all() and z[0] > 0: errs.append(float(np.linalg.norm(uv[0]-u)))
    rows.append(dict(view=cid, inner_mae=float(np.mean(d_in)), outer_mae=float(np.mean(d_out)),
                     inner_p95=float(np.percentile(d_in, 95)), outer_p95=float(np.percentile(d_out, 95)),
                     raw_mae=float(rmin.mean()), raw_p95=float(np.percentile(rmin, 95)),
                     E_inner=float(np.sum(inner_r**2)), E_outer=float(np.sum(outer_r**2)),
                     E_barrier=float(np.sum(bar**2)), rgb_train_mae=float(np.mean(errs)) if errs else np.nan,
                     rgb_train_n=len(errs), margin_mm=J.cad_margin_analytic(cams[i]),
                     vis_inner=int(ob['inner_vis'].sum()), vis_outer=int(ob['outer_vis'].sum())))
    # --- gradient of each block w.r.t. a local SE(3) perturbation (rot in mrad, trans in mm)
    def f_ring(dx):
        M = cams[i].copy()
        R = Rot.from_rotvec(dx[:3]/1000.0).as_matrix()
        M[:3, :3] = R @ M[:3, :3]; M[:3, 3] = M[:3, 3] + dx[3:]
        b, _ = J.blocks(M, K, ob, which='both')
        return 0.5*float(np.sum(b**2))
    g = approx_fprime(np.zeros(6), f_ring, 1e-3)
    grad_rows.append(dict(view=cid, g_rot=float(np.linalg.norm(g[:3])), g_trans=float(np.linalg.norm(g[3:])),
                          g_norm=float(np.linalg.norm(g)), margin_mm=J.cad_margin_analytic(cams[i])))
pd.DataFrame(rows).to_csv(T/'metrics/LOSS_COMPONENTS.csv', index=False)
pd.DataFrame(grad_rows).to_csv(T/'metrics/GRADIENT_DIAGNOSTICS.csv', index=False)
d = pd.DataFrame(rows)
print(d[['inner_mae','outer_mae','raw_mae','E_inner','E_outer','E_barrier','rgb_train_mae']].mean().round(4).to_string())
print('margin min %.2f mm; vis_inner mean %.0f; vis_outer mean %.0f' % (d.margin_mm.min(), d.vis_inner.mean(), d.vis_outer.mean()))
g = pd.DataFrame(grad_rows); print('ring grad: |rot| %.1f  |trans| %.1f  (per view mean)' % (g.g_rot.mean(), g.g_trans.mean()))
