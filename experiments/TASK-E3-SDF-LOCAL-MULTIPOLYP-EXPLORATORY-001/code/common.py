"""One algorithm, independent scene assets/models; historical inputs read-only."""
from pathlib import Path
from functools import lru_cache
import os,sys,ast,json,csv,hashlib,datetime,time,subprocess
TASK=Path(__file__).resolve().parents[1];REPO=TASK.parents[1]
SCENE=os.environ.get('MONOSDF_SCENE','G01_004')
ORDERS={'G01_004':['G01_004_ref08','G01_004_ref13','G01_004_ref03'],
        'G06_004':['G06_004_ref04','G06_004_growth_r01','G06_004_growth_r06'],
        'G08_005':['G08_005_ref04','G08_005_growth_r02','G08_005_growth_r01']}
assert SCENE in ORDERS;SOURCES=ORDERS[SCENE];R=TASK/'groups'/SCENE
N0=TASK
HISTORY_N0=Path('/home/liu/ring_first_3d_e3n0_eight/experiments/TASK-E3-N0-NEURALFUSION-EIGHT-VIEW-001')
PREV=Path('/home/liu/ring_first_3d_e3_sdf_full/experiments/TASK-E3-SDF-MONOSDF-FULL-TRAINING-REVALIDATION-001')
E0=Path('/home/liu/ring_first_3d_neural_e0/experiments/TASK-NEURAL-E0-COMPARE-001')
E1=Path('/home/liu/ring_first_3d_neural_e1/experiments/TASK-NEURAL-E1-PIPELINE-RECOVERY-001')
GA=Path('/home/liu/ring_first_3d_e3n0/experiments/TASK-E3-N0-GATE-A-COMPAT-CROP-METRIC-001')
A2=Path('/home/liu/ring_first_3d_e3n0_a2/experiments/TASK-E3-N0-GATE-A2-PROJECTIVE-CLEANUP-001')
A3=Path('/home/liu/ring_first_3d_e3n0_a3/experiments/TASK-E3-N0-GATE-A3-MASK-BOUNDARY-CLEANUP-001')
PART=Path('/home/liu/ring_first_3d_view_partition/experiments/TASK-VIEW-PARTITION-MAST3R-FUSION-001')
ORIGINAL_SDF=E0/'runtime/monosdf_official'
VENDOR=Path('/home/liu/polyp_research/ring_anchor_3d/experiments/surface_fusion_v3/vendor')
for p in ['runtime/tmp','runtime/cache','runtime/mpl','config','metrics','provenance','figures','local_results','checkpoints']:(R/p).mkdir(parents=True,exist_ok=True)
os.environ.update(PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='2',
 MPLCONFIGDIR=str(R/'runtime/mpl'),TMPDIR=str(R/'runtime/tmp'),XDG_CACHE_HOME=str(R/'runtime/cache'),TORCH_HOME=str(R/'runtime/cache/torch'),CUDA_CACHE_PATH=str(R/'runtime/cache/cuda'))
sys.dont_write_bytecode=True
def extract(path,names,ns=None):
    ns=globals()if ns is None else ns;t=ast.parse(Path(path).read_text());nodes=[n for n in t.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))and n.name in names];assert len(nodes)==len(names),(path,names)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),ns)
extract(HISTORY_N0/'code/common.py',['sha','load','clean','save','table','rows','asset','stats'])
ALL_IDS=sum(ORDERS.values(),[])
CC={a['id']:a for a in load(E1/'provenance/INPUT_ELIGIBILITY.json')['references']if a['id']in ALL_IDS}
ALLOWED={str(Path(c[k]).resolve())for c in CC.values()for k in ['pack','source_points','mesh','camera_file']}
ALLOWED.update(str(Path(c['E1_actual_native']['path']).resolve())for c in CC.values())
ALLOWED.update(str(Path(c['Ring_CAD']['path']).resolve())for c in CC.values())
ALLOWED.update(str((HISTORY_N0/'frozen_inputs'/d/(cid+'.npz')).resolve())for d in ['native','crops']for cid in ALL_IDS)
ALLOWED.update(str((PREV/'frozen_inputs'/(cid+'.npz')).resolve())for cid in ORDERS['G01_004'])
ACCESSED=set();DENIALS=[]
def guard(event,args):
    if event in ['socket.connect','socket.getaddrinfo']:raise PermissionError('OFFLINE_COMPUTATION')
    if event!='open'or not isinstance(args[0],(str,bytes)):return
    p=Path(os.fsdecode(args[0])).resolve();s=str(p);mode=args[1]if len(args)>1 and isinstance(args[1],str)else'';flags=args[2]if len(args)>2 and isinstance(args[2],int)else 0
    writing=any(v in mode for v in 'wax+')or flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)
    if writing and s.startswith('/home/liu/')and not p.is_relative_to(TASK):raise PermissionError('TASK_LOCAL_WRITE_ONLY:'+s)
    if not p.is_relative_to(TASK):
        if p.suffix=='.blend'or p.name.lower().startswith('gt_')or any(k in s.lower()for k in ['/private_gt/','/oracle/','/evaluation_only/','/new-polyp-dxy/']):raise PermissionError('NO_GT_ORACLE_DXY:'+s)
        if s.startswith('/home/liu/')and p.suffix in ['.npz','.npy','.ply','.obj','.glb','.pt','.pth','.ckpt','.safetensors']and s not in ALLOWED:DENIALS.append(s);raise PermissionError('NOT_SOURCE_ALLOWLISTED:'+s)
        if not writing and s.startswith('/home/liu/'):ACCESSED.add(s)
sys.addaudithook(guard)
import numpy as np,cv2,trimesh
from PIL import Image
from scipy.spatial import cKDTree
sys.path.insert(0,str(VENDOR));import open3d as o3d
sys.path.insert(0,str(REPO));from visualization import real_p0_renderer as vis
extract(HISTORY_N0/'code/common.py',['source','native','original','ringmesh','mesh_scene','ringscene','cast','distance','affine_uv'])
extract(Path('/home/liu/polyp_research/ring_anchor_3d/experiments/ring_first_v1/scripts/common.py'),['unproject'])
def protocol():return load(R/'config/PREREGISTERED.json')
@lru_cache(None)
def frozen(cid):return dict(np.load(R/'frozen_inputs'/(cid+'.npz')))
def config():return load(GA/'config/GATE_A_PREREGISTERED.json')
extract(GA/'code/crop.py',['make_crop'])
extract(HISTORY_N0/'code/common.py',['cleaned','block'])
# Inherited cleaned() refers to R; baseline native files are shared at TASK, not per-group.
def cleaned(cid):
    n=native(cid);p=np.load(TASK/'frozen_inputs/native'/(cid+'.npz'));valid=p['valid'];depth=p['depth_mm'];v,u=np.nonzero(valid);uv=np.c_[u,v]
    assert not(valid&~n['valid']).any()and np.array_equal(depth[valid],n['depth'][valid])and(depth[~valid]==0).all()
    return dict(n,depth=depth,valid=valid,native_uv=uv,native_id=v*depth.shape[1]+u,X=unproject(depth[v,u].astype(float),n['T'],uv,n['Kn']))
