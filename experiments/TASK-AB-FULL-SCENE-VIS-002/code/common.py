"""Bounded task wrapper around frozen source identities and approved renderers."""
from pathlib import Path
import os,sys,json,csv,hashlib,datetime,subprocess
R=Path(__file__).resolve().parents[1];REPO=R.parents[1]
AUDIT=Path('/home/liu/ring_first_3d_view_eval/experiments/TASK-VIEW-OBSERVABILITY-GT-EVAL-001')
INC=Path('/home/liu/ring_first_3d_incremental/experiments/TASK-PHASED-INCREMENTAL-FUSION-MULTIGROUP-001')
HIST=Path('/home/liu/ring_first_3d_scene_vis/experiments/TASK-PHASEC-VIDEO-SCENE-VIS-001')
OLD=Path('/home/liu/polyp_research/ring_anchor_3d/experiments');VENDOR=OLD/'surface_fusion_v3/vendor'
os.environ.setdefault('MPLCONFIGDIR',str(R/'runtime/mpl'));sys.path.insert(0,str(REPO))
import numpy as np,cv2,trimesh
from PIL import Image
from visualization import real_p0_renderer as vis
from visualization import pointcloud_audit_renderer as diag
from visualization.same_camera_scene import SameCameraScene
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
def cases():return load(INC/'provenance/CASES.json')
def case(cid):return next(c for c in cases()if c['id']==cid)
def source(cid):
    c=case(cid);z=dict(np.load(c['source_points']));p=dict(np.load(c['pack']));P=z.get('XYZ_mm',z.get('points_mm'));uv=z.get('pixel_uv',z.get('source_uv',z.get('uv')));rgb=np.asarray(Image.open(c['RGB']).convert('RGB'));C=rgb[uv[:,1],uv[:,0]]/255.;m=trimesh.load(c['mesh'],process=False);assert len(P)==len(m.vertices)and np.allclose(P,m.vertices,atol=1e-5,rtol=0);return c,P,C,m,p,uv
def ring_path(c):return OLD/'surface_fusion_v2/inputs/R10_ring.obj'if c['ring']=='R10'else Path('/home/liu/polyp_research/ring_anchor_3d/assets/ring_R5.obj')
def ring(c):return trimesh.load(ring_path(c),process=False)
def stamp(files,**kw):return dict(UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=[dict(path=str(p),bytes=Path(p).stat().st_size,sha256=sha(p))for p in sorted(set(map(Path,files)))],**kw)
def angle(a,b):return float(np.degrees(np.arccos(np.clip(np.dot(a,b)/np.linalg.norm(a)/np.linalg.norm(b),-1,1))))
def guard(event,args):
    if event!='open'or not isinstance(args[0],(str,bytes)):return
    p=Path(os.fsdecode(args[0])).resolve();s=str(p);n=p.name.lower()
    if n.endswith('.blend')or'/gt_mapping/'in s or'/evaluation_only/'in s or'oracle'in n:raise PermissionError('No GT in visualization '+s)
    flags=args[2]if len(args)>2 and isinstance(args[2],int)else 0;mode=args[1]if len(args)>1 and isinstance(args[1],str)else''
    if(any(c in mode for c in 'wax+')or flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC))and s.startswith('/home/liu/')and not p.is_relative_to(R):raise PermissionError('Task outputs only '+s)
sys.addaudithook(guard)
def verify():
    for r in load(R/'provenance/INPUTS_FROZEN.json')['files']:assert sha(r['path'])==r['sha256'],r['path']
def state(p):
    def git(*args):return subprocess.check_output(['git','-C',str(p),*args]).decode(errors='replace')
    modified={}
    for row in git('status','--porcelain','-z','-uno').split('\0'):
        if row and(p/row[3:]).is_file():modified[row[3:]]=sha(p/row[3:])
    index=Path(git('rev-parse','--git-path','index').strip());index=index if index.is_absolute()else p/index
    return dict(HEAD=git('rev-parse','HEAD').strip(),branch=git('branch','--show-current').strip(),index_sha256=sha(index),status=git('status','--porcelain','-z','-uall'),modified_sha256=modified)
