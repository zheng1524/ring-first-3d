"""E2.5 bounded CPU diagnostics. Exact E1/E2 reuse with NEW user authorization."""
from pathlib import Path
from functools import lru_cache
import os,sys,ast,json,csv,hashlib,datetime,subprocess,importlib.util
R=Path(__file__).resolve().parents[1];REPO=R.parents[1]
E0=Path('/home/liu/ring_first_3d_neural_e0/experiments/TASK-NEURAL-E0-COMPARE-001')
E1=Path('/home/liu/ring_first_3d_neural_e1/experiments/TASK-NEURAL-E1-PIPELINE-RECOVERY-001')
E2=Path('/home/liu/ring_first_3d_neural_e2/experiments/TASK-NEURAL-E2-C2A-C2B-CONTRACT-001')
E2C=Path('/home/liu/ring_first_3d_neural_e2_cpu/experiments/TASK-NEURAL-E2-C2A-C2B-CONTRACT-001')
GROW=Path('/home/liu/ring_first_3d_boundary_growth/experiments/TASK-BOUNDARY-GUIDED-SURFACE-GROWTH-001')
PART=Path('/home/liu/ring_first_3d_view_partition/experiments/TASK-VIEW-PARTITION-MAST3R-FUSION-001')
INC=Path('/home/liu/ring_first_3d_incremental/experiments/TASK-PHASED-INCREMENTAL-FUSION-MULTIGROUP-001')
OLD=Path('/home/liu/polyp_research/ring_anchor_3d/experiments');VENDOR=OLD/'surface_fusion_v3/vendor'
SDF=E0/'runtime/monosdf_official';MAP=E0/'runtime/map-anything'
os.environ.update(CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
    MPLCONFIGDIR=str(R/'runtime/mpl'),TMPDIR=str(R/'runtime/tmp'),OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='2')
sys.dont_write_bytecode=True
for p in ['metrics','provenance','config','figures','docs','inputs','local_results','runtime/tmp','visualizations']:(R/p).mkdir(parents=True,exist_ok=True)
ACCESSED=set();REUSE=[]
src=E1/'code/common.py';tree=ast.parse(src.read_text())
names=['guard','sha','load','clean','save','table','stats','extract','asset','git','protected_state','ring','cad_scene']
nodes=[x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name in names]
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(src),'exec'),globals())
_old_guard=guard
def guard(event,args):
    # Explicit E2.5 user grant permits real official MonoSDF CPU modules. No
    # network/GT/Dxy/external writes are relaxed; Map models remain prohibited.
    if event=='import' and str(args[0])=='model.network':return
    _old_guard(event,args)
    if event=='open' and isinstance(args[0],(str,bytes)) and Path(os.fsdecode(args[0])).suffix.lower() in ['.pt','.pth','.ckpt','.safetensors']:
        raise PermissionError('E25_NO_CHECKPOINT_IO')
sys.addaudithook(guard)
import numpy as np,cv2,trimesh
from PIL import Image
sys.path.insert(0,str(REPO));from visualization import real_p0_renderer as vis
from visualization.same_camera_scene import SameCameraScene
unproject=extract(OLD/'ring_first_v1/scripts/common.py',['unproject'])['unproject']
def registry():return load(E1/'provenance/INPUT_ELIGIBILITY.json')
def selected():return load(E1/'provenance/G01_PROPOSED_INPUTS.json')['proposals']
def e2_asset(relative):
    m=load(E2/'provenance/DELIVERY_MANIFEST.json');d={x['path']:x for x in m['files']+m['LOCAL_ONLY']};p=E2/relative
    assert sha(p)==d[relative]['sha256'],'frozen E2 asset changed: '+relative
    return p
def source(ref):
    C={c['id']:c for c in registry()['references']};c=C[ref]
    p=np.load(c['pack']);r=np.load(e2_asset('local_results/rays/'+ref+'.npz'))
    assert sha(c['pack'])==c['files']['pack']['sha256']
    return c,p,r
def grid():return np.c_[np.tile(np.arange(640),360),np.repeat(np.arange(360),640)]
def official_method(path,cls,name):
    t=ast.parse(Path(path).read_text());c=next(n for n in t.body if isinstance(n,ast.ClassDef)and n.name==cls);f=next(n for n in c.body if isinstance(n,ast.FunctionDef)and n.name==name)
    return f,dict(path=str(path),class_name=cls,method=name,line=f.lineno,file_SHA256=sha(path),AST_SHA256=hashlib.sha256(ast.dump(f,include_attributes=False).encode()).hexdigest())
def import_exact(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module);return module
sys.modules['context']=sys.modules[__name__]
sys.modules['continuation_context']=sys.modules[__name__]
opacity=import_exact('opacity',E2C/'code/opacity.py')
def freeze(name,extra=None):
    save('provenance/'+name,dict(UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        code=[asset(p) for p in sorted((R/'code').glob('*.py'))],config=[asset(p) for p in sorted((R/'config').glob('*.json'))],extra=extra,
        GT_opened=False,GPU='NOT_AUTHORIZED',optimizer_step_N=0))
def residual_stats(x):
    x=np.asarray(x,float);x=x[np.isfinite(x)]
    if not len(x):return dict(N=0,median_signed=None,MAD=None,median_abs=None,p90_abs=None,p95_abs=None,positive_fraction=None,negative_fraction=None)
    med=float(np.median(x))
    return dict(N=len(x),median_signed=med,MAD=float(np.median(abs(x-med))),median_abs=float(np.median(abs(x))),
        p90_abs=float(np.quantile(abs(x),.9)),p95_abs=float(np.quantile(abs(x),.95)),positive_fraction=float((x>0).mean()),negative_fraction=float((x<0).mean()))
def region_fields(p,r):
    labels=p['labels'];mask=(labels==1).astype(np.uint8);kernel=np.ones((5,5),np.uint8)
    boundary=(mask>0)&(cv2.erode(mask,kernel)==0)
    near_ring=cv2.distanceTransform((labels!=2).astype(np.uint8),cv2.DIST_L2,5)<=8
    uv=grid();z=p['depth_mm'].ravel();P=unproject(z,p['pose'],uv,p['K']).reshape(360,640,3)
    dx=np.roll(P,-1,axis=1)-np.roll(P,1,axis=1);dy=np.roll(P,-1,axis=0)-np.roll(P,1,axis=0)
    n=np.cross(dx,dy);norm=np.linalg.norm(n,axis=2);nv=np.isfinite(n).all(2)&(norm>1e-10)&(cv2.erode(mask,np.ones((3,3),np.uint8))>0)
    n=n/np.maximum(norm[...,None],1e-10);dirs=vis.camera_rays(uv,p['K'],p['pose'])[:,3:].reshape(360,640,3);dirs/=np.linalg.norm(dirs,axis=2)[...,None]
    flip=(n*dirs).sum(2)>0;n[flip]*=-1
    incidence=-(n*dirs).sum(2);side=nv&(incidence<.5)
    region=np.full((360,640),-1,np.int8);region[labels==1]=0;region[side]=3;region[boundary]=1;region[(labels==1)&near_ring]=2
    return dict(region=region.ravel(),normal=n.reshape(-1,3),normal_valid=nv.ravel(),incidence=incidence.ravel())
