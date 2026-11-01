"""E3-A read-only CPU audit. No LocalField/global fit/model implementation."""
from pathlib import Path
from functools import lru_cache
import os,sys,ast,json,csv,hashlib,datetime,subprocess,importlib.util
R=Path(__file__).resolve().parents[2];REPO=R.parents[1]
OLD=Path('/home/liu/polyp_research/ring_anchor_3d/experiments')
E0=Path('/home/liu/ring_first_3d_neural_e0/experiments/TASK-NEURAL-E0-COMPARE-001')
E1=Path('/home/liu/ring_first_3d_neural_e1/experiments/TASK-NEURAL-E1-PIPELINE-RECOVERY-001')
E2=Path('/home/liu/ring_first_3d_neural_e2/experiments/TASK-NEURAL-E2-C2A-C2B-CONTRACT-001')
E25=Path('/home/liu/ring_first_3d_neural_e2p5/experiments/TASK-NEURAL-E2P5-DEPTH-AND-NEURAL-WIRING-001')
E27=Path('/home/liu/ring_first_3d_neural_e2p7/experiments/TASK-NEURAL-E2P7-BOUNDED-LEARNING-PILOT-001')
INC=Path('/home/liu/ring_first_3d_incremental/experiments/TASK-PHASED-INCREMENTAL-FUSION-MULTIGROUP-001')
PART=Path('/home/liu/ring_first_3d_view_partition/experiments/TASK-VIEW-PARTITION-MAST3R-FUSION-001')
GROW=Path('/home/liu/ring_first_3d_boundary_growth/experiments/TASK-BOUNDARY-GUIDED-SURFACE-GROWTH-001')
SPARSE=Path('/home/liu/ring_first_3d/experiments/TASK-PHASEC-SPARSE-STRETCH-CLEAN-VIS-001')
VENDOR=OLD/'surface_fusion_v3/vendor';EXTRA=OLD/'multigroup_ring_hero_visual_audit_v1'
for d in ['config','metrics','provenance','docs','figures','local_results','runtime/tmp']:(R/d).mkdir(exist_ok=True,parents=True)
os.environ.update(CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',MPLCONFIGDIR=str(R/'runtime/mpl'),TMPDIR=str(R/'runtime/tmp'),
    XDG_CACHE_HOME=str(R/'runtime/cache'),OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='2')
sys.dont_write_bytecode=True;ACCESSED=set();REUSE=[]
names=['guard','sha','load','clean','save','table','stats','extract','asset','git','protected_state','ring','cad_scene']
tree=ast.parse((E1/'code/common.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in names],type_ignores=[]),str(E1/'code/common.py'),'exec'),globals())
_prior_guard=guard
def guard(event,args):
    _prior_guard(event,args)
    if event=='import'and str(args[0]).startswith(('torch','tensorflow','model.network','mapanything.models')):
        raise PermissionError('E3A_NO_MODEL_OR_GPU_IMPORT')
    if event=='open'and isinstance(args[0],(str,bytes))and Path(os.fsdecode(args[0])).suffix.lower()in ['.pt','.pth','.ckpt','.safetensors']:
        raise PermissionError('E3A_NO_CHECKPOINT_IO')
sys.addaudithook(guard)
import numpy as np,cv2,trimesh
from PIL import Image
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree
sys.path.insert(0,str(REPO));from visualization import real_p0_renderer as vis
from visualization.same_camera_scene import SameCameraScene
unproject=extract(OLD/'ring_first_v1/scripts/common.py',['unproject'])['unproject']
_topology=extract(SPARSE/'code/run.py',['source_components','face_components','edge_counts'])
source_components=_topology['source_components'];face_components=_topology['face_components'];edge_counts=_topology['edge_counts']
D=load(E1/'provenance/INPUT_ELIGIBILITY.json');CC={c['id']:c for c in D['references']};VV={v['id']:v for v in D['views']}
points=extract(E0/'code/evidence.py',['points'],dict(globals()))['points']
def cfg():return load(R/'config/AUDIT_PROTOCOL_FROZEN.json')
def scenes():return list(dict.fromkeys(c['scene_id']for c in D['references']))
def eligible(c):return bool(c['source_camera_qualified'])and'UNQUALIFIED'not in c['condition']
@lru_cache(None)
def source(cid):
    c=CC[cid];P,C,F,uv=points(cid);p=np.load(c['pack']);q=np.load(c['cleaned_flags']['path'])
    return dict(c=c,P=P,C=C,F=F,uv=uv.astype(int),K=p['K'],T=p['pose'],depth=p['depth_mm'],labels=p['labels'],clean=q,area=trimesh.triangles.area(P[F]))
def readrows(p):return list(csv.DictReader(Path(p).open()))
def metadata_roles():return load(R/'provenance/SOURCE_ROLES.json')if(R/'provenance/SOURCE_ROLES.json').exists()else{}
def freeze(name,extra=None):
    save('provenance/'+name,dict(UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),code=[asset(p)for p in sorted((R/'code').rglob('*.py'))],
        config=[asset(p)for p in sorted((R/'config').glob('*.json'))],extra=extra,model_forward_N=0,optimizer_step_N=0,GT_opened=False,GPU='NOT_AUTHORIZED_E3A'))
def angle(a,b):return float(np.degrees(np.arccos(np.clip(np.dot(a,b)/np.linalg.norm(a)/np.linalg.norm(b),-1,1))))
@lru_cache(None)
def mesh_scene(cid):
    sys.path.insert(0,str(VENDOR));import open3d as o3d
    s=source(cid);sc=o3d.t.geometry.RaycastingScene(nthreads=2);sc.add_triangles(o3d.core.Tensor(np.asarray(s['P'],np.float32)),o3d.core.Tensor(np.asarray(s['F'],np.uint32)));return sc
@lru_cache(None)
def source_camera(cid):
    s=source(cid);return SameCameraScene(ring(s['c']['ring']),s['K'],s['T'],(640,360),VENDOR)
def cast_mesh(cid,uv):
    sys.path.insert(0,str(VENDOR));import open3d as o3d
    s=source(cid);rays=vis.camera_rays(np.asarray(uv),s['K'],s['T']);h=mesh_scene(cid).cast_rays(o3d.core.Tensor(rays.astype(np.float32)))
    return h['t_hit'].numpy(),h['primitive_ids'].numpy()
