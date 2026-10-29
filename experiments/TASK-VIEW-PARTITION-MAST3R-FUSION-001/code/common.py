"""Frozen P0 / source cameras only. All writes confined to this task."""
from pathlib import Path
from functools import lru_cache
import os, sys, json, csv, hashlib, datetime, ast, subprocess
R = Path(__file__).resolve().parents[1]
REPO = R.parents[1]
INC = Path('/home/liu/ring_first_3d_incremental/experiments/TASK-PHASED-INCREMENTAL-FUSION-MULTIGROUP-001')
DENS = Path('/home/liu/ring_first_3d/experiments/TASK-PHASEC-DENSITY-MULTIGROUP-001')
SPARSE = DENS.parent/'TASK-PHASEC-SPARSE-STRETCH-CLEAN-VIS-001'
ABS = Path('/home/liu/ring_first_3d_abs_density/experiments/TASK-PHASEC-ABS-DENSITY-REPROJ-001')
PHASE = Path('/home/liu/ring_first_3d_phase_d/experiments/TASK-PHASED-MAIN-SURFACE-CROSSVIDEO-001')
AB = Path('/home/liu/ring_first_3d_ab_scene/experiments/TASK-AB-FULL-SCENE-VIS-002')
DEPTH = Path('/home/liu/ring_first_3d_panel2_depth/experiments/TASK-AB-SCENE-PANEL2-DEPTH-COLOR-003')
OLD = Path('/home/liu/polyp_research/ring_anchor_3d/experiments')
VENDOR = OLD/'surface_fusion_v3/vendor'
os.environ.setdefault('MPLCONFIGDIR',str(R/'runtime/mpl'))
sys.path.insert(0,str(REPO))
import numpy as np, cv2, trimesh
from PIL import Image
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree
from visualization import real_p0_renderer as vis
from visualization import pointcloud_audit_renderer as diag
from visualization.same_camera_scene import SameCameraScene

def guard(event,args):
    if event!='open' or not isinstance(args[0],(str,bytes)): return
    p=Path(os.fsdecode(args[0])).resolve(); s=str(p); n=p.name.lower()
    if n.endswith('.blend') or n.startswith('gt_') or 'oracle' in n or any(x in s for x in ['/gt_mapping/','/private_gt/','/evaluation_exports/','/evaluation_only/']):
        raise PermissionError('GT excluded: '+s)
    flags=args[2] if len(args)>2 and isinstance(args[2],int) else 0
    mode=args[1] if len(args)>1 and isinstance(args[1],str) else ''
    if (any(x in mode for x in 'wax+') or flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)) and s.startswith('/home/liu/') and not p.is_relative_to(R):
        raise PermissionError('Task outputs only: '+s)
sys.addaudithook(guard)

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(2**20),b''): h.update(b)
    return h.hexdigest()
def load(p): return json.loads(Path(p).read_text())
def clean(v):
    if isinstance(v,dict): return {str(k):clean(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)): return [clean(x) for x in v]
    if isinstance(v,np.ndarray): return clean(v.tolist())
    if isinstance(v,(np.integer,np.bool_)): return v.item()
    if isinstance(v,(float,np.floating)): return float(v) if np.isfinite(v) else None
    return v
def save(p,v):
    p=R/p;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(clean(v),ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def both(name,rows):
    save('metrics/'+name+'.json',rows);p=R/'metrics'/(name+'.csv');p.parent.mkdir(exist_ok=True)
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,keys,lineterminator='\n');w.writeheader()
        for r in rows:w.writerow({k:json.dumps(clean(v),ensure_ascii=False) if isinstance(v,(dict,list,tuple,np.ndarray)) else clean(v) for k,v in r.items()})
def stats(x):
    a=np.asarray(x,float);a=a[np.isfinite(a)]
    return dict(N=len(a),median=np.median(a) if len(a) else None,MAE=np.mean(abs(a)) if len(a) else None,p05=np.quantile(a,.05) if len(a) else None,p95=np.quantile(a,.95) if len(a) else None,maximum=a.max() if len(a) else None)
def stamp(files,**kw):return dict(UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=[dict(path=str(p),bytes=Path(p).stat().st_size,sha256=sha(p)) for p in sorted(set(map(Path,files)))],**kw)
def cfg():return load(R/'config/rules.json')
def cases():return load(INC/'provenance/CASES.json')
def case(cid):return next(c for c in cases() if c['id']==cid)
def sceneid(c):return c['group']+'_'+c['video']
def scenes():return [dict(id=g+'_'+v,group=g,video=v,refs=[c['id']for c in cases()if c['group']==g and c['video']==v])for g,v in dict.fromkeys((c['group'],c['video'])for c in cases())]
def transform(P,H):return np.asarray(P)@np.asarray(H)[:3,:3].T+np.asarray(H)[:3,3]
def angle(a,b):return float(np.degrees(np.arccos(np.clip(np.dot(a,b)/np.linalg.norm(a)/np.linalg.norm(b),-1,1))))
def rotangle(H):return float(np.degrees(np.arccos(np.clip((np.trace(H[:3,:3])-1)/2,-1,1))))
def ring_path(c):return OLD/'surface_fusion_v2/inputs/R10_ring.obj' if c['ring']=='R10' else Path('/home/liu/polyp_research/ring_anchor_3d/assets/ring_R5.obj')
@lru_cache(None)
def source(cid):
    c=case(cid);a=dict(np.load(DENS/f'local_fields/{cid}_fields.npz'));p=dict(np.load(c['pack']));P=a['XYZ_mm'];uv=np.c_[a['source_u'],a['source_v']];rgb=np.asarray(Image.open(c['RGB']).convert('RGB'));m=trimesh.load(c['mesh'],process=False)
    assert len(P)==len(m.vertices) and np.allclose(P,m.vertices,atol=1e-5,rtol=0)
    camera=(P-p['pose'][:3,3])@p['pose'][:3,:3]
    assert np.allclose(camera[:,2],p['depth_mm'][uv[:,1],uv[:,0]],atol=1e-8,rtol=0)
    back=vis.project_camera(P,p['K'],p['pose'])[0];assert np.max(abs(back-uv))<1e-7
    return dict(c=c,a=a,p=p,P=P,C=rgb[uv[:,1],uv[:,0]]/255.,uv=uv,m=m,F=np.asarray(m.faces),areas=m.area_faces,frame=rgb,ring=trimesh.load(ring_path(c),process=False))
def background(cid):
    z=dict(np.load(INC/f'local_results/background/{cid}.npz'));i=np.flatnonzero(z['display']);return dict(P=z['XYZ_mm'][i],C=z['RGB'][i],uv=z['source_uv'][i],ids=i)
def target_source(cid):
    s=source(cid);return dict(id=s['c']['reference'],K=s['p']['K'],c2w=s['p']['pose'],RGB=s['c']['RGB'],Mask=s['c']['Mask'],ring_case=cid,role='SOURCE_REFERENCE')
def selection(sid):return load(INC/'provenance/TARGETS_FROZEN.json')[sid]
def targets(sid):return [x['target']|dict(role=x['role']) for x in load(INC/'provenance/REVIEW_TARGETS_FROZEN.json') if x['scene']==sid]
def extract(path,names):
    nodes=[n for n in ast.parse(Path(path).read_text()).body if isinstance(n,ast.FunctionDef)and n.name in names]
    assert len(nodes)==len(names)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),globals())
extract(SPARSE/'code/run.py',['source_components','face_components','edge_counts','interior_deletion_patches'])
def cohorts(s):
    a=s['a'];uv=s['uv'];_,cl,head=source_components(s['p'],uv);minor=cl!=head;cut=np.quantile(uv[minor,1],.8)if minor.any()else np.inf
    reg=np.load(ABS/f'local_results/{s["c"]["id"]}/spatial_regions.npz')
    return dict(head_source_proxy=cl==head,possible_stalk_proxy=minor&(uv[:,1]>=cut),Ring_near=a['Ring_near'],Mask_boundary=a['boundary'],historical_low_region=reg['largest_low_region'],sparse_stretched_proxy=(a['knn_k_distance_mm']/((s['P']-s['p']['pose'][:3,3])@s['p']['pose'][:3,:3])[:,2]>=np.quantile(a['knn_k_distance_mm']/((s['P']-s['p']['pose'][:3,3])@s['p']['pose'][:3,:3])[:,2],.75))&(a['adjacency_perspective_stretch_max']>=4))
def state(p):
    def git(*a):return subprocess.check_output(['git','-C',str(p),*a]).decode(errors='replace')
    index=Path(git('rev-parse','--git-path','index').strip());index=index if index.is_absolute()else p/index
    mod={}
    for row in git('status','--porcelain','-z','-uno').split('\0'):
        if row and(p/row[3:]).is_file():mod[row[3:]]=sha(p/row[3:])
    return dict(HEAD=git('rev-parse','HEAD').strip(),branch=git('branch','--show-current').strip(),index_sha256=sha(index),status=git('status','--porcelain','-z','-uall'),modified_sha256=mod)
GRAZ=Path('/home/liu/ring_first_3d_grazing/experiments/TASK-PHASED-GRAZING-SELECTIVE-AGGREGATION-001')
AUDIT=Path('/home/liu/ring_first_3d_view_eval/experiments/TASK-VIEW-OBSERVABILITY-GT-EVAL-001')
V8=OLD/'ring_first_v8_registration_narrow_baseline'
V9=OLD/'ring_first_v9_ring_guided_recovery'
F1=OLD/'surface_fusion_v1'

def verify():
    for f in load(R/'provenance/INPUTS_FROZEN.json')['files']:assert sha(f['path'])==f['sha256'],f['path']
