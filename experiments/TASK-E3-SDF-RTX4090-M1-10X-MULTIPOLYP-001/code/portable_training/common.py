"""Relocated IO; immutable numeric assets and historical coordinate functions."""
from pathlib import Path
from functools import lru_cache
import os,sys,ast,json,csv,hashlib,datetime,time,subprocess,types
TASK=Path(__file__).resolve().parents[1];REPO=TASK
PLAN=json.loads((TASK/'config/MIGRATION_PLAN.json').read_text());ORDERS=PLAN['orders']
SCENE=os.environ.get('MONOSDF_SCENE','G01_004');assert SCENE in ORDERS
SOURCES=ORDERS[SCENE];ALL_IDS=sum(ORDERS.values(),[]);R=TASK/'groups'/SCENE;N0=TASK
E0=TASK/'vendor';HISTORY_N0=TASK/'vendor/history';VENDOR=TASK/'vendor'
for folder in ['runtime/tmp','runtime/cache','runtime/mpl','metrics','provenance','local_results','checkpoints','figures']:(R/folder).mkdir(parents=True,exist_ok=True)
os.environ.update(PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='2',
    MPLCONFIGDIR=str(R/'runtime/mpl'),TMPDIR=str(R/'runtime/tmp'),XDG_CACHE_HOME=str(R/'runtime/cache'),
    TORCH_HOME=str(R/'runtime/cache/torch'),CUDA_CACHE_PATH=str(R/'runtime/cache/cuda'))
sys.dont_write_bytecode=True
def extract(path,names,ns=None):
    ns=globals()if ns is None else ns;tree=ast.parse(Path(path).read_text());nodes=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))and n.name in names]
    assert {n.name for n in nodes}==set(names)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),ns)
ACCESSED=set();DENIALS=[]
def guard(event,args):
    if event in ['socket.connect','socket.getaddrinfo']:raise PermissionError('OFFLINE_TRAINING_NO_NETWORK')
    if event!='open'or not isinstance(args[0],(str,bytes)):return
    p=Path(os.fsdecode(args[0])).resolve();s=str(p);mode=args[1]if len(args)>1 and isinstance(args[1],str)else'';flags=args[2]if len(args)>2 and isinstance(args[2],int)else 0
    write=any(v in mode for v in 'wax+')or flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)
    if p.name.lower().startswith('gt_')or p.suffix=='.blend'or any(k in s.lower()for k in ['/private_gt/','/oracle/','/evaluation_only/','/new-polyp-dxy/']):raise PermissionError('NO_GT_ORACLE_DXY:'+s)
    if write and s.startswith(('/root/','/home/'))and not p.is_relative_to(TASK):raise PermissionError('EXPERIMENT_LOCAL_WRITE_ONLY:'+s)
    if p.is_relative_to(TASK):ACCESSED.add(s)
sys.addaudithook(guard)
import numpy as np,cv2,trimesh,open3d as o3d
from PIL import Image
from scipy.spatial import cKDTree
helper=TASK/'code/historical_helpers.py'
exec(compile(helper.read_text(),str(helper),'exec'),globals())
vis=types.SimpleNamespace(scaled_intrinsics=scaled_intrinsics,project_camera=project_camera,camera_rays=camera_rays)
CC=load(TASK/'data/REFERENCES.json')
for c in CC.values():
    for k in ['RGB','Mask','pack','source_points','mesh','camera_file']:c[k]=str(TASK/c[k])
    c['E1_actual_native']['path']=str(TASK/c['E1_actual_native']['path'])
    c['Ring_CAD']['path']=str(TASK/c['Ring_CAD']['path'])
def protocol():return load(R/'config/PREREGISTERED.json')
@lru_cache(None)
def frozen(cid):return dict(np.load(R/'frozen_inputs'/(cid+'.npz')))
def block(cid):return CC[cid]['frozen_block']
