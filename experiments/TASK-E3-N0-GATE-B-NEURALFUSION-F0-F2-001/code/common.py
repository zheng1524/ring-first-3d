"""Frozen-input inference/evaluation helpers. No historical geometry fallback."""
from pathlib import Path
from functools import lru_cache
import os, sys, json, csv, hashlib, ast, time
R=Path(__file__).resolve().parents[1]; REPO=R.parents[1]
A3=Path('/home/liu/ring_first_3d_e3n0_a3/experiments/TASK-E3-N0-GATE-A3-MASK-BOUNDARY-CLEANUP-001')
GA=Path('/home/liu/ring_first_3d_e3n0/experiments/TASK-E3-N0-GATE-A-COMPAT-CROP-METRIC-001')
E1=Path('/home/liu/ring_first_3d_neural_e1/experiments/TASK-NEURAL-E1-PIPELINE-RECOVERY-001')
NF=GA/'runtime/neuralfusion_official'
VENDOR=Path('/home/liu/polyp_research/ring_anchor_3d/experiments/surface_fusion_v3/vendor')
IDS=['G01_004_ref08','G01_004_ref13','G01_004_ref03','G01_004_growth_r04','G01_004_new_r00','G01_004_growth_r14']; CORE=IDS[:3]
for p in ['runtime/tmp','runtime/mpl','runtime/cache','local_results','config','figures','provenance','meshes']:(R/p).mkdir(parents=True,exist_ok=True)
os.environ.update(PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='2',MPLCONFIGDIR=str(R/'runtime/mpl'),XDG_CACHE_HOME=str(R/'runtime/cache'),TMPDIR=str(R/'runtime/tmp'),HF_HUB_OFFLINE='1')
sys.dont_write_bytecode=True
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def clean(v):
    if isinstance(v,dict):return {str(k):clean(a)for k,a in v.items()}
    if isinstance(v,(list,tuple)):return [clean(a)for a in v]
    if hasattr(v,'tolist'):return clean(v.tolist())
    if isinstance(v,Path):return str(v)
    if isinstance(v,float)and not __import__('math').isfinite(v):return None
    return v
def save(p,v):
    p=R/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(clean(v),ensure_ascii=False,indent=2)+'\n')
def table(p,rows):
    p=R/p;p.parent.mkdir(parents=True,exist_ok=True)
    if not rows:p.write_text('');return
    with p.open('w',newline='')as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader()
        for r in rows:w.writerow({k:json.dumps(clean(v),ensure_ascii=False)if isinstance(v,(dict,list,tuple))else v for k,v in r.items()})
def asset(p):return dict(path=str(p),bytes=Path(p).stat().st_size,sha256=sha(p))
def extract(p,names,ns):
    t=ast.parse(Path(p).read_text());nodes=[n for n in t.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))and n.name in names]
    assert {n.name for n in nodes}==set(names)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(p),'exec'),ns)
MANIFEST=load(REPO/'experiments/TASK-E3-D0-OPEN3D-TSDF-BASELINE-001/HERO_TSDF_INPUT_MANIFEST.json')
CAD=Path(MANIFEST['CAD']['path'])
CC={a['id']:a for a in load(E1/'provenance/INPUT_ELIGIBILITY.json')['references']if a['id']in IDS}
ALLOWED={str(Path(a['path']).resolve())for row in MANIFEST['sources']for a in row['assets'].values()}
ALLOWED.add(str(CAD.resolve()))
ALLOWED.update(str(p.resolve())for v in ['V2','V6']for folder in ['inputs','crops']for p in (A3/'local_results'/folder/v).glob('*.npz'))
ALLOWED.add(str((NF/'pretrained_models/shapenet_noise_005/version_0/checkpoints/best.ckpt').resolve()))
ACCESSED=set()
def guard(event,args):
    if event in ['socket.connect','socket.getaddrinfo']:raise PermissionError('OFFLINE_FIXED_INFERENCE')
    if event=='import'and str(args[0]).startswith(('training','dataset','pytorch_lightning','graphics')):raise PermissionError('NO_TRAINING_DATASET_GT_ENTRYPOINT')
    if event!='open'or not isinstance(args[0],(str,bytes)):return
    p=Path(os.fsdecode(args[0])).resolve();s=str(p)
    mode=args[1]if len(args)>1 and isinstance(args[1],str)else '';flags=args[2]if len(args)>2 and isinstance(args[2],int)else 0
    writing=any(v in mode for v in 'wax+')or flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)
    if writing and s.startswith('/home/liu/')and not p.is_relative_to(R):raise PermissionError('TASK_LOCAL_WRITE_ONLY:'+s)
    if not p.is_relative_to(R):
        if p.name.lower().startswith('gt_')or p.suffix=='.blend'or any(k in s.lower()for k in ['/private_gt/','/oracle/','/evaluation_only/','/new-polyp-dxy/']):raise PermissionError('NO_GT_ORACLE_DXY:'+s)
        if s.startswith('/home/liu/')and p.suffix.lower()in ['.npz','.npy','.ply','.obj','.glb','.ckpt','.pt','.pth']and s not in ALLOWED:raise PermissionError('INPUT_NOT_ALLOWLISTED:'+s)
        if not writing and s.startswith('/home/liu/'):ACCESSED.add(s)
sys.addaudithook(guard)
import numpy as np, cv2, trimesh
from PIL import Image
sys.path.insert(0,str(VENDOR));import open3d as o3d
sys.path.insert(0,str(REPO));from visualization import real_p0_renderer as vis
from visualization.same_camera_scene import SameCameraScene
extract(Path('/home/liu/polyp_research/ring_anchor_3d/experiments/ring_first_v1/scripts/common.py'),['unproject'],globals())
@lru_cache(None)
def camera(cid):
    c=CC[cid];p=np.load(c['pack']);K=p['K'];T=p['pose']
    assert np.allclose(T,c['c2w_mm'],atol=1e-10)
    return K,T
@lru_cache(None)
def original(cid):
    c=CC[cid];K,T=camera(cid);q=np.load(c['source_points'])
    P=q['points_mm']if'points_mm'in q else q['XYZ_mm'];F=q['original_faces']
    labels=np.asarray(Image.open(c['Mask']));RGB=np.asarray(Image.open(c['RGB']).convert('RGB'))
    return dict(P=P,F=F,K=K,T=T,labels=labels,RGB=RGB,area=trimesh.triangles.area(P[F]))
def crop(cid,v):return np.load(R/'frozen_inputs'/v/'crops'/(cid+'.npz'))
def native(cid,v):
    p=np.load(R/'frozen_inputs'/v/'inputs'/(cid+'.npz'));z=p['depth_mm'];valid=p['valid'];K,T=camera(cid)
    Kn=vis.scaled_intrinsics(K,(640,360),(640,352));vv,uu=np.nonzero(valid);uv=np.c_[uu,vv]
    return dict(depth=z,valid=valid,uv=uv,ids=vv*640+uu,X=unproject(z[vv,uu].astype(float),T,uv,Kn),K=Kn,T=T)
def cfg():return load(R/'config/PREREGISTERED.json')
@lru_cache(None)
def ringmesh():return trimesh.load(CAD,process=False)
def mesh_scene(P,F):
    s=o3d.t.geometry.RaycastingScene(nthreads=2)
    if len(F):s.add_triangles(o3d.core.Tensor(np.asarray(P,np.float32)),o3d.core.Tensor(np.asarray(F,np.uint32)))
    return s
@lru_cache(None)
def ringscene():return mesh_scene(ringmesh().vertices,ringmesh().faces)
def cast(scene,uv,K,T):
    rays=vis.camera_rays(uv,K,T).astype(np.float32)
    r=scene.cast_rays(o3d.core.Tensor(rays));return r['t_hit'].numpy().astype(float)
def output_mesh(method,v,F):return trimesh.load(R/'meshes'/f'{method}_{v}_{F}_mm.ply',process=False)
def metric(a):
    a=np.asarray(a);a=a[np.isfinite(a)]
    return dict(N=len(a),median=float(np.median(a))if len(a)else None,MAE=float(np.abs(a).mean())if len(a)else None,p95=float(np.quantile(np.abs(a),.95))if len(a)else None,maximum=float(np.abs(a).max())if len(a)else None)
