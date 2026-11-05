"""Task-local IO. No historical experiment is imported or mutated."""
from pathlib import Path
import os, sys, json, hashlib, csv, time
R = Path(__file__).resolve().parents[1]
REPO = R.parents[1]
OLD = REPO/'experiments/TASK-E4-2D3D-OBSERVABILITY-001'
EV = Path('/home/liu/ring_first_3d_e4_sdf_evolution/experiments/E4-SDF-EVOLUTION-001')
R1 = Path('/home/liu/ring_first_3d_e4_pmgr_r1/experiments/TASK-E4-PMGR-R1')
FFD = Path('/home/liu/ring_first_3d_e4_ffd/experiments/TASK-E4-PMGR-FFD-002')
for d in ['runtime/mpl','runtime/tmp','inputs','metrics','figures','assets_index','local_results','config','upstream']:
    (R/d).mkdir(parents=True, exist_ok=True)
os.environ.update(OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='2', MPLCONFIGDIR=str(R/'runtime/mpl'), PYTHONDONTWRITEBYTECODE='1')
sys.dont_write_bytecode = True
sys.path[:0] = [str(R/'runtime/packages'), str(R/'runtime/pytorch3d'), str(EV/'runtime/packages'), '/home/liu/polyp_research/ring_anchor_3d/experiments/surface_fusion_v3/vendor']
import numpy as np, cv2, trimesh
from PIL import Image
from scipy.spatial import cKDTree
cv2.setNumThreads(2)
def load(p): return json.loads(Path(p).read_text())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def asset(p): return dict(path=str(p), bytes=Path(p).stat().st_size, sha256=sha(p))
def clean(v):
    if isinstance(v, dict): return {str(k):clean(a) for k,a in v.items()}
    if isinstance(v, (list,tuple)): return [clean(a) for a in v]
    if isinstance(v, Path): return str(v)
    if hasattr(v, 'tolist'): return clean(v.tolist())
    if isinstance(v, float) and not np.isfinite(v): return None
    return v
def save(p, v):
    p=R/p; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(clean(v),ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def table(p, rows):
    if not rows: return
    p=R/p; p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',newline='') as f:
        keys=list(dict.fromkeys(k for r in rows for k in r)); w=csv.DictWriter(f,keys,lineterminator='\n');w.writeheader()
        for r in rows: w.writerow({k:json.dumps(clean(v),ensure_ascii=False) if isinstance(v,(dict,list,tuple,np.ndarray)) else clean(v) for k,v in r.items()})
def stats(a):
    a=np.asarray(a); a=a[np.isfinite(a)]
    return dict(N=len(a),MAE=float(abs(a).mean()) if len(a) else None,median=float(np.median(abs(a))) if len(a) else None,p95=float(np.quantile(abs(a),.95)) if len(a) else None,maximum=float(max(abs(a))) if len(a) else None)
def scene(V,F):
    import open3d as o3d
    s=o3d.t.geometry.RaycastingScene(nthreads=2); s.add_triangles(o3d.core.Tensor(np.asarray(V,np.float32)),o3d.core.Tensor(np.asarray(F,np.uint32))); return s
def cast(s,K,T,h,w):
    import open3d as o3d
    v,u=np.mgrid[:h,:w]; p=np.c_[u.ravel(),v.ravel(),np.ones(h*w)]@np.linalg.inv(K).T
    rays=np.c_[np.broadcast_to(T[:3,3],p.shape),p@T[:3,:3].T].astype(np.float32)
    z=s.cast_rays(o3d.core.Tensor(rays))['t_hit'].numpy().reshape(h,w).astype(float);return z
def contour(m):
    cs,_=cv2.findContours(m.astype(np.uint8),cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE)
    return np.concatenate([c[:,0] for c in cs]).astype(float) if cs else np.empty((0,2))
def getcase(name): return load(R/'inputs'/name/'CASE.json')
def guard_optimizer():
    def guard(event,args):
        if event!='open' or not isinstance(args[0],(str,bytes)): return
        p=Path(os.fsdecode(args[0])).resolve(); mode=args[1] if isinstance(args[1],str) else ''; flags=args[2] if isinstance(args[2],int) else 0
        writing=any(x in mode for x in 'wax+') or flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)
        if writing and str(p).startswith('/home/liu/') and not p.is_relative_to(R): raise PermissionError('TASK_LOCAL_WRITES_ONLY:'+str(p))
        if not writing and ('/audit_only/' in str(p) or p.suffix=='.blend' or 'NATIVE_CAD_GT' in p.name): raise PermissionError('NO_PROJECT_GT_IN_OPTIMIZATION:'+str(p))
    sys.addaudithook(guard)
