from pathlib import Path
import os, sys, json, csv, hashlib, time, ast
R=Path(__file__).resolve().parents[1]; REPO=R.parents[1]
LEG=Path('/home/liu/polyp_research/ring_anchor_3d/experiments')
RUN009=REPO/'experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/BODY_BASE_INIT_009'
PHC=Path('/home/liu/ring_first_3d/experiments')
os.environ.update(CUDA_VISIBLE_DEVICES='',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='2',MPLCONFIGDIR=str(R/'runtime/mpl'),PYTHONDONTWRITEBYTECODE='1')
sys.dont_write_bytecode=True
sys.path.insert(0,str(LEG/'surface_fusion_v3/vendor'))
import numpy as np, cv2, trimesh
from PIL import Image
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
import open3d as o3d
cv2.setNumThreads(2)
def firewall(event,args):
    if event!='open' or not isinstance(args[0],(str,bytes)):return
    p=Path(os.fsdecode(args[0])).resolve();s=str(p);low=s.lower()
    flags=args[2] if len(args)>2 and isinstance(args[2],int) else 0
    mode=args[1] if len(args)>1 and isinstance(args[1],str) else ''
    writing=any(x in mode for x in 'wax+') or flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)
    if writing and s.startswith('/home/liu/') and not p.is_relative_to(R):raise PermissionError('017_TASK_LOCAL_WRITES_ONLY '+s)
    if not writing and any(t in low for t in ['/gt_mapping/','/evaluation_only/','/audit_only/','oracle','.blend','native_cad_gt','/private_gt/']):raise PermissionError('017_NO_GT '+s)
sys.addaudithook(firewall)
def load(p):return json.loads(Path(p).read_text())
def clean(x):
    if isinstance(x,dict):return {str(k):clean(v)for k,v in x.items()}
    if isinstance(x,(list,tuple)):return [clean(v)for v in x]
    if isinstance(x,np.ndarray):return clean(x.tolist())
    if isinstance(x,(np.integer,np.bool_)):return x.item()
    if isinstance(x,(float,np.floating)):return float(x) if np.isfinite(x) else None
    if isinstance(x,Path):return str(x)
    return x
def save(p,x):
    p=R/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(clean(x),ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def table(p,rows):
    p=R/p;p.parent.mkdir(parents=True,exist_ok=True)
    if not rows:return
    with p.open('w',newline='')as f:
        w=csv.DictWriter(f,list(dict.fromkeys(k for r in rows for k in r)),lineterminator='\n');w.writeheader()
        for r in rows:w.writerow({k:json.dumps(clean(v),ensure_ascii=False)if isinstance(v,(dict,list,tuple,np.ndarray))else clean(v)for k,v in r.items()})
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb')as f:
        for x in iter(lambda:f.read(2**20),b''):h.update(x)
    return h.hexdigest()
def asset(p):return dict(path=str(Path(p).resolve()),bytes=Path(p).stat().st_size,sha256=sha(p))
def stats(x):
    x=np.asarray(x,float);x=x[np.isfinite(x)]
    return dict(N=len(x),mean=float(x.mean())if len(x)else None,median=float(np.median(x))if len(x)else None,p95=float(np.quantile(x,.95))if len(x)else None,maximum=float(x.max())if len(x)else None)
def extract(path,names):
    nodes=[x for x in ast.parse(Path(path).read_text()).body if isinstance(x,ast.FunctionDef)and x.name in names]
    assert len(nodes)==len(names);exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),globals())
extract(LEG/'ring_first_v1/scripts/common.py',['unproject'])
extract(PHC/'TASK-PHASEC-SPARSE-STRETCH-CLEAN-VIS-001/code/run.py',['face_components','edge_counts'])
def cfg():return load(R/'config/PROTOCOL.json')['inherited_density']
extract(PHC/'TASK-PHASEC-DENSITY-MULTIGROUP-001/code/density.py',['features'])
def scene(V,F):
    s=o3d.t.geometry.RaycastingScene(nthreads=2);s.add_triangles(o3d.core.Tensor(np.asarray(V,np.float32)),o3d.core.Tensor(np.asarray(F,np.uint32)));return s
def cast(s,uv,K,T):
    ray=np.c_[uv,np.ones(len(uv))]@np.linalg.inv(K).T
    return s.cast_rays(o3d.core.Tensor(np.c_[np.broadcast_to(T[:3,3],ray.shape),ray@T[:3,:3].T].astype(np.float32)))
def native_grid(z,lab,K,T):
    valid=np.isfinite(z)&(z>0)&(lab==1);y,x=np.nonzero(valid);uv=np.c_[x,y];P=unproject(z[y,x],T,uv,K)
    ids=np.full(z.shape,-1,int);ids[y,x]=np.arange(len(x));a=ids[:-1,:-1];b=ids[:-1,1:];c=ids[1:,:-1];d=ids[1:,1:]
    fs=[];lattice=[];q=np.arange((z.shape[0]-1)*(z.shape[1]-1)).reshape(a.shape)
    for side,t in enumerate([np.stack([a,b,c],-1),np.stack([b,d,c],-1)]):
        good=(t>=0).all(-1);fs.append(t[good]);lattice.append(2*q[good]+side)
    return P,np.concatenate(fs),uv,np.concatenate(lattice)
