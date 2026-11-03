"""CPU-only frozen-asset adapters; no historical main, network or learned model."""
from pathlib import Path
from functools import lru_cache
from types import SimpleNamespace
import os,sys,ast,json,csv,hashlib,datetime
R=Path(__file__).resolve().parents[1]; REPO=R.parents[1]
N0=Path('/home/liu/ring_first_3d_e3n0_eight/experiments/TASK-E3-N0-NEURALFUSION-EIGHT-VIEW-001')
MULTI=Path('/home/liu/ring_first_3d_e3_sdf_multi/experiments/TASK-E3-SDF-LOCAL-MULTIPOLYP-EXPLORATORY-001')
E1=Path('/home/liu/ring_first_3d_neural_e1/experiments/TASK-NEURAL-E1-PIPELINE-RECOVERY-001')
PART=Path('/home/liu/ring_first_3d_view_partition/experiments/TASK-VIEW-PARTITION-MAST3R-FUSION-001')
CG=Path('/home/liu/ring_first_3d_camera_gate/experiments/TASK-CAMERA-GATE-G01-004-PILOT-001')
OLD=Path('/home/liu/polyp_research/ring_anchor_3d/experiments')
VENDOR=OLD/'surface_fusion_v3/vendor'
for d in ['config','provenance','metrics','figures','local_results','runtime/mpl','runtime/tmp']:(R/d).mkdir(parents=True,exist_ok=True)
os.environ.update(CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='2',MPLCONFIGDIR=str(R/'runtime/mpl'),TMPDIR=str(R/'runtime/tmp'))
sys.dont_write_bytecode=True
def load(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def clean(a):
    if isinstance(a,dict):return {str(k):clean(v)for k,v in a.items()}
    if isinstance(a,(list,tuple)):return [clean(v)for v in a]
    if hasattr(a,'tolist'):return clean(a.tolist())
    if isinstance(a,Path):return str(a)
    if isinstance(a,float)and not __import__('math').isfinite(a):return None
    return a
def save(p,a):
    p=R/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(clean(a),ensure_ascii=False,indent=2)+'\n')
def table(p,aa):
    p=R/p;p.parent.mkdir(parents=True,exist_ok=True)
    if not aa:p.write_text('');return
    with p.open('w',newline='')as f:
        w=csv.DictWriter(f,fieldnames=list(aa[0]));w.writeheader()
        for a in aa:w.writerow({k:json.dumps(clean(v),ensure_ascii=False)if isinstance(v,(dict,list,tuple))else clean(v)for k,v in a.items()})
def asset(p):return dict(path=str(p),sha256=sha(p),bytes=Path(p).stat().st_size)
def extract(p,names,ns=None):
    ns=globals()if ns is None else ns;t=ast.parse(Path(p).read_text());nodes=[n for n in t.body if isinstance(n,ast.FunctionDef)and n.name in names];assert {n.name for n in nodes}==set(names)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(p),'exec'),ns);return ns
CC={c['id']:c for c in load(E1/'provenance/INPUT_ELIGIBILITY.json')['references']if c['scene_id']in ['G01_004','G06_004','G08_005']}
GATE={c['source']:c for c in load(N0/'config/CAMERA_GATE_RESULTS.json')['sources']}
ACCESSED=set()
def guard(event,args):
    if event in ['socket.connect','socket.getaddrinfo']:raise PermissionError('OFFLINE_DIAGNOSTICS')
    if event=='import'and str(args[0]).split('.')[0]in ['torch','tensorflow','mast3r','training']:raise PermissionError('NO_MODEL_RUNTIME')
    if event!='open'or not isinstance(args[0],(str,bytes)):return
    p=Path(os.fsdecode(args[0])).resolve();s=str(p);mode=args[1]if isinstance(args[1],str)else '';flags=args[2]if len(args)>2 and isinstance(args[2],int)else 0
    writing=any(c in mode for c in 'wax+')or flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)
    if s.startswith('/home/liu/')and writing and not p.is_relative_to(R):raise PermissionError('TASK_LOCAL_WRITES_ONLY:'+s)
    if not p.is_relative_to(R):
        if p.suffix in ['.pt','.pth','.ckpt','.blend','.safetensors']or p.name.lower().startswith('gt_')or any(c in s.lower()for c in ['/oracle/','/private_gt/','/evaluation_only/','/new-polyp-dxy/','/local_results/scenes/','/pointcloud_blocks/']):raise PermissionError('NO_GT_MODELS_OR_FUSION:'+s)
        if s.startswith('/home/liu/')and not writing:ACCESSED.add(s)
sys.addaudithook(guard)
import numpy as np,cv2,trimesh
from PIL import Image
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation
from scipy.ndimage import map_coordinates
from scipy.linalg import expm
sys.path.insert(0,str(VENDOR));import open3d as o3d
sys.path.insert(0,str(REPO));from visualization import real_p0_renderer as vis
cv2.setNumThreads(2)
extract(N0/'code/common.py',['source','native','original','ringmesh','mesh_scene','ringscene','cast'])
extract(OLD/'ring_first_v1/scripts/common.py',['unproject'])
extract(CG/'code/common.py',['boundary','fit_partition','skew','fundamental','sampson'])
extract(OLD.parent/'scripts/geometry.py',['torus_contours'])
cfg=load(N0/'config/CAMERA_GATE_RULES.json')
extract(PART/'code/matching.py',['sift'],dict(np=np,cv2=cv2,cfg=lambda:cfg,image=lambda c:source(c['id'])['RGB']))
SIFT=extract(PART/'code/matching.py',['sift'],dict(np=np,cv2=cv2,cfg=lambda:cfg,image=lambda c:source(c['id'])['RGB']))['sift']
def protocol():return load(R/'config/PROTOCOL.json')
def select(ii,n):return ii[np.linspace(0,len(ii)-1,min(n,len(ii)),dtype=int)]if len(ii)else ii
def inside(uv):return np.isfinite(uv).all(1)&(uv[:,0]>=0)&(uv[:,0]<640)&(uv[:,1]>=0)&(uv[:,1]<360)
def pix(uv,shape=(360,640)):
    return np.clip(np.floor(uv+.5).astype(int),[0,0],[shape[1]-1,shape[0]-1])
def at(a,uv):
    p=pix(uv,a.shape[:2]);return a[p[:,1],p[:,0]]
def stats(a):
    a=np.asarray(a);a=a[np.isfinite(a)]
    return dict(N=len(a),median_abs=float(np.median(abs(a)))if len(a)else None,MAE=float(abs(a).mean())if len(a)else None,p95_abs=float(np.quantile(abs(a),.95))if len(a)else None,max_abs=float(abs(a).max())if len(a)else None)
def signed_distance(mask):
    return cv2.distanceTransform((~mask).astype(np.uint8),cv2.DIST_L2,cv2.DIST_MASK_PRECISE)-cv2.distanceTransform(mask.astype(np.uint8),cv2.DIST_L2,cv2.DIST_MASK_PRECISE)
def sample(a,uv):return map_coordinates(a.astype(float),[uv[:,1],uv[:,0]],order=1,mode='nearest')
@lru_cache(None)
def cleaned(cid):
    n=native(cid);p=N0/'frozen_inputs/native'/(cid+'.npz')
    if not p.exists():p=MULTI/'frozen_inputs/native'/(cid+'.npz')
    a=np.load(p);valid=a['valid'];d=a['depth_mm'];assert not(valid&~n['valid']).any()and np.array_equal(d[valid],n['depth'][valid])and(d[~valid]==0).all()
    v,u=np.nonzero(valid);uv=np.c_[u,v]
    return dict(n,valid=valid,depth=d,native_uv=uv,native_id=v*d.shape[1]+u,X=unproject(d[v,u].astype(float),n['T'],uv,n['Kn']),cleanup_path=str(p))
def archived_mesh(cid,kind='Cleaned'):
    a=original(cid);s=source(cid);P,F,uv=a['P'],a['F'],a['uv'];keep=np.ones(len(P),bool)
    if kind=='Cleaned':
        n=cleaned(cid);uvn=(uv+.5)*np.array(n['depth'].shape[::-1])/np.array([640,360])-.5;xy=pix(uvn,n['depth'].shape);keep=n['valid'][xy[:,1],xy[:,0]]
        F=F[keep[F].all(1)]
    return P,F,s['RGB'][uv[:,1],uv[:,0]]/255.,keep
def raw_rays(uv,K,T):return vis.camera_rays(uv,K,T)
def surface(cid,uv,bias=0,T=None):
    n=cleaned(cid);uvn=(uv+.5)*np.array(n['depth'].shape[::-1])/np.array([640,360])-.5;xy=pix(uvn,n['depth'].shape);z=n['depth'][xy[:,1],xy[:,0]].astype(float)+bias
    # Native Pixel ID depth, native center ray; RGB subpixel correspondence retained separately.
    return unproject(z,n['T']if T is None else T,xy,n['Kn']),n['valid'][xy[:,1],xy[:,0]],xy,z
def perturb(T,x):
    # Right/body SE(3), x=[mm translations, rad rotations].
    H=np.zeros((4,4));H[:3,:3]=skew(x[3:]);H[:3,3]=x[:3];return T@expm(H)
def canonical_ring(T):
    a=np.arctan2(T[1,3],T[0,3]);Z=np.eye(4);Z[:3,:3]=Rotation.from_rotvec([0,0,-a]).as_matrix();return Z@T
def ring_curves(cid,T):
    m=ringmesh(CC[cid]['scene_id']);r=np.linalg.norm(m.vertices[:,:2],axis=1);major=(r.max()+r.min())/2;minor=(r.max()-r.min())/2
    assert np.max(abs(np.sqrt((r-major)**2+m.vertices[:,2]**2)-minor))<1e-4
    C=canonical_ring(T);return torus_contours(C[:3,3],C[:3,:3],source(cid)['K'],R=major,r=minor,n=2048)
def matching(a,b):
    path=R/'local_results/matches'/(a+'__'+b+'.npz')
    if path.exists():return dict(np.load(path))
    origin=None;reverse=False
    # Reuse actual SIFT caches only, with source IDs from audited Camera Gate.
    for x,y,rev in [(a,b,False),(b,a,True)]:
        for parent,name in [(N0/'local_results/matches',x+'__'+y+'_SIFT.npz'),(CG/'config/matches',x.removeprefix('G01_004_')+'__'+y.removeprefix('G01_004_')+'_SIFT.npz')]:
            f=parent/name
            if f.exists():origin=f;reverse=rev;break
        if origin:break
    if origin:
        d=np.load(origin);p,q=(d['q'],d['p'])if reverse else(d['p'],d['q'])
    else:p,q,_=SIFT(CC[a],CC[b])
    sa,sb=source(a),source(b);usable=inside(p)&inside(q)&(at(sa['labels'],p)==at(sb['labels'],q))&(at(sa['labels'],p)!=2)&(at(sa['RGB'],p).min(1)<245)&(at(sb['RGB'],q).min(1)<245)
    held=fit_partition(p,q);F=np.full((3,3),np.nan)
    if (usable&~held).sum()>=12:
        cv2.setRNGSeed(0);f,_=cv2.findFundamentalMat(p[usable&~held],q[usable&~held],cv2.FM_RANSAC,2.,.999,2000)
        if f is not None and f.shape==(3,3):F=f
    error=sampson(F,p,q);d=dict(p=p,q=q,usable=usable,held=held,F=F,independent_good=usable&np.isfinite(error)&(error<=2.),origin=np.array(str(origin)if origin else'NEW_CPU_SIFT'))
    path.parent.mkdir(exist_ok=True);np.savez_compressed(path,**d);return d
