from pathlib import Path
import os,sys,json,csv,hashlib,ast
R=Path(__file__).resolve().parents[1];REPO=R.parents[1]
PREV=Path('/home/liu/ring_first_3d_e4_sdf_evolution/experiments/E4-SDF-EVOLUTION-001')
OLD=Path('/home/liu/polyp_research/experiments/realistic_simulation_mask_v2')
BLENDER='/home/liu/blender/blender-5.0.1-linux-x64/blender'
for name in ['runtime/mpl','runtime/tmp','inputs','local_results','audit_only','metrics','assets_index','figures/full','config']:(R/name).mkdir(parents=True,exist_ok=True)
os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='2',MKL_NUM_THREADS='1',MPLCONFIGDIR=str(R/'runtime/mpl'),TMPDIR=str(R/'runtime/tmp'),PYTHONDONTWRITEBYTECODE='1');sys.dont_write_bytecode=True
sys.path[:0]=[str(PREV/'runtime/packages'),'/home/liu/polyp_research/ring_anchor_3d/experiments/surface_fusion_v3/vendor']
import numpy as np,cv2,trimesh
from PIL import Image
import open3d as o3d
from scipy.spatial import cKDTree
sys.path.insert(0,str(REPO));from visualization import real_p0_renderer as vis
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def asset(p):return dict(path=str(p),sha256=sha(p),bytes=Path(p).stat().st_size)
def load(p):return json.loads(Path(p).read_text())
def clean(v):
    if isinstance(v,dict):return {k:clean(x)for k,x in v.items()}
    if isinstance(v,(list,tuple)):return [clean(x)for x in v]
    if isinstance(v,Path):return str(v)
    if hasattr(v,'tolist'):return clean(v.tolist())
    if isinstance(v,float)and not np.isfinite(v):return None
    return v
def save(p,obj):(R/p).parent.mkdir(parents=True,exist_ok=True);(R/p).write_text(json.dumps(clean(obj),ensure_ascii=False,indent=2)+'\n')
def table(p,rows):
    if not rows:return
    with (R/p).open('w',newline='')as f:
        keys=list(dict.fromkeys(k for r in rows for k in r));w=csv.DictWriter(f,keys,lineterminator='\n');w.writeheader()
        for r in rows:w.writerow({k:json.dumps(clean(v),ensure_ascii=False)if isinstance(v,(dict,list,tuple,np.ndarray))else clean(v)for k,v in r.items()})
def stats(x):
    x=np.asarray(x);x=x[np.isfinite(x)];return dict(N=len(x),median_signed=float(np.median(x))if len(x)else None,median_absolute=float(np.median(abs(x)))if len(x)else None,MAE=float(np.mean(abs(x)))if len(x)else None,p95=float(np.quantile(abs(x),.95))if len(x)else None,maximum=float(max(abs(x)))if len(x)else None)
def scene(V,F):
    s=o3d.t.geometry.RaycastingScene(nthreads=2);s.add_triangles(o3d.core.Tensor(np.asarray(V,np.float32)),o3d.core.Tensor(np.asarray(F,np.uint32)));return s
def signed(rt,X):return rt.compute_signed_distance(o3d.core.Tensor(np.asarray(X,np.float32)),nsamples=3).numpy().astype(float)
def cast(rt,uv,K,T):
    x=rt.cast_rays(o3d.core.Tensor(vis.camera_rays(uv,K,T).astype(np.float32)));return x['t_hit'].numpy().astype(float),x['primitive_ids'].numpy().astype(int)
def contour(mask):
    cs,_=cv2.findContours(mask.astype(np.uint8),cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE);return np.concatenate([c[:,0]for c in cs]).astype(float)if cs else np.empty((0,2))
def protocol():return load(R/'config/LOCKED_PROTOCOL.json')
def guard(event,args):
    if event!='open'or not isinstance(args[0],(str,bytes)):return
    p=Path(os.fsdecode(args[0])).resolve();s=str(p);mode=args[1]if isinstance(args[1],str)else'';flags=args[2]if isinstance(args[2],int)else 0;write=any(k in mode for k in 'wax+')or flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)
    if write and s.startswith('/home/liu/')and not p.is_relative_to(R):raise PermissionError('TASK_LOCAL_WRITES_ONLY:'+s)
    if os.environ.get('E4_OPTIMIZER_ONLY')=='1'and not write:
        if p.suffix=='.blend' or '/audit_only/' in s or '/realistic_simulation_mask_v2/' in s or (p.suffix.lower() in {'.npz','.npy','.png','.ply','.glb','.obj','.stl'} and not p.is_relative_to(R)):raise PermissionError('GT_NOT_AN_OPTIMIZER_INPUT:'+s)
sys.addaudithook(guard);cv2.setNumThreads(2)
