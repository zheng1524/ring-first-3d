from pathlib import Path
import os,sys,json,csv,hashlib,datetime
R=Path(__file__).resolve().parents[1];REPO=R.parents[1]
PREV=Path('/home/liu/ring_first_3d_incremental/experiments/TASK-PHASED-INCREMENTAL-FUSION-MULTIGROUP-001')
OLD=Path('/home/liu/polyp_research/ring_anchor_3d/experiments')
V13=OLD/'ring_first_v13_multisource'
PHASE=Path('/home/liu/ring_first_3d_phase_d/experiments/TASK-PHASED-MAIN-SURFACE-CROSSVIDEO-001')
os.environ.setdefault('MPLCONFIGDIR',str(R/'runtime/mpl'));sys.path.insert(0,str(REPO))
import numpy as np,cv2,trimesh
from PIL import Image
from visualization import real_p0_renderer as vis
from visualization import pointcloud_audit_renderer as diag
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
def save(name,x):
    p=R/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(clean(x),ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def csvsave(name,rows):
    p=R/name;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',newline='')as f:
        w=csv.DictWriter(f,list(dict.fromkeys(k for r in rows for k in r)),lineterminator='\n');w.writeheader()
        for row in rows:w.writerow({k:json.dumps(clean(v),ensure_ascii=False)if isinstance(v,(dict,list,tuple,np.ndarray))else clean(v)for k,v in row.items()})
def both(name,rows):save('metrics/'+name+'.json',rows);csvsave('metrics/'+name+'.csv',rows)
def verify_predictions():
    f=load(R/'provenance/PREDICTIONS_FROZEN.json')
    for x in f['files']:assert sha(x['path'])==x['sha256'],x['path']
    for n,h in f['snapshots'].items():assert sha(R/'prediction_snapshot'/n)==h
def cases():return load(PREV/'provenance/CASES.json')
def case(cid):return next(c for c in cases()if c['id']==cid)
def source(cid):
    c=case(cid);z=dict(np.load(c['source_points']));p=dict(np.load(c['pack']));P=z.get('XYZ_mm',z.get('points_mm'));uv=z.get('pixel_uv',z.get('source_uv',z.get('uv')));assert uv is not None
    rgb=np.asarray(Image.open(c['RGB']).convert('RGB'));C=rgb[uv[:,1],uv[:,0]]/255.;m=trimesh.load(c['mesh'],process=False);assert len(P)==len(m.vertices)and np.allclose(P,m.vertices,atol=1e-5,rtol=0)
    return c,P,C,m,p,uv
def ring(c):return trimesh.load(OLD/'surface_fusion_v2/inputs/R10_ring.obj'if c['ring']=='R10'else Path('/home/liu/polyp_research/ring_anchor_3d/assets/ring_R5.obj'),process=False)
def stamp(files,**kw):return dict(UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=[dict(path=str(p),bytes=Path(p).stat().st_size,sha256=sha(p))for p in sorted(set(map(Path,files)))],**kw)
def angle(a,b):return float(np.degrees(np.arccos(np.clip(np.dot(a,b)/np.linalg.norm(a)/np.linalg.norm(b),-1,1))))
def guard_no_gt(event,args):
    if event=='open'and isinstance(args[0],(str,bytes)):
        s=os.fsdecode(args[0]);n=Path(s).name.lower()
        if n.endswith('.blend')or'/gt_mapping/'in s or'/evaluation_only/'in s or'oracle'in n:raise PermissionError('GT forbidden in observability/reprojection '+s)
