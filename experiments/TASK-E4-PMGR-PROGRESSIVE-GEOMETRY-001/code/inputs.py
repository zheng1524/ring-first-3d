"""Controlled pure-function extraction; never imports A1's CPU/audit bootstrap."""
from pathlib import Path
from functools import lru_cache
import os, sys, ast, json, csv, hashlib
R=Path(__file__).resolve().parents[1]; REPO=R.parents[1]
OLD=Path('/home/liu/polyp_research/ring_anchor_3d/experiments')
E1ROOT=Path('/home/liu/ring_first_3d_neural_e1/experiments/TASK-NEURAL-E1-PIPELINE-RECOVERY-001')
N0=Path('/home/liu/ring_first_3d_e3n0_eight/experiments/TASK-E3-N0-NEURALFUSION-EIGHT-VIEW-001')
MULTI=Path('/home/liu/ring_first_3d_e3_sdf_multi/experiments/TASK-E3-SDF-LOCAL-MULTIPOLYP-EXPLORATORY-001')
A1=Path('/home/liu/ring_first_3d_e4_e1e2/experiments/TASK-E4-A1-ELLIPSE-VS-FULLMASK-001')
for d in ['runtime/mpl','runtime/tmp','inputs','metrics','assets_index','local_results','figures/full','config']:(R/d).mkdir(parents=True,exist_ok=True)
os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='2',MPLCONFIGDIR=str(R/'runtime/mpl'),TMPDIR=str(R/'runtime/tmp'),PYTHONDONTWRITEBYTECODE='1')
sys.dont_write_bytecode=True
sys.path.insert(0,str(R/'runtime/packages'))
import numpy as np, cv2, trimesh
from PIL import Image
from scipy.spatial.transform import Rotation
sys.path.insert(0,str(OLD/'surface_fusion_v3/vendor')); import open3d as o3d
sys.path.insert(0,str(REPO)); from visualization import real_p0_renderer as vis
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def clean(x):
    if isinstance(x,dict):return {str(k):clean(v)for k,v in x.items()}
    if isinstance(x,(list,tuple)):return [clean(v)for v in x]
    if hasattr(x,'tolist'):return clean(x.tolist())
    if isinstance(x,Path):return str(x)
    if isinstance(x,float)and not np.isfinite(x):return None
    return x
def save(name,x):
    p=R/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(clean(x),ensure_ascii=False,indent=2)+'\n')
def table(name,rows):
    if not rows:return
    p=R/name;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',newline='')as f:
        keys=list(dict.fromkeys(k for row in rows for k in row));w=csv.DictWriter(f,keys,lineterminator='\n');w.writeheader()
        for row in rows:w.writerow({k:json.dumps(clean(v),ensure_ascii=False)if isinstance(v,(dict,list,tuple))else clean(v)for k,v in row.items()})
def asset(p):return dict(path=str(p),sha256=sha(p),bytes=Path(p).stat().st_size)
EXTRACTED=[]
def extract(p,names):
    nodes=[n for n in ast.parse(Path(p).read_text()).body if isinstance(n,ast.FunctionDef)and n.name in names]
    assert {n.name for n in nodes}==set(names)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(p),'exec'),globals())
    EXTRACTED.append(dict(path=str(p),sha256=sha(p),functions=names))
CC={x['id']:x for x in load(E1ROOT/'provenance/INPUT_ELIGIBILITY.json')['references']}
GATE={x['source']:x for x in load(N0/'config/CAMERA_GATE_RESULTS.json')['sources']}
extract(N0/'code/common.py',['source','native','original','ringmesh','mesh_scene','ringscene','cast'])
extract(OLD/'ring_first_v1/scripts/common.py',['unproject'])
extract(A1/'code/common.py',['decode','first_depth','ray_components','cleaned','contour'])
cv2.setNumThreads(2)
def protocol():return load(R/'config/LOCKED_PROTOCOL.json')
@lru_cache(None)
def obs(cid):return dict(np.load(R/'inputs'/(cid+'.npz')))
def p0s():return load(A1/'metrics/PRIMARY_A_ONLY.json')
def p0(scene,initial):return next(x for x in p0s()if x['scene']==scene and x['arm']==initial and x['variant']=='full')
def stats(a):
    a=np.asarray(a);a=a[np.isfinite(a)]
    return dict(N=len(a),median=float(np.median(a))if len(a)else None,MAE=float(abs(a).mean())if len(a)else None,p95=float(np.quantile(abs(a),.95))if len(a)else None,maximum=float(abs(a).max())if len(a)else None)
def readonly_guard(event,args):
    if event!='open'or not isinstance(args[0],(str,bytes)):return
    p=Path(os.fsdecode(args[0])).resolve();s=str(p);mode=args[1]if isinstance(args[1],str)else'';flags=args[2]if len(args)>2 and isinstance(args[2],int)else 0
    write=any(c in mode for c in 'wax+')or flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)
    if write and s.startswith('/home/liu/')and not p.is_relative_to(R):raise PermissionError('PMGR_TASK_WRITES_ONLY:'+s)
    if not write and not p.is_relative_to(R):
        if any(k in s.lower()for k in ['/private_gt/','/oracle/','/gt_mapping','/evaluation_only/','/local_results/scenes/']):raise PermissionError('NO_GT_OR_FUSION:'+s)
sys.addaudithook(readonly_guard)
