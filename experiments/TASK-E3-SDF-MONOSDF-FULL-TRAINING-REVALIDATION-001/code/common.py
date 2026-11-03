"""Three frozen G01_004 sources only; no historical prediction as training input."""
from pathlib import Path
from functools import lru_cache
import os,sys,json,csv,ast,hashlib,datetime,time,subprocess
R=Path(__file__).resolve().parents[1];REPO=R.parents[1]
N0=Path('/home/liu/ring_first_3d_e3n0_eight/experiments/TASK-E3-N0-NEURALFUSION-EIGHT-VIEW-001')
E0=Path('/home/liu/ring_first_3d_neural_e0/experiments/TASK-NEURAL-E0-COMPARE-001')
E1=Path('/home/liu/ring_first_3d_neural_e1/experiments/TASK-NEURAL-E1-PIPELINE-RECOVERY-001')
ORIGINAL_SDF=E0/'runtime/monosdf_official'
VENDOR=Path('/home/liu/polyp_research/ring_anchor_3d/experiments/surface_fusion_v3/vendor')
SOURCES=['G01_004_ref08','G01_004_ref13','G01_004_ref03'];SCENE='G01_004'
for folder in ['runtime/tmp','runtime/cache','runtime/mpl','config','provenance','metrics','figures','local_results','checkpoints']:(R/folder).mkdir(parents=True,exist_ok=True)
os.environ.update(PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='2',MPLCONFIGDIR=str(R/'runtime/mpl'),TMPDIR=str(R/'runtime/tmp'),XDG_CACHE_HOME=str(R/'runtime/cache'),TORCH_HOME=str(R/'runtime/cache/torch'),CUDA_CACHE_PATH=str(R/'runtime/cache/cuda'))
sys.dont_write_bytecode=True
def extract(path,names,ns=None):
    ns=globals()if ns is None else ns;t=ast.parse(Path(path).read_text());nodes=[n for n in t.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))and n.name in names];assert len(nodes)==len(names)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),ns)
extract(N0/'code/common.py',['sha','load','clean','save','table','rows','asset','stats'])
CC={a['id']:a for a in load(E1/'provenance/INPUT_ELIGIBILITY.json')['references']if a['id']in SOURCES}
ALLOWED={str(Path(c[k]).resolve())for c in CC.values()for k in ['pack','source_points','mesh','camera_file']}
ALLOWED.update(str(Path(c['E1_actual_native']['path']).resolve())for c in CC.values());ALLOWED.update(str(Path(c['Ring_CAD']['path']).resolve())for c in CC.values())
ALLOWED.update(str((N0/'frozen_inputs'/folder/(cid+'.npz')).resolve())for folder in ['native','crops']for cid in SOURCES)
ACCESSED=set();DENIALS=[]
def guard(event,args):
    if event in ['socket.connect','socket.getaddrinfo']:raise PermissionError('OFFLINE_COMPUTATION')
    if event!='open'or not isinstance(args[0],(str,bytes)):return
    p=Path(os.fsdecode(args[0])).resolve();s=str(p);mode=args[1]if len(args)>1 and isinstance(args[1],str)else'';flags=args[2]if len(args)>2 and isinstance(args[2],int)else 0
    writing=any(v in mode for v in 'wax+')or flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)
    if writing and s.startswith('/home/liu/')and not p.is_relative_to(R):raise PermissionError('TASK_LOCAL_WRITE_ONLY:'+s)
    if not p.is_relative_to(R):
        if p.suffix=='.blend'or p.name.lower().startswith('gt_')or any(k in s.lower()for k in ['/private_gt/','/oracle/','/evaluation_only/','/new-polyp-dxy/']):raise PermissionError('NO_GT_ORACLE_DXY:'+s)
        if s.startswith('/home/liu/')and p.suffix in ['.npz','.npy','.ply','.obj','.glb','.pt','.pth','.ckpt','.safetensors']and s not in ALLOWED:DENIALS.append(s);raise PermissionError('SOURCE_NOT_ALLOWLISTED:'+s)
        if not writing and s.startswith('/home/liu/'):ACCESSED.add(s)
sys.addaudithook(guard)
import numpy as np,cv2,trimesh
from PIL import Image
from scipy.spatial import cKDTree
sys.path.insert(0,str(VENDOR));import open3d as o3d
sys.path.insert(0,str(REPO));from visualization import real_p0_renderer as vis
extract(N0/'code/common.py',['source','native','original','ringmesh','mesh_scene','ringscene','cast','distance','affine_uv'])
extract(Path('/home/liu/polyp_research/ring_anchor_3d/experiments/ring_first_v1/scripts/common.py'),['unproject'])
def protocol():return load(R/'config/PREREGISTERED.json')
@lru_cache(None)
def frozen(cid):return dict(np.load(R/'frozen_inputs'/(cid+'.npz')))
