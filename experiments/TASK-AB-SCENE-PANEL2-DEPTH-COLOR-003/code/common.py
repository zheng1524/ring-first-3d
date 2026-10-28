"""Read-only last-task assets, new Panel-2-only outputs."""
from pathlib import Path
import os,sys,json,csv,hashlib,datetime,subprocess
R=Path(__file__).resolve().parents[1];REPO=R.parents[1]
PREV=Path('/home/liu/ring_first_3d_ab_scene/experiments/TASK-AB-FULL-SCENE-VIS-002')
INC=Path('/home/liu/ring_first_3d_incremental/experiments/TASK-PHASED-INCREMENTAL-FUSION-MULTIGROUP-001')
OLD=Path('/home/liu/polyp_research/ring_anchor_3d/experiments');VENDOR=OLD/'surface_fusion_v3/vendor'
os.environ['MPLCONFIGDIR']=str(R/'runtime/mpl');sys.path.insert(0,str(REPO))
import numpy as np,trimesh
from PIL import Image
from visualization import real_p0_renderer as vis
from visualization.same_camera_scene import SameCameraScene
plt=vis.configure()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
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
def both(name,rows):
    save('audit/'+name+'.json',rows);p=R/'audit'/(name+'.csv')
    with p.open('w',newline='')as f:
        w=csv.DictWriter(f,list(dict.fromkeys(k for r in rows for k in r)),lineterminator='\n');w.writeheader()
        for r in rows:w.writerow({k:json.dumps(clean(v),ensure_ascii=False)if isinstance(v,(dict,list,tuple,np.ndarray))else clean(v)for k,v in r.items()})
def stamp(files,**kw):return dict(UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=[dict(path=str(p),sha256=sha(p),bytes=Path(p).stat().st_size)for p in sorted(set(map(Path,files)))],**kw)
def guard(event,args):
    if event!='open'or not isinstance(args[0],(str,bytes)):return
    p=Path(os.fsdecode(args[0])).resolve();s=str(p);n=p.name.lower()
    if n.endswith('.blend')or'/gt_mapping/'in s or'/evaluation_only/'in s or'oracle'in n:raise PermissionError('No GT access '+s)
    flags=args[2]if len(args)>2 and isinstance(args[2],int)else 0;mode=args[1]if len(args)>1 and isinstance(args[1],str)else''
    if(any(c in mode for c in 'wax+')or flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC))and s.startswith('/home/liu/')and not p.is_relative_to(R):raise PermissionError('New task only '+s)
sys.addaudithook(guard)
def rows():return load(PREV/'metrics/results.json')
def layers(cid):
    r=next(r for r in rows()if r['A']==cid);a=dict(np.load(r['source_geometry_path']));c=next(c for c in load(INC/'provenance/CASES.json')if c['id']==cid);rp=OLD/'surface_fusion_v2/inputs/R10_ring.obj'if c['ring']=='R10'else Path('/home/liu/polyp_research/ring_anchor_3d/assets/ring_R5.obj');return a,trimesh.load(rp,process=False),rp
def state(p):
    git=lambda *a:subprocess.check_output(['git','-C',str(p),*a]).decode(errors='replace');index=Path(git('rev-parse','--git-path','index').strip());index=index if index.is_absolute()else p/index;modified={}
    for s in git('status','--porcelain','-z','-uno').split('\0'):
        if s and(p/s[3:]).is_file():modified[s[3:]]=sha(p/s[3:])
    return dict(HEAD=git('rev-parse','HEAD').strip(),index_sha256=sha(index),status=git('status','--porcelain','-z','-uall'),modified_sha256=modified)
