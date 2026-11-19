"""Task-local adapters; mature geometry is compiled unchanged from frozen ASTs."""
from ring_first_3d.mainline.paths import historical_path as _mainline_path
from pathlib import Path
import ast, csv, hashlib, json, os, sys, time, types, subprocess
from functools import lru_cache
R = Path(__file__).resolve().parents[1]
REPO = R.parents[1]
ASSETS = Path(str(_mainline_path('/home/liu/ring_first_3d_e4_sdf_localization/experiments')))
OLD = REPO/'experiments/TASK-E4-BODY-GUIDED-HERO-RELOCALIZATION-001'
A1 = REPO/'experiments/TASK-E4-A1-ELLIPSE-VS-FULLMASK-001/code'
MODEL = REPO/'experiments/TASK-E4-A1-COARSE-BODY-001/code/models.py'
DXY = Path('/home/liu/new-polyp-dxy')
for d in ['config','metrics','provenance','inputs','local_results','figures','runtime/tmp','runtime/mpl']:
    (R/d).mkdir(parents=True, exist_ok=True)
os.environ.update(OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1', MPLCONFIGDIR=str(R/'runtime/mpl'), TMPDIR=str(R/'runtime/tmp'))
sys.dont_write_bytecode=True
sys.path.insert(0,'/home/liu/polyp_research/ring_anchor_3d/experiments/surface_fusion_v3/vendor')
import numpy as np, cv2, trimesh, open3d as o3d
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation
from scipy.special import expit
from scipy.ndimage import map_coordinates, distance_transform_edt
from scipy.optimize import least_squares
cv2.setNumThreads(1)
def load(p): return json.loads(Path(p).read_text())
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def asset(p): return dict(path=str(p),sha256=sha(p),bytes=Path(p).stat().st_size)
def clean(x):
    if isinstance(x,dict): return {str(k):clean(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)): return [clean(v) for v in x]
    if hasattr(x,'tolist'): return clean(x.tolist())
    if isinstance(x,Path): return str(x)
    if isinstance(x,float) and not np.isfinite(x): return None
    return x
def save(p,x):
    p=R/p;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(clean(x),ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def table(p,rows):
    p=R/p;p.parent.mkdir(parents=True,exist_ok=True)
    fields=list(dict.fromkeys(k for row in rows for k in row))
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fields,lineterminator='\n');w.writeheader()
        for row in rows: w.writerow({k:json.dumps(clean(v),ensure_ascii=False) if isinstance(v,(dict,list,tuple,np.ndarray)) else clean(v) for k,v in row.items()})
REUSE=[]
def reuse(path,names,namespace=None,cls=None):
    path=Path(path);tree=ast.parse(path.read_text())
    nodes=tree.body if cls is None else next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==cls).body
    chosen=[n for n in nodes if isinstance(n,ast.FunctionDef) and n.name in names]
    assert {n.name for n in chosen}==set(names),(path,names)
    space=globals() if namespace is None else namespace
    exec(compile(ast.Module(body=chosen,type_ignores=[]),str(path),'exec'),space)
    for n in chosen:
        REUSE.append(dict(file=asset(path),function=(cls+'.' if cls else '')+n.name,line=n.lineno,end_line=n.end_lineno,AST_sha256=hashlib.sha256(ast.dump(n,include_attributes=False).encode()).hexdigest(),mathematics_modified=False))
    return space
reuse(MODEL,['decode','sphere_mesh'])
reuse(A1/'common.py',['contour','ray_components','first_depth','mesh'])
reuse(REPO/'visualization/real_p0_renderer.py',['camera_rays'])
vis=types.SimpleNamespace(camera_rays=camera_rays)
reuse(Path(str(_mainline_path('/home/liu/ring_first_3d_e4_a1/experiments/TASK-E4-A1-COARSE-BODY-001/code/common.py'))),['camera_frame'])
reuse(Path(str(_mainline_path('/home/liu/ring_first_3d_e3n0_eight/experiments/TASK-E3-N0-NEURALFUSION-EIGHT-VIEW-001/code/common.py'))),['mesh_scene','cast'])
reuse(A1/'losses.py',['robust','ellipse_projection','signed_distance','field_sample','distance_field_sample','target_data','cad_visibility','two_d_parts'])
reuse(REPO/'experiments/TASK-E4-MULTIVIEW-INIT-STALK-015/code/prepare.py',['skeleton_proxy'])
def stats(a):
    a=np.asarray(a);a=a[np.isfinite(a)]
    return dict(N=len(a),MAE=float(abs(a).mean()) if len(a) else None,median=float(np.median(abs(a))) if len(a) else None,p95=float(np.quantile(abs(a),.95)) if len(a) else None,maximum=float(max(abs(a))) if len(a) else None)
@lru_cache(None)
def ringscene(group):
    a=np.load(ASSETS/'TASK-E4-BODY-ANCHORED-MULTIHERO-001/inputs'/group/'RING.npz')
    return mesh_scene(a['V'],a['F'])
@lru_cache(None)
def source(cid): return dict(np.load(R/'inputs'/(cid+'.npz')))
def guard(stage):
    def audit(event,args):
        if event in ['socket.connect','socket.getaddrinfo']: raise PermissionError('OFFLINE_SCIENCE')
        if event!='open' or not isinstance(args[0],(str,bytes)): return
        p=Path(os.fsdecode(args[0])).resolve();s=str(p);mode=args[1] if isinstance(args[1],str) else '';flags=args[2] if len(args)>2 and isinstance(args[2],int) else 0
        writing=any(c in mode for c in 'wax+') or flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)
        if writing and s.startswith('/home/liu/') and not p.is_relative_to(R): raise PermissionError('TASK_WRITES_ONLY:'+s)
        if not writing:
            if any(k in s.lower() for k in ['/private_gt/','/gt_mapping','/oracle/','/evaluation_only/']) or p.name.lower().startswith('gt_') or p.suffix=='.blend': raise PermissionError('NO_GT:'+s)
            if p.is_relative_to(DXY) and any(p.is_relative_to(DXY/k) for k in ['outputs','data','validation']): raise PermissionError('NO_HISTORICAL_DXY_PREDICTIONS:'+s)
            if stage in ['prepare','fit','dxy'] and ('Body-U.npz' in s or p.name=='FINAL.npz' and '/runs/' in s): raise PermissionError('NO_BODY_U_BEFORE_EVALUATION:'+s)
    sys.addaudithook(audit)
