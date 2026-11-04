"""E4 CPU-only source-bound geometry IO; no model weights, GT or old predictions."""
from pathlib import Path
from functools import lru_cache
import os,sys,json,csv,ast,hashlib,datetime,time
R=Path(__file__).resolve().parents[1];REPO=R.parents[1]
OLD=Path('/home/liu/polyp_research/ring_anchor_3d/experiments')
E1=Path('/home/liu/ring_first_3d_neural_e1/experiments/TASK-NEURAL-E1-PIPELINE-RECOVERY-001')
N0=Path('/home/liu/ring_first_3d_e3n0_eight/experiments/TASK-E3-N0-NEURALFUSION-EIGHT-VIEW-001')
MULTI=Path('/home/liu/ring_first_3d_e3_sdf_multi/experiments/TASK-E3-SDF-LOCAL-MULTIPOLYP-EXPLORATORY-001')
PART=Path('/home/liu/ring_first_3d_view_partition/experiments/TASK-VIEW-PARTITION-MAST3R-FUSION-001')
INC=Path('/home/liu/ring_first_3d_incremental/experiments/TASK-PHASED-INCREMENTAL-FUSION-MULTIGROUP-001')
VENDOR=OLD/'surface_fusion_v3/vendor';DXY=Path('/home/liu/new-polyp-dxy/src/dxy_mid/_engine')
for d in ['config','provenance','metrics','figures','inputs','local_results','runtime/tmp','runtime/mpl']:(R/d).mkdir(parents=True,exist_ok=True)
os.environ.update(CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='2',MPLCONFIGDIR=str(R/'runtime/mpl'),TMPDIR=str(R/'runtime/tmp'))
sys.dont_write_bytecode=True
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def clean(v):
    if isinstance(v,dict):return {str(k):clean(x)for k,x in v.items()}
    if isinstance(v,(list,tuple)):return [clean(x)for x in v]
    if hasattr(v,'tolist'):return clean(v.tolist())
    if isinstance(v,Path):return str(v)
    if isinstance(v,float)and not __import__('math').isfinite(v):return None
    return v
def save(p,v):
    p=R/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(clean(v),ensure_ascii=False,indent=2)+'\n')
def table(p,rr):
    p=R/p;p.parent.mkdir(parents=True,exist_ok=True)
    if not rr:p.write_text('');return
    keys=list(dict.fromkeys(k for row in rr for k in row))
    with p.open('w',newline='')as f:
        w=csv.DictWriter(f,keys,lineterminator='\n');w.writeheader()
        for row in rr:w.writerow({k:json.dumps(clean(v),ensure_ascii=False)if isinstance(v,(dict,list,tuple))else clean(v)for k,v in row.items()})
def asset(p):return dict(path=str(p),sha256=sha(p),bytes=Path(p).stat().st_size)
def extract(p,names,ns=None):
    ns=globals()if ns is None else ns;tree=ast.parse(Path(p).read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in names];assert {n.name for n in nodes}==set(names)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(p),'exec'),ns);return ns
CC={c['id']:c for c in load(E1/'provenance/INPUT_ELIGIBILITY.json')['references']}
GATE={c['source']:c for c in load(N0/'config/CAMERA_GATE_RESULTS.json')['sources']}
READS=set()
def guard(event,args):
    if event in ['socket.connect','socket.getaddrinfo']:raise PermissionError('E4_OFFLINE')
    if event=='import'and str(args[0]).split('.')[0]in ['torch','tensorflow','mast3r']:raise PermissionError('E4_NO_NEURAL_RUNTIME')
    if event!='open'or not isinstance(args[0],(str,bytes)):return
    p=Path(os.fsdecode(args[0])).resolve();s=str(p);mode=args[1]if isinstance(args[1],str)else '';flags=args[2]if len(args)>2 and isinstance(args[2],int)else 0
    writing=any(x in mode for x in 'wax+')or flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)
    if writing and s.startswith('/home/liu/')and not p.is_relative_to(R):raise PermissionError('E4_TASK_WRITES_ONLY:'+s)
    if not p.is_relative_to(R):
        if p.suffix in ['.blend','.pt','.pth','.ckpt','.safetensors']or p.name.lower().startswith('gt_')or any(k in s.lower()for k in ['/private_gt/','/oracle/','/evaluation_only/','/gt_mapping/','/local_results/scenes/','/pointcloud_blocks/','/checkpoints/']):raise PermissionError('E4_NO_GT_WEIGHTS_FUSED_OUTPUT:'+s)
        if '/new-polyp-dxy/'in s and p.suffix!='.py':raise PermissionError('E4_DXY_CODE_ONLY_NO_OLD_MEASUREMENTS:'+s)
        if s.startswith('/home/liu/')and not writing:READS.add(s)
sys.addaudithook(guard)
import numpy as np,cv2,trimesh
from PIL import Image
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation
sys.path.insert(0,str(VENDOR));import open3d as o3d
sys.path.insert(0,str(REPO));from visualization import real_p0_renderer as vis
extract(N0/'code/common.py',['source','native','original','ringmesh','mesh_scene','ringscene','cast'])
extract(OLD/'ring_first_v1/scripts/common.py',['unproject'])
extract(DXY/'v2.py',['disk','contour'])
cv2.setNumThreads(2)
def select(ii,n):return ii[np.linspace(0,len(ii)-1,min(n,len(ii)),dtype=int)]if len(ii)else ii
def stats(x):
    x=np.asarray(x,float);x=x[np.isfinite(x)]
    return dict(N=len(x),median=float(np.median(x))if len(x)else None,median_abs=float(np.median(abs(x)))if len(x)else None,MAE=float(abs(x).mean())if len(x)else None,p95=float(np.quantile(abs(x),.95))if len(x)else None,maximum=float(abs(x).max())if len(x)else None)
def protocol():return load(R/'config/PREREGISTERED.json')
@lru_cache(None)
def cleaned(cid):
    n=native(cid);paths=[N0/'frozen_inputs/native'/(cid+'.npz'),MULTI/'frozen_inputs/native'/(cid+'.npz')];p=next((p for p in paths if p.exists()),None)
    if p is None:return dict(n,cleanup_state='RAW_NO_QUALIFIED_CLEANED_BRANCH',cleanup_path=None)
    z=np.load(p);valid=z['valid'];depth=z['depth_mm'];assert not(valid&~n['valid']).any()and np.array_equal(depth[valid],n['depth'][valid])
    return dict(n,valid=valid,depth=depth,cleanup_state='FROZEN_DERIVED_REUSED',cleanup_path=str(p))
def head_cue(labels,kind):
    mask=labels==1
    if kind!='Ip':return mask.copy(),dict(method='original Polyp mask',manual_head_truth=False)
    # Original DXY disk/contour functions; an E4 frozen soft cue, not a DXY measurement.
    dt=cv2.distanceTransform(mask.astype(np.uint8),cv2.DIST_L2,cv2.DIST_MASK_PRECISE);radius=max(1,int(round(.35*dt.max())))
    opened=cv2.morphologyEx(mask.astype(np.uint8),cv2.MORPH_OPEN,disk(radius));n,comp,st,cent=cv2.connectedComponentsWithStats(opened,8)
    seed=np.unravel_index(np.argmax(dt),dt.shape);lab=comp[seed]
    if lab==0 and n>1:lab=1+int(np.argmax(st[1:,cv2.CC_STAT_AREA]))
    cue=(comp==lab)&mask if lab>0 else np.zeros_like(mask)
    return cue,dict(method='Ip max-thickness component after fixed opening .35*Mask_DTmax; DXY disk/contour reused',radius_px=radius,full_mask_N=int(mask.sum()),head_N=int(cue.sum()),manual_head_truth=False,status='HEAD_CUE_UNCERTAIN')
@lru_cache(None)
def observation(cid):
    return dict(np.load(R/'inputs'/(cid+'.npz')))
def camera_frame(z,x):
    z=np.array(z,float);z/=np.linalg.norm(z);x=np.array(x,float)-np.dot(x,z)*z;x/=np.linalg.norm(x);return np.c_[x,np.cross(z,x),z]
