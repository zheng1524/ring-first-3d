"""E2 context: exact E1 AST reuse, with all writes redirected to E2."""
from pathlib import Path
from functools import lru_cache
import os,sys,ast,json,csv,hashlib,datetime,subprocess
R=Path(__file__).resolve().parents[1];REPO=R.parents[1]
E1=Path('/home/liu/ring_first_3d_neural_e1/experiments/TASK-NEURAL-E1-PIPELINE-RECOVERY-001')
E0=Path('/home/liu/ring_first_3d_neural_e0/experiments/TASK-NEURAL-E0-COMPARE-001')
GROW=Path('/home/liu/ring_first_3d_boundary_growth/experiments/TASK-BOUNDARY-GUIDED-SURFACE-GROWTH-001')
PART=Path('/home/liu/ring_first_3d_view_partition/experiments/TASK-VIEW-PARTITION-MAST3R-FUSION-001')
INC=Path('/home/liu/ring_first_3d_incremental/experiments/TASK-PHASED-INCREMENTAL-FUSION-MULTIGROUP-001')
OLD=Path('/home/liu/polyp_research/ring_anchor_3d/experiments');VENDOR=OLD/'surface_fusion_v3/vendor'
MAP=E0/'runtime/map-anything';SDF=E0/'runtime/monosdf_official'
sys.dont_write_bytecode=True
os.environ.update(PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',MPLCONFIGDIR=str(R/'runtime/mpl'),TMPDIR=str(R/'runtime/tmp'),OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='2')
for p in ['config','metrics','provenance','local_results','figures','visualizations','runtime/tmp']:(R/p).mkdir(parents=True,exist_ok=True)
ACCESSED=set();REUSE=[]
_src=(E1/'code/common.py').read_text();_tree=ast.parse(_src)
_names=['guard','sha','load','clean','save','table','stats','extract','asset','git','protected_state','ring','cad_scene','legacy_geometry_namespace']
_nodes=[n for n in _tree.body if isinstance(n,ast.FunctionDef)and n.name in _names];assert len(_nodes)==len(_names)
exec(compile(ast.Module(body=_nodes,type_ignores=[]),str(E1/'code/common.py'),'exec'),globals())
sys.addaudithook(guard)
def deny_weights(event,args):
    if event=='open' and isinstance(args[0],(str,bytes)):
        p=Path(os.fsdecode(args[0]))
        if p.suffix.lower() in ['.safetensors','.ckpt','.pth','.pt','.blend']:raise PermissionError('E2_WEIGHTS_GT_DENIED: '+str(p))
sys.addaudithook(deny_weights)
import numpy as np,cv2,trimesh
from PIL import Image
sys.path.insert(0,str(REPO))
from visualization import real_p0_renderer as vis
from visualization.same_camera_scene import SameCameraScene
unproject=extract(OLD/'ring_first_v1/scripts/common.py',['unproject'])['unproject']
_sdf=extract(E1/'code/sdf_contract.py',['sphere_interval','density'])
sphere_interval=_sdf['sphere_interval'];numpy_density=_sdf['density']
def registry():return load(E1/'provenance/INPUT_ELIGIBILITY.json')
def selected():return load(E1/'provenance/G01_PROPOSED_INPUTS.json')['proposals']
def freeze(name,extra=None):
    save('provenance/'+name,dict(UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),code=[asset(p)for p in sorted((R/'code').glob('*.py'))],config=[asset(p)for p in sorted((R/'config').glob('*.json'))],extra=extra,GT_opened=False,model_forward_N=0,GPU_authorization='NOT_GRANTED'))
def e1_depth(sid,family,mode='points'):return E1/f'local_results/depth_conditions/{sid}_{family}_{mode}.npz'
def verify_selected_assets():
    """Integrity of six reused inputs only; does not rerun E1 source auditing."""
    C={c['id']:c for c in registry()['references']};rows=[]
    for ids in selected().values():
        for cid in ids:
            c=C[cid]
            for role in ['RGB','Mask','pack','mesh','source_points','camera_file']:
                a=c['files'][role];rows.append(asset(a['path'],role,a['sha256']))
            a=c['E1_actual_native'];rows.append(asset(a['path'],'native',a['sha256']))
    assert all(r.get('hash_match')for r in rows),'selected reused asset changed since E1'
    return rows
def require_c2a():
    state=load(R/'metrics/C2A_GATE.json')
    if state['mandatory_CPU_tests_passed']is not True:raise RuntimeError('C2B_BLOCKED_C2A_NOT_PASS')
    return state
