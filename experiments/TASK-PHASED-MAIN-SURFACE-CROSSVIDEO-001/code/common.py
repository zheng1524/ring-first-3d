"""Read-only frozen assets; own task outputs only. No upstream or GT execution."""
import os,sys,json,csv,ast,hashlib,datetime
from pathlib import Path
R=Path(__file__).resolve().parents[1];REPO=R.parents[1]
PREV=Path('/home/liu/ring_first_3d/experiments/TASK-PHASEC-DENSITY-MULTIGROUP-001')
SPARSE=PREV.parent/'TASK-PHASEC-SPARSE-STRETCH-CLEAN-VIS-001'
OLD=Path('/home/liu/polyp_research/ring_anchor_3d/experiments');ICF=OLD/'independent_confidence_fusion_v1'
os.environ.setdefault('MPLCONFIGDIR',str(R/'runtime/mpl'));sys.path.insert(0,str(REPO))
import numpy as np,cv2,trimesh
from PIL import Image
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree
from visualization import real_p0_renderer as vis
from visualization import pointcloud_audit_renderer as diag
from visualization.same_camera_scene import SameCameraScene
def guard(event,args):
    if event!='open'or not isinstance(args[0],(str,bytes)):return
    p=Path(os.fsdecode(args[0])).resolve();s=str(p);n=p.name.lower()
    if n.endswith('.blend')or n.startswith('gt_')or'oracle'in n or any(x in s for x in ['/gt_mapping/','/private_gt/','/evaluation_exports/']):raise PermissionError('GT excluded '+s)
    flags=args[2]if len(args)>2 and isinstance(args[2],int)else 0;mode=args[1]if len(args)>1 and isinstance(args[1],str)else''
    if(any(x in mode for x in 'wax+')or flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC))and s.startswith('/home/liu/')and not p.is_relative_to(R):raise PermissionError('Task outputs only '+s)
sys.addaudithook(guard)
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb')as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b)
    return h.hexdigest()
def load(p):return json.loads(Path(p).read_text())
def clean(x):
    if isinstance(x,dict):return{str(k):clean(v)for k,v in x.items()}
    if isinstance(x,(list,tuple)):return[clean(v)for v in x]
    if isinstance(x,np.ndarray):return clean(x.tolist())
    if isinstance(x,(np.integer,np.bool_)):return x.item()
    if isinstance(x,(float,np.floating)):return float(x)if np.isfinite(x)else None
    return x
def save(p,x):
    p=R/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(clean(x),ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def csvsave(p,rows):
    p=R/p;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',newline='')as f:
        w=csv.DictWriter(f,list(dict.fromkeys(k for r in rows for k in r)),lineterminator='\n');w.writeheader()
        for row in rows:w.writerow({k:json.dumps(clean(v),ensure_ascii=False)if isinstance(v,(dict,list,tuple,np.ndarray))else clean(v)for k,v in row.items()})
def stats(v):
    v=np.asarray(v,float);n=len(v);v=v[np.isfinite(v)]
    return dict(n=n,finite=len(v),median=np.median(v)if len(v)else None,MAE=np.mean(abs(v))if len(v)else None,p05=np.quantile(v,.05)if len(v)else None,p95=np.quantile(v,.95)if len(v)else None,max=v.max()if len(v)else None)
def cases():return load(PREV/'provenance/CASES.json')[:6]
def data(c):
    a=dict(np.load(PREV/f'local_fields/{c["id"]}_fields.npz'));p=dict(np.load(c['pack']));rgb=np.asarray(Image.open(c['RGB']).convert('RGB'));m=trimesh.load(c['mesh'],process=False);P=a['XYZ_mm'];uv=np.c_[a['source_u'],a['source_v']]
    assert np.allclose(m.vertices,P,atol=1e-5,rtol=0)and len(m.vertices)==len(P)
    return a,p,rgb[uv[:,1],uv[:,0]]/255.,m
def ring_path(c):return OLD/'surface_fusion_v2/inputs/R10_ring.obj'if c['ring']=='R10'else Path('/home/liu/polyp_research/ring_anchor_3d/assets/ring_R5.obj')
def ring(c):return trimesh.load(ring_path(c),process=False)
def unproject(uv,z,K,pose):return(np.c_[uv,np.ones(len(uv))]@np.linalg.inv(K).T*z[:,None])@pose[:3,:3].T+pose[:3,3]
def extract(path,names):
    nodes=[n for n in ast.parse(Path(path).read_text()).body if isinstance(n,ast.FunctionDef)and n.name in names];assert len(nodes)==len(names)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),globals())
extract(SPARSE/'code/run.py',['source_components','face_components','edge_counts','interior_deletion_patches'])
def cohorts(a,p):
    uv=np.c_[a['source_u'],a['source_v']];_lab,comp,head=source_components(p,uv);minor=comp!=head;cut=np.quantile(uv[minor,1],.8)if minor.any()else np.inf
    return dict(head_source_proxy=comp==head,possible_stalk_proxy=minor&(uv[:,1]>=cut),Ring_near=a['Ring_near'],Mask_boundary=a['boundary'])
def stamp(files):return dict(UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=[dict(path=str(p),sha256=sha(p),bytes=Path(p).stat().st_size)for p in sorted(set(map(Path,files)))],GT_used=False)
def verify():
    for x in load(R/'provenance/INPUTS.json')['files']:assert sha(x['path'])==x['sha256'],x['path']
