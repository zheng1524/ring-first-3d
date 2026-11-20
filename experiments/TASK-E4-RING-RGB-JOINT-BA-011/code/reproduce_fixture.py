import json, sys, argparse
from pathlib import Path
import numpy as np
T = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(T/'code')); sys.path.insert(0, '/home/liu/ring_first_3d_workspace/src')
import contour_geometry as CG, joint_ring_observation as JO
from ring_first_3d.mainline.native.camera import torus_contours
K = np.array([[490., 0, 319.5], [0, 490., 179.5], [0, 0, 1]])
ap = argparse.ArgumentParser(); ap.add_argument('--pkg', required=True); a = ap.parse_args()
pkg = Path(a.pkg)
exp = json.loads((pkg/'fixture/expected.json').read_text())
T006 = Path('/home/liu/ring_first_3d_workspace/experiments/TASK-E4-UNIFIED-RING-CONTOUR-REFINEMENT-005')
T008 = Path('/home/liu/ring_first_3d_workspace/experiments/TASK-E4-REAL-JOINT-BA-008')
views = json.loads((T006/'runs/prepared/G03_005/PREPARED.json').read_text())['views']
cams = dict(np.load(T008/'runs/G03_005/B0/cameras.npz')); ids = [str(s) for s in cams['ids']]
rows, ok = [], True
for v, ei, eo in zip(exp['views'], exp['inner_mae'], exp['outer_mae']):
    i = ids.index(v); q = [x for x in views if x['view'] == v][0]
    labels = np.load(q['cache'])['labels']
    rec = JO.load(v)
    ob = {}
    for key in ('inner', 'outer'):
        pts, vis = JO.trusted_support(rec, key, labels)
        ob[key+'_pts'], ob[key+'_vis'] = pts, vis
    ci, co = CG.split_by_area(torus_contours(cams['c2w'][i], K))
    din = float(CG.dist_to_polyline(CG.resample_closed(ci, 256), ob['inner_pts']).mean())
    dout = float(CG.dist_to_polyline(CG.resample_closed(co, 256), ob['outer_pts']).mean())
    good = abs(din-ei) <= exp['tol_px'] and abs(dout-eo) <= exp['tol_px']
    ok &= good
    rows.append(dict(view=v, inner=round(din, 3), outer=round(dout, 3), exp_inner=ei, exp_outer=eo, pass_=bool(good)))
print(json.dumps(rows, indent=1))
(pkg/'REPRO_RESULT.json').write_text(json.dumps(dict(pass_=bool(ok), rows=rows,
    commit=__import__('subprocess').check_output(['git', '-C', str(T.parents[1]), 'rev-parse', 'HEAD']).decode().strip()), indent=1))
print('REPRO:', 'PASS' if ok else 'FAIL')
sys.exit(0 if ok else 1)
