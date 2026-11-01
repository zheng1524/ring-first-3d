"""Read-only historical adapters for the five-camera pilot; no historical main."""
from pathlib import Path
from functools import lru_cache
import os, sys, ast, json, csv, hashlib, datetime, subprocess
SOURCE_ROOT=Path(__file__).resolve().parents[1]; REPO=SOURCE_ROOT.parents[1]
R=Path(os.environ.get('CAMERA_GATE_OUTPUT_ROOT',str(SOURCE_ROOT))).resolve()
assert R==SOURCE_ROOT or R.is_relative_to(SOURCE_ROOT/'runtime'),'reproduction output must stay in this task runtime'
OLD=Path('/home/liu/polyp_research/ring_anchor_3d/experiments')
E1=Path('/home/liu/ring_first_3d_neural_e1/experiments/TASK-NEURAL-E1-PIPELINE-RECOVERY-001')
PART=Path('/home/liu/ring_first_3d_view_partition/experiments/TASK-VIEW-PARTITION-MAST3R-FUSION-001')
LEG=OLD/'ring_first_v13_multisource'
A=REPO/'experiments/TASK-E3-A-SOURCE-AUDIT-AND-PROBLEM-DEFINITION-001'
VENDOR=OLD/'surface_fusion_v3/vendor'
for p in ['config','figures','runtime/tmp']:(R/p).mkdir(parents=True,exist_ok=True)
if R!=SOURCE_ROOT and not (R/'config/protocol.json').exists():(R/'config/protocol.json').write_bytes((SOURCE_ROOT/'config/protocol.json').read_bytes())
os.environ.update(CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',MPLCONFIGDIR=str(R/'runtime/mpl'),TMPDIR=str(R/'runtime/tmp'),XDG_CACHE_HOME=str(R/'runtime/cache'),OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='2')
sys.dont_write_bytecode=True;ACCESSED=set();REUSE=[]
tree=ast.parse((E1/'code/common.py').read_text())
names=['guard','sha','load','clean','save','table','stats','extract','asset','git','protected_state']
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),str(E1/'code/common.py'),'exec'),globals())
_guard=guard
def guard(event,args):
    _guard(event,args)
    if event=='import' and str(args[0]).startswith(('torch','tensorflow','mast3r','lightglue','romatch')):raise PermissionError('CAMERA_GATE_NO_MODEL_RUNTIME')
    if event=='open' and isinstance(args[0],(str,bytes)):
        p=Path(os.fsdecode(args[0])).resolve();s=str(p)
        if p.suffix.lower() in ['.pth','.pt','.ckpt','.safetensors']:raise PermissionError('NO_MODEL_WEIGHTS')
        if any(k in s for k in ['/local_results/glb/','/pointcloud_blocks/','/local_results/scenes/','/local_results/sdf_scene/']):raise PermissionError('NO_FUSED_GEOMETRY_INPUT')
sys.addaudithook(guard)
import numpy as np, cv2, trimesh
from PIL import Image
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation
from scipy.optimize import least_squares
sys.path.insert(0,str(REPO))
from visualization import real_p0_renderer as vis
from visualization.same_camera_scene import SameCameraScene
cv2.setNumThreads(2)
cfg=load(R/'config/protocol.json'); IDS=cfg['scope'];BASE=IDS[:3];NEW=IDS[3:]
CC={c['id']:c for c in load(E1/'provenance/INPUT_ELIGIBILITY.json')['references'] if c['id'] in IDS}
assert list(CC)==IDS
torus_contours=extract(OLD.parent/'scripts/geometry.py',['torus_contours'])['torus_contours']
SIFT=extract(PART/'code/matching.py',['sift'],dict(np=np,cv2=cv2,cfg=lambda:cfg,image=lambda v:np.asarray(Image.open(v['RGB']).convert('RGB'))))['sift']
def short(cid):return cid.removeprefix('G01_004_')
def pair_id(a,b):return short(a)+'__'+short(b)
PAIRS=[(IDS[0],IDS[1]),(IDS[0],IDS[2]),(IDS[1],IDS[2])]+[(a,b) for a in NEW for b in BASE]
def freeze(name,extra=None):
    save('config/'+name,dict(UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),parent_commit=cfg['parent_commit'],code=[asset(p) for p in sorted((SOURCE_ROOT/'code').glob('*.py'))],protocol=asset(R/'config/protocol.json'),extra=extra,GT=False,GPU=0,new_model_forward=0))
@lru_cache(None)
def source(cid):
    c=CC[cid];p=np.load(c['pack']);K=np.asarray(p['K']);T=np.asarray(p['pose']);labels=cv2.imread(c['Mask'],0);rgb=np.asarray(Image.open(c['RGB']).convert('RGB'))
    assert labels.shape==(360,640) and rgb.shape==(360,640,3)
    assert np.array_equal(K,np.array(c['K_after_resize'])) and np.allclose(T,c['c2w_mm'],rtol=0,atol=1e-12)
    assert np.array_equal(labels,p['labels'])
    cam=np.load(c['camera_file']);assert np.allclose(cam['c2w'][c['reference_index']],T,rtol=0,atol=1e-12)
    return dict(id=cid,c=c,K=K,T=T,labels=labels,RGB=rgb)
@lru_cache(None)
def ring():return trimesh.load(CC[IDS[0]]['Ring_CAD']['path'],process=False)
def camera(cid,T=None):
    s=source(cid);return SameCameraScene(ring(),s['K'],s['T'] if T is None else T,(640,360),VENDOR)
def boundary(mask):
    curves,_=cv2.findContours(mask.astype(np.uint8),cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE)
    return np.concatenate([c[:,0,:] for c in curves]).astype(float) if curves else np.empty((0,2))
def at(a,p):
    ij=np.clip(np.floor(np.asarray(p)+.5).astype(int),[0,0],[639,359]);return a[ij[:,1],ij[:,0]]
def inside(p):return np.isfinite(p).all(1)&(p[:,0]>=0)&(p[:,0]<640)&(p[:,1]>=0)&(p[:,1]<360)
def fit_partition(p,q):return (np.floor(p[:,0]/16).astype(int)+3*np.floor(q[:,1]/16).astype(int))%5==0
def select_uniform(ii,n):return ii[np.linspace(0,len(ii)-1,min(n,len(ii)),dtype=int)] if len(ii) else ii
def local_pose(T,x):
    t=T.copy();t[:3,:3]=Rotation.from_rotvec(x[:3]).as_matrix()@T[:3,:3];t[:3,3]=T[:3,3]+x[3:];return t
def skew(v):
    x,y,z=v;return np.array([[0,-z,y],[z,0,-x],[-y,x,0]])
def fundamental(Ka,Ta,Kb,Tb):
    rel=np.linalg.inv(Tb)@Ta;F=np.linalg.inv(Kb).T@skew(rel[:3,3])@rel[:3,:3]@np.linalg.inv(Ka)
    n=np.linalg.norm(F);return F/n if n>1e-14 else np.full((3,3),np.nan)
def sampson(F,p,q,signed=False):
    x=np.c_[p,np.ones(len(p))];y=np.c_[q,np.ones(len(q))];fx=x@F.T;fy=y@F
    d=np.sum(y*fx,1)/np.sqrt(np.maximum(1e-24,np.sum(fx[:,:2]**2,1)+np.sum(fy[:,:2]**2,1)))
    return d if signed else abs(d)
def coverage(p):
    n=len(np.unique((p//cfg['coverage_cell_px']).astype(int),axis=0))
    area=float(cv2.contourArea(cv2.convexHull(np.asarray(p,np.float32))))/(640*360) if len(p)>=3 else 0.
    return dict(cells=n,hull_fraction=area)
def enough(p,q,n):
    a,b=coverage(p),coverage(q)
    return len(p)>=n and min(a['cells'],b['cells'])>=cfg['minimum_occupied_cells_each_image'] and min(a['hull_fraction'],b['hull_fraction'])>=cfg['minimum_hull_fraction_each_image']
def observations_path(a,b,method):return R/'config/matches'/f'{pair_id(a,b)}_{method}.npz'
def match_data(a,b,method):return dict(np.load(observations_path(a,b,method)))
def input_manifest():
    paths={E1/'provenance/INPUT_ELIGIBILITY.json',A/'metrics/E3_CAMERA_QUALIFICATION.csv',PART/'config/rules.json',LEG/'config.json',LEG/'inputs/views.json',PART/'provenance/MATCHING_PAIRS_FROZEN.json'}
    expected={}
    for c in CC.values():
        for k in ['RGB','Mask','pack','source_points','mesh','camera_file']:
            paths.add(Path(c[k]));expected[c[k]]=c['files'][k]['sha256']
        paths.add(Path(c['Ring_CAD']['path']));expected[c['Ring_CAD']['path']]=c['Ring_CAD']['sha256']
    assets=[asset(p,expected=expected.get(str(p))) for p in sorted(paths)]
    assert all(a['status']=='AVAILABLE' and a.get('hash_match',True) for a in assets)
    return assets
