"""E1 CPU-only bridge; no legacy module main, neural import or forward."""
from pathlib import Path
from functools import lru_cache
import os, sys, ast, json, csv, hashlib, datetime, subprocess

R = Path(__file__).resolve().parents[1]
REPO = R.parents[1]
E0 = Path('/home/liu/ring_first_3d_neural_e0/experiments/TASK-NEURAL-E0-COMPARE-001')
GROW = Path('/home/liu/ring_first_3d_boundary_growth/experiments/TASK-BOUNDARY-GUIDED-SURFACE-GROWTH-001')
PART = Path('/home/liu/ring_first_3d_view_partition/experiments/TASK-VIEW-PARTITION-MAST3R-FUSION-001')
INC = Path('/home/liu/ring_first_3d_incremental/experiments/TASK-PHASED-INCREMENTAL-FUSION-MULTIGROUP-001')
OLD = Path('/home/liu/polyp_research/ring_anchor_3d/experiments')
VENDOR = OLD / 'surface_fusion_v3/vendor'
MAP = E0 / 'runtime/map-anything'
SDF = E0 / 'runtime/monosdf_official'
os.environ.update(CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
                  HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                  MPLCONFIGDIR=str(R/'runtime/mpl'), TMPDIR=str(R/'runtime/tmp'),
                  OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='2')
sys.dont_write_bytecode = True
for p in ['metrics','provenance','config','figures','visualizations','runtime/tmp','local_results']:
    (R/p).mkdir(parents=True, exist_ok=True)
ACCESSED = set()
REUSE = []

def guard(event, args):
    if event.startswith('socket.') and event in ('socket.connect', 'socket.getaddrinfo'):
        raise PermissionError('E1_NETWORK_DISABLED')
    if event == 'import':
        name = str(args[0])
        if name.startswith(('mapanything.models', 'model.network', 'transformers.models')):
            raise PermissionError('E1_NEURAL_MODEL_IMPORT_DENIED: '+name)
    if event != 'open' or not isinstance(args[0], (str, bytes)):
        return
    p = Path(os.fsdecode(args[0])).resolve()
    s, n = str(p), p.name.lower()
    if n.endswith('.blend') or n.startswith('gt_') or 'oracle' in n or any(
        x in s for x in ['/private_gt/', '/gt_mapping/', '/evaluation_exports/',
                         '/evaluation_only/', '/new-polyp-dxy/']):
        raise PermissionError('E1_GT_DXY_DENIED: '+s)
    mode = args[1] if len(args)>1 and isinstance(args[1], str) else ''
    flags = args[2] if len(args)>2 and isinstance(args[2], int) else 0
    writing = any(x in mode for x in 'wax+') or flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)
    if writing and s.startswith('/home/liu/') and not p.is_relative_to(R):
        raise PermissionError('E1_TASK_OUTPUT_ONLY: '+s)
    if not writing and s.startswith('/home/liu/') and not p.is_relative_to(R):
        ACCESSED.add(s)

sys.addaudithook(guard)
import numpy as np, cv2, trimesh
from PIL import Image
sys.path.insert(0, str(REPO))
from visualization import real_p0_renderer as vis
from visualization.same_camera_scene import SameCameraScene

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(2**20), b''): h.update(b)
    return h.hexdigest()

def load(p): return json.loads(Path(p).read_text())
def clean(v):
    if isinstance(v, dict): return {str(k):clean(x) for k,x in v.items()}
    if isinstance(v, (list,tuple)): return [clean(x) for x in v]
    if isinstance(v, np.ndarray): return clean(v.tolist())
    if isinstance(v, (np.integer,np.bool_)): return v.item()
    if isinstance(v, (float,np.floating)): return float(v) if np.isfinite(v) else None
    if isinstance(v, Path): return str(v)
    return v
normal=clean
def save(p, data):
    p=R/p; p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(clean(data),ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def table(p, rows):
    p=R/p; p.parent.mkdir(parents=True, exist_ok=True)
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with p.open('w', newline='') as f:
        w=csv.DictWriter(f, keys, lineterminator='\n'); w.writeheader()
        for row in rows:
            w.writerow({k:json.dumps(clean(v),ensure_ascii=False) if isinstance(v,(dict,list,tuple,np.ndarray)) else ('NaN' if isinstance(v,(float,np.floating)) and not np.isfinite(v) else clean(v)) for k,v in row.items()})
def stats(a):
    a=np.asarray(a,float); a=a[np.isfinite(a)]
    return dict(N=len(a),median=float(np.median(a)) if len(a) else None,
                MAE=float(np.mean(abs(a))) if len(a) else None,
                p95=float(np.quantile(abs(a),.95)) if len(a) else None,
                maximum=float(np.max(abs(a))) if len(a) else None)
def extract(path,names,ns=None):
    path=Path(path); tree=ast.parse(path.read_text())
    nodes=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names]
    if not set(names).issubset({n.name for n in nodes}): raise ValueError('missing entrypoint '+str(path))
    if ns is None: ns=dict(globals())
    for n in nodes:
        REUSE.append(dict(path=str(path),file_SHA256=sha(path),name=n.name,line=n.lineno,
                          signature=ast.unparse(n.args) if isinstance(n,ast.FunctionDef) else 'class',
                          AST_SHA256=hashlib.sha256(ast.dump(n,include_attributes=False).encode()).hexdigest(),
                          status='AST_EXTRACTED_EXACT_NO_MODULE_MAIN'))
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),ns)
    return ns

unproject=extract(OLD/'ring_first_v1/scripts/common.py',['unproject'])['unproject']

def asset(p, role='', expected=None):
    p=Path(p); d=dict(path=str(p),role=role,status='AVAILABLE' if p.is_file() else 'MISSING')
    if p.is_file(): d.update(bytes=p.stat().st_size,sha256=sha(p))
    if expected: d.update(expected_SHA256=expected,hash_match=d.get('sha256')==expected)
    return d

def git(root,*args):
    return subprocess.check_output(['git','--no-optional-locks','-C',str(root),*args],text=True).strip()

def protected_state():
    roots=[Path('/home/liu/polyp_research'),*sorted(Path('/home/liu').glob('ring_first_3d*'))]
    out=[]
    for root in roots:
        if root==REPO or not (root/'.git').exists(): continue
        status=git(root,'status','--porcelain=v1','--untracked-files=no')
        modified={}
        for line in status.splitlines():
            p=root/line[3:]
            if p.is_file(): modified[line[3:]]=sha(p)
        out.append(dict(path=str(root),HEAD=git(root,'rev-parse','HEAD'),status=status,modified=modified))
    return out

@lru_cache(None)
def ring(kind):
    return trimesh.load(OLD/'surface_fusion_v2/inputs/R10_ring.obj' if kind=='R10' else OLD.parent/'assets/ring_R5.obj',process=False)

@lru_cache(None)
def cad_scene(kind):
    sys.path.insert(0,str(VENDOR)); import open3d as o3d
    m=ring(kind); s=o3d.t.geometry.RaycastingScene(nthreads=2)
    s.add_triangles(o3d.core.Tensor(np.asarray(m.vertices,np.float32)),o3d.core.Tensor(np.asarray(m.faces,np.uint32)))
    return s

def legacy_geometry_namespace(D):
    ns=dict(globals(),D=D,CC={c['id']:c for c in D['references']})
    extract(E0/'code/evidence.py',['points','combine','f3'],ns)
    return ns

def conventions(): return load(R/'config/CPU_CONTRACT.json')
