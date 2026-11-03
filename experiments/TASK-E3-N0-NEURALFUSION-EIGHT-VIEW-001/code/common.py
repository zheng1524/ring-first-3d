"""Task-local, provenance-bound IO. Original observations are immutable."""
from pathlib import Path
from functools import lru_cache
import os,sys,ast,json,csv,hashlib,datetime,time
R=Path(__file__).resolve().parents[1];REPO=R.parents[1]
OLD=Path('/home/liu/polyp_research/ring_anchor_3d/experiments')
E1=Path('/home/liu/ring_first_3d_neural_e1/experiments/TASK-NEURAL-E1-PIPELINE-RECOVERY-001')
GA=Path('/home/liu/ring_first_3d_e3n0/experiments/TASK-E3-N0-GATE-A-COMPAT-CROP-METRIC-001')
A2=Path('/home/liu/ring_first_3d_e3n0_a2/experiments/TASK-E3-N0-GATE-A2-PROJECTIVE-CLEANUP-001')
A3=Path('/home/liu/ring_first_3d_e3n0_a3/experiments/TASK-E3-N0-GATE-A3-MASK-BOUNDARY-CLEANUP-001')
RB=Path('/home/liu/ring_first_3d_e3n0_gate_b/experiments/TASK-E3-N0-GATE-B-NEURALFUSION-F0-F2-001')
PART=Path('/home/liu/ring_first_3d_view_partition/experiments/TASK-VIEW-PARTITION-MAST3R-FUSION-001')
CG=REPO/'experiments/TASK-CAMERA-GATE-G01-004-PILOT-001'
D0=REPO/'experiments/TASK-E3-D0-OPEN3D-TSDF-BASELINE-001'
NF=GA/'runtime/neuralfusion_official';VENDOR=OLD/'surface_fusion_v3/vendor'
SCENES=['G01_004','G06_004','G07_004','G08_005']
for p in ['runtime/tmp','runtime/mpl','runtime/cache','local_results','config','figures','provenance','meshes','metrics']:(R/p).mkdir(parents=True,exist_ok=True)
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
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader()
        for r in rows:w.writerow({k:json.dumps(clean(v),ensure_ascii=False)if isinstance(v,(dict,list,tuple))else v for k,v in r.items()})
def rows(p):return list(csv.DictReader(Path(p).open()))
def asset(p):return dict(path=str(p),bytes=Path(p).stat().st_size,sha256=sha(p))
def extract(p,names,ns=None):
    ns=globals()if ns is None else ns;t=ast.parse(Path(p).read_text());nodes=[n for n in t.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))and n.name in names]
    assert {n.name for n in nodes}==set(names),(p,names)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(p),'exec'),ns);return ns
CC={a['id']:a for a in load(E1/'provenance/INPUT_ELIGIBILITY.json')['references']if a['scene_id']in SCENES}
IDS=list(CC);CORE=['G01_004_ref03','G01_004_ref08','G01_004_ref13']
ALLOWED={str(Path(c[k]).resolve())for c in CC.values()for k in ['pack','source_points','mesh','camera_file']}
ALLOWED.update(str(Path(c['E1_actual_native']['path']).resolve())for c in CC.values())
ALLOWED.update(str(Path(c['Ring_CAD']['path']).resolve())for c in CC.values())
for folder in [A3/'local_results/inputs/V6',A3/'local_results/inputs/V2',A2/'local_results/derived_inputs',CG/'config/matches',PART/'local_results/matches',OLD/'ring_first_v13_multisource/observations',RB/'meshes']:
    ALLOWED.update(str(p.resolve())for p in folder.glob('*')if p.is_file())
# Historical Open3D meshes are comparison-only; no inference code reads them.
for p in (D0/'local_results').glob('**/*.ply'):ALLOWED.add(str(p.resolve()))
ALLOWED.add(str((NF/'pretrained_models/shapenet_noise_005/version_0/checkpoints/best.ckpt').resolve()))
ACCESSED=set();DENIALS=[]
def guard(event,args):
    if event in ['socket.connect','socket.getaddrinfo']:raise PermissionError('OFFLINE_COMPUTATION')
    if event=='import'and str(args[0]).startswith(('training','dataset','pytorch_lightning','graphics')):raise PermissionError('NO_TRAINING_OR_GT_DATABASE')
    if event!='open'or not isinstance(args[0],(str,bytes)):return
    p=Path(os.fsdecode(args[0])).resolve();s=str(p);mode=args[1]if len(args)>1 and isinstance(args[1],str)else '';flags=args[2]if len(args)>2 and isinstance(args[2],int)else 0
    writing=any(v in mode for v in 'wax+')or flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)
    if writing and s.startswith('/home/liu/')and not p.is_relative_to(R):raise PermissionError('TASK_LOCAL_WRITE_ONLY:'+s)
    if not p.is_relative_to(R):
        if p.name.lower().startswith('gt_')or p.suffix.lower()=='.blend'or any(k in s.lower()for k in ['/private_gt/','/oracle/','/evaluation_only/','/new-polyp-dxy/']):raise PermissionError('NO_GT_ORACLE_DXY:'+s)
        if s.startswith('/home/liu/')and p.suffix.lower()in ['.npz','.npy','.ply','.obj','.glb','.ckpt','.pt','.pth']and s not in ALLOWED:
            DENIALS.append(s);raise PermissionError('NOT_ALLOWLISTED:'+s)
        if not writing and s.startswith('/home/liu/'):ACCESSED.add(s)
sys.addaudithook(guard)
import numpy as np,cv2,trimesh
from PIL import Image
from scipy.spatial import cKDTree
sys.path.insert(0,str(VENDOR));import open3d as o3d
sys.path.insert(0,str(REPO));from visualization import real_p0_renderer as vis
from visualization.same_camera_scene import SameCameraScene
extract(OLD/'ring_first_v1/scripts/common.py',['unproject'])
cv2.setNumThreads(2)
def stats(a):
    a=np.asarray(a,float);a=a[np.isfinite(a)]
    return dict(N=len(a),median=float(np.median(a))if len(a)else None,MAE=float(np.abs(a).mean())if len(a)else None,p95=float(np.quantile(np.abs(a),.95))if len(a)else None,maximum=float(np.abs(a).max())if len(a)else None)
@lru_cache(None)
def source(cid):
    c=CC[cid];p=np.load(c['pack']);K=np.asarray(p['K']);T=np.asarray(p['pose']);labels=np.asarray(Image.open(c['Mask']));rgb=np.asarray(Image.open(c['RGB']).convert('RGB'))
    assert labels.shape==(360,640)and rgb.shape==(360,640,3)
    assert np.allclose(T,c['c2w_mm'],rtol=0,atol=1e-10)and np.allclose(K,c['K_after_resize'],rtol=0,atol=1e-10)
    assert np.array_equal(labels,p['labels'])
    assert np.allclose(np.load(c['camera_file'])['c2w'][c['reference_index']],T,rtol=0,atol=1e-10)
    assert np.allclose(T[:3,:3].T@T[:3,:3],np.eye(3),atol=1e-10)and np.linalg.det(T[:3,:3])>0
    return dict(id=cid,c=c,K=K,T=T,labels=labels,RGB=rgb)
@lru_cache(None)
def native(cid):
    s=source(cid);c=s['c'];p=np.load(c['E1_actual_native']['path']);depth=p['depth_mm'];h,w=depth.shape
    Kn=vis.scaled_intrinsics(s['K'],(640,360),(w,h));stored=next((p[k]for k in ['K_index_native','K_index']if k in p),None)
    assert stored is None or np.allclose(Kn,stored,rtol=0,atol=1e-10)
    nt=next((p[k]for k in ['reference_pose_mm','pose']if k in p),None);assert nt is None or np.allclose(nt,s['T'],rtol=0,atol=1e-10)
    labels=cv2.resize(s['labels'],(w,h),interpolation=cv2.INTER_NEAREST);rgb=cv2.resize(s['RGB'],(w,h),interpolation=cv2.INTER_AREA)
    valid=(labels==1)&np.isfinite(depth)&(depth>0);v,u=np.nonzero(valid);uv=np.c_[u,v];X=unproject(depth[v,u].astype(float),s['T'],uv,Kn)
    return dict(s,depth=depth,Kn=Kn,native_labels=labels,native_RGB=rgb,valid=valid,native_uv=uv,native_id=v*w+u,X=X)
@lru_cache(None)
def original(cid):
    c=CC[cid];q=np.load(c['source_points']);P=q['points_mm']if'points_mm'in q else q['XYZ_mm'];mesh=trimesh.load(c['mesh'],process=False)
    F=q['original_faces']if'original_faces'in q else np.asarray(mesh.faces)
    uv=q['uv']if'uv'in q else(q['source_uv']if'source_uv'in q else q['pixel_uv']);uv=np.asarray(uv,int);s=source(cid)
    z=np.load(c['pack'])['depth_mm'];assert np.max(abs(unproject(z[uv[:,1],uv[:,0]],s['T'],uv,s['K'])-P))<1e-6
    assert np.array_equal(F,mesh.faces)and np.max(abs(P-mesh.vertices))<1e-5
    return dict(P=P,F=F,uv=uv,area=trimesh.triangles.area(P[F]))
@lru_cache(None)
def ringmesh(scene):return trimesh.load(next(c['Ring_CAD']['path']for c in CC.values()if c['scene_id']==scene),process=False)
def mesh_scene(P,F):
    s=o3d.t.geometry.RaycastingScene(nthreads=2)
    if len(F):s.add_triangles(o3d.core.Tensor(np.asarray(P,np.float32)),o3d.core.Tensor(np.asarray(F,np.uint32)))
    return s
@lru_cache(None)
def ringscene(scene):
    m=ringmesh(scene);return mesh_scene(m.vertices,m.faces)
def cast(scene,uv,K,T):
    result=scene.cast_rays(o3d.core.Tensor(vis.camera_rays(np.asarray(uv),K,T).astype(np.float32)))
    return result['t_hit'].numpy().astype(float),result['primitive_ids'].numpy().astype(np.int64)
def distance(scene,X):return scene.compute_distance(o3d.core.Tensor(np.asarray(X,np.float32))).numpy().astype(float)
def affine_uv(uv,A):return np.c_[uv,np.ones(len(uv))]@np.asarray(A)[:2].T
def config():return load(GA/'config/GATE_A_PREREGISTERED.json')
extract(GA/'code/crop.py',['make_crop'])
@lru_cache(None)
def cleaned(cid):
    n=native(cid);p=np.load(R/'frozen_inputs/native'/(cid+'.npz'));depth=p['depth_mm'];valid=p['valid'];v,u=np.nonzero(valid);uv=np.c_[u,v]
    assert not (valid&~n['valid']).any();assert np.array_equal(depth[valid],n['depth'][valid]);assert (depth[~valid]==0).all()
    return dict(n,depth=depth,valid=valid,native_uv=uv,native_id=v*depth.shape[1]+u,X=unproject(depth[v,u].astype(float),n['T'],uv,n['Kn']))
def crop(cid):return np.load(R/'frozen_inputs/crops'/(cid+'.npz'))
def protocol():return load(R/'config/EXPERIMENT_FROZEN.json')
def block(cid):
    c=CC[cid];vv=load(PART/'metrics/view_distribution.json');return next(v['block']for v in vv if v.get('source_id')==c['group']+'_video'+c['video']and v.get('index')==c['reference_index'])
