"""Isolated IO and read-only reuse for unified RF BA."""
from pathlib import Path
import os,sys,json,hashlib,csv,time,ast,collections
N=Path(__file__).resolve().parents[1];REPO=N.parent.parent;P=REPO/'experiments/TASK-E4-RING-ANCHORED-JOINT-BA-021';G=P/'geometric_pose_optimization';OLD=Path('/home/liu/polyp_research/ring_anchor_3d');DXY=Path('/home/liu/new-polyp-dxy')
os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MPLCONFIGDIR=str(N/'runtime/mpl'),PYTHONDONTWRITEBYTECODE='1')
sys.dont_write_bytecode=True
sys.path[:0]=[str(N/'runtime/packages'),str(P/'code'),str(REPO/'experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runtime/packages'),'/home/liu/ring_first_3d_e4_sdf_evolution/experiments/E4-SDF-EVOLUTION-001/runtime/packages','/home/liu/ring_first_3d_e4_pmgr_r1/experiments/TASK-E4-PMGR-R1/runtime/packages',str(OLD/'experiments/surface_fusion_v3/vendor')]
import numpy as np,cv2
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation
cv2.setNumThreads(1)
GROUPS=['G01','G03','G05','G06'];METHODS=['B0','B1','B2','B3','B4']
def load(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def asset(p):p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
def clean(v):
 if isinstance(v,dict):return {str(k):clean(x)for k,x in v.items()}
 if isinstance(v,(list,tuple)):return [clean(x)for x in v]
 if isinstance(v,Path):return str(v)
 if hasattr(v,'tolist'):return clean(v.tolist())
 if isinstance(v,float)and not np.isfinite(v):return None
 return v

def save(p,v):
 p=N/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(clean(v),ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def table(p,rows):
 if not rows:return
 p=N/p;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('w',newline='')as f:
  w=csv.DictWriter(f,list(dict.fromkeys(k for r in rows for k in r)),lineterminator='\n');w.writeheader()
  for r in rows:w.writerow({k:json.dumps(clean(v),ensure_ascii=False)if isinstance(v,(list,tuple,dict,np.ndarray))else clean(v)for k,v in r.items()})
def stats(a):
 a=np.asarray(a,float);a=a[np.isfinite(a)];return dict(N=len(a),MAE=float(abs(a).mean())if len(a)else None,median=float(np.median(abs(a)))if len(a)else None,p95=float(np.quantile(abs(a),.95))if len(a)else None,maximum=float(abs(a).max())if len(a)else None)
def extract(path,names,ns):
 for node in ast.parse(Path(path).read_text()).body:
  if isinstance(node,ast.FunctionDef)and node.name in names:exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'),ns)
 return ns
ORIGINAL=OLD/'scripts/geometry.py';torus_original=extract(ORIGINAL,['torus_contours'],dict(np=np))['torus_contours']
def projection(X,C,K):
 q=(np.asarray(X)-C[:3,3])@C[:3,:3];uv=q@K.T;return uv[...,:2]/uv[...,2:],q[...,2]
def freeze(path,files,**kw):save(path,dict(epoch=time.time(),files=[asset(p)for p in files],**kw))
def checkfreeze(path):
 for a in load(N/path)['files']:assert sha(a['path'])==a['sha256'],a['path']
def fit_guard():
 def hook(event,args):
  if event!='open'or not isinstance(args[0],(str,bytes)):return
  p=Path(os.fsdecode(args[0])).resolve();mode=args[1]if isinstance(args[1],str)else'';flags=args[2]if isinstance(args[2],int)else 0;wr=any(k in mode for k in 'wax+')or flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)
  if wr and str(p).startswith('/home/liu/')and not p.is_relative_to(N):raise PermissionError('NEW_TASK_WRITES_ONLY '+str(p))
  if not wr and(p.suffix=='.blend'or p.name in ['BODY018.npz','OBS_TRUSTED.npz','TRUSTED_HERO.npz']or'/hero_fit/'in str(p)):raise PermissionError('NO_BODY_HERO_GT_IN_FIT '+str(p))
 sys.addaudithook(hook)
