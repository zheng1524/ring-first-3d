"""Frozen source IO and universal CPU-only geometry; writes isolated to this task."""
from pathlib import Path
from functools import lru_cache
import os,sys,ast,json,csv,hashlib,time,datetime
R=Path(__file__).resolve().parents[1];REPO=R.parents[1]
OLD=Path('/home/liu/polyp_research/ring_anchor_3d/experiments')
E1ROOT=Path('/home/liu/ring_first_3d_neural_e1/experiments/TASK-NEURAL-E1-PIPELINE-RECOVERY-001')
N0=Path('/home/liu/ring_first_3d_e3n0_eight/experiments/TASK-E3-N0-NEURALFUSION-EIGHT-VIEW-001')
MULTI=Path('/home/liu/ring_first_3d_e3_sdf_multi/experiments/TASK-E3-SDF-LOCAL-MULTIPOLYP-EXPLORATORY-001')
PREV=Path('/home/liu/ring_first_3d_e4_a1/experiments/TASK-E4-A1-COARSE-BODY-001')
DXY=Path('/home/liu/new-polyp-dxy');VENDOR=OLD/'surface_fusion_v3/vendor'
for folder in ['runtime/tmp','runtime/mpl','inputs','local_results','metrics','provenance','figures','config']:(R/folder).mkdir(parents=True,exist_ok=True)
os.environ.update(CUDA_VISIBLE_DEVICES='',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1',MPLCONFIGDIR=str(R/'runtime/mpl'),TMPDIR=str(R/'runtime/tmp'))
sys.dont_write_bytecode=True
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def clean(x):
    if isinstance(x,dict):return {str(k):clean(v)for k,v in x.items()}
    if isinstance(x,(list,tuple)):return [clean(v)for v in x]
    if hasattr(x,'tolist'):return clean(x.tolist())
    if isinstance(x,Path):return str(x)
    if isinstance(x,float)and not __import__('math').isfinite(x):return None
    return x
def save(name,x):
    p=R/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(clean(x),ensure_ascii=False,indent=2)+'\n')
def table(name,rows):
    keys=list(dict.fromkeys(k for row in rows for k in row));p=R/name
    with p.open('w',newline='')as f:
        w=csv.DictWriter(f,keys,lineterminator='\n');w.writeheader()
        for row in rows:w.writerow({k:json.dumps(clean(v),ensure_ascii=False)if isinstance(v,(dict,list,tuple))else clean(v)for k,v in row.items()})
def asset(p):return dict(path=str(p),sha256=sha(p),bytes=Path(p).stat().st_size)
def extract(p,names):
    nodes=[n for n in ast.parse(Path(p).read_text()).body if isinstance(n,ast.FunctionDef)and n.name in names];assert {n.name for n in nodes}==set(names)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(p),'exec'),globals())
CC={x['id']:x for x in load(E1ROOT/'provenance/INPUT_ELIGIBILITY.json')['references']}
GATE={x['source']:x for x in load(N0/'config/CAMERA_GATE_RESULTS.json')['sources']}
READS=set()
def guard(event,args):
    if event in ['socket.connect','socket.getaddrinfo']:raise PermissionError('OFFLINE_SCIENCE')
    if event=='import'and str(args[0]).split('.')[0]in ['torch','tensorflow','mast3r']:raise PermissionError('NO_NEURAL_RUNTIME')
    if event!='open'or not isinstance(args[0],(str,bytes)):return
    p=Path(os.fsdecode(args[0])).resolve();s=str(p);mode=args[1]if isinstance(args[1],str)else'';flags=args[2]if len(args)>2 and isinstance(args[2],int)else 0
    writing=any(c in mode for c in 'wax+')or flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)
    if writing and s.startswith('/home/liu/')and not p.is_relative_to(R):raise PermissionError('TASK_WRITES_ONLY:'+s)
    if not p.is_relative_to(R):
        if p.suffix in ['.blend','.pt','.pth','.ckpt','.safetensors']or p.name.lower().startswith('gt_')or any(k in s.lower()for k in ['/private_gt/','/gt_mapping','/oracle/','/pointcloud_blocks/','/checkpoints/','/evaluation_only/','/local_results/scenes/']):raise PermissionError('NO_GT_WEIGHTS_FUSED_OUTPUT:'+s)
        if p.is_relative_to(DXY)and p.suffix not in ['.py','.toml','.json']and p.name!='AGENTS.md':raise PermissionError('DXY_CODE_ONLY_NO_OLD_PREDICTIONS:'+s)
        if s.startswith('/home/liu/')and not writing:READS.add(s)
sys.addaudithook(guard)
import numpy as np,cv2,trimesh
from PIL import Image
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation
from scipy.special import expit
sys.path.insert(0,str(VENDOR));import open3d as o3d
sys.path.insert(0,str(REPO));from visualization import real_p0_renderer as vis
extract(N0/'code/common.py',['source','native','original','ringmesh','mesh_scene','ringscene','cast'])
extract(OLD/'ring_first_v1/scripts/common.py',['unproject'])
extract(PREV/'code/models.py',['sphere_mesh','quadratic_interval'])
extract(PREV/'code/common.py',['camera_frame','stats'])
cv2.setNumThreads(2)
def contour(mask):
    contours,_=cv2.findContours(mask.astype(np.uint8),cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE)
    return np.concatenate([c[:,0,:]for c in contours]).astype(float)if contours else np.empty((0,2),float)
def protocol():return load(R/'config/PROTOCOL.json')
@lru_cache(None)
def obs(cid):return dict(np.load(R/'inputs'/(cid+'.npz')))
@lru_cache(None)
def cleaned(cid):
    n=native(cid);path=next((p for p in [N0/'frozen_inputs/native'/(cid+'.npz'),MULTI/'frozen_inputs/native'/(cid+'.npz')]if p.exists()),None)
    if path is None:return dict(n,cleanup_state='RAW_NO_QUALIFIED_CURRENT_CLEANUP',cleanup_path=None)
    a=np.load(path);assert not(a['valid']&~n['valid']).any()and np.array_equal(a['depth_mm'][a['valid']],n['depth'][a['valid']])
    return dict(n,depth=a['depth_mm'],valid=a['valid'],cleanup_state='EXACT_FROZEN_NATIVE_VALIDITY',cleanup_path=str(path))
def decode(p,R0):return p[:3],R0@Rotation.from_rotvec(p[3:6]).as_matrix(),np.exp(p[6:9])
def mesh(p,R0,high=True):
    c,Q,a=decode(p,R0);P,F=sphere_mesh(96 if high else 32,48 if high else 16);return(P*a)@Q.T+c,F
def ray_components(p,R0,rays):
    c,Q,a=decode(p,R0);o=(rays[:,:3]-c)@Q/a;d=rays[:,3:]@Q/a
    A=(d*d).sum(1);B=(o*d).sum(1);C=(o*o).sum(1)-1;disc=B*B-A*C;return A,B,C,disc
def first_depth(p,R0,rays):
    A,B,C,disc=ray_components(p,R0,rays);root=np.sqrt(np.maximum(disc,0));near=(-B-root)/A;far=(-B+root)/A
    return np.where((disc>=0)&(far>0),np.where(near>0,near,far),np.inf)
